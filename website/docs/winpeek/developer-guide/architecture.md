---
sidebar_position: 1
title: "WinPeek Architecture"
description: "WinPeek module structure — how Automation, MIM, and Assets extend Hermes Agent"
---

# WinPeek Architecture

WinPeek adds three modules to Hermes Agent, following upstream conventions for plugins, tools, skills, and documentation.

## System Overview

```text
Hermes Desktop (Electron + React)
  │
  ├── /automation  →  Platform swatch (WeChat/Douyin/Kuaishou/…)
  │     └── Each platform = backend(plugins/winpeek_rpa/platforms/<name>/)
  │                       + tools(winpeek_<name>_*)
  │                       + skills/ + website/docs/
  │
  ├── /mim          →  Multi-agent messaging
  │     └── Backend(gateway/winpeek_hub/) + MQTT broker + Hermes tools
  │
  └── /assets       →  Computer management
        └── Backend(plugins/winpeek_rpa/shared/) + Hermes tools
```

## Three Modules

### Automation

A platform matrix. Each platform (WeChat, Douyin, Kuaishou, …) is an independent desktop automation target with its own UIA driver, database, and tools. WeChat is the first and most complex — a full CRM with portrait scoring, sales pipeline, and bulk messaging.

→ [WeChat CRM](../features/automation/wechat.md)
→ [Automation Engine](./automation-engine.md)
→ [Automation Database](./automation-database.md)

### MIM (Multi-agent Instant Messaging)

Real-time messaging between Hermes agents via MQTT. Identity registration, peer discovery, message send/receive, group chat. Migrated from PeekabooWin chat engine.

→ [MIM Chat](../features/mim-chat.md)
→ [MIM Protocol](./mim-protocol.md)

### Assets

Computer management dashboard. Software inventory scanner, disk usage, file browser, hardware info, process manager.

→ [Computer Assets](../features/assets.md)

## Directory Layout

```text
hermes-agent/
│
├── plugins/winpeek_rpa/          # Automation backends
│   ├── platforms/                #   One directory per platform
│   │   ├── wechat/               #   WeChat UIA + CRM engine
│   │   ├── douyin/               #   Douyin stub
│   │   └── ...                   #   kuaishou, bilibili, xiaohongshu, shipinhao
│   └── shared/                   #   RPA utils + Assets backends
│
├── gateway/winpeek_hub/          # MIM messaging backend
│
├── tools/winpeek_tools.py        # All WinPeek Hermes tools
│
├── skills/                       # Agent knowledge
│   ├── wechat-automation-rules/  #   WeChat operation rules
│   ├── trace-to-template/        #   Learn from operation traces
│   └── software-self-learning/   #   Self-learn new software
│
├── apps/desktop/src/app/winpeek/ # Desktop frontend
│   ├── automation/               #   Platform switcher
│   ├── wechat/                    #   WeChat CRM panel
│   ├── mim/                       #   MIM chat panel
│   └── assets/                    #   Asset dashboard
│
└── website/docs/winpeek/          # User + developer docs
    ├── features/                  #   Feature guides
    ├── developer-guide/           #   Architecture, internals
    └── reference/                 #   Tools, schemas
```

## Data Flow

### WeChat Automation

```text
Hermes Agent → winpeek_wechat_send tool → WeChatUIA (UIA driver)
  → search + click + type in WeChat GUI → result returned to agent
```

### MIM Messaging

```text
Agent A → winpeek_mim_send → MQTT publish comms/say/{uid}
  → Broker → MQTT push comms/inbox/{uid} → Agent B's message queue
  → winpeek_mim_poll picks it up → frontend displays
```

### Asset Scan

```text
Frontend click → winpeek_scan_software tool → software_scanner.py
  → Registry + Start Menu + portable dirs → JSON → frontend renders
```

## Design Principles

| Principle | Practice |
|-----------|----------|
| **Plugin-first** | Backend code goes in `plugins/` or `gateway/`, not in core Hermes |
| **Tool registration** | Every capability exposed as a Hermes tool via `tools/winpeek_tools.py` |
| **Skill for knowledge** | Agent operational rules live in `skills/`, auto-loaded by agent |
| **Doc in one place** | Module README = requirements + design. Website doc = user guide |
| **Platform parity** | New platforms follow the same directory structure as existing ones |

## Recommended Reading

1. **This page** — orient yourself
2. [WeChat CRM](../features/automation/wechat.md) — the most complex platform, start here
3. [Automation Engine](./automation-engine.md) — UIA driver internals
4. [MIM Protocol](./mim-protocol.md) — MQTT topics and message format
5. [Quality Gate](./quality-gate.md) — CI enforcement and commit rules
6. [Tools Reference](../reference/tools.md) — complete tool catalog
