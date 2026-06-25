"""
AI Service: DeepSeek API integration for diagnosis and exercise generation.
No hardcoded fallback data — API errors propagate cleanly.
"""
import json
import re
from typing import List, Optional, Dict
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from app.services.models import GenerateRequest, Exercise, GenerationResult
from app.services import database as db


DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = ""  # Set via config


def set_api_key(key: str):
    global API_KEY
    API_KEY = key


def _build_system_prompt(req: GenerateRequest) -> str:
    """Build the system prompt based on weakness types and level."""
    level_info = db.get_level_info(req.level)
    level_desc = level_info["description"] if level_info else f"{req.level}级别"

    # Get vocabulary scope
    word_count = len(db.get_words_by_level(req.level))
    coll_count = len(db.get_collocations_by_level(req.level))

    prompt_parts = [
        f"你是一位专业英语听力教师。等级限制：{req.level}（{level_desc}，词汇量约{word_count}词）。",
        "",
        "## 任务",
        "分析用户提供的句子在听力理解中的难点，然后生成针对性练习句子。",
        "生成的句子必须严格控制在当前等级的词汇范围内，不可超纲。",
        "",
        f"## 薄弱类型分析",
    ]

    if "pronunciation" in req.weakness_types:
        prompt_parts.append("""
### 单词发音听不懂
分析维度：
1. 连读(liaison)：如 "an apple" → /əˈnæpl/
2. 弱读(weak form)：如 "I can do it" → /aɪ kən duː ɪt/
3. 同化(assimilation)：如 "don't you" → /ˈdəʊntʃuː/
4. 省音(elision)：如 "government" → /ˈɡʌvnmənt/
""")

    if "collocation" in req.weakness_types:
        prompt_parts.append(f"""
### 固定搭配听不出来
分析常见的固定搭配、短语动词、习惯表达。
当前等级有 {coll_count} 条固定搭配数据可供参考。
""")

    if "structure" in req.weakness_types:
        prompt_parts.append("""
### 句式结构没听懂
分析句子结构（简单句/复合句/倒装/从句等），进行句子成分拆解。
""")

    if "implicature" in req.weakness_types:
        # Get few-shot examples
        examples = db.get_exercises_by_level_type(req.level, 4, 2)
        if examples:
            prompt_parts.append(f"""
### 言外之意未获取到
参考以下同类题型示例（来自真实考题）：
{json.dumps(examples, ensure_ascii=False, indent=2)}
""")
        else:
            prompt_parts.append("""
### 言外之意未获取到
分析语用策略：间接请求、隐含否定、含蓄拒绝、隐含态度等。
""")

    prompt_parts.append("""
## 输出格式
严格以下面的JSON格式输出，不要包含任何其他文字。diagnosis是一个对象，key为薄弱类型：

{
  "diagnosis": {
    "pronunciation": {
      "summary": "分析总结文本",
      "details": [
        {"item": "具体难点", "explanation": "解释说明"}
      ]
    },
    "collocation": {
      "summary": "分析总结文本",
      "details": [
        {"item": "短语", "explanation": "说明"}
      ]
    }
  },
  "exercises": [
    {
      "sentence": "练习句子（必须与用户原句同类难度）",
      "translation": "中文翻译",
      "weakness_type": "对应类型",
      "target": "目标（发音词/搭配/结构名）",
      "phonetic": "音标（发音类型需要）",
      "explanation": "为什么这句能帮助训练"
    }
  ]
}
""")

    return "\n".join(prompt_parts)


def _build_user_prompt(req: GenerateRequest) -> str:
    prompt = f"原句：{req.sentence}\n"
    prompt += f"等级：{req.level}\n"
    prompt += f"薄弱类型：{'、'.join(req.weakness_types)}\n"
    if req.details:
        prompt += f"补充信息：{req.details}\n"
    prompt += f"\n请生成 {req.exercise_count} 个练习句。"
    return prompt


def _call_deepseek(messages: List[Dict], temperature: float = 0.7,
                   max_tokens: int = 2048) -> Optional[str]:
    """Call DeepSeek API and return response text."""
    if not API_KEY:
        raise RuntimeError("API 密钥未配置，请在设置页面填入 DeepSeek API Key")

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }).encode("utf-8")

    req = Request(DEEPSEEK_API_URL, data=payload,
                  headers={
                      "Content-Type": "application/json",
                      "Authorization": f"Bearer {API_KEY}",
                  })

    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.code >= 400 else ""
        raise RuntimeError(f"DeepSeek API error {e.code}: {error_body}")
    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"API response parse error: {e}")


def _parse_response(text: str) -> Optional[Dict]:
    """Extract JSON from API response, handling markdown code blocks."""
    if not text:
        return None

    # Try to find JSON in ```json ... ``` blocks first
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        text = match.group(1)

    # Try to parse
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try finding first { and last }
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return None
        return None


class AIService:
    """AI diagnosis and exercise generation via DeepSeek. No mock fallback."""

    def __init__(self):
        self._last_error: Optional[str] = None

    def generate(self, req: GenerateRequest) -> GenerationResult:
        """Generate diagnosis and exercises via DeepSeek API.

        Returns a result with empty exercises list on failure.
        Call get_last_error() for the error message.
        """
        messages = [
            {"role": "system", "content": _build_system_prompt(req)},
            {"role": "user", "content": _build_user_prompt(req)},
        ]

        try:
            text = _call_deepseek(messages)
            if not text:
                self._last_error = "API 返回为空"
                return GenerationResult(session_id="error", exercises=[])

            parsed = _parse_response(text)
            if not parsed:
                self._last_error = "API 返回格式解析失败"
                return GenerationResult(session_id="error", exercises=[])

            return self._parse_result(parsed, req)
        except RuntimeError as e:
            self._last_error = str(e)
            return GenerationResult(session_id="error", exercises=[])
        except Exception as e:
            self._last_error = f"未知错误: {str(e)[:60]}"
            return GenerationResult(session_id="error", exercises=[])

    def _parse_result(self, parsed: Dict,
                       req: GenerateRequest) -> GenerationResult:
        raw_diagnosis = parsed.get("diagnosis", {})
        exercises_raw = parsed.get("exercises", [])

        # Normalize diagnosis
        diagnosis = {}
        if "analysis" in raw_diagnosis:
            for item in raw_diagnosis["analysis"]:
                if isinstance(item, dict) and "type" in item:
                    diag_type = item["type"]
                    diagnosis[diag_type] = {
                        "summary": item.get("summary", ""),
                        "details": item.get("details", []),
                    }
        else:
            diagnosis = raw_diagnosis

        exercises = []
        for i, ex in enumerate(exercises_raw[:req.exercise_count]):
            exercises.append(Exercise(
                index=i + 1,
                weakness_type=ex.get("weakness_type", req.weakness_types[0] if req.weakness_types else ""),
                sentence=ex.get("sentence", ""),
                translation=ex.get("translation", ""),
                target=ex.get("target", ""),
                phonetic=ex.get("phonetic", ""),
                explanation=ex.get("explanation", ""),
                audio_duration=3.0,
            ))

        return GenerationResult(
            session_id=f"ds_{id(req)}",
            diagnosis=diagnosis,
            exercises=exercises,
        )

    def get_last_error(self) -> Optional[str]:
        return self._last_error
