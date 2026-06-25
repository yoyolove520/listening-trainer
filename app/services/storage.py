"""
Storage service: file system operations for archives, sessions, and config.
"""
import json
import os
import shutil
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path

from app.services.models import (
    GenerateRequest, GenerationResult, Exercise,
    ArchiveSummary, ArchiveDetail
)


# ── Config Management ────────────────────────────────────────

def get_config_dir() -> str:
    """Get application data directory."""
    if os.name == "nt":  # Windows
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif os.name == "posix":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.path.expanduser("~/.local/share")
    path = os.path.join(base, "ListeningTrainer")
    os.makedirs(path, exist_ok=True)
    return path


def get_config_path() -> str:
    return os.path.join(get_config_dir(), "config.json")


def load_config() -> dict:
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "api_key": "",
        "voice": "美式英语",
        "default_count": 5,
        "default_speed": "正常",
        "theme": "浅色",
        "default_save_dir": "",
        "window_geometry": "",
        "student_history": [],
    }


def save_config(config: dict) -> bool:
    try:
        with open(get_config_path(), "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


# ── Archive Management ───────────────────────────────────────

def get_default_save_dir() -> str:
    config = load_config()
    if config.get("default_save_dir"):
        return config["default_save_dir"]
    # Default to Documents/ListeningTrainer
    docs = os.path.join(os.path.expanduser("~"), "Documents", "ListeningTrainer")
    os.makedirs(docs, exist_ok=True)
    return docs


def build_archive_path(base_dir: str, level: str, student: str,
                        weakness_types: List[str]) -> str:
    """Build the 4-level archive directory path. Each call creates a unique folder."""
    from app.theme import WEAKNESS_LABELS
    # Level 1: exam level
    level_dir = os.path.join(base_dir, level)
    # Level 2: student name
    student_dir = os.path.join(level_dir, student)
    # Level 3: date + problem types (Chinese labels) + unique suffix
    date_str = datetime.now().strftime("%Y-%m-%d")
    type_labels = [WEAKNESS_LABELS.get(wt, wt) for wt in weakness_types]
    type_str = "+".join(type_labels)
    ts = datetime.now().strftime("%H%M%S")
    session_dir = os.path.join(student_dir, f"{date_str}_{type_str}_{ts}")

    os.makedirs(session_dir, exist_ok=True)
    return session_dir


def save_session_json(session_dir: str, req: GenerateRequest,
                       result: GenerationResult, audio_files: List[str]) -> str:
    """Save session.json with complete generation data."""
    # Build exercise list with audio paths
    exercises_json = []
    for i, ex in enumerate(result.exercises):
        audio_file = os.path.basename(audio_files[i]) if i < len(audio_files) and audio_files[i] else ""
        exercises_json.append({
            "index": ex.index,
            "type": ex.weakness_type,
            "sentence": ex.sentence,
            "translation": ex.translation,
            "target": ex.target,
            "phonetic": ex.phonetic,
            "explanation": ex.explanation,
            "audio_file": audio_file,
            "audio_duration": ex.audio_duration,
        })

    session = {
        "session_id": result.session_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "student": req.student,
        "level": req.level,
        "weakness_types": req.weakness_types,
        "input": {
            "sentence": req.sentence,
            "details": req.details,
            "exercise_count": req.exercise_count,
        },
        "diagnosis": result.diagnosis,
        "exercises": exercises_json,
        "status": "success",
    }

    filepath = os.path.join(session_dir, "session.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)
    return filepath


def save_diagnosis_txt(session_dir: str, result: GenerationResult) -> str:
    """Save diagnosis analysis as plain text."""
    lines = ["=" * 50, "诊断分析", "=" * 50, ""]

    diagnosis = result.diagnosis
    if isinstance(diagnosis, dict):
        for key, analysis in diagnosis.items():
            lines.append(f"【{key}】")
            if isinstance(analysis, dict):
                for k, v in analysis.items():
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                for ik, iv in item.items():
                                    lines.append(f"  {ik}: {iv}")
                            else:
                                lines.append(f"  {item}")
                    elif isinstance(v, str) and v:
                        lines.append(f"  {v}")
            lines.append("")

    filepath = os.path.join(session_dir, "诊断分析.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filepath


def save_exercise_txt(session_dir: str, ex: Exercise, index: int) -> str:
    """Save single exercise as text file."""
    lines = [
        f"句子: {ex.sentence}",
        f"翻译: {ex.translation}",
        f"类型: {ex.weakness_type}",
        "",
    ]
    if ex.target:
        lines.append(f"目标: {ex.target}")
    if ex.phonetic:
        lines.append(f"音标: {ex.phonetic}")
    if ex.explanation:
        lines.append(f"解析: {ex.explanation}")

    filepath = os.path.join(session_dir, f"{index:02d}_句子解析.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filepath


def delete_archive(session_dir: str) -> bool:
    """Delete an archive directory and all its contents."""
    if os.path.exists(session_dir):
        try:
            shutil.rmtree(session_dir)
            return True
        except OSError:
            return False
    return False


def list_archives(base_dir: str, student: Optional[str] = None,
                   level: Optional[str] = None) -> List[ArchiveSummary]:
    """Scan archive directories and return summaries."""
    archives = []
    if not os.path.exists(base_dir):
        return archives

    try:
        for level_dir in os.listdir(base_dir):
            level_path = os.path.join(base_dir, level_dir)
            if not os.path.isdir(level_path):
                continue
            if level and level_dir != level:
                continue

            for student_dir in os.listdir(level_path):
                student_path = os.path.join(level_path, student_dir)
                if not os.path.isdir(student_path):
                    continue
                if student and student_dir != student:
                    continue

                for session_dir in os.listdir(student_path):
                    session_path = os.path.join(student_path, session_dir)
                    if not os.path.isdir(session_path):
                        continue

                    # Read session.json if exists
                    session_file = os.path.join(session_path, "session.json")
                    if os.path.exists(session_file):
                        try:
                            with open(session_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            archives.append(ArchiveSummary(
                                session_id=data.get("session_id", session_dir),
                                student=data.get("student", student_dir),
                                level=level_dir,
                                weakness_types=data.get("weakness_types", []),
                                sentence=data.get("input", {}).get("sentence", ""),
                                created_at=data.get("created_at", ""),
                                path=session_path.replace("\\", "/"),
                                exercise_count=len(data.get("exercises", [])),
                            ))
                        except (json.JSONDecodeError, IOError):
                            # Fallback: directory name only
                            archives.append(ArchiveSummary(
                                session_id=session_dir,
                                student=student_dir,
                                level=level_dir,
                                path=session_path.replace("\\", "/"),
                                created_at=session_dir[:16] if len(session_dir) >= 16 else "",
                            ))
    except OSError:
        pass

    return sorted(archives, key=lambda a: a.created_at, reverse=True)


def load_session_json(session_dir: str) -> Optional[dict]:
    """Load session.json from archive directory."""
    path = os.path.join(session_dir, "session.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None
