"""Run the real HTTP worker with threaded SDK fakes, including backpressure."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TtsClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        include = Path(cls.tmp.name)
        fake = (ROOT / "tests/muse_tts_fake_sdk.h").as_posix()
        for name in ["sdkconfig.h", "esp_heap_caps.h", "esp_http_client.h", "esp_log.h", "esp_timer.h",
                     "freertos/FreeRTOS.h", "freertos/idf_additions.h", "freertos/stream_buffer.h", "freertos/task.h"]:
            p = include / name
            p.parent.mkdir(exist_ok=True)
            p.write_text(f'#include "{fake}"\n')
        cls.exe = include / ("tts.exe" if os.name == "nt" else "tts")
        subprocess.run(shlex.split(os.environ.get("CXX", "c++")) + ["-std=c++17", "-pthread",
                       "-I", str(include), "-I", str(ROOT / "components/muse"),
                       str(ROOT / "components/muse/muse_tts.cpp"),
                       str(ROOT / "tests/muse_tts_client_harness.cpp"), "-o", str(cls.exe)], check=True,
                       capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_stream_larger_than_queue_has_no_missing_bytes(self):
        subprocess.run([str(self.exe), "large"], check=True, timeout=10, capture_output=True)

    def test_cancel_releases_worker_and_buffers(self):
        subprocess.run([str(self.exe), "cancel"], check=True, timeout=10, capture_output=True)

    def test_incomplete_utf8_suffix_is_removed(self):
        subprocess.run([str(self.exe), "utf8"], check=True, timeout=10, capture_output=True)

    def test_failure_is_distinguished_from_success(self):
        for mode in ["badhttp", "badtype", "timeout", "truncated"]:
            with self.subTest(mode=mode):
                subprocess.run([str(self.exe), mode], check=True, timeout=10, capture_output=True)


if __name__ == "__main__":
    unittest.main()
