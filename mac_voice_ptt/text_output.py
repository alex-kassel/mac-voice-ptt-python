from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class InsertResult:
    success: bool
    mode: str
    detail: str


def copy_to_clipboard(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True, check=True)


def paste_active_app() -> None:
    script = 'tell application "System Events" to keystroke "v" using command down'
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)


def insert_transcript(text: str) -> InsertResult:
    copy_to_clipboard(text)
    try:
        paste_active_app()
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or "Transcript copied to clipboard; paste manually with ⌘V."
        return InsertResult(success=False, mode="clipboard", detail=detail)
    return InsertResult(success=True, mode="paste", detail="Transcript pasted into the active app.")
