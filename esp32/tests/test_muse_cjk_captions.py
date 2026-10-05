"""Chinese caption regression: actual bitmap/cmap coverage and UTF-8 paging."""
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "components/muse/fonts/muse_font_cjk_16.c"


def array(source, name):
    body = re.search(r"\b" + name + r"\[\]\s*=\s*\{(.*?)\};", source, re.S).group(1)
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    return [int(n.strip(), 0) for n in body.split(",") if n.strip()]


def read_font():
    source = FONT.read_text(encoding="utf-8")
    glyphs = [dict((k, int(v)) for k, v in re.findall(r"\.(\w+)\s*=\s*(-?\d+)", g))
              for g in re.findall(r"\{([^{}]*)\}", re.search(r"glyph_dsc\[\]\s*=\s*\{(.*?)\n\};", source, re.S).group(1))]
    cmaps = re.search(r"cmaps\[\]\s*=\s*\{(.*?)\n\};", source, re.S).group(1)
    mapping = {}
    for block in re.findall(r"\{(.*?)\}", cmaps, re.S):
        fields = dict(re.findall(r"\.(\w+)\s*=\s*([\w]+)", block))
        start, length, gid = (int(fields[k]) for k in ("range_start", "range_length", "glyph_id_start"))
        if fields["type"] == "LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY":
            mapping.update((start + i, gid + i) for i in range(length))
        elif fields["type"] == "LV_FONT_FMT_TXT_CMAP_SPARSE_TINY":
            mapping.update((start + off, gid + i) for i, off in enumerate(array(source, fields["unicode_list"])))
        elif fields["type"] == "LV_FONT_FMT_TXT_CMAP_FORMAT0_FULL":
            mapping.update((start + i, gid + off) for i, off in enumerate(array(source, fields["glyph_id_ofs_list"])) if off or i == 0)
        else:
            raise AssertionError("Unknown cmap format")
    return source, mapping, glyphs, bytes(array(source, "glyph_bitmap"))


class FontCoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.mapping, cls.glyphs, cls.bitmap = read_font()

    def test_every_gb2312_han_has_real_bitmap(self):
        han = set()
        for hi in range(0xB0, 0xF8):
            for lo in range(0xA1, 0xFF):
                try:
                    han.add(ord(bytes((hi, lo)).decode("gb2312")))
                except UnicodeDecodeError:
                    pass
        self.assertEqual(len(han), 6763)
        self.assertFalse(han - self.mapping.keys())
        for cp in han:
            g = self.glyphs[self.mapping[cp]]
            size = (g["box_w"] * g["box_h"] * 2 + 7) // 8
            self.assertGreater(size, 0, hex(cp))
            self.assertTrue(any(self.bitmap[g["bitmap_index"]:g["bitmap_index"] + size]), hex(cp))

    def test_mixed_caption_and_punctuation_coverage(self):
        sample = "刚介绍完，耳朵还热乎呢——再来一遍：我是 Atlas，你的 AI 助手，查资料、管日程、推屏幕、听语音，样样都行。Muse 123！"
        self.assertFalse(set(map(ord, sample)) - self.mapping.keys())
        expected = set(map(ord, (FONT.parent / "codepoints.txt").read_text(encoding="utf8").rstrip("\n")))
        self.assertEqual(expected, self.mapping.keys())
        self.assertEqual(len(expected), 6990)

    def test_caption_grid_fits_actual_metrics(self):
        self.assertEqual(len(self.glyphs), 6991)  # includes LVGL's reserved missing-glyph slot
        self.assertEqual(self.glyphs[0]["adv_w"], 0)
        self.assertEqual(self.glyphs[self.mapping[ord(" ")]]["box_w"], 0)
        self.assertLessEqual(max(g["adv_w"] for g in self.glyphs), 16 * 16)
        self.assertIn(".line_height = 21", self.source)
        self.assertIn(".bitmap_format = 0", self.source)
        self.assertLessEqual(19 * 16, 320 - 16)


class CaptionPagingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cc = shlex.split(os.environ.get("CC", "cc"))
        if not cc or not shutil.which(cc[0]):
            raise unittest.SkipTest("C compiler not available")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.binary = Path(cls.tmp.name) / "caption_harness"
        proc = subprocess.run([*cc, "-std=gnu11", "-Wall", "-Wextra", "-Werror",
                        "-include", str(ROOT / "tests/host_compat.h"),
                        "-I", str(ROOT / "components/muse"),
                        str(ROOT / "tests/muse_caption_harness.c"),
                        str(ROOT / "components/muse/muse_chat_text.c"),
                        str(ROOT / "components/muse/muse_text.c"), "-o", str(cls.binary)], capture_output=True, text=True)
        if proc.returncode:
            raise AssertionError(proc.stdout + proc.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def page(self, text, at):
        p = subprocess.run([str(self.binary), str(at)], input=text.encode("utf8"), capture_output=True, check=True)
        return p.stdout.decode("utf8")  # strict decode catches cut UTF-8 characters

    def test_chinese_pages_overlap_without_lost_characters(self):
        text = "刚介绍完，耳朵还热乎呢，再来一遍：我是你的人工智能助手，查资料、管日程、推屏幕、听语音，样样都行。"
        lines = [text[i:i + 19] for i in range(0, len(text), 19)]
        for at in range(len(text.encode("utf8")) + 1):
            current = min(at // (19 * 3), len(lines) - 1)
            self.assertEqual(self.page(text, at), "\n".join(lines[current:current + 2]))

    def test_mixed_text_has_at_most_two_safe_lines(self):
        text = "我是 Atlas，你的 AI 助手。Muse 支持中文 English 123，查资料、听语音，都可以！"
        for at in range(len(text.encode("utf8")) + 1):
            page = self.page(text, at)
            self.assertLessEqual(len(page.splitlines()), 2)
            self.assertTrue(all(len(line) <= 19 for line in page.splitlines()))

    def test_ascii_standins_leave_chinese_intact(self):
        self.assertEqual(self.page("你好，Muse！", 0), "你好，Muse！")
        self.assertEqual(self.page("中文—English…", 0), "中文--English...")


if __name__ == "__main__":
    unittest.main()
