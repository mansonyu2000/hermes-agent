# Hermes 收消息：两种方案对比

> 最后更新: 2026-06-24
> 上游相同：MQTT broker (192.168.3.23:11883) push 消息到 `comms/inbox/{uid}`
> 区别在"最后一公里"——消息怎么从 MQTT 进 Hermes 终端。

---

## 共同基础

```
任意发送者 (say.py / WinPeek API)
        │
        ▼
MQTT Broker: 192.168.3.23:11883
  topic: comms/inbox/{hermes_uid}
        │
        │  push (不是 pull)
        │
        ├──→ 方案A: Bridge 进程 + .inject 文件
        │
        └──→ 方案B: paho-mqtt 内置线程
```

**消息格式** (MQTT payload，两种方案一样):

```json
{
  "from_uid": 1002,
  "from": "码哥",
  "body": "消息内容",
  "gid": ""
}
```

**配置来源** (两种方案一样): `agent.conf`

```json
{
  "hermes_uid": 2022,
  "mqtt_host": "192.168.3.23",
  "mqtt_port": 11883
}
```

---

## 方案A: Bridge 进程 + .inject 文件

```
MQTT Broker
    │
    ▼
hermes-mqtt-bridge.py          ← 独立 Python 进程
  paho-mqtt 持久连接
  收到消息 → 格式化 → 写文件
    │
    ▼
~/.winpeek/inbox/.inject       ← 中间文件
    │
    ▼
cli.py process_loop             ← Hermes 主循环
  每 0.1s 检查文件是否存在
  存在 → 读内容 → 删文件 → 注入 _pending_input
```

### 优点

- **进程隔离**：bridge 挂了不影响 Hermes 主进程
- **可独立重启**：bridge 崩了 cron watchdog 自动拉起来，Hermes 不用动
- **调试方便**：`cat ~/.winpeek/inbox/.inject` 直接看消息内容
- **已验证**：当前生产在用，跑了 10+ 天稳定
- **不侵入 Hermes 源码**：cli.py 只加了一个文件检查，改动极小

### 缺点

- **多一个进程要维护**：bridge + watchdog cron，运维多两个东西
- **文件 IO**：每条消息一次写文件 + 一次读文件 + 一次删文件
- **有中间状态**：文件写入一半崩溃可能丢消息或读到半截
- **Agent 误读风险**：Agent 看到 `.inject` 文件轮询代码会推理"消息靠轮询"
- **格式耦合**：bridge 决定消息格式（`name[uid] said: body`），改格式要改 bridge

### 代码位置

| 文件 | 作用 |
|------|------|
| `bin/hermes-mqtt-bridge.py` | bridge 进程 (winpeek-prod 仓库) |
| `cli.py` L14059-14069 | 文件检查 (Hermes 端) |
| cron `bridge-watchdog` | 守护重启 |

---

## 方案B: paho-mqtt 内置线程

```
MQTT Broker
    │
    ▼
hermes_cli/winpeek_mqtt.py     ← Hermes 进程内的 daemon 线程
  paho-mqtt 持久连接
  收到消息 → 入队 _inbox_queue (内存)
    │
    ▼
cli.py process_loop             ← Hermes 主循环
  每 0.1s 调用 drain_inbox()
  有消息 → format_inbox_summary() → _console_print()
```

### 优点

- **零额外进程**：一切在 Hermes 进程内
- **无文件 IO**：纯内存队列，无磁盘开销
- **无中间状态**：消息从 MQTT 直达内存，不落盘
- **代码集中**：收发逻辑都在 cli.py + winpeek_mqtt.py
- **Agent 不会误读**：没有文件轮询代码，Agent 不会建议"5秒轮询"

### 缺点

- **线程崩了 Hermes 收不到消息**：需重启 Hermes 才能恢复（但 daemon 线程有自动重连，断了 MQTT 连接会自动重试）
- **需要 paho-mqtt**：`pip install paho-mqtt`（Hermes 本身不依赖它）
- **调试不如文件直观**：消息在内存队列里，不能 `cat` 看
- **侵入 Hermes 源码**：需要修改 cli.py + 新增 winpeek_mqtt.py
- **未生产验证**：刚实现，没跑过

### 代码位置

| 文件 | 作用 |
|------|------|
| `hermes_cli/winpeek_mqtt.py` | MQTT 线程模块 |
| `cli.py` L5483-5491 | 启动时初始化 |
| `cli.py` L14056-14062 | 主循环 drain |

---

## 对比总表

| 维度 | 方案A (bridge+.inject) | 方案B (内置线程) |
|------|----------------------|-----------------|
| 进程数 | Hermes + bridge (2个) | Hermes (1个) |
| 中间存储 | 文件 (.inject) | 内存队列 |
| IO 次数/消息 | 写+读+删 = 3次 | 0次 |
| 消息延迟 | <0.1s (轮询周期) | <0.1s (轮询周期) |
| bridge 崩了 | cron 自动拉起 | 需重启 Hermes |
| Hermes 重启 | bridge 不受影响 | 线程跟着重启 |
| 调试方式 | cat .inject 文件 | 无直接手段 |
| 运维负担 | 多 bridge + watchdog | 无额外 |
| 对 Hermes 侵入 | 极小 (1个文件检查) | 较大 (新模块+2处修改) |
| paho-mqtt 依赖 | bridge 需要 | Hermes 需要 |
| 生产验证 | ✅ 10+ 天 | ❌ 未验证 |
| Agent 误读风险 | 高 (看到轮询代码) | 低 |

---

## 切换方法

### 当前默认：方案A

```bash
# 启动 bridge
python bin/hermes-mqtt-bridge.py 2022

# cron 守护 (每分钟)
hermes cron create --name bridge-watchdog \
  --schedule "every 1m" \
  --script check-bridge.sh
```

### 切到方案B

```bash
# 1. 确保 cli.py 有方案B代码 (L5483 + L14056)
# 2. 停 bridge 进程 + 删 watchdog cron
# 3. 删除 cli.py 中的 .inject 检查代码 (L14059-14069)
# 4. 确保 paho-mqtt 已安装
pip install paho-mqtt
# 5. 重启 Hermes
```

---

## 发送消息 (两种方案都一样)

```bash
# 发给 uid=1 (yu2)
bash bin/wsay.sh 1 "消息内容"

# 直接调 API
curl -X POST http://192.168.3.44:2000/api/chat/post \
  -H "Content-Type: application/json" \
  -d '{"to_uid": 1, "body": "消息内容", "from_type": "ai"}'
```

---

## 排查

```bash
# === 方案A 排查 ===
# bridge 在跑吗
ps aux | grep hermes-mqtt-bridge
# 最近有消息吗
cat ~/.winpeek/inbox/.inject
# bridge watchdog 状态
hermes cron list | grep bridge

# === 方案B 排查 ===
# paho-mqtt 装了吗
pip show paho-mqtt
# 手动测 MQTT 连接
python -c "
import paho.mqtt.client as mqtt
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.connect('192.168.3.23', 11883, 10)
print('connected OK')
c.disconnect()
"

# === 通用 ===
# 手动订阅看 broker 有没有消息
python -c "
import paho.mqtt.client as mqtt, json
def on_msg(c, u, m):
    print(json.loads(m.payload.decode()))
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.on_message = on_msg
c.connect('192.168.3.23', 11883)
c.subscribe('comms/inbox/2022')
c.loop_forever()
"
```
