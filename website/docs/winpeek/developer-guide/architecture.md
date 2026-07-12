---
sidebar_position: 1
title: "WinPeck Architecture"
description: "WinPeck module framework — Automation (6+ platforms), MIM (messaging), Assets (5 sub-modules)"
---

# WinPeck Architecture

WinPeck extends Hermes Agent with three modules, each is a **platform** containing multiple independent sub-features:

| Module | Type | Sub-Features |
|--------|------|--------------|
| **Automation** | Multi-platform desktop automation | WeChat, Douyin, Kuaishou, Bilibili, Xiaohongshu, Shipinhao, ... |
| **MIM** | Multi-agent instant messaging | Identity, Messages, Groups, Agent Discovery, Personas |
| **Assets** | Computer management | Software, Disk, Files, Hardware, Processes |

Each sub-feature follows the same structure: backend code + Hermes tools + Agent skill + user doc.

## Full File Tree

```
hermes-agent/
│
├── plugins/winpeek_rpa/                        Automation Backend
│   ├── plugin.yaml
│   ├── README.md                               All platforms overview
│   ├── mcp_server.py
│   ├── platforms/                              ← One directory per platform
│   │   ├── wechat/       (11 files, ✅)        WeChat desktop automation + CRM
│   │   ├── douyin/       (🆕)                   Douyin short-video
│   │   ├── kuaishou/     (🆕)                   Kuaishou automation
│   │   ├── bilibili/     (🆕)                   Bilibili video
│   │   ├── xiaohongshu/  (🆕)                   Xiaohongshu notes
│   │   └── shipinhao/    (🆕)                   WeChat Channels
│   ├── shared/                                 Shared RPA utils + Assets backends
│   │   ├── software_scanner.py (✅ 381 lines)  Software inventory scanner
│   │   ├── disk_scanner.py     (🆕)             Disk usage scanner
│   │   ├── hardware_info.py    (🆕)             CPU/Memory/GPU info
│   │   ├── file_browser.py     (🆕)             File system browser
│   │   ├── process_manager.py  (🆕)             Running process manager
│   │   ├── crm_schema.sql                       CRM 13 tables DDL
│   │   ├── hub_schema.sql                       Hub 4 tables DDL
│   │   ├── rpa_tools.py                         UIA utilities
│   │   ├── bg_input.py                          Background input
│   │   ├── position_memory.py                   Bayesian position memory
│   │   └── config.py                            Shared config
│   └── skills/                                  Per-platform skill loaders
│
├── gateway/winpeek_hub/                         MIM Messaging Backend
│   ├── README.md
│   ├── identity.py            ✅ (91 lines)     Identity register/login
│   ├── mqtt_adapter.py        ✅ (189 lines)    MQTT send/receive
│   ├── archive.py             ✅                Message archive
│   ├── hub_bridge.py          ✅                Gateway integration
│   ├── routing.py             ✅                Cross-platform routing
│   ├── tenant.py              ✅                Multi-tenant
│   ├── chat.py                🆕                Message engine
│   ├── hub.py                 🆕                Node registry + heartbeat
│   ├── group.py               🆕                Group chat
│   ├── personas.py            🆕                Agent personas
│   ├── greeting.py            🆕                Online greeting
│   └── agent_launcher.py      🆕                Agent launcher + discovery
│
├── tools/
│   └── winpeek_tools.py                         All WinPeek Hermes tools
│       ├── winpeek_wechat_*        (4 ✅ + 11 🆕)
│       ├── winpeek_mim_*           (4 🆕)
│       ├── winpeek_scan_software   (🆕)
│       ├── winpeek_get_disk_info   (🆕)
│       ├── winpeek_list_files      (🆕)
│       ├── winpeek_get_hardware    (🆕)
│       ├── winpeek_list_processes  (🆕)
│       └── winpeek_{platform}_*    (future)
│
├── skills/                                      Agent Knowledge
│   ├── wechat-automation-rules/SKILL.md         ✅ WeChat operation rules
│   ├── trace-to-template/SKILL.md               ✅ Learn from traces
│   ├── software-self-learning/SKILL.md          ✅ Self-learn software ops
│   ├── software-assets/wechat.md                ✅ WeChat asset card
│   └── mim-guidelines/SKILL.md                  🆕 MIM operation rules
│
├── apps/desktop/src/app/winpeek/                Desktop Frontend
│   ├── README.md                                 ✅
│   │
│   ├── automation/index.tsx                      ← Platform switcher (6 tabs)
│   ├── wechat/index.tsx                          ← WeChat CRM panel
│   │
│   ├── mim/index.tsx                             ← MIM chat panel
│   │
│   ├── assets/index.tsx                          ← Assets sub-module switcher
│   │   (tabs: Software | Disk | Files | Hardware | Processes)
│   │
│   └── components/                               ← Shared WinPeek components
│
├── scripts/
│   └── winpeek-quality-check.py                  ✅ CI quality gate (6 checks)
│
├── .gitlab-ci.yml                                 ✅ CI pipeline (2 jobs)
│
├── .claude/skills/
│   ├── multica-integration/SKILL.md              ✅ Task tracking
│   ├── update-docs/
│   │   ├── SKILL.md                              ✅ Doc update workflow
│   │   └── references/CODE-TO-DOCS-MAPPING.yaml  ✅ 31 source→doc mappings
│   └── winpeek-quality-gate/
│       ├── SKILL.md                              ✅ 3-agent unified guide
│       └── DEPLOY.md                             ✅ Per-agent deploy steps
│
└── website/docs/winpeek/                         User + Developer Docs (Docusaurus)
    ├── index.mdx                          🆕 Landing page
    ├── quickstart.md                      ✅ (needs lowercase rename)
    │
    ├── developer-guide/
    │   ├── _category_.json                🆕
    │   ├── architecture.md                ✅ This document
    │   ├── automation-engine.md           🆕 UIA engine internals
    │   ├── automation-database.md         🆕 DB schemas (CRM + Hub)
    │   ├── mim-protocol.md                🆕 MQTT topics + message format
    │   └── quality-gate.md                🆕 CI/CD quality enforcement
    │
    ├── features/
    │   ├── _category_.json                🆕
    │   ├── overview.md                    🆕 Feature overview
    │   │
    │   ├── automation/                    ← One page per platform
    │   │   ├── _category_.json            🆕
    │   │   ├── overview.md                🆕 Automation overview
    │   │   ├── wechat.md                  🆕 WeChat CRM user guide
    │   │   ├── douyin.md                  🆕 Douyin guide
    │   │   ├── kuaishou.md                🆕 Kuaishou guide
    │   │   ├── bilibili.md                🆕 Bilibili guide
    │   │   ├── xiaohongshu.md             🆕 Xiaohongshu guide
    │   │   └── shipinhao.md               🆕 Shipinhao guide
    │   │
    │   ├── mim-chat.md                    ✅ MIM chat guide
    │   │
    │   └── assets/                        ← One page per sub-module
    │       ├── _category_.json            🆕
    │       ├── overview.md                🆕 Asset management overview
    │       ├── software.md                🆕 Software inventory guide
    │       ├── disk.md                    🆕 Disk management guide
    │       ├── files.md                   🆕 File browser guide
    │       ├── hardware.md                🆕 Hardware info guide
    │       └── processes.md               🆕 Process manager guide
    │
    └── reference/
        ├── _category_.json                🆕
        ├── tools.md                       🆕 All Hermes tools reference
        └── schemas.md                     ✅ (needs lowercase rename + frontmatter)
```

