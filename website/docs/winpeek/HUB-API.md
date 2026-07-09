---
sidebar_position: 2
title: "Hub API"
description: "WinPeek Hub REST API + MQTT topic 规范"
---

# Hub API

WinPeek Hub 不暴露独立 HTTP 端口，它的 API 通过 **MQTT Topic** 和 **Hermes Gateway 内部函数调用** 实现。

## MQTT Topic 协议

### 发送消息

```
Topic: comms/say/{target_uid}
QoS: 1 (至少一次)
```

**Payload：**
```json
{
  "from_uid": 2022,
  "from_name": "yuyangmin",
  "content": "你好，任务完成了",
  "msg_type": "text",
  "ts": "2026-07-09T12:00:00Z"
}
```

**Hermes CLI 发送：**
```bash
say 2028 "你好，任务完成了"
```

### 接收消息

```
Topic: comms/inbox/{my_uid}
QoS: 1
```

**Payload：** 同发送格式。

**终端显示：**
```
● yuyangmin[2022] said: 任务完成了
```

**回复：**
```
[re:2022]:收到，已处理
```
或发消息：
```
say 2022 "已处理完毕"
```

### 回执（可选）

```
Topic: comms/ack/{target_uid}
QoS: 0
```

**Payload：**
```json
{
  "ack_for": "原消息内容",
  "status": "received|read|processed",
  "ts": "2026-07-09T12:00:05Z"
}
```

## Hub Bridge API（进程内函数调用）

Hub 不在独立端口上提供 REST API，而是通过 Python 函数导出给 Gateway 调用。

### 初始化

```python
from gateway.winpeek_hub.hub_bridge import try_load_hub, is_enabled

# 加载 Hub（幂等）
try_load_hub()  # 返回 True/False
```

### 消息接收

```python
from hub_bridge import on_message_received

on_message_received(
    platform="wechat",
    from_uid="wxid_xxx",
    from_name="张三",
    content="你好",
    msg_type="text"
)
```

### 租户查询

```python
from gateway.winpeek_hub.tenant import (
    get_tenant_for_user,
    list_tenant_members,
)

# 查找用户所属租户
tenant = get_tenant_for_user("wechat", "wxid_xxx")
# → {"tenant_id": "company_a", "tenant_name": "XX公司", "user_id": 42}

# 列出租户下所有成员
members = list_tenant_members("company_a")
# → [{"user_id": 1, "platform": "wechat", "platform_uid": "wxid_xxx", "display_name": "张三"}, ...]
```

### 路由

```python
from gateway.winpeek_hub.routing import (
    resolve_cross_platform_target,
    get_member_platforms,
)

# 找李四在哪个平台
target = resolve_cross_platform_target("wechat", "wxid_xxx", "李四")
# → {"platform": "dingtalk", "platform_uid": "dt_xxx", "display_name": "李四", "tenant_id": "company_a"}

# 查看某个用户有哪些平台绑定
platforms = get_member_platforms("company_a", 1)
# → [{"platform": "wechat", "platform_uid": "wxid_xxx"}, {"platform": "dingtalk", "platform_uid": "dt_xxx"}]
```

### 归档

```python
from gateway.winpeek_hub.archive import archive_message

archive_message(
    tenant_id="company_a",
    from_platform="wechat",
    from_uid="wxid_xxx",
    to_platform="dingtalk",
    to_uid="dt_xxx",
    content="你好",
    msg_type="text",
)
# → True/False
```

### Identity

```python
from gateway.winpeek_hub.identity import register, login, get_by_uid, list_all

# 注册身份
register("yuyangmin", role="Architect", host="192.168.3.44")
# → {"uid": 2001, "nickname": "yuyangmin", "role": "Architect", ...}

# 登录
login("yuyangmin")
# → {"uid": 2001, ...}

# 按 UID 查找
get_by_uid(2001)

# 列出所有
list_all()
```

## WinPeek RPA Tools API

通过 Hermes 工具系统注册，Agent 对话中直接调用。

### winpeek_wechat_send

给微信好友发送消息。

```python
winpeek_wechat_send(contact_name="张三", message="你好")
# → {"ok": True, "contact": "张三", "sent": "你好"}
```

### winpeek_wechat_collect_msgs

采集微信好友聊天记录。

```python
winpeek_wechat_collect_msgs(contact_name="张三", max_pages=80)
# → {"ok": True, "inserted": 350, "duplicates": 12}
```

### winpeek_wechat_collect_contacts

采集微信通讯录所有联系人。

```python
winpeek_wechat_collect_contacts()
# → {"ok": True, "contacts_collected": 128}
```

### winpeek_list_templates

列出已学习的 MCP 自动化模板。

```python
winpeek_list_templates()
# → {"count": 3, "templates": [{"name": "wechat_send_message", ...}]}
```

## MCP Server API

WinPeek RPA 的 MCP Server 通过 stdio JSON-RPC 通信。

```bash
# 手动启动 MCP Server
python -m plugins.winpeek_rpa.mcp_server
```

暴露的工具：

| 工具 | 说明 | 参数 |
|------|------|------|
| `list_templates` | 列出所有 MCP 模板 | 无 |
| `wechat_send_message` | 微信发消息 | `contact_name`, `message` |
| `learn_new_skill` | 启动自学习流程 | `app`, `task_description` |
| `get_uia_map` | 获取 UIA 控件映射 | `app`（默认 wechat） |
