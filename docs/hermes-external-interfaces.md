# Hermes 外部接口 — WinPeek 消息 + 桌面控制

> **这是唯一文档。** Hermes 跟外部世界交互的全部手段，都在这一个文件里。
> 不要去看 `hermes-mqtt-setup.md` / `hermes-send-receive.md` / `desktop-agent-integration.md` ——那些是旧碎片，已合并到此。
>
> 最后更新: 2026-06-25

---

## 一、总览

Hermes 有两条对外通道：

```
                    ┌─────────────────────────┐
                    │      Hermes Agent        │
                    │  (cli.py 主循环)          │
                    │                          │
                    │  ┌────────────────────┐  │
              ① ───│──│ winpeek_mqtt.py    │  │─── ① MQTT 收发 WinPeek 消息
              收/发 │  │ (daemon 线程)       │  │    broker: 192.168.3.23:11883
                    │  └────────────────────┘  │
                    │                          │
                    │  ┌────────────────────┐  │
              ② ───│──│ desktop_agent.py   │  │─── ② HTTP 调用桌面自动化
              控制  │  │ (工具注册)           │  │    Desktop Agent :18791
                    │  └────────────────────┘  │
                    └─────────────────────────┘
```

| 通道 | 方向 | 用途 | 协议 | 状态 |
|------|------|------|------|------|
| ① WinPeek MQTT | 收 + 发 | Agent 之间聊天 | MQTT (paho) | ✅ 生产 |
| ② Desktop Agent | 发 (控制) | 操控 Windows 桌面 | HTTP | ⚠️ 代码就绪，待集成 |

---

## 二、WinPeek MQTT 消息 (通道①)

### 2.1 工作原理

```
发送方 (say.py / API)                    Hermes 进程内
    │                                        │
    ▼                                        │
MQTT Broker: 192.168.3.23:11883              │
  topic: comms/inbox/{hermes_uid}            │
    │  push (paho 持久连接)                    │
    ▼                                        │
hermes_cli/winpeek_mqtt.py                   │
  _loop() daemon 线程                         │
  on_message → 过滤 → _inbox_queue (内存)      │
                                             ▼
                                    cli.py process_loop
                                      每 0.1s drain_inbox()
                                      → _console_print() 打印
                                      → _pending_input 注入对话
```

**消息格式** (MQTT payload):

```json
{
  "from_uid": 1002,
  "from": "码哥",
  "body": "消息内容",
  "gid": ""
}
```

**过滤规则** (winpeek_mqtt.py `on_message`):
- 跳过自己发的消息 (`from_uid == 自己的uid`)
- 跳过系统回声 (`body.startswith("收到来自")`)
- 正文截断到 500 字符

### 2.2 涉及文件

| 文件 | 作用 | 关键行 |
|------|------|--------|
| `hermes_cli/winpeek_mqtt.py` | MQTT 收发模块（daemon 线程 + 队列 + send） | 全文 207 行 |
| `cli.py` | Hermes 主循环 | L5483-5491 (启动), L14060-14073 (drain) |

**cli.py 启动时 (L5483-5491)**：导入模块 → `start_mqtt_listener()` 启动后台线程 → `drain_inbox()` 清空启动前积压消息。

**cli.py 主循环 (L14060-14073)**：每次循环 `drain_inbox()` → 有消息就打印 `📬 WinPeek:` 摘要 → 注入 `_pending_input` 让 Agent 处理。

### 2.3 代码文件说明：`hermes_cli/winpeek_mqtt.py`

```
核心变量:
  _inbox_queue: list[dict]     — 线程安全消息队列
  _queue_lock: threading.Lock  — 队列锁
  _mqtt_client: mqtt.Client    — paho 客户端 (收发复用)
  _listener_started: bool      — 幂等保护

核心函数:
  start_mqtt_listener(uid, host, port)  — 启动 daemon 线程，订阅 comms/inbox/{uid}
  drain_inbox() → list[dict]             — 取出+清空队列
  format_inbox_summary(msgs) → str       — 格式化为 📬 WinPeek: ...
  send_message(to_uid, body) → bool      — 用已有连接发送
  _read_config() → dict                  — 读 agent.conf
  _find_agent_conf() → Path | None       — 按优先级查找 agent.conf
```

### 2.4 安装步骤 (新机器)

