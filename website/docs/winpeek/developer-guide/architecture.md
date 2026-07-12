---
sidebar_position: 1
title: "WinPeek Architecture"
description: "How WinPeek's Automation, MIM, and Assets modules extend Hermes Agent"
---

# WinPeek Architecture

WinPeek adds three independent modules to Hermes Agent. Each follows the same extension pattern: backend in `plugins/` or `gateway/`, tools in `tools/`, agent knowledge in `skills/`, and user docs in `website/docs/`.

## Module Overview

```text
Hermes Agent
  │
  ├── WinPeek ─────────────────────────────────────────────
  │     │
  │     ├── Automation — multi-platform desktop automation
  │     │     Uses Windows UIA to drive desktop apps
  │     │     (WeChat, Douyin, Kuaishou, …)
  │     │
  │     ├── MIM — multi-agent instant messaging
  │     │     MQTT-based real-time chat between Hermes instances
  │     │
  │     └── Assets — computer management
  │           Software scanner, disk usage, hardware info, …
  │
  └── Core (unchanged)
        CLI, Gateway, Agent loop, Sessions, Cron, 20+ platforms
```

The three modules are independent. None depends on the others. A user can enable just MIM without Automation, or just Assets without MIM.

## Where Code Lives

| Layer | Automation | MIM | Assets |
|-------|-----------|-----|--------|
| Backend | `plugins/winpeek_rpa/platforms/` | `gateway/winpeek_hub/` | `plugins/winpeek_rpa/shared/` |
| Tools | `tools/winpeek_tools.py` | same file | same file |
| Skills | `skills/wechat-automation-rules/` etc. | `skills/mim-guidelines/` | `skills/software-assets/` |
| Frontend | `apps/desktop/.../winpeek/automation/` + per-platform panels | `apps/desktop/.../winpeek/mim/` | `apps/desktop/.../winpeek/assets/` |
| Docs | `website/docs/winpeek/features/automation/` | `website/docs/winpeek/features/mim-chat.md` | `website/docs/winpeek/features/assets.md` |

### Why this layout

Hermes upstream places each feature in the layer it belongs to:
- Runtime logic that needs Python → `plugins/` or `gateway/`
- Agent-callable commands → `tools/` (registered via `registry.register()`)
- Agent operational knowledge → `skills/` (loaded on trigger)
- User-facing web docs → `website/docs/` (Docusaurus)

WinPeek follows the same layering. We don't create new top-level directories or separate doc systems.

## Automation: Platform Matrix

One backend directory per platform. WeChat is the first and most complex.

```text
plugins/winpeek_rpa/platforms/
  wechat/      — UIA driver + CRM engine (11 files, production)
  douyin/      — stub
  kuaishou/    — stub
  bilibili/    — stub
  xiaohongshu/ — stub
  shipinhao/   — stub
```

Each platform provides the same interface: UIA driver, data collector, content analyzer. The frontend platform switcher (`apps/desktop/.../winpeek/automation/index.tsx`) renders whichever platform the user selects.

WeChat is an outlier in complexity — it includes CRM features (friend portrait, sales pipeline, bulk messaging) because WeChat is primarily a contact management tool. Other platforms (Douyin, Bilibili, …) are content publishing platforms and will have lighter feature sets.

→ [Automation Engine](automation-engine.md)
→ [WeChat CRM](../features/automation/wechat.md)

## MIM: Agent Messaging

Real-time chat between Hermes instances over MQTT. Migrated from the PeekabooWin chat engine.

```text
Agent A ──→ winpeek_mim_send ──→ MQTT comms/say/{uid} ──→ Broker
                                                              │
Agent B ←── winpeek_mim_poll ←── MQTT comms/inbox/{uid} ←────┘
```

Identity is stored locally (JSONL). Messages are persisted in SQLite. MQTT provides real-time delivery. WebSocket push to the frontend is planned for V2.0; V1.0 uses polling.

→ [MIM Protocol](mim-protocol.md)
→ [MIM Chat](../features/mim-chat.md)

## Assets: Computer Management

Five independent scanners sharing a frontend dashboard with sub-tabs.

```text
apps/desktop/.../assets/index.tsx  (tab bar)
  ├── Software tab   →  winpeek_scan_software  →  software_scanner.py
  ├── Disk tab       →  winpeek_get_disk_info  →  disk_scanner.py
  ├── Files tab      →  winpeek_list_files     →  file_browser.py
  ├── Hardware tab   →  winpeek_get_hardware   →  hardware_info.py
  └── Processes tab  →  winpeek_list_processes →  process_manager.py
```

Each scanner is a standalone Python module that can be called from the command line or through a Hermes tool.

→ [Computer Assets](../features/assets.md)

## Data Flow

### User types in Hermes chat

```text
User: "Send hello to 许国勇"
  → Hermes Agent matches skill `wechat-automation-rules`
  → Calls `winpeek_wechat_send(contact_name="许国勇", message="hello")`
  → tools/winpeek_tools.py → plugins/winpeek_rpa/platforms/wechat/uia.py
  → Windows UIA clicks WeChat GUI
  → Result returned to agent → displayed to user
```

### Agent sends message to another Agent

```text
Agent A: say 2022 "task done"
  → gateway/winpeek_hub/mqtt_adapter.py → MQTT publish comms/say/2022
  → Agent B's mqtt_adapter receives → enqueued in memory
  → Agent B's frontend polls winpeek_mim_poll → displays new message
```

## Design Principles

| Principle | Practice |
|-----------|----------|
| **Hermes-native** | Use `plugins/`, `tools/`, `skills/`, `website/docs/` — no custom layers |
| **Module independence** | Automation, MIM, and Assets share zero code and can be enabled separately |
| **Plugin-first** | Backend code goes in `plugins/` or `gateway/`. No changes to core Hermes |
| **One README per module** | Requirements + technical design in the module's own README, not in a separate docs/ tree |
| **Quality gate enforced** | `scripts/winpeek-quality-check.py` runs on every MR. Blocked on failure |

## Recommended Reading

1. **This page** — orient yourself
2. [WeChat CRM](../features/automation/wechat.md) — the first and most complex platform
3. [Automation Engine](automation-engine.md) — UIA driver internals
4. [MIM Protocol](mim-protocol.md) — MQTT topics and message format
5. [Quality Gate](quality-gate.md) — CI enforcement rules
6. [Tools Reference](../reference/tools.md) — complete tool catalog
