---
sidebar_position: 3
title: "代码文件关系图"
description: "MIM 相关 13 个核心文件的职责、依赖关系、对应文档章节"
---

# MIM 代码文件关系图

## 分层依赖

```
┌─ 前端 ────────────────────────────────────────────┐
│ apps/desktop/src/app/winpeek/mim/index.tsx         │
│   └─ useGatewayRequest → JSON-RPC (WS)             │
├─ RPC 注册层 ──────────────────────────────────────┤
│ tui_gateway/server.py                              │
│   └─ @method 注册 → 转发到 tools 层 handler         │
├─ 工具层 ──────────────────────────────────────────┤
│ tools/winpeek_tools.py                             │
│   ├─ _mim_center_call() — 转发层 (R1: 禁改)        │
│   ├─ _handle_mim_login / send / poll / contacts    │
│   ├─ _handle_mim_online / history / user_info      │
│   └─ (包A新增) runtime_report / local_agents       │
├─ Hub 内核 ────────────────────────────────────────┤
│ gateway/winpeek_hub/                               │
│   ├─ hub_bridge.py  — 启动协调 (包B 改动)          │
│   ├─ identity.py    — 身份注册/登录 (MySQL)        │
│   ├─ chat.py        — 消息引擎 (MySQL + 内存队列)  │
│   ├─ mqtt_adapter.py — MQTT 收发                   │
│   ├─ hub.py         — 在线状态 (nodes.json)        │
│   ├─ archive.py     — 消息归档                     │
│   ├─ routing.py     — 跨平台路由                   │
│   └─ tenant.py      — 多租户                       │
├─ 公共 DB 层 ──────────────────────────────────────┤
│ gateway/winpeek_hub/db.py                          │
│   └─ get_conn() → pymysql (仅中心模式 import)      │
├─ Daemon ──────────────────────────────────────────┤
│ apps/winpeek_injector/daemon.py                    │
│   └─ 发现 → 注册 → 心跳 (全部走转发入口，无直连)   │
├─ 认证层 ──────────────────────────────────────────┤
│ hermes_cli/web_server.py                           │
│ hermes_cli/dashboard_auth/middleware.py             │
└────────────────────────────────────────────────────┘
```

## 模块依赖

```dot
digraph mim_modules {
  rankdir=TB;
  node [shape=box, style=filled, fillcolor="#f0f0f0"];

  server   [label="tui_gateway/server.py\n@method 注册"];
  tools    [label="tools/winpeek_tools.py\nhandler + 转发层"];
  bridge   [label="hub_bridge.py\n启动协调"];
  identity [label="identity.py\n身份管理"];
  chat     [label="chat.py\n消息引擎"];
  mqtt     [label="mqtt_adapter.py\nMQTT 收发"];
  hub      [label="hub.py\n在线状态"];
  db       [label="db.py\nMySQL连接"];
  daemon   [label="daemon.py\n运行时守护者"];
  frontend [label="mim/index.tsx\n前端UI"];
  auth     [label="dashboard_auth/\n认证中间件", fillcolor="#e8e8e8"];

  server   -> tools;
  tools    -> chat [label=" send/poll/history"];
  tools    -> identity [label=" login/contacts/user_info"];
  tools    -> daemon [label=" local_agents", style=dashed];
  bridge   -> identity;
  bridge   -> mqtt;
  bridge   -> chat;
  bridge   -> daemon [label=" start_daemon()"];
  identity -> db;
  chat     -> db;
  chat     -> mqtt;
  chat     -> identity [label=" list_all()"];
  archive  -> db;
  frontend -> server [label=" JSON-RPC/WS"];
  daemon   -> tools [label=" _handle_mim_login()\n_handle_mim_online()"];
  server   -> auth [label=" WS认证"];
}
```

## 代码 ↔ 文档交叉索引

| 代码文件 | 对应文档 |
|---------|---------|
| `db.py` | 架构 §4.1, DB 重构 Review |
| `chat.py` | PRD §4, 架构 §4.1, DB 重构 Review |
| `identity.py` | PRD §3, 架构 §4.1, DB 重构 Review |
| `mqtt_adapter.py` | PRD §5, 架构 §2 |
| `hub_bridge.py` | 架构 §4.2-G1, §5.1, 实施计划书 包B |
| `hub.py` | 架构 §4.1 |
| `tools/winpeek_tools.py` | 架构 §4.1, 实施计划书 包A, IDOR 文档 |
| `daemon.py` | 架构 §5.2, 实施计划书 包C |
| `mim/index.tsx` | 架构 §5.4, 实施计划书 包D |
| `web_server.py` | 架构 §4.1 (Hub 加载), 实施计划书 R2 |
| `tui_gateway/server.py` | 实施计划书 包A |
| `middleware.py` | 实施计划书 R2 |
