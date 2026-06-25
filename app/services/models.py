"""
Service interfaces and data models for frontend-backend communication.
Frontend calls these services; backend implements them.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────

class WeaknessType(str, Enum):
    PRONUNCIATION = "pronunciation"
    COLLOCATION = "collocation"
    STRUCTURE = "structure"
    IMPLICATURE = "implicature"

class ExamLevel(str, Enum):
    KET = "KET"
    PET = "PET"
    ZHONGKAO = "中考"
    GAOKAO = "高考"
    IELTS = "雅思"

class VoiceType(str, Enum):
    AMERICAN = "美式英语"
    BRITISH = "英式英语"

class SpeedType(str, Enum):
    NORMAL = "正常"
    SLOW = "慢速"


# ── Data Models ───────────────────────────────────────────────────

@dataclass
class Student:
    id: int = 0
    name: str = ""
    level_tags: List[str] = field(default_factory=list)
    last_practice: str = ""
    practice_count: int = 0

@dataclass
class GenerateRequest:
    student: str = ""
    level: str = ""
    weakness_types: List[str] = field(default_factory=list)
    sentence: str = ""
    details: str = ""
    exercise_count: int = 5

@dataclass
class Exercise:
    index: int = 0
    weakness_type: str = ""
    sentence: str = ""
    translation: str = ""
    target: str = ""
    explanation: str = ""
    phonetic: str = ""
    audio_file: str = ""
    audio_duration: float = 3.0

@dataclass
class GenerationResult:
    session_id: str = ""
    diagnosis: Dict[str, Any] = field(default_factory=dict)
    exercises: List[Exercise] = field(default_factory=list)

@dataclass
class ArchiveSummary:
    session_id: str = ""
    student: str = ""
    level: str = ""
    weakness_types: List[str] = field(default_factory=list)
    sentence: str = ""
    created_at: str = ""
    path: str = ""
    exercise_count: int = 0
    total_duration: float = 0.0

@dataclass
class ArchiveDetail:
    summary: Optional[ArchiveSummary] = None
    diagnosis: Dict[str, Any] = field(default_factory=dict)
    exercises: List[Exercise] = field(default_factory=list)

@dataclass
class ArchiveFilter:
    student: Optional[str] = None
    level: Optional[str] = None
    weakness_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 20

@dataclass
class Config:
    api_key: str = ""
    voice: str = "美式英语"
    default_count: int = 5
    default_speed: str = "正常"
    theme: str = "浅色"
    default_save_dir: str = ""

@dataclass
class LevelStat:
    level: str = ""
    count: int = 0

@dataclass
class WeaknessStat:
    weakness: str = ""
    label: str = ""
    count: int = 0

@dataclass
class DayStat:
    date: str = ""
    count: int = 0

@dataclass
class StatsOverview:
    total_practices: int = 0
    total_students: int = 0
    total_archives: int = 0