## Three Modules

### 1. Automation — Multi-Platform Desktop Automation

6+ platforms, each with its own UIA driver, database schema, and UI panel.

```
plugins/winpeek_rpa/platforms/{name}/
├── __init__.py
├── README.md              ← Requirements + technical design
├── uia.py                 ← UIA driver (window/focus/nav/click/type)
├── db.py                  ← Platform-specific storage
├── api.py                 ← Eyes/Hands/Engine orchestrator
├── collect.py             ← Content collector
└── analyze.py             ← Content analyzer

tools/winpeek_tools.py     ← winpeek_{name}_* tools
skills/{name}-*/SKILL.md   ← Agent operation knowledge
website/.../automation/{name}.md ← User guide
```

| Platform | Backend | Frontend | Complexity |
|----------|---------|----------|------------|
| **WeChat** | ✅ 11 files, 4200+ lines | ✅ 354 lines (CRM panel) | High — full CRM |
| Douyin | 🆕 stub | placeholder | Medium |
| Kuaishou | 🆕 stub | placeholder | Medium |
| Bilibili | 🆕 stub | placeholder | Medium |
| Xiaohongshu | 🆕 stub | placeholder | Medium |
| Shipinhao | 🆕 stub | placeholder | Medium |

### 2. MIM — Multi-Agent Instant Messaging

