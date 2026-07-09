---
sidebar_position: 1
title: "Architecture"
description: "WinPeek 模块关系、数据流、关键交互时序"
---

# WinPeek Architecture

WinPeek 是构建在 Hermes Agent 之上的 Windows 桌面自动化与多 Agent 编排系统。由 4 个模块组成，零侵入集成。

## Module Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Hermes Agent Core                     │
│  (run_agent.py / cli.py / model_tools.py)               │
└────────────────────┬────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────────┐
     ▼               ▼                   ▼
┌──────────┐  ┌──────────┐  ┌──────────────────────┐
│ Desktop  │  │ Gateway  │  │ WinPeek RPA Plugin    │
│ Frontend │  │ Platform │  │ (plugins/winpeek_rpa/)│
│ (React)  │  │ Adapters │  │                      │
│          │  │          │  │ MCP Server ── WeChat  │
│ winpeek/ │  │ winpeek_ │  │ stdio RPC    Douyin   │
│  views   │  │  hub/    │  │              ...      │
└──────────┘  └────┬─────┘  └──────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                  ▼
   ┌────────────┐   ┌──────────────┐
   │  MQTT      │   │  MySQL /     │
   │  Broker    │   │  SQLite      │
   │  1883      │   │  (archive)   │
   └────────────┘   └──────────────┘
```

## Module Breakdown

### 1. WinPeek Hub (`gateway/winpeek_hub/`)

多租户消息路由与归档中心。集成在 Hermes Gateway 同一个进程中，通过环境变量 `WINPEEK_HUB_ENABLED=1` 激活。

| 组件 | 文件 | 职责 |
|------|------|------|
| Hub Bridge | `hub_bridge.py` | 零侵入启动器，在 gateway 启动时 hook 加载 |
| Tenant | `tenant.py` | 多租户管理，MySQL users 表查找 |
| Routing | `routing.py` | 跨平台消息投递（微信→钉钉等） |
| Archive | `archive.py` | 消息归档（MySQL / JSONL / off 三种引擎） |
| Identity | `identity.py` | MIM 身份注册与登录（JSONL 持久化） |
| MQTT | `mqtt_adapter.py` | MIM MQTT 消息收发 |

**启用方式：**
```bash
export WINPEEK_HUB_ENABLED=1
hermes serve   # Gateway 启动时自动加载 Hub
```

### 2. WinPeek RPA (`plugins/winpeek_rpa/`)

桌面自动化引擎，以 Hermes Plugin 形式加载。支持微信、抖音等平台。

```
plugins/winpeek_rpa/
├── __init__.py         # Plugin 注册入口
├── plugin.yaml         # 插件元数据
├── mcp_server.py       # MCP stdio server（模板执行）
├── shared/             # 共享工具（rpa_tools.py, config.py）
├── platforms/
│   ├── wechat/         # 微信自动化（~15 文件）
│   │   ├── uia.py      # WeChatUIA 基础控件封装
│   │   ├── api.py      # 三层架构：Eyes / Hands / Engine
│   │   ├── db.py       # 微信 SQLite 数据库操作
│   │   ├── contacts.py # 通讯录采集
│   │   ├── collect.py  # 消息采集
│   │   └── ...
│   └── douyin/         # 抖音自动化（预留）
└── skills/             # 自学习技能模板
```

#### WeChat 三层架构

从 `api.py` 提取的设计模式：

```
🧠 LLM (决策层)
    │  决定：点哪个会话、翻几页、什么时候停
    ▼
👁️ WeChatEyes (感知层)
    │  纯读不写：get_sessions(), get_messages(), is_right_place()
    ▼
🤖 WeChatHands (执行层)
    │  全写不读：click_session(), scrollbar_sink(), send_message()
    ▼
💾 WeChatEngine (采集引擎)
    调度 eyes+hands+db，执行采集策略
