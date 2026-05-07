# mac-voice-ptt-python

Python MVP of a macOS Apple Silicon push-to-talk dictation app.

The app is designed as a small menu bar utility for macOS rather than a foreground windowed app. Hold the configured global hotkey to record, release to transcribe, and the app will try to paste the transcript into the active app.

## MVP scope

- macOS-focused menu bar utility built with Python
- Global hold-to-record hotkey
- Microphone recording while the hotkey is held
- Offline transcription with `faster-whisper`
- Paste-into-active-app attempt through macOS Accessibility automation
- Clipboard fallback when direct paste is blocked by permissions or app behavior

## Platform target

- macOS on Apple Silicon (`arm64`)
- Developed for MacBook M1 / compatible Apple Silicon Macs
- Should also run on Intel macOS, but the project is intentionally optimized and documented for Apple Silicon

## Dependencies

### System packages

Install Homebrew packages first:

```bash
brew install portaudio ffmpeg
```

`portaudio` is used by `sounddevice` for microphone capture, and `ffmpeg` improves local media handling for `faster-whisper`.

### Python packages

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

The app reads settings from environment variables and optionally from a local `.env` file.

Example `.env`:

```dotenv
VOICE_PTT_HOTKEY=<cmd>+<shift>+space
VOICE_PTT_MODEL=base
VOICE_PTT_LANGUAGE=
VOICE_PTT_SAMPLE_RATE=16000
VOICE_PTT_CHANNELS=1
VOICE_PTT_MAX_RECORD_SECONDS=120
```

### Important settings

- `VOICE_PTT_HOTKEY` - hold this hotkey to record. Default: `<cmd>+<shift>+space`
- `VOICE_PTT_MODEL` - Whisper model name. Good MVP defaults: `base` or `small`
- `VOICE_PTT_LANGUAGE` - optional fixed language code such as `en` or `ru`
- `VOICE_PTT_SAMPLE_RATE` - recording sample rate, default `16000`
- `VOICE_PTT_MAX_RECORD_SECONDS` - safety cutoff for unusually long recordings

## Required macOS permissions

You should expect the first run to require these permissions:

1. **Microphone** - required for audio capture
2. **Accessibility** - required to send the paste shortcut to the active application

Grant them in:

- `System Settings` → `Privacy & Security` → `Microphone`
- `System Settings` → `Privacy & Security` → `Accessibility`

If Accessibility permission is denied or the target app blocks automation, the transcript is still copied to the clipboard and the menu bar app shows a notification telling you to paste manually.

## Run

```bash
python main.py
```

For a quick environment check without launching the menu bar app:

```bash
python main.py --check
```

## Usage

1. Launch the app with `python main.py`
2. Look for the `🎙️` menu bar icon
3. Hold the configured hotkey
4. Speak while holding it
5. Release the hotkey
6. Wait for transcription
7. The app tries to paste the result into the active app

## How text insertion works

The MVP uses a practical macOS approach:

1. Copy the transcript to the system clipboard
2. Ask `System Events` to send `⌘V`

This is intentionally simple and reliable for a first pass. It works well in many native and web apps after Accessibility permission is granted.

### Fallback behavior

If the app cannot automate paste:

- the transcript remains on the clipboard
- the app shows a notification
- you can paste manually with `⌘V`

## Known limitations

- Global hotkey behavior depends on `pynput`, which is good enough for an MVP but not as macOS-native as a Swift/AppKit implementation
- The first transcription can be slower because the Whisper model is loaded lazily
- Some sandboxed or highly restricted apps may ignore synthetic paste events
- This repository intentionally favors a small, readable Python MVP over a fully polished native macOS app

## Project layout

```text
main.py
mac_voice_ptt/
  app.py
  audio.py
  config.py
  hotkey.py
  text_output.py
  transcription.py
tests/
```
