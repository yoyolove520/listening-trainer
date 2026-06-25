"""
Generate service: orchestrates AI diagnosis + TTS + archive storage.
"""
import json
import os
import threading
from typing import Optional

from app.services.models import GenerateRequest, GenerationResult, Exercise
from app.services.ai_service import AIService, set_api_key
from app.services.tts_service import TTSService
from app.services import storage as store
from app.services import database as db


class GenerateService:
    """Full generation pipeline: AI → TTS → Archive → DB."""

    def __init__(self):
        self.ai = AIService()
        self.tts = TTSService()
        self._running = False
        self._cancel_flag = False
        self._last_error: Optional[str] = None

        # Load API key from config
        config = store.load_config()
        if config.get("api_key"):
            set_api_key(config["api_key"])
        if config.get("voice"):
            self.tts.set_voice(config["voice"])

    def generate(self, req: GenerateRequest) -> GenerationResult:
        """Run the full generation pipeline."""
        self._running = True
        self._cancel_flag = False
        self._last_error = None

        try:
            # Step 1: AI generates diagnosis + exercises
            result = self.ai.generate(req)
            if self._cancel_flag:
                self._running = False
                return result

            # Step 2: Ensure student exists in DB
            student = db.get_student_by_name(req.student)
            if not student:
                student = db.add_student(req.student)

            # Step 3: Build archive path and save files
            base_dir = store.get_default_save_dir()
            archive_dir = store.build_archive_path(
                base_dir, req.level, req.student, req.weakness_types
            )

            # Step 4: Synthesize audio
            audio_files = self.tts.synthesize_batch(
                result.exercises, archive_dir
            )
            if self._cancel_flag:
                self._running = False
                return result

            # Update exercises with audio info (full path)
            for i, ex in enumerate(result.exercises):
                if i < len(audio_files) and audio_files[i]:
                    ex.audio_file = audio_files[i]  # full path

            # Step 5: Save session.json and text files
            store.save_session_json(archive_dir, req, result, audio_files)
            store.save_diagnosis_txt(archive_dir, result)
            for i, ex in enumerate(result.exercises):
                store.save_exercise_txt(archive_dir, ex, i + 1)

            # Step 6: Save practice record to DB
            output_json = json.dumps({
                "diagnosis": result.diagnosis,
                "exercises": [{
                    "sentence": e.sentence, "translation": e.translation,
                    "target": e.target, "explanation": e.explanation,
                    "weakness_type": e.weakness_type,
                } for e in result.exercises],
            }, ensure_ascii=False)

            db.save_practice_record(
                student_id=student.id,
                req=req,
                session_id=result.session_id,
                output_json=output_json,
                audio_dir=archive_dir,
            )

            self._running = False
            return result

        except Exception as e:
            self._last_error = str(e)
            self._running = False
            return self._empty_result(req)

    def cancel(self) -> bool:
        self._cancel_flag = True
        self._running = False
        return True

    def is_running(self) -> bool:
        return self._running

    def get_last_error(self) -> Optional[str]:
        return self._last_error

    def _empty_result(self, req: GenerateRequest) -> GenerationResult:
        return GenerationResult(
            session_id="error",
            diagnosis={"error": self._last_error or "生成失败"},
            exercises=[],
        )
