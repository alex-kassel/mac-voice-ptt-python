from __future__ import annotations

import os
import platform
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - keeps --check and tests usable before pip install
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


DEFAULT_HOTKEY = "<cmd>+<shift>+space"


def _parse_optional_int(value: str | None, default: int) -> int:
    if not value:
        return default
    return int(value)


def parse_hotkey(value: str) -> tuple[str, ...]:
    return tuple(part.strip().lower() for part in value.split("+") if part.strip())


@dataclass(frozen=True)
class AppConfig:
    hotkey: tuple[str, ...]
    hotkey_display: str
    sample_rate: int
    channels: int
    whisper_model: str
    language: str | None
    max_record_seconds: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv(override=False)
        hotkey_display = os.getenv("VOICE_PTT_HOTKEY", DEFAULT_HOTKEY)
        language = (os.getenv("VOICE_PTT_LANGUAGE") or "").strip() or None
        return cls(
            hotkey=parse_hotkey(hotkey_display),
            hotkey_display=hotkey_display,
            sample_rate=_parse_optional_int(os.getenv("VOICE_PTT_SAMPLE_RATE"), 16000),
            channels=_parse_optional_int(os.getenv("VOICE_PTT_CHANNELS"), 1),
            whisper_model=os.getenv("VOICE_PTT_MODEL", "base"),
            language=language,
            max_record_seconds=_parse_optional_int(os.getenv("VOICE_PTT_MAX_RECORD_SECONDS"), 120),
        )


def platform_summary() -> dict[str, str]:
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "platform_target": "Apple Silicon ready"
        if platform.system() == "Darwin" and platform.machine() == "arm64"
        else "Non-target environment",
    }
