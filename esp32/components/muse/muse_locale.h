/* SPDX-License-Identifier: Apache-2.0 */
#pragma once

#ifdef ESP_PLATFORM
#include "sdkconfig.h"
#endif
#ifndef CONFIG_MUSE_UI_CHINESE
#define CONFIG_MUSE_UI_CHINESE 0
#endif

/* Only controlled UI copy uses this macro. User text and wire values stay intact. */
#if CONFIG_MUSE_UI_CHINESE
#define MUSE_TX(english, chinese) chinese
#else
#define MUSE_TX(english, chinese) english
#endif

const char *muse_ui_status_text(const char *status);
const char *muse_ui_error_text(const char *error);
const char *muse_ui_detail_text(const char *detail, char *buf, unsigned size);
const char *muse_ui_button_name(const char *name);
