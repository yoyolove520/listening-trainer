"""
Configuration service: read/write config.json and apply settings.
"""
from app.services.models import Config
from app.services import storage as store
from app.services.ai_service import set_api_key
from app.services.tts_service import TTSService


class ConfigService:
    """Application configuration management."""

    def __init__(self):
        self._data = store.load_config()
        # Apply saved API key
        if self._data.get("api_key"):
            set_api_key(self._data["api_key"])

    def get_all(self) -> Config:
        return Config(
            api_key=self._data.get("api_key", ""),
            voice=self._data.get("voice", "美式英语"),
            default_count=self._data.get("default_count", 5),
            default_speed=self._data.get("default_speed", "正常"),
            theme=self._data.get("theme", "浅色"),
            default_save_dir=self._data.get("default_save_dir", ""),
        )

    def save(self, config: Config) -> bool:
        data = {
            "api_key": config.api_key,
            "voice": config.voice,
            "default_count": config.default_count,
            "default_speed": config.default_speed,
            "theme": config.theme,
            "default_save_dir": config.default_save_dir,
            "window_geometry": self._data.get("window_geometry", ""),
        }
        result = store.save_config(data)
        if result:
            self._data = data
            # Apply settings
            if config.api_key:
                set_api_key(config.api_key)
        return result

    def verify_api_key(self, key: str) -> dict:  # returns {"valid": bool, "message": str}
        """Verify DeepSeek API key by making a test call."""
        if not key or not key.strip():
            return {"valid": False, "message": "请输入 API Key"}
        if len(key.strip()) < 10:
            return {"valid": False, "message": "API Key 格式不正确（长度不足）"}
        # Save temporarily for verification
        from app.services.ai_service import _call_deepseek
        old_key = self._data.get("api_key", "")
        set_api_key(key.strip())

        try:
            messages = [
                {"role": "user",
                 "content": "Respond with exactly: OK"}
            ]
            from app.services.ai_service import _call_deepseek
            result = _call_deepseek(messages, temperature=0.1, max_tokens=10)
            set_api_key(old_key)  # Restore old key
            if result:
                return {"valid": True, "message": "密钥有效，API 连接成功"}
            return {"valid": False, "message": "API 返回为空，请检查密钥"}
        except Exception as e:
            set_api_key(old_key)
            err_msg = str(e)
            if "401" in err_msg or "unauthorized" in err_msg.lower():
                return {"valid": False, "message": "密钥无效，请检查后重试"}
            if "timeout" in err_msg.lower():
                return {"valid": False, "message": "连接超时，请检查网络"}
            return {"valid": False, "message": f"验证失败: {err_msg[:50]}"}

    def get_balance(self, key_override: str = "") -> dict:
        """Query DeepSeek API balance. Returns {"available": bool, "amount": str}."""
        key = key_override or self._data.get("api_key", "")
        if not key or len(key) < 10:
            return {"available": False, "amount": "未配置"}
        from urllib.request import Request, urlopen
        from urllib.error import URLError
        import json
        try:
            req = Request("https://api.deepseek.com/user/balance",
                          headers={"Authorization": f"Bearer {key}",
                                   "Accept": "application/json"})
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                bal = data.get("balance_infos", [])
                if bal:
                    total = sum(float(b.get("total_balance", 0)) for b in bal)
                    return {"available": True, "amount": f"¥{total:.2f}"}
                return {"available": True, "amount": "未知"}
        except Exception as e:
            err = str(e)
            if "401" in err:
                return {"available": False, "amount": "不支持"}
            return {"available": False, "amount": "查询失败"}
