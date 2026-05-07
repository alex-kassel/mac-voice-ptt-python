from __future__ import annotations


class WhisperTranscriber:
    def __init__(self, model_name: str, language: str | None = None) -> None:
        self.model_name = model_name
        self.language = language
        self._model = None

    def transcribe(self, audio_path: str) -> str:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self.model_name, device="auto", compute_type="int8")

        segments, _info = self._model.transcribe(audio_path, language=self.language, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