```bash
# 第 1 步：拉代码 + 安装依赖
cd ~/hermes-agent
git pull
pip install paho-mqtt

# 第 2 步：创建 agent.conf
mkdir -p ~/.hermes/data

cat > ~/.hermes/data/agent.conf << 'EOF'
{
  "hermes_uid": 2022,
  "mqtt_host": "192.168.3.23",
  "mqtt_port": 11883
}
EOF

# 第 3 步：重启 Hermes
hermes
# 启动后看到 📬 WinPeek: 就是通了
```

### 2.5 agent.conf 配置

| 字段 | 说明 | 例 |
|------|------|-----|
| `hermes_uid` | 你的 WinPeek uid | 2022 (Hermes), 1002 (码哥) |
| `mqtt_host` | MQTT broker | 192.168.3.23 |
| `mqtt_port` | MQTT 端口 | 11883 |

**查找顺序**（找到第一个就停）：
1. `~/.winpeek/agent.conf`
2. `~/.hermes/data/agent.conf` ← 推荐
3. `~/.claude/data/agent.conf`
4. `./agent.conf`（项目目录）
5. `./bin/agent.conf`
6. 都找不到 → 用默认值 (uid=2022, host=192.168.3.23, port=11883)

### 2.6 发送消息

```bash
# 方式 1: say.py (在 winpeek-prod 仓库)
python bin/say.py <目标uid> "消息内容"
# 例: python bin/say.py 2022 "你好"

# 方式 2: wsay.sh
bash bin/wsay.sh <目标uid> "消息内容"

# 方式 3: API
curl -X POST http://192.168.3.44:2000/api/chat/post \
  -H "Content-Type: application/json" \
  -d '{"to_uid": 2022, "body": "消息内容", "from_type": "ai"}'

# 方式 4: winpeek_mqtt.send_message() (Python, 复用 Hermes MQTT 连接)
from hermes_cli.winpeek_mqtt import send_message
send_message(to_uid=2022, body="消息内容")
```

### 2.7 验证 & 排查

```bash
# ① 检查 paho-mqtt
pip show paho-mqtt

# ② 检查 agent.conf
cat ~/.hermes/data/agent.conf

# ③ 测试 MQTT 连接
python -c "
import paho.mqtt.client as mqtt
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.connect('192.168.3.23', 11883, 10)
print('MQTT broker 连通 ✅')
c.disconnect()
"

# ④ 手动订阅，看 broker 是否有消息到达
python -c "
import paho.mqtt.client as mqtt, json
def on_msg(c, u, m):
    p = json.loads(m.payload.decode())
    print(f'收到: {p.get(\"from\")}[{p.get(\"from_uid\")}]: {p.get(\"body\",\"\")[:80]}')
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.on_message = on_msg
c.connect('192.168.3.23', 11883)
c.subscribe('comms/inbox/2022')
print('监听中... Ctrl+C 退出')
c.loop_forever()
"

# ⑤ 检查 Hermes 终端是否有 SyntaxError (静默失败)
python -c "
from hermes_cli.winpeek_mqtt import start_mqtt_listener
start_mqtt_listener()
print('监听线程启动 ✅')
"
```

### 2.8 已知陷阱

1. **`try/except: pass` 吞错** — cli.py 两处 MQTT 调用都包了静默异常处理，任何导入/启动错误都不会显示。验证方法见上方第⑤步。
2. **`global` vs `nonlocal`** — `_mqtt_client` 是模块级全局变量，`_loop()` 内必须用 `global`（历史 bug：commit `755415510` 误写 `nonlocal`）。
3. **paho-mqtt 没装** — Hermes 静默跳过，不报错。必须先 `pip install paho-mqtt`。
4. **agent.conf hermes_uid 写错** — MQTT 订阅了错的 topic，自然收不到消息。
5. **换 uid 要重启 Hermes** — 改 agent.conf 后重启才生效。

---

## 三、桌面自动化 Desktop Agent (通道②)

### 3.1 工作原理

```
Hermes Agent
    │ HTTP POST :18791
    ▼
Desktop Agent (Electron 独立进程)
  ├── server.mjs    — HTTP API 服务
  ├── main.mjs      — Electron 主进程
  └── vision.mjs    — 5 层视觉识别层联
    │
    ▼
Windows 桌面 (鼠标/键盘/截图/OCR)
```

Desktop Agent 是**独立进程**，Hermes 通过 HTTP 调用它。它负责所有桌面操作，Hermes 只发指令。

### 3.2 涉及文件

