# Muse BOX-3 中文界面与中文 TTS

基于 Meta 的 [Muse Gadget SDK](https://github.com/facebookincubator/muse-gadget-sdk) 开发，目标硬件为 **ESP32-S3-BOX-3**。本仓库发布两部分修改：中文界面，以及把 Muse 的文字回复转换成中文女声、在 BOX-3 扬声器播放的 TTS。

上游基线：[`7e88df2bbb3fa92403024b9d161d798f937d6716`](https://github.com/facebookincubator/muse-gadget-sdk/tree/7e88df2bbb3fa92403024b9d161d798f937d6716)。采用干净源码快照，不包含本地开发历史、Wi-Fi 密码、SDK token、配对凭据、签名私钥或设备固件备份。其他板型代码沿用上游，主要开发和硬件验证针对 BOX-3。

## 1. 中文化

- 主界面状态：就绪、启动中、聆听中、思考中、回复中、出错。
- 设置、无线网络、Muse、蓝牙、声音、自动息屏、电池和电源菜单中文化。
- 配对、连接失败、未收到回复、语音识别失败等提示中文化；原始诊断仍保留在日志。
- 人物下方显示两行中文字幕；6990 字形字库覆盖全部 6763 个 GB2312 汉字、ASCII、全角字符及常用标点。
- 菜单与字幕共用中文位图，菜单图标使用内置字体回退，无需第二套中文字库。
- 修复 320×240 屏幕的网络名称和密码输入框布局。

BOX-3 默认启用 `CONFIG_MUSE_CJK_CAPTIONS` 和 `CONFIG_MUSE_UI_CHINESE`。其他板型默认保持原英文界面。字库并不覆盖所有生僻字、繁体字或其他语言；软键盘保留 ASCII 按键，尚无拼音输入法。

## 2. 中文 TTS

```text
BOX-3 按住 BOOT/CONFIG 说话 → Muse → 完整文字回复
                                      ↓ POST UTF-8 text/plain
                            局域网 Python TTS 服务
                                      ↓ edge-tts / 流式 MP3
                      BOX-3 解码、重采样、字幕与扬声器播放
```

- 默认音色 `zh-CN-XiaoxiaoNeural`，24 kHz、48 kbps、单声道 MP3。
- 固件使用独立 HTTP 工作任务、有界队列与背压，支持取消、超时和音频失败后的字幕回退。
- 最多接收 4095 字节回复，截断时保留完整 UTF-8 字符。
- Python 服务不缓存回复、不记录回复原文；限制两个并发请求。
- TTS 默认关闭，通过 `CONFIG_MUSE_LOCAL_TTS` 开启，并设置自己的 `CONFIG_MUSE_LOCAL_TTS_URL`。

服务需要互联网访问语音上游，当前不是离线 TTS。Muse 回复会由设备发送到你配置的局域网服务，再送到语音上游。HTTP 接口用于可信局域网，未实现鉴权。**从 BOX-3 发起语音对话才会播放 TTS；官方串口文字回合保持静音。**

## 构建 BOX-3 固件

需要 **ESP-IDF v6.0.1**。先使用该版本的 `export.sh` 或 `export.ps1` 激活环境。生成一个只保存在本机的开发签名密钥：

```sh
cd esp32
python -m espsecure generate-signing-key --version 2 dev_signing_key.pem
```

该密钥已加入 Git 忽略规则。后续使用同一密钥构建兼容的签名 OTA 更新；USB 开发刷写不要求沿用上游公开密钥。保持硬件 Secure Boot、Flash 加密及 eFuse 配对认证关闭，不修改分区表偏移。

PowerShell 示例：

```powershell
$box3Args = @(
    '-B', 'build-box3',
    '-DIDF_TARGET=esp32s3',
    '-DSDKCONFIG=build-box3/sdkconfig',
    '-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;devices/sdkconfig.muse;devices/sdkconfig.muse-espressif-box-3;devices/sdkconfig.muse-local-tts'
)
idf.py @box3Args menuconfig
idf.py @box3Args build
# 先核对 BOX-3 的 USB 身份和实际端口；COM5 仅为示例。
idf.py @box3Args -p COM5 flash
```

Linux 的配置命令：

```sh
idf.py -B build-box3 -DIDF_TARGET=esp32s3 -DSDKCONFIG=build-box3/sdkconfig \
  '-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;devices/sdkconfig.muse;devices/sdkconfig.muse-espressif-box-3;devices/sdkconfig.muse-local-tts' menuconfig
```

构建、刷写沿用相同参数，将 `menuconfig` 替换成 `build` 或 `-p /dev/ttyACM0 flash`。

在菜单中填写：

1. `ESP32 Device SDK` 下的自己的 Gadget SDK token，可在 [SDK tokens](https://gadgets.muse.ai/settings/sdk-tokens) 获取。
2. `Muse` 下的本地 TTS 地址，例如 `http://你的服务器IP:8765/tts`。仓库中的地址为空，需要自行配置。
3. Wi-Fi 通过 Muse App 配网，或在本机 `menuconfig` 填写。不要把生成的 `sdkconfig` 上传。

Muse App 中开启 Settings → Devices → Developer mode，然后添加对应 `MuseGadget`。首次配对需按设备提示确认。常规刷写保留 NVS 中的网络和配对信息；刷写前自行备份已有设备。详细上游流程见 [ESP32 README](esp32/README.md)。

## 部署语音服务

见 [tts-server/README.md](tts-server/README.md)，支持树莓派或其他 Python 3.11+ Linux 主机。服务地址、代理和音色都使用你自己的配置，不包含开发设备的固定网关或代理补丁。

## 测试与硬件验证

2026-10-05 的 BOX-3 中文固件已完成 11 个页面截图检查和正式刷写；用户确认菜单、中文字幕和中文女声正常。该已验证构建的 4 MiB 应用分区剩余约 37%。公开版去除了个人网络配置，实际大小以自己的构建输出为准。

固件主机回归运行 161 项测试，1 项跳过，其余通过；服务端有 6 项测试。AIPI Lite 的默认英文 UI 已通过兼容编译，未在其硬件运行。主机测试需要 C/C++ 编译器；先构建一次以获取 `managed_components` 中的依赖：

```sh
cd esp32
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

服务测试命令见服务目录。新增验证覆盖中文字库、格式占位符、动态连接状态、UTF-8 截断、TTS 队列/取消/HTTP 异常与服务器资源释放。

## 目录与许可

| 目录 | 内容 |
|---|---|
| `esp32/` | 上游固件及中文化、TTS 客户端修改 |
| `esp32/components/muse/fonts/` | 中文字体、字形列表、OFL 许可与生成说明 |
| `tts-server/` | Python 流式语音服务、测试与 systemd 示例 |

代码沿用 [Apache-2.0](LICENSE)，第三方文件保留原有许可：中文字体依据 **SIL OFL 1.1**，见 [字体说明](esp32/components/muse/fonts/README.md)；minimp3 为 CC0，`pixel_font.c` 为 BSD-2-Clause。上游 Jollybot 角色素材带有 Meta 版权声明，不属于 Apache 许可覆盖范围。
