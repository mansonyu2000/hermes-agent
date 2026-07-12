# MIM — 开发执行计划

## 基础信息

- MQTT: 192.168.3.23:1883
- MySQL: 192.168.3.23:3306/winpeek
- PeekabooWin: 192.168.3.44:2000 (参考源, 不依赖)
- 消息格式: PeekabooWin 生产验证 (from_uid/from/to_uid/body/ts)

## 前置条件检查

| 组件 | 状态 | 说明 |
|------|------|------|
| identity.py | ✅ | register/login/list_all 可用, JSONL 存储 |
| mqtt_adapter.py | ✅ | connect/send_message/_on_message 可用 |
| paho-mqtt | ✅ | 已安装 |
| MQTT Broker | ✅ | 192.168.3.23:1883 |
| Frontend | ✅ | 371行, 登录/联系人/聊天气泡/输入框 完整 |

## 并发任务（4 个独立模块同时开工）

### Task A: Backend — chat.py (消息引擎)

新建 1 文件，~150 行。

```python
# gateway/winpeek_hub/chat.py
# SQLite mim.db — messages 表
# send_message(from_uid, from_name, to_uid, body) → MQTT publish
# poll_messages(to_uid) → 返回+清空内存队列
# enqueue(msg) → mqtt_adapter._on_message 调用
# get_history(uid1, uid2, limit=50) → 分页查询
```

### Task B: Backend — mqtt_adapter 补丁

修改 1 处，+5 行。

在 `_on_message` 函数内，echo 跳过之后，调用 `chat.enqueue(msg)`。

### Task C: Tools — 4 个 Hermes 工具

修改 `tools/winpeek_tools.py`，+80 行。

- `winpeek_mim_login` → identity.register/login
- `winpeek_mim_send` → chat.send_message + MQTT
- `winpeek_mim_poll` → chat.poll_messages
- `winpeek_mim_contacts` → identity.list_all

### Task D: Frontend — 4 处替换

修改 `apps/desktop/.../mim/index.tsx`。

- Login: localStorage → winpeek_mim_login
- Contacts: DEFAULT_CONTACTS → winpeek_mim_contacts
- Send: setMessages → winpeek_mim_send
- Receive: 新增 setInterval(3000) → winpeek_mim_poll

## 执行顺序

```
A (chat.py) ──┐
              ├──→ C (tools) ──→ D (frontend) ──→ Verify
B (mqtt patch)┘
```

A 和 B 并行。C 依赖 A。D 依赖 C。

## 验证场景

1. Python: register + send + poll
2. Two identities in same Python process: A sends, B polls
3. Frontend: login → see contacts → send message → receive reply
