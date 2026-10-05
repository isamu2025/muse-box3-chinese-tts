# Muse Chinese caption font

`muse_font_cjk_16.c` is a bitmap subset derived from **Noto Sans CJK SC Regular
2.004**, copyright 2014–2021 Adobe. The font data remains under the **SIL Open
Font License 1.1** in [OFL.txt](OFL.txt); the project's Apache license does not
replace that license. The generated subset has the distinct name
`muse_font_cjk_16`.

Source: [official Noto CJK font](https://github.com/notofonts/noto-cjk/blob/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf).
Source SHA256: `2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b`.

The 6990 glyphs cover all **6763 GB2312 Han characters**, printable ASCII,
fullwidth ASCII and common Chinese punctuation (exact set: `codepoints.txt`).
Rare Han characters outside this set, most traditional Chinese characters
and other scripts are not guaranteed. Emoji keep the existing text filtering.
`CONFIG_MUSE_CJK_CAPTIONS` selects it for captions. With
`CONFIG_MUSE_UI_CHINESE` (BOX-3's default), state labels and settings reuse the
same bitmap data; `muse_locale_ui.c` adds a built-in Montserrat symbol fallback
for menu and keyboard icons. No second Chinese font is embedded. Disabling the
Chinese interface keeps the original English UI fonts.

The 16 px, 2 bpp glyphs have a 21 px line height and at most 16 px advance.
Uncompressed bitmap data lives in flash. No dynamic font loader, decompression
buffer, SD card or network font request is needed. BOX-3 captions use a 304 px
wide band with two lines, conservatively paginated at 19 Unicode characters
per line. ASCII is narrower, so mixed text always fits that grid.

To regenerate, install [lv_font_conv](https://github.com/lvgl/lv_font_conv) **1.5.3**
in a tooling directory, download the pinned source OTF, then run from `esp32`:

```sh
python tools/muse/gen_cjk_font.py --font /path/to/NotoSansCJKsc-Regular.otf \
  --converter /path/to/node_modules/lv_font_conv/lv_font_conv.js --node node
```

The source font is not bundled into firmware. Generation uses no credentials;
normal firmware builds compile the checked-in C asset without Node or conversion.
