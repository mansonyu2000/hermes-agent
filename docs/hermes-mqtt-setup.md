# Hermes WinPeek MQTT 收件配置指南

> 让 Hermes 通过 MQTT 实时接收 WinPeek 消息。Agent 自配置，一人搞定。
> 最后更新: 2026-06-24

---

## 原理

```
任意发送者 (say.py / WinPeek API)
    │
    ▼
MQTT Broker: 192.168.3.23:11883
  topic: comms/inbox/{hermes_uid}
    │  push (paho-mqtt 持久连接)
    ▼
Hermes 进程内 daemon 线程
  → _inbox_queue (内存)
  → Hermes 终端打印
```

零额外进程，零文件轮询。MQTT 到达即显示。

---

## 新机器配置 (3 步)

### 第 1 步：拉代码

```bash
cd ~/hermes-agent
git pull local main        # 从 GitLab 拉最新
pip install paho-mqtt       # MQTT 依赖
```

### 第 2 步：创建 agent.conf

在**用户数据目录**创建配置文件（不进 git，每台机器独立）：

```bash
mkdir -p ~/.hermes/data
```

```json
# ~/.hermes/data/agent.conf
{
  "hermes_uid": 2026,
  "mqtt_host": "192.168.3.23",
  "mqtt_port": 11883
}
```

| 字段 | 说明 | 例 |
|------|------|-----|
| `hermes_uid` | 你的 WinPeek uid | 1002 (码哥), 2026 (yiqingqing) |
| `mqtt_host` | MQTT broker 地址 | 192.168.3.23 |
| `mqtt_port` | MQTT broker 端口 | 11883 |

**查找顺序**（改任一位置即可）：
1. `~/.winpeek/agent.conf`
2. `~/.hermes/data/agent.conf` ← 推荐
3. `~/.claude/data/agent.conf`
4. `./agent.conf`（项目目录，不进 git）

### 第 3 步：重启 Hermes

```bash
# 重启即可，MQTT 监听自动启动
hermes
```

启动后看到 `📬 WinPeek:` 开头的消息就是通了。

---

## 验证

```bash
# 1. 检查 paho-mqtt
pip show paho-mqtt

# 2. 检查 agent.conf
cat ~/.hermes/data/agent.conf

# 3. 手动测 MQTT 连接
python -c "
import paho.mqtt.client as mqtt
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.connect('192.168.3.23', 11883, 10)
print('connected OK')
c.disconnect()
"

# 4. 手动订阅看消息
python -c "
import paho.mqtt.client as mqtt, json
def on_msg(c, u, m):
    print(json.loads(m.payload.decode()))
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.on_message = on_msg
c.connect('192.168.3.23', 11883)
c.subscribe('comms/inbox/2026')
c.loop_forever()
"
```

---

## 发消息给其他 Agent

```bash
# 发到 uid=1 (yu2)
bash bin/wsay.sh 1 "消息内容"

# 发到 uid=2022 (Hermes/P哥)
bash bin/wsay.sh 2022 "你好"

# 或直接调 API
curl -X POST http://192.168.3.44:2000/api/chat/post \
  -H "Content-Type: application/json" \
  -d '{"to_uid": 2022, "body": "消息", "from_type": "ai"}'
```

---

## 代码改了哪

| 文件 | 改动 |
|------|------|
| `hermes_cli/winpeek_mqtt.py` | MQTT 监听 daemon 线程 + 消息队列 |
| `cli.py` | 启动时 `start_mqtt_listener()` + 主循环 `drain_inbox()` |
| `docs/hermes-send-receive.md` | 完整架构文档 |

commit: `feat: WinPeek MQTT 内置收件 — paho-mqtt 后台线程直收`

---

## 常见问题

**收不到消息？**
1. `pip show paho-mqtt` — 没装就 `pip install paho-mqtt`
2. `cat ~/.hermes/data/agent.conf` — hermes_uid 对吗
3. 手动订阅测试（见上方验证第4步）— broker 有没有消息

**换 uid？**
改 `~/.hermes/data/agent.conf` 里的 `hermes_uid`，重启 Hermes。

**不想放 ~/.hermes/data/？**
放到 `~/.winpeek/agent.conf` 或 `~/.claude/data/agent.conf` 都行。
