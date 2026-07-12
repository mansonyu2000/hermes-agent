---
sidebar_position: 15
title: "WinPeek"
description: "WinPeek overview — three modules (Automation, MIM, Assets) and how they extend Hermes Agent"
---

# WinPeek

WinPeek adds three independent modules to Hermes Agent: multi-platform desktop automation, multi-agent instant messaging, and computer asset management. Each module follows Hermes conventions — `plugins/` or `gateway/` for backend, `tools/` for tool registration, `skills/` for agent knowledge, `website/docs/` for user docs.

## Module Overview

| Module | What it does | Backend | Tools |
|--------|-------------|---------|-------|
| **Automation** | Drive desktop apps (WeChat, Douyin, Kuaishou, …) via Windows UIA | `plugins/winpeek_rpa/platforms/` | `winpeek_{platform}_*` |
| **MIM** | Real-time messaging between Hermes agents over MQTT | `gateway/winpeek_hub/` | `winpeek_mim_*` |
| **Assets** | Computer management dashboard (software, disk, hardware) | `plugins/winpeek_rpa/shared/` | `winpeek_*` |

The three modules are independent. None depends on the others.

## Automation: Platform Matrix

Each platform (WeChat, Douyin, …) is a directory under `plugins/winpeek_rpa/platforms/` containing its own UIA driver, database, and tools. The frontend platform switcher renders whichever platform the user selects.

WeChat is the first and most complex — a full CRM with friend portraits, sales pipeline, and bulk messaging.

## MIM: Multi-Agent Messaging

Real-time chat between Hermes instances. Agents register an identity, discover peers, send and receive messages over MQTT. Identity stored in JSONL. Messages persisted in SQLite.

## Assets: Computer Management

A dashboard with sub-tabs for software inventory, disk usage, file browser, hardware info, and process management. Each sub-tab connects to its own Hermes tool and Python backend.

## Data Flow

```text
User: "Send hello to 许国勇"
  → Agent loads skill `wechat-automation-rules`
  → Calls winpeek_wechat_send(contact="许国勇", message="hello")
  → tools/winpeek_tools.py → plugins/.../wechat/uia.py
  → Windows UIA clicks WeChat GUI → result returned

Agent A: say 2022 "task done"
  → winpeek_mim_send → MQTT publish comms/say/2022
  → Broker → MQTT push comms/inbox/2022 → Agent B receives
```

## Quality Gate

Every MR runs `scripts/winpeek-quality-check.py` (TypeScript, CSS, Python, frontmatter, naming, dead links). Blocked on failure. Each agent follows the [WinPeek quality gate skill](../../.claude/skills/winpeek-quality-gate/SKILL.md).

## How to Add Features

Follow the [WinPeek Development Guide](../guides/winpeek-development.md) — a step-by-step cookbook covering backend directory layout, tool registration, skill creation, frontend panels, docs, and quality checks.

## Related

- [Build a Hermes Plugin](../guides/build-a-hermes-plugin.md) — upstream guide for plugin development
- [Adding Tools](./adding-tools.md) — Hermes tool registration reference
- [WinPeek Quickstart](../getting-started/winpeek-quickstart.md) — 5-minute setup
