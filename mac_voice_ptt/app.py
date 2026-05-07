from __future__ import annotations

import argparse
import os
import platform
import threading
from dataclasses import dataclass

from mac_voice_ptt.audio import AudioRecorder
from mac_voice_ptt.config import AppConfig, platform_summary
from mac_voice_ptt.hotkey import HoldToTalkHotkeyListener
from mac_voice_ptt.text_output import insert_transcript
from mac_voice_ptt.transcription import WhisperTranscriber


@dataclass
class AppState:
    listening_enabled: bool = True
    recording: bool = False
    processing: bool = False


class MacVoicePTTApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.state = AppState()
        self.recorder = AudioRecorder(
            sample_rate=config.sample_rate,
            channels=config.channels,
            max_record_seconds=config.max_record_seconds,
        )
        self.transcriber = WhisperTranscriber(config.whisper_model, config.language)
        self.hotkey_listener = HoldToTalkHotkeyListener(
            hotkey=config.hotkey,
            on_start=self.begin_recording,
            on_stop=self.finish_recording,
        )
        self._status_label = None
        self._app = None
        self._lock = threading.Lock()

    def run(self) -> None:
        import rumps

        self._status_label = rumps.MenuItem(f"Hotkey: {self.config.hotkey_display}")
        toggle_item = rumps.MenuItem("Disable Listening", callback=self.toggle_listening)
        quit_item = rumps.MenuItem("Quit", callback=self.quit)
        self._app = rumps.App("Mac Voice PTT", title="🎙️", menu=[self._status_label, toggle_item, quit_item])
        self.hotkey_listener.start()
        rumps.notification("Mac Voice PTT", "Ready", f"Hold {self.config.hotkey_display} to dictate.")
        self._app.run()

    def toggle_listening(self, sender) -> None:  # noqa: ANN001
        self.state.listening_enabled = not self.state.listening_enabled
        sender.title = "Disable Listening" if self.state.listening_enabled else "Enable Listening"
        self._update_status("Idle" if self.state.listening_enabled else "Paused")

    def quit(self, _sender) -> None:  # noqa: ANN001
        import rumps

        self.hotkey_listener.stop()
        rumps.quit_application()

    def begin_recording(self) -> None:
        with self._lock:
            if not self.state.listening_enabled or self.state.recording or self.state.processing:
                return
            self.recorder.start()
            self.state.recording = True
        self._update_status("Recording")

    def finish_recording(self) -> None:
        with self._lock:
            if not self.state.recording:
                return
            self.state.recording = False
            self.state.processing = True
        self._update_status("Transcribing")
        result = self.recorder.stop()
        threading.Thread(target=self._process_recording, args=(result.path, result.duration_seconds), daemon=True).start()

    def _process_recording(self, path: str, duration_seconds: float) -> None:
        import rumps

        try:
            if duration_seconds < 0.15:
                rumps.notification("Mac Voice PTT", "Recording skipped", "The recording was too short.")
                return

            transcript = self.transcriber.transcribe(path)
            if not transcript:
                rumps.notification("Mac Voice PTT", "No speech detected", "Try speaking a little closer to the microphone.")
                return

            insert_result = insert_transcript(transcript)
            subtitle = "Pasted" if insert_result.success else "Copied to clipboard"
            rumps.notification("Mac Voice PTT", subtitle, transcript[:120])
            if not insert_result.success:
                print(insert_result.detail)
        except Exception as error:  # noqa: BLE001
            rumps.notification("Mac Voice PTT", "Error", str(error))
        finally:
            with self._lock:
                self.state.processing = False
            self._update_status("Idle" if self.state.listening_enabled else "Paused")
            if path and os.path.exists(path):
                os.remove(path)

    def _update_status(self, state: str) -> None:
        if self._status_label is not None:
            self._status_label.title = f"{state} · {self.config.hotkey_display}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="macOS push-to-talk dictation MVP")
    parser.add_argument("--check", action="store_true", help="print environment info without launching the app")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.check:
        summary = platform_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        return 0

    if platform.system() != "Darwin":
        print("This MVP targets macOS. Use --check from non-macOS environments.")
        return 1

    config = AppConfig.from_env()
    MacVoicePTTApp(config).run()
    return 0
