"""
Archive service: list, view, delete practice archives using DB + filesystem.
"""
import os
from typing import List, Optional

from app.services.models import (
    ArchiveSummary, ArchiveDetail, Exercise, ArchiveFilter
)
from app.services import storage as store
from app.services import database as db


class ArchiveService:
    """Manage practice archives via file system and database."""

    def list_archives(self, filter: Optional[ArchiveFilter] = None) -> List[ArchiveSummary]:
        """List archives matching filter."""
        base_dir = store.get_default_save_dir()

        student = filter.student if filter and filter.student != "全部" else None
        level = filter.level if filter and filter.level != "全部" else None

        archives = store.list_archives(base_dir, student, level)

        # Additional filtering
        if filter:
            if filter.weakness_type and filter.weakness_type != "全部":
                archives = [a for a in archives
                            if filter.weakness_type in a.weakness_types]
            if filter.date_from:
                archives = [a for a in archives
                            if a.created_at[:10] >= filter.date_from]
            if filter.date_to:
                archives = [a for a in archives
                            if a.created_at[:10] <= filter.date_to]
            if filter.keyword:
                kw = filter.keyword.lower()
                archives = [a for a in archives if kw in a.sentence.lower()]

        return archives

    def get_detail(self, session_id: str) -> Optional[ArchiveDetail]:
        """Get full archive detail by scanning directories."""
        base_dir = store.get_default_save_dir()
        # Scan all archives for matching session_id
        for level_dir in os.listdir(base_dir):
            level_path = os.path.join(base_dir, level_dir)
            if not os.path.isdir(level_path):
                continue
            for student_dir in os.listdir(level_path):
                student_path = os.path.join(level_path, student_dir)
                if not os.path.isdir(student_path):
                    continue
                for session_dir in os.listdir(student_path):
                    session_path = os.path.join(student_path, session_dir)
                    if not os.path.isdir(session_path):
                        continue

                    data = store.load_session_json(session_path)
                    if data and data.get("session_id") == session_id:
                        summary = ArchiveSummary(
                            session_id=session_id,
                            student=data.get("student", student_dir),
                            level=level_dir,
                            weakness_types=data.get("weakness_types", []),
                            sentence=data.get("input", {}).get("sentence", ""),
                            created_at=data.get("created_at", ""),
                            path=session_path.replace("\\", "/"),
                            exercise_count=len(data.get("exercises", [])),
                        )
                        exercises = []
                        for ex_data in data.get("exercises", []):
                            exercises.append(Exercise(
                                index=ex_data.get("index", 0),
                                weakness_type=ex_data.get("type", ""),
                                sentence=ex_data.get("sentence", ""),
                                translation=ex_data.get("translation", ""),
                                target=ex_data.get("target", ""),
                                phonetic=ex_data.get("phonetic", ""),
                                explanation=ex_data.get("explanation", ""),
                                audio_file=ex_data.get("audio_file", ""),
                                audio_duration=ex_data.get("audio_duration", 0),
                            ))
                        return ArchiveDetail(
                            summary=summary,
                            diagnosis=data.get("diagnosis", {}),
                            exercises=exercises,
                        )
        return None

    def delete(self, session_id: str) -> bool:
        """Delete archive by session_id."""
        base_dir = store.get_default_save_dir()
        for level_dir in os.listdir(base_dir):
            level_path = os.path.join(base_dir, level_dir)
            if not os.path.isdir(level_path):
                continue
            for student_dir in os.listdir(level_path):
                student_path = os.path.join(level_path, student_dir)
                if not os.path.isdir(student_path):
                    continue
                for session_dir in os.listdir(student_path):
                    session_path = os.path.join(student_path, session_dir)
                    data = store.load_session_json(session_path)
                    if data and data.get("session_id") == session_id:
                        return store.delete_archive(session_path)
        return False

    def add_archive(self, summary: ArchiveSummary):
        """Add is handled by generate_service; this is for testing."""
        pass
