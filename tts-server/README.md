# 中文 TTS 服务

接收 BOX-3 的 UTF-8 文字回复，使用 edge-tts 获取音频，通过 HTTP 流式返回 MP3。需要 Python 3.11+ 与互联网；不包含离线语音引擎。

## 本机启动

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn tts_server:app --host 0.0.0.0 --port 8765 --no-access-log
```

环境变量：

| 变量 | 默认值 | 用途 |
|---|---|---|
| `MUSE_TTS_VOICE` | `zh-CN-XiaoxiaoNeural` | 音色 |
| `MUSE_TTS_PROXY` | 空，不使用代理 | 可选 HTTP 代理地址 |

需要代理时，在启动服务前设置自己的 `MUSE_TTS_PROXY`，例如 `http://127.0.0.1:7890`。代理服务由你自行配置。本仓库不修改网关、DNS 或第三方代理服务。

## Linux / 树莓派 systemd 部署

在本目录执行以下命令。使用独立服务账号与虚拟环境，不覆盖系统 Python 包：

```sh
sudo useradd --system --home /opt/muse-box3-tts --shell /usr/sbin/nologin muse-tts
sudo install -d -m 755 /opt/muse-box3-tts
sudo install -m 644 tts_server.py requirements.txt /opt/muse-box3-tts/
sudo python3 -m venv /opt/muse-box3-tts/.venv
sudo /opt/muse-box3-tts/.venv/bin/python -m pip install -r /opt/muse-box3-tts/requirements.txt
sudo install -m 644 muse-box3-tts.service /etc/systemd/system/
sudo install -m 600 muse-box3-tts.env.example /etc/muse-box3-tts.env
# 如需代理或其他音色，编辑 /etc/muse-box3-tts.env。
sudo systemctl daemon-reload
sudo systemctl enable --now muse-box3-tts.service
```

账号已存在时，跳过 `useradd`。服务环境文件应仅在主机本地保存。启动后：

```sh
systemctl status muse-box3-tts.service
curl -fsS http://127.0.0.1:8765/health
curl -f -H 'Content-Type: text/plain; charset=utf-8' \
  --data '你好，这是中文语音测试。' http://127.0.0.1:8765/tts -o test.mp3
```

`/health` 检查进程状态，不保证语音上游可达；用 `/tts` 请求及实际播放验证完整链路。服务监听可信局域网，未加入鉴权，回复会转发到语音上游。服务不缓存音频、不记录回复原文。

## BOX-3 配置

在固件 `menuconfig` 中启用 `CONFIG_MUSE_LOCAL_TTS`，填写 `CONFIG_MUSE_LOCAL_TTS_URL=http://你的服务器IP:8765/tts`，重新构建。按住 BOX-3 的 BOOT/CONFIG 说话，松开发送。收到完整回复后播放女声，人物下方显示中文字幕。

从设备发起语音对话时，日志应能观察到 `speech stream complete` 与 `reply audio: 24000 Hz, 1 ch, 48 kbps`；再确认扬声器实际出声。串口文字回合按官方设计保持静音。

## 接口与测试

- `POST /tts`：`Content-Type: text/plain; charset=utf-8`，最大 4095 字节，返回 `audio/mpeg` 流。
- 格式不匹配、UTF-8 无效/空文本、超限和服务忙分别返回 415、400、413、503。
- 最多两个并发请求，上游每次读取超时 20 秒；取消和异常均释放并发槽位。
- 上游失败中止音频流，固件继续显示字幕。

```sh
python -m pip install -r requirements-dev.txt
python -m unittest -v test_tts_server.py
```

6 项测试使用模拟上游，不需要 token、代理或互联网合成请求。
