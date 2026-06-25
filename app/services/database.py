"""
Database service: SQLite operations for all application data.
"""
import sqlite3
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from app.services.models import (
    Student, ArchiveSummary, ArchiveDetail, Exercise,
    GenerateRequest, Config, StatsOverview, LevelStat,
    WeaknessStat, DayStat
)

DB_PATH = None


def set_db_path(path: str):
    global DB_PATH
    DB_PATH = path


def get_db_path() -> str:
    if DB_PATH:
        return DB_PATH
    # Default: next to app or in app data dir
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "listening_app.db")


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Vocabulary Queries ────────────────────────────────────────

def get_words_by_level(level: str) -> List[Dict]:
    """Get all words for a given exam level."""
    with get_db() as db:
        rows = db.execute(
            "SELECT word, phonetic, pos, meaning, source_detail, category "
            "FROM words WHERE level = ? ORDER BY word", (level,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_collocations_by_level(level: str) -> List[Dict]:
    """Get all collocations for a given level."""
    with get_db() as db:
        rows = db.execute(
            "SELECT collocation, meaning, phonetic, example, category "
            "FROM collocations WHERE level = ? ORDER BY collocation", (level,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_match_words(sentence: str) -> List[Dict]:
    """Find which words in a sentence are in our database."""
    import re
    words = set(re.findall(r"[a-zA-Z'-]+", sentence.lower()))
    if not words:
        return []

    placeholders = ",".join("?" for _ in words)
    with get_db() as db:
        rows = db.execute(
            f"SELECT word, level, phonetic, meaning FROM words "
            f"WHERE LOWER(word) IN ({placeholders})",
            list(words)
        ).fetchall()
        return [dict(r) for r in rows]


def get_exercises_by_level_type(level: str, problem_type_id: int = 4,
                                 limit: int = 3) -> List[Dict]:
    """Get sample exercises for few-shot prompting."""
    with get_db() as db:
        rows = db.execute(
            "SELECT category, dialogue, pragmatic_clues, "
            "implied_q, implied_options "
            "FROM exercises WHERE level = ? AND problem_type_id = ? "
            "ORDER BY RANDOM() LIMIT ?",
            (level, problem_type_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def get_level_info(level: str) -> Optional[Dict]:
    """Get level description."""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM level_info WHERE level = ?", (level,)
        ).fetchone()
        return dict(row) if row else None


def search_words(keyword: str, level: Optional[str] = None,
                 limit: int = 20) -> List[Dict]:
    """Search words by keyword."""
    with get_db() as db:
        if level:
            rows = db.execute(
                "SELECT word, phonetic, meaning, level FROM words "
                "WHERE word LIKE ? AND level = ? LIMIT ?",
                (f"%{keyword}%", level, limit)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT word, phonetic, meaning, level FROM words "
                "WHERE word LIKE ? LIMIT ?",
                (f"%{keyword}%", limit)
            ).fetchall()
        return [dict(r) for r in rows]


# ── Student CRUD ─────────────────────────────────────────────

def get_all_students() -> List[Student]:
    with get_db() as db:
        rows = db.execute(
            "SELECT id, name FROM students "
            "ORDER BY (SELECT MAX(created_at) FROM practice_records "
            "          WHERE practice_records.student_id = students.id) "
            "DESC NULLS LAST, name"
        ).fetchall()
        students = []
        for r in rows:
            # Get level tags from practice records (most recent first)
            tags = db.execute(
                "SELECT DISTINCT level FROM practice_records "
                "WHERE student_id = ? AND level IS NOT NULL "
                "ORDER BY created_at DESC LIMIT 3",
                (r["id"],)
            ).fetchall()
            # Get last practice time
            last = db.execute(
                "SELECT created_at FROM practice_records "
                "WHERE student_id = ? ORDER BY created_at DESC LIMIT 1",
                (r["id"],)
            ).fetchone()
            # Get count
            cnt = db.execute(
                "SELECT COUNT(*) FROM practice_records "
                "WHERE student_id = ?", (r["id"],)
            ).fetchone()[0]
            students.append(Student(
                id=r["id"], name=r["name"],
                level_tags=[t["level"] for t in tags if t["level"]],
                last_practice=last["created_at"][:10] if last else "",
                practice_count=cnt
            ))
        return students


def add_student(name: str) -> Student:
    with get_db() as db:
        cur = db.execute("INSERT INTO students (name) VALUES (?)", (name,))
        return Student(id=cur.lastrowid, name=name)


def delete_student(student_id: int) -> bool:
    with get_db() as db:
        db.execute("DELETE FROM students WHERE id = ?", (student_id,))
        return True


def get_student_by_name(name: str) -> Optional[Student]:
    with get_db() as db:
        row = db.execute(
            "SELECT id, name FROM students WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return Student(id=row["id"], name=row["name"])
        return None


# ── Practice Records ─────────────────────────────────────────

def save_practice_record(student_id: int, req: GenerateRequest,
                          session_id: str, output_json: str,
                          audio_dir: str) -> int:
    """Save a practice record with multi-select weakness types. Returns record id."""
    import json as _json
    weakness_types_json = _json.dumps(req.weakness_types, ensure_ascii=False)

    with get_db() as db:
        # Ensure weakness_types column exists
        try:
            db.execute("ALTER TABLE practice_records ADD COLUMN weakness_types TEXT")
        except Exception:
            pass  # Column already exists

        # Map first weakness type to problem_type_id for backward compatibility
        type_id_map = {"pronunciation": 1, "collocation": 2,
                       "structure": 3, "implicature": 4}
        first_type = req.weakness_types[0] if req.weakness_types else "pronunciation"
        problem_type = type_id_map.get(first_type, 1)

        cur = db.execute(
            "INSERT INTO practice_records "
            "(student_id, level, problem_type_id, input_sentence, "
            "input_details, output_json, audio_dir, weakness_types) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (student_id, req.level, problem_type,
             req.sentence, req.details, output_json,
             audio_dir, weakness_types_json)
        )
        return cur.lastrowid


def get_practice_records(student_id: Optional[int] = None,
                          level: Optional[str] = None,
                          limit: int = 50) -> List[Dict]:
    """Get practice records for listing."""
    with get_db() as db:
        sql = ("SELECT pr.*, s.name as student_name "
               "FROM practice_records pr "
               "LEFT JOIN students s ON pr.student_id = s.id "
               "WHERE 1=1 ")
        params = []
        if student_id:
            sql += "AND pr.student_id = ? "
            params.append(student_id)
        if level:
            sql += "AND pr.level = ? "
            params.append(level)
        sql += "ORDER BY pr.created_at DESC LIMIT ?"
        params.append(limit)
        rows = db.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


# ── Statistics ────────────────────────────────────────────────

def get_stats_overview() -> StatsOverview:
    with get_db() as db:
        total_p = db.execute("SELECT COUNT(*) FROM practice_records").fetchone()[0]
        total_s = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        # Approximate archives by counting practice records with audio_dir
        total_a = db.execute(
            "SELECT COUNT(*) FROM practice_records "
            "WHERE audio_dir IS NOT NULL"
        ).fetchone()[0]
        return StatsOverview(
            total_practices=total_p,
            total_students=total_s,
            total_archives=total_a,
        )


def get_level_stats() -> List[LevelStat]:
    with get_db() as db:
        rows = db.execute(
            "SELECT level, COUNT(*) as cnt FROM practice_records "
            "WHERE level IS NOT NULL "
            "GROUP BY level ORDER BY cnt DESC"
        ).fetchall()
        return [LevelStat(level=r["level"], count=r["cnt"]) for r in rows]


def get_weakness_stats() -> List[WeaknessStat]:
    """Get stats by problem type."""
    with get_db() as db:
        rows = db.execute(
            "SELECT pr.problem_type_id, pt.label, COUNT(*) as cnt "
            "FROM practice_records pr "
            "LEFT JOIN problem_types pt ON pr.problem_type_id = pt.id "
            "WHERE pr.problem_type_id IS NOT NULL "
            "GROUP BY pr.problem_type_id ORDER BY cnt DESC"
        ).fetchall()
        return [
            WeaknessStat(weakness=f"type_{r['problem_type_id']}",
                          label=r["label"] or "未知",
                          count=r["cnt"])
            for r in rows
        ]


def get_daily_trend(days: int = 30) -> List[DayStat]:
    with get_db() as db:
        rows = db.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as cnt "
            "FROM practice_records "
            "WHERE created_at >= DATE('now', ? || ' days') "
            "GROUP BY day ORDER BY day",
            (f"-{days}",)
        ).fetchall()
        return [DayStat(date=r["day"], count=r["cnt"]) for r in rows]