| 文件 | 作用 | 状态 |
|------|------|------|
| `tools/desktop_agent.py` | Hermes 端的 HTTP 客户端 + 工具注册 | ⚠️ 代码就绪，未接入 toolsets |
| `scripts/start-desktop-agent.sh` | 启动 Desktop Agent 进程 | ✅ 就绪 |
| `external/openclaw/` | Git Submodule (OpenClaw 仓库，含 ai-supervisor 插件) | ⚠️ 未初始化 |

**注意**: Desktop Agent 代码在 `external/openclaw/extensions/ai-supervisor/desktop-agent/`，需要先 `git submodule update --init`。

### 3.3 安装步骤

```bash
# 第 1 步：初始化 OpenClaw 子模块
cd ~/hermes-agent
git submodule update --init --recursive

# 第 2 步：安装 Desktop Agent 依赖
cd external/openclaw/extensions/ai-supervisor/desktop-agent
npm install

# 第 3 步：启动 Desktop Agent
cd ~/hermes-agent
bash scripts/start-desktop-agent.sh

# 第 4 步：验证服务
curl http://localhost:18791/health
```

### 3.4 可用工具

| 工具 | 功能 |
|------|------|
| `desktop_click` | 点击屏幕坐标 |
| `desktop_double_click` | 双击 |
| `desktop_mouse_move` | 移动鼠标 |
| `desktop_scroll` | 滚轮 |
| `desktop_type` | 输入文字 |
| `desktop_keypress` | 快捷键 (ctrl+c 等) |
| `desktop_screenshot` | 截图 |
| `desktop_vision_find` | 视觉查找 UI 元素 |
| `desktop_vision_analyze` | 视觉分析截图 |
| `desktop_list_windows` | 列出窗口 |
| `desktop_activate_window` | 激活窗口 |
| `desktop_launch` | 启动程序 |
| `desktop_human_click` | 点击 UI 元素 (视觉定位 + 点击) |
| `desktop_reset` | 回到桌面 |

### 3.5 视觉识别层联

Desktop Agent 内置 5 层级联视觉识别，从快到慢自动降级：

| 层 | 技术 | 适用 | 速度 |
|----|------|------|------|
| L0 | Win32 API (SysListView32) | 桌面图标 | ~500ms |
| L0.5 | OpenCV 模板匹配 | 已知图标 | ~300ms |
| L1 | OmniParser | UI 元素 | ~3s |
| L2 | PaddleOCR | 文字识别 | ~250ms |
| L3 | Qwen2.5-VL-7B (Ollama) | 语义理解 | ~600ms |

### 3.6 验证 & 排查

```bash
# 检查 Desktop Agent 是否运行
curl http://localhost:18791/health

# 检查视觉服务
curl http://localhost:18791/vision/health

# 查看日志
tail -f ~/.openclaw/desktop-agent/logs/agent.log

# 在 Hermes 内测试
python -c "
from tools.desktop_agent import check_desktop_agent
print('Desktop Agent:', '运行中 ✅' if check_desktop_agent() else '未启动 ❌')
"
```

### 3.7 已知陷阱

1. **Desktop Agent 必须单独启动** — 它不是 Hermes 的一部分，是独立进程。忘记启动 → 工具调用全部失败。
2. **OpenClaw 子模块未初始化** — `git clone` 后子模块是空的，`git submodule update --init` 才拉代码。
3. **依赖 Node.js** — Desktop Agent 基于 Electron/Node.js，Windows 上需要装 Node.js。
4. **未接入 Hermes 工具集** — `tools/desktop_agent.py` 代码写了但 `toolsets.py` 和 `cli.py` 还没引用，需要手动接入。

---

## 四、快速排障清单

Hermes 收不到消息？按顺序查：

```
□ 1. pip show paho-mqtt                     — 装了吗？
□ 2. cat ~/.hermes/data/agent.conf          — uid 对吗？
□ 3. python 测 MQTT broker 连通              — 网络通吗？
□ 4. 手动订阅 comms/inbox/{uid} 看消息       — broker 有消息吗？
□ 5. python -c "from hermes_cli.winpeek_mqtt import start_mqtt_listener; start_mqtt_listener()"  — 线程启了吗？
□ 6. 发一条 say 消息 + 等 5 秒               — 终端出现 📬 WinPeek 了吗？
```

桌面工具不可用？

```
□ 1. curl http://localhost:18791/health     — Desktop Agent 在跑吗？
□ 2. ls external/openclaw/extensions/       — 子模块初始化了吗？
□ 3. npm list (在 desktop-agent 目录)        — npm 依赖装了吗？
```