```

关键设计原则：
- **Eyes 纯读，Hands 全写** — 每层只做一件事，输入→输出，无副作用
- **Engine 调度** — 组合 eyes+hands+db 完成复杂工作流
- **降级路径** — 微信 UIA 直连失败 → 降级 cua-driver 模板

### 3. MIM 协议 (`gateway/winpeek_hub/mqtt_adapter.py`)

Multi-agent Inter-agent Messaging — 基于 MQTT 的多 Hermes 实例通信协议。

**Topic 规范：**
```
comms/inbox/{uid}   → Agent 订阅，接收发给自己的消息
comms/say/{uid}     → Agent 发布，发送消息给指定 uid
comms/ack/{uid}     → 消息回执（可选）
```

**环境变量：**
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MIM_UID` | `0` | 当前 Agent 唯一 ID |
| `MIM_NAME` | `user_{UID}` | 显示名 |
| `MIM_BROKER` | `192.168.3.23` | MQTT Broker 地址 |
| `MIM_PORT` | `1883` | MQTT 端口 |

**通信流程：**
```
Agent A 想给 Agent B 发消息
    │ say <B的uid> "内容"
    ▼
Hermes → MQTT publish comms/say/{B的uid}
    │
    ▼
MQTT Broker → deliver to Agent B's comms/inbox/{B.uid}
    │
    ▼
Agent B 收到 → 处理 → 回复
```

### 4. Frontend (`apps/desktop/src/app/winpeek/`)

Electron Desktop 内的 WinPeek 视图。

```
apps/desktop/src/app/winpeek/
├── index.tsx          # WinPeek 主入口（路由挂载）
├── mim/               # MIM 聊天界面（微信风格双栏）
├── wechat/            # 微信管理面板
├── automation/        # 自动化任务配置
└── assets/            # 资产视图（文件/截图管理）
```

## Data Flow

### RPA 执行路径

```
用户输入"给张三发你好"
    │
    ▼
AIAgent 对话循环
    │ 匹配 tools/winpeek_tools.py 注册的 winpeek_wechat_send
    ▼
handle_function_call("winpeek_wechat_send")
    │
    ├── 方式1：直接调 wechat_uia.py (毫秒级)
    │   WeChatUIA.search_and_open("张三")
    │   WeChatUIA.send_message("你好")
    │
    └── 方式2：降级 cua-driver 模板 (秒级)
        mcp_server → execute_template("wechat_send_message")
```

### Hub 消息路由

```
微信(张三) 发消息给 Hermes
    │
    ▼
Gateway 收到 → Hub.on_message_received()
    │
    ├── tenant.get_tenant_for_user("wechat", "wxid_xxx")
    │   → 找到 tenant "公司A"
    │
    ├── resolve_cross_platform_target("公司A", "李四")
    │   → 李四在钉钉上有绑定
    │
    ├── archive_message(...)  // 归档
    │
    └── 跨平台投递到钉钉(李四)
```

## Configuration

| 环境变量 | 默认值 | 模块 | 说明 |
|----------|--------|------|------|
| `WINPEEK_HUB_ENABLED` | `0` | Hub | 启用 Hub 集成 |
| `WINPEEK_DB_HOST` | `192.168.3.23` | Hub | MySQL 主机 |
| `WINPEEK_DB_PORT` | `3306` | Hub | MySQL 端口 |
| `WINPEEK_DB_USER` | `winpeek` | Hub | MySQL 用户 |
| `WINPEEK_DB_PASS` | `` | Hub | MySQL 密码 |
| `WINPEEK_DB_NAME` | `winpeek` | Hub | MySQL 数据库名 |
| `HUB_ARCHIVE_ENGINE` | `mysql` | Hub | 归档引擎: mysql\|jsonl\|off |
| `MIM_UID` | `0` | MQTT | Agent ID |
| `MIM_NAME` | `user_{UID}` | MQTT | Agent 显示名 |
| `MIM_BROKER` | `192.168.3.23` | MQTT | MQTT Broker |
| `MIM_PORT` | `1883` | MQTT | MQTT 端口 |
| `DB_BACKEND` | `sqlite` | RPA | 数据库后端: sqlite\|mysql |
