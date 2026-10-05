"""UI translation safety: actual font coverage, formats and untouched wire/user text."""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest
from test_muse_cjk_captions import read_font

ROOT = Path(__file__).resolve().parents[1]
MUSE = ROOT / 'components/muse'
STRING = r'"(?:\\.|[^"\\])*"'
GROUP = r'(?:' + STRING + r'\s*)+'
PAIRS = re.compile(r'MUSE_TX\((' + GROUP + r'),\s*(' + GROUP + r')\)', re.S)

def decode(group):
    return ''.join(json.loads(s) for s in re.findall(STRING, group))

def formats(text):
    return re.findall(r'%(?!%)(?:[-+#0]*\d*(?:\.\d+)?)(?:hh|ll|[hljztL])?[diuoxXfFeEgGaAcspn]', text.replace('%%', ''))

class TranslationAssetsTest(unittest.TestCase):
    def test_all_ui_translations_have_real_font_glyphs_and_matching_formats(self):
        _, mapping, _, _ = read_font()
        pairs = []
        for p in MUSE.glob('muse_*.c'):
            source = p.read_text(encoding='utf8')
            for en, zh in PAIRS.findall(source):
                en, zh = decode(en), decode(zh)
                pairs.append((en, zh))
                self.assertEqual(formats(en), formats(zh), en)
                self.assertFalse(set(map(ord, zh)) - mapping.keys() - {10, 13}, zh)
        self.assertGreater(len(pairs), 200)
        for s in re.findall(STRING, (MUSE / 'muse_locale.c').read_text(encoding='utf8')):
            text = decode(s)
            if any(ord(ch) > 127 for ch in text):
                self.assertFalse(set(map(ord, text)) - mapping.keys(), text)

class LocaleRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cc = shlex.split(os.environ.get('CC', 'cc'))
        if not shutil.which(cc[0]):
            raise unittest.SkipTest('C compiler unavailable')
        cls.tmp = tempfile.TemporaryDirectory()
        cls.binaries = []
        for chinese in (0, 1):
            binary = Path(cls.tmp.name) / ('locale' + str(chinese))
            r = subprocess.run([*cc, '-std=c11', '-Wall', '-Wextra', '-Werror',
                '-DCONFIG_MUSE_UI_CHINESE=' + str(chinese), '-I', str(MUSE),
                str(ROOT / 'tests/muse_locale_harness.c'), str(MUSE / 'muse_locale.c'),
                '-o', str(binary)], capture_output=True, text=True)
            if r.returncode:
                raise AssertionError(r.stdout + r.stderr)
            cls.binaries.append(binary)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def translate(self, op, text, chinese=1, size=128):
        r = subprocess.run([str(self.binaries[chinese]), op, str(size)],
            input=(text + '\n').encode('utf8'), capture_output=True, check=True)
        return r.stdout.decode('utf8')

    def test_all_backend_state_names_are_localized_only_at_ui_boundary(self):
        for filename, function in [('muse_link.c', 'muse_link_state_name'), ('muse_chat.c', 'muse_hatch_state_name')]:
            source = (MUSE / filename).read_text(encoding='utf8')
            block = re.search(function + r'\([^)]*\)\s*\{(.*?)\n\}', source, re.S).group(1)
            for quoted in re.findall(r'return\s*(' + STRING + ')', block):
                en = decode(quoted)
                if not en: continue
                self.assertTrue(any(ord(c) > 127 for c in self.translate('status', en)), en)
                self.assertEqual(self.translate('status', en, chinese=0), en)

    def test_unknown_status_and_user_text_stay_intact(self):
        for text in ['Sound', 'READY', '网络名称 Muse', '你好，我是 Atlas。', '192.0.2.10']:
            self.assertEqual(self.translate('status', text), text)

    def test_errors_localize_and_unknown_error_has_readable_fallback(self):
        self.assertEqual(self.translate('error', 'NO REPLY FROM MUSE'), '暂未收到回复，请重试')
        self.assertEqual(self.translate('error', 'unknown failure'), '请求失败，请稍后重试')
        self.assertEqual(self.translate('error', 'unknown failure', chinese=0), 'unknown failure')
        self.assertEqual(self.translate('error', ''), '')

    def test_detail_keeps_host_ssid_and_http_code(self):
        self.assertEqual(self.translate('detail', 'Connected to 中文网络'), '已连接：中文网络')
        self.assertEqual(self.translate('detail', "Can't reach 192.0.2.10"), '无法连接：192.0.2.10')
        self.assertEqual(self.translate('detail', 'VM connect failed (HTTP 403)'), '连接失败 (HTTP 403)')
        self.assertEqual(self.translate('detail', 'Waiting for Wi-Fi'), '等待无线网络')

    def test_small_detail_buffers_never_split_utf8_or_overrun(self):
        expected = '已连接：中文网络 Atlas'
        for size in range(1, 44):
            output = self.translate('detail', 'Connected to 中文网络 Atlas', size=size)
            self.assertLess(len(output.encode('utf8')), size)
            self.assertTrue(expected.startswith(output))

    def test_box3_button_prompt_names_real_button(self):
        self.assertEqual(self.translate('button', 'boot'), 'BOOT/CONFIG')
        self.assertEqual(self.translate('button', 'boot', chinese=0), 'boot')

if __name__ == '__main__':
    unittest.main()