5 sub-features, all in `gateway/winpeek_hub/`.

| Sub-Feature | Backend | Frontend | Tools |
|-------------|---------|----------|-------|
| Identity | identity.py ✅ | mim/index.tsx (login panel) | winpeek_mim_login 🆕 |
| Messages | chat.py 🆕 | mim/index.tsx (chat panel) | winpeek_mim_send, winpeek_mim_poll 🆕 |
| Groups | group.py 🆕 | — | — |
| Agent Discovery | agent_launcher.py 🆕 | — | — |
| Personas | personas.py 🆕, greeting.py 🆕 | — | — |

### 3. Assets — Computer Management

5 sub-features. Backend code goes into `plugins/winpeek_rpa/shared/` (or a new `plugins/assets/` plugin if preferred). Frontend is one panel with sub-tabs.

| Sub-Feature | Backend | Frontend Tab | Hermes Tool |
|-------------|---------|-------------|-------------|
| Software | software_scanner.py ✅ (381 lines) | "全部软件" Tab | winpeek_scan_software 🆕 |
| Disk | disk_scanner.py 🆕 | "磁盘管理" Tab | winpeek_get_disk_info 🆕 |
| Files | file_browser.py 🆕 | "文件管理" Tab | winpeek_list_files 🆕 |
| Hardware | hardware_info.py 🆕 | "硬件信息" Tab | winpeek_get_hardware 🆕 |
| Processes | process_manager.py 🆕 | "进程管理" Tab | winpeek_list_processes 🆕 |

## How to Add a New Feature

### Add a Platform to Automation

1. `mkdir plugins/winpeek_rpa/platforms/{name}/`
2. Write `README.md` with requirements + design
3. Implement `uia.py` (UIA driver), `db.py`, `api.py`
4. Register `winpeek_{name}_*` tools in `tools/winpeek_tools.py`
5. Write `skills/{name}-automation/SKILL.md`
6. Add tab in `apps/.../winpeek/automation/index.tsx` + create panel component
7. Write `website/.../features/automation/{name}.md`
8. Run `python scripts/winpeek-quality-check.py`

### Add a Sub-Feature to Assets

1. Add backend in `plugins/winpeek_rpa/shared/{name}.py`
2. Register `winpeek_{name}` tool in `tools/winpeek_tools.py`
3. Add tab in `apps/.../winpeek/assets/index.tsx`
4. Write `website/.../features/assets/{name}.md`
5. Run `python scripts/winpeek-quality-check.py`

## Documentation Convention

| Where | What | Example |
|-------|------|---------|
| `plugins/*/README.md` | Requirements + technical design (single file) | `plugins/winpeek_rpa/platforms/wechat/README.md` |
| `gateway/*/README.md` | Requirements + technical design | `gateway/winpeek_hub/README.md` |
| `website/docs/winpeek/features/*/` | User-facing feature guides | `features/automation/wechat.md` |
| `website/docs/winpeek/developer-guide/` | Architecture, internals, reference | `developer-guide/automation-engine.md` |
| `skills/*/SKILL.md` | Agent operational knowledge | `skills/wechat-automation-rules/SKILL.md` |
| `.claude/skills/*/SKILL.md` | Cross-cutting agent workflows | `.claude/skills/update-docs/SKILL.md` |
