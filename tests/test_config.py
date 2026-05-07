import os
import unittest
from unittest.mock import patch

from mac_voice_ptt.config import AppConfig, parse_hotkey, platform_summary


class ConfigTests(unittest.TestCase):
    def test_parse_hotkey_normalizes_tokens(self) -> None:
        self.assertEqual(parse_hotkey(" <cmd> + <shift> + Space "), ("<cmd>", "<shift>", "space"))

    def test_from_env_reads_overrides(self) -> None:
        values = {
            "VOICE_PTT_HOTKEY": "<ctrl>+<alt>+d",
            "VOICE_PTT_MODEL": "small",
            "VOICE_PTT_LANGUAGE": "en",
            "VOICE_PTT_SAMPLE_RATE": "22050",
            "VOICE_PTT_CHANNELS": "2",
            "VOICE_PTT_MAX_RECORD_SECONDS": "30",
        }
        with patch.dict(os.environ, values, clear=False):
            config = AppConfig.from_env()

        self.assertEqual(config.hotkey, ("<ctrl>", "<alt>", "d"))
        self.assertEqual(config.whisper_model, "small")
        self.assertEqual(config.language, "en")
        self.assertEqual(config.sample_rate, 22050)
        self.assertEqual(config.channels, 2)
        self.assertEqual(config.max_record_seconds, 30)

    def test_platform_summary_contains_expected_keys(self) -> None:
        summary = platform_summary()
        self.assertIn("system", summary)
        self.assertIn("machine", summary)
        self.assertIn("python", summary)
        self.assertIn("target", summary)


if __name__ == "__main__":
    unittest.main()
