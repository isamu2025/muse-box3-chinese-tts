/* SPDX-License-Identifier: Apache-2.0 */
#pragma once
#include "muse_locale.h"
#include "lvgl.h"

#if CONFIG_MUSE_UI_CHINESE
const lv_font_t *muse_ui_text_font(const lv_font_t *original);
#else
static inline const lv_font_t *muse_ui_text_font(const lv_font_t *original) { return original; }
#endif
