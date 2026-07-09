---
sidebar_position: 3
title: "Data Schemas"
description: "WinPeek 核心数据模型定义"
---

# Data Schemas

## Identity

存储在 `~/.hermes/winpeek/identities.jsonl`。每条记录一行，`\n` 分隔。

:::note
UID 从 2001 开始自动递增，最大支持到 2099（共 99 个身份）。身份数据本地持久化，无需数据库。
:::

```python
{
    "uid": 2001,                      # int, 自增, 起始 2001
    "nickname": "yuyangmin",          # str, 唯一标识
    "role": "Architect",             # str, 可选: Developer|Architect|Ops|QA|PM|Director|Boss
    "host": "192.168.3.44",          # str, 所在主机地址
    "created_at": "2026-07-09T12:00:00Z",  # ISO 时间
}
```

## Tenant

MySQL `tenants` 表。

```sql
CREATE TABLE tenants (
    id          VARCHAR(64) PRIMARY KEY,  -- tenant_id
    name        VARCHAR(128) NOT NULL,    -- 租户显示名
    created_at  DATETIME DEFAULT NOW()
);
```

## User（租户成员）

MySQL `users` 表。

```sql
CREATE TABLE users (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id       VARCHAR(64) NOT NULL,
    platform        VARCHAR(32) NOT NULL,    -- wechat|dingtalk|feishu|...
    platform_uid    VARCHAR(128) NOT NULL,   -- wxid_xxx|dt_xxx|...
    display_name    VARCHAR(128),            -- 显示名
    created_at      DATETIME DEFAULT NOW(),
    UNIQUE KEY uk_platform (platform, platform_uid),
    INDEX idx_tenant (tenant_id)
);
```

## Hub Message

MySQL `hub_messages` 表。

```sql
CREATE TABLE hub_messages (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id       VARCHAR(64) NOT NULL,
    from_platform   VARCHAR(32) NOT NULL,
    from_uid        VARCHAR(128) NOT NULL,
    to_platform     VARCHAR(32) NOT NULL,
    to_uid          VARCHAR(128) NOT NULL,
    content         TEXT,
    msg_type        VARCHAR(32) DEFAULT 'text',
    created_at      DATETIME DEFAULT NOW(),
    INDEX idx_tenant_ts (tenant_id, created_at)
);
```

JSONL 归档格式相同：

```jsonl
{"tenant_id":"company_a","from":"wxid_xxx@wechat","to":"dt_xxx@dingtalk","content":"你好","type":"text","ts":"2026-07-09T12:00:00Z"}
```

## MQTT Message

话题 payload JSON。详见 [Hub API → MQTT Topic](./HUB-API.md#mqtt-topic-协议)。

```json
{
    "from_uid": 2022,             # int, 发送者 UID
    "from_name": "yuyangmin",     # str, 发送者显示名
    "content": "任务完成",        # str, 消息内容
    "msg_type": "text",          # str, 消息类型
    "ts": "2026-07-09T12:00:00Z"  # str, ISO 时间戳
}
```

## WeChat Session

UIA 控件采集到的会话结构。

```python
{
    "name": "张三",                      # str, 会话名
    "aid": "session_item_张三",          # str, UIA AutomationId
    "unread": 3,                         # int, 未读数
    "is_pinned": False,                  # bool, 是否置顶
    "is_muted": True,                    # bool, 是否免打扰
    "rect": (100, 200, 300, 65),         # tuple, UIA BoundingRectangle (left, top, width, height)
    "raw": "张三(3)"                     # str, UIA 原始 Name
}
```

## WeChat Message

采集到的聊天消息。

```python
{
    "content": "你好",                    # str, 消息内容
    "msg_type": "text",                  # str, 消息类型
    "is_from_me": False,                 # bool, 是否自己发的
    "is_date": False,                    # bool, 是否日期分隔行
    "is_bubble": True,                   # bool, 是否气泡消息
    "aid": "chat_bubble_item_view_xxx",  # str, UIA AutomationId
    "rect": (500, 300, 200, 40),         # tuple, UIA BoundingRectangle
    "time": "14:30"                      # str, 消息时间
}
```

## RPA MCP Template

存储在 `~/.hermes/winpeek/templates/` 下的 JSON 文件。

```json
{
    "meta": {
        "name": "wechat_send_message",
        "version": "2.1",
        "description": "给微信好友发送消息",
        "app": "wechat",
        "tested": true,
        "confidence": 0.92
    },
    "steps": [
        {
            "id": "step_1",
            "name": "搜索联系人",
            "tool": "uia_click",
            "args": {
                "control": "search_input",
                "text": "${contact_name}"
            }
        },
        {
            "id": "step_2",
            "name": "输入消息",
            "tool": "uia_type_text",
            "args": {
                "control": "message_input",
                "text": "${message}"
            }
        },
        {
            "id": "step_3",
            "name": "点击发送",
            "tool": "uia_click",
            "args": {
                "control": "send_button"
            }
        }
    ]
}
```

## 配置

### WinPeek Hub 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WINPEEK_HUB_ENABLED` | `0` | 启用 Hub（设 `1` 激活） |
| `WINPEEK_DB_HOST` | `192.168.3.23` | MySQL 主机 |
| `WINPEEK_DB_PORT` | `3306` | MySQL 端口 |
| `WINPEEK_DB_USER` | `winpeek` | MySQL 用户 |
| `WINPEEK_DB_PASS` | `(空)` | MySQL 密码 |
| `WINPEEK_DB_NAME` | `winpeek` | MySQL 数据库 |
| `HUB_ARCHIVE_ENGINE` | `mysql` | 归档引擎: `mysql`\|`jsonl`\|`off` |
| `MIM_UID` | `0` | MIM Agent 唯一 ID |
| `MIM_NAME` | `user_{UID}` | MIM 显示名 |
| `MIM_BROKER` | `192.168.3.23` | MQTT Broker 地址 |
| `MIM_PORT` | `1883` | MQTT 端口 |
| `DB_BACKEND` | `sqlite` | RPA 数据库后端 |

---

参见 [架构总览](./ARCHITECTURE.md) · [Hub API](./HUB-API.md)
