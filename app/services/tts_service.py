"""
TTS Service: Edge TTS integration for audio generation.
"""
import asyncio
import os
from typing import List, Optional

from app.services.models import Exercise

# Voice mapping
VOICE_MAP = {
    "美式英语": "en-US-JennyNeural",
    "英式英语": "en-GB-SoniaNeural",
}

FALLBACK_VOICE = "en-US-JennyNeural"


class TTSService:
    """Text-to-speech synthesis using Edge TTS."""

    def __init__(self, voice: str = "美式英语"):
        self.voice = VOICE_MAP.get(voice, FALLBACK_VOICE)
        self._last_error: Optional[str] = None

    def set_voice(self, voice: str):
        self.voice = VOICE_MAP.get(voice, FALLBACK_VOICE)

    def synthesize_batch(self, exercises: List[Exercise],
                          output_dir: str,
                          speed: str = "正常") -> List[str]:
        """Synthesize audio for all exercises. Single event loop for batch."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_files = []
        try:
            for ex in exercises:
                filepath = self._safe_filename(output_dir, ex)
                try:
                    loop.run_until_complete(
                        self._synthesize_one(ex.sentence, filepath, speed)
                    )
                    audio_files.append(filepath)
                except Exception as e:
                    self._last_error = f"TTS failed for #{ex.index}: {e}"
                    audio_files.append("")
        finally:
            loop.close()
        return audio_files

    def synthesize_one(self, text: str, output_path: str,
                        speed: str = "正常") -> bool:
        """Synthesize a single sentence."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self._synthesize_one(text, output_path, speed)
            )
            loop.close()
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    async def _synthesize_one(self, text: str, output_path: str,
                               speed: str):
        """Internal: run edge-tts for one sentence."""
        import edge_tts

        rate = "+0%" if speed == "正常" else "-30%"
        communicate = edge_tts.Communicate(text, self.voice, rate=rate)
        await communicate.save(output_path)

    def _safe_filename(self, output_dir: str, ex: Exercise) -> str:
        """Generate safe filename for an exercise."""
        os.makedirs(output_dir, exist_ok=True)
        # Use first few words of sentence as filename
        words = ex.sentence.split()[:4]
        name = "_".join(w.lower().strip(".,!?;:'\"") for w in words if w)
        if not name:
            name = f"exercise_{ex.index}"
        return os.path.join(output_dir, f"{ex.index:02d}_{name}.mp3")

    def get_last_error(self) -> Optional[str]:
        return self._last_error
