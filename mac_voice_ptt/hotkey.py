from __future__ import annotations

import threading
from collections.abc import Callable


def _normalize_key(key: object) -> str | None:
    name = getattr(key, "name", None)
    if isinstance(name, str):
        return f"<{name.lower()}>"

    char = getattr(key, "char", None)
    if isinstance(char, str) and char:
        return char.lower()

    vk = getattr(key, "vk", None)
    if vk == 49:
        return "space"

    return None


class HoldToTalkHotkeyListener:
    def __init__(
        self,
        hotkey: tuple[str, ...],
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ) -> None:
        self.hotkey = frozenset(hotkey)
        self.on_start = on_start
        self.on_stop = on_stop
        self._listener = None
        self._pressed: set[str] = set()
        self._active = False
        self._lock = threading.Lock()

    def start(self) -> None:
        from pynput import keyboard

        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key: object) -> None:
        normalized = _normalize_key(key)
        if not normalized:
            return
        with self._lock:
            self._pressed.add(normalized)
            if not self._active and self.hotkey.issubset(self._pressed):
                self._active = True
                self.on_start()

    def _on_release(self, key: object) -> None:
        normalized = _normalize_key(key)
        if not normalized:
            return
        with self._lock:
            self._pressed.discard(normalized)
            if self._active and not self.hotkey.issubset(self._pressed):
                self._active = False
                self.on_stop()
