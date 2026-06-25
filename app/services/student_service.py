"""
Student service: CRUD operations via database.
"""
from typing import List, Optional
from app.services.models import Student
from app.services import database as db


class StudentService:
    """Manage student records using SQLite database."""

    def get_all(self) -> List[Student]:
        return db.get_all_students()

    def get_by_name(self, name: str) -> Optional[Student]:
        return db.get_student_by_name(name)

    def add(self, name: str) -> Student:
        existing = db.get_student_by_name(name)
        if existing:
            return existing
        return db.add_student(name)

    def delete(self, student_id: int) -> bool:
        return db.delete_student(student_id)
