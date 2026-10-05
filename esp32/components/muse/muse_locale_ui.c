/* SPDX-License-Identifier: Apache-2.0 */
#include "muse_locale_ui.h"

#if CONFIG_MUSE_UI_CHINESE
LV_FONT_DECLARE(muse_font_cjk_16);
/* UI construction runs under the display lock. Reuse bitmap data, with the
 * built-in icon font as fallback for LV_SYMBOL_* in buttons and keyboard keys. */
static lv_font_t ui_font;
static bool initialized;

const lv_font_t *muse_ui_text_font(const lv_font_t *original)
{
    (void)original;
    if (!initialized) {
        ui_font = muse_font_cjk_16;
        ui_font.fallback = &lv_font_montserrat_20;
        initialized = true;
    }
    return &ui_font;
}
#endif
