/* SPDX-License-Identifier: Apache-2.0 */
#include "muse_locale.h"
#include <stdio.h>
#include <string.h>

#if CONFIG_MUSE_UI_CHINESE
typedef struct { const char *english, *chinese; } translation_t;
static const translation_t statuses[] = {
    {"Starting", "启动中"}, {"Starting...", "启动中..."},
    {"Ready to pair", "等待配对"}, {"App connected", "手机已连接"},
    {"Confirm pairing", "请确认配对"}, {"Connecting", "连接中"},
    {"Online", "在线"}, {"Offline", "离线"}, {"Error", "出错"},
    {"Not set up", "未配置"}, {"Saved", "已保存"},
    {"Connected", "已连接"}, {"Can't connect", "连接失败"},
    {"Pair in the Muse app", "请在 Muse App 中配对"},
    {"Waiting for Wi-Fi", "等待无线网络"},
    {"Connects when you talk", "说话时自动连接"},
    {"Joining...", "连接中..."},
    {"No saved network nearby", "附近没有已保存的网络"},
    {"Can't join; retrying", "连接失败，正在重试"},
    {"Connecting...", "连接中..."}, {"Not paired", "尚未配对"},
    {"Out of memory", "内存不足，请重启设备"}, {"Token rejected", "令牌无效，请检查配置"},
    {"Can't reach Muse's server", "无法连接 Muse 服务器"},
    {"VM refused the token", "虚拟机拒绝了令牌"},
    {"Noise handshake failed", "安全连接握手失败"}, {"Subscribe failed", "消息订阅失败"},
    {"Through Home Link, text replies", "通过 Home Link 接收文字回复"},
};
static const translation_t errors[] = {
    {"INTERRUPTED", "已中断"}, {"CAN'T REACH MUSE", "无法连接 Muse"},
    {"MUSE NOT SET UP", "请先配置 Muse"}, {"DIDN'T CATCH THAT", "没听清，请再说一次"},
    {"MUSE STOPPED LISTENING", "语音连接已结束"},
    {"MUSE COULDN'T LISTEN", "语音识别失败，请重试"},
    {"NO REPLY FROM MUSE", "暂未收到回复，请重试"},
    {"MUSE DIDN'T TAKE IT", "消息发送失败，请重试"},
    {"LOST CONNECTION TO MUSE", "与 Muse 的连接已断开"},
    {"SETTINGS CHANGED", "设置已更改，请重试"}, {"CANCELLED", "已取消"},
    {"BUSY", "正在处理，请稍候"}, {"BUSY WITH A VOICE TURN", "正在处理语音，请稍候"},
};
static const char *lookup(const translation_t *table, unsigned count, const char *text)
{
    if (!text) return "";
    for (unsigned i = 0; i < count; ++i) {
        if (strcmp(text, table[i].english) == 0) return table[i].chinese;
    }
    return text;
}
#define LOOKUP(table, text) lookup(table, sizeof(table) / sizeof(table[0]), text)
#endif

const char *muse_ui_status_text(const char *status)
{
#if CONFIG_MUSE_UI_CHINESE
    return LOOKUP(statuses, status);
#else
    return status ? status : "";
#endif
}

const char *muse_ui_error_text(const char *error)
{
#if CONFIG_MUSE_UI_CHINESE
    const char *text = LOOKUP(errors, error);
    return text != error || !text[0] ? text : "请求失败，请稍后重试";
#else
    return error ? error : "";
#endif
}

const char *muse_ui_detail_text(const char *detail, char *buf, unsigned size)
{
#if CONFIG_MUSE_UI_CHINESE
    const char *text = muse_ui_status_text(detail);
    if (text != detail || !text[0]) return text;
    const char *prefix = NULL, *value = NULL;
    if (strncmp(detail, "Connected to ", 13) == 0) {
        prefix = "已连接："; value = detail + 13;
    } else if (strncmp(detail, "Can't reach ", 12) == 0) {
        prefix = "无法连接："; value = detail + 12;
    } else if (strncmp(detail, "VM connect failed (HTTP ", 24) == 0) {
        prefix = "连接失败 (HTTP "; value = detail + 24;
    } else if (strncmp(detail, "Socket error", 12) == 0) {
        return "网络连接异常，请重试";
    }
    if (prefix && buf && size) {
        int n = snprintf(buf, size, "%s%s", prefix, value);
        /* A byte limit must never leave half a UTF-8 character on screen. */
        if (n >= (int)size) {
            unsigned end = size - 1;
            if (end) {
                unsigned start = end - 1;
                while (start && ((unsigned char)buf[start] & 0xc0) == 0x80) --start;
                unsigned char first = (unsigned char)buf[start];
                unsigned need = first < 0x80 ? 1 : first < 0xe0 ? 2 : first < 0xf0 ? 3 : 4;
                if (end - start < need) buf[start] = '\0';
            }
        }
        return buf;
    }
    return "连接异常，请检查网络和设置";
#else
    (void)buf; (void)size;
    return detail ? detail : "";
#endif
}

const char *muse_ui_button_name(const char *name)
{
#if CONFIG_MUSE_UI_CHINESE
    if (name && strcmp(name, "boot") == 0) return "BOOT/CONFIG";
#endif
    return name ? name : MUSE_TX("button", "按键");
}
