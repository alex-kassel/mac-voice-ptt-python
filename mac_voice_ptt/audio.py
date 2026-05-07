from __future__ import annotations

import logging
import os
import queue
import tempfile
import threading
import time
from dataclasses import dataclass
from typing import Any


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecordingResult:
    path: str
    duration_seconds: float


class AudioRecorder:
    def __init__(self, sample_rate: int, channels: int, max_record_seconds: int) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.max_record_seconds = max_record_seconds
        self._audio_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._writer_thread: threading.Thread | None = None
        self._stream = None
        self._sound_file = None
        self._started_at: float | None = None
        self._path: str | None = None

    def start(self) -> None:
        import sounddevice as sd
        import soundfile as sf

        temp_file = tempfile.NamedTemporaryFile(prefix="mac-voice-ptt-", suffix=".wav", delete=False)
        temp_file.close()
        self._path = temp_file.name
        self._started_at = time.monotonic()
        self._stop_event.clear()
        self._sound_file = sf.SoundFile(self._path, mode="w", samplerate=self.sample_rate, channels=self.channels)
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thread.start()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> RecordingResult:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self._stop_event.set()
        if self._writer_thread is not None:
            self._writer_thread.join(timeout=5)
            self._writer_thread = None

        if self._sound_file is not None:
            self._sound_file.close()
            self._sound_file = None

        duration = 0.0 if self._started_at is None else max(0.0, time.monotonic() - self._started_at)
        return RecordingResult(path=self._path or "", duration_seconds=duration)

    def discard(self) -> None:
        if self._path and os.path.exists(self._path):
            os.remove(self._path)
        self._path = None

    def _callback(self, indata: Any, frames: int, time_info: Any, status: Any) -> None:
        del frames, time_info
        if status:
            LOGGER.warning("Audio status: %s. Check microphone availability and macOS Microphone permission.", status)
        if self._started_at and (time.monotonic() - self._started_at) >= self.max_record_seconds:
            self._stop_event.set()
            return
        self._audio_queue.put(indata.copy())

    def _writer_loop(self) -> None:
        while not self._stop_event.is_set() or not self._audio_queue.empty():
            try:
                data = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if self._sound_file is not None:
                self._sound_file.write(data)
