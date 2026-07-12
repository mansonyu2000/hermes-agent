---
sidebar_position: 1
title: "WinPeek Architecture"
description: "WinPeek module framework — Automation (multi-platform), MIM (messaging), Assets (computer management)"
---

# WinPeek Architecture

WinPeek extends Hermes Agent with three capabilities: **Automation** (multi-platform desktop automation), **MIM** (multi-agent messaging), and **Assets** (computer management).

Each capability follows Hermes upstream conventions: `plugin/` or `gateway/` for backend, `tools/` for Hermes tool registration, `skills/` for Agent knowledge, `website/docs/` for user docs.

## Module Map

```
hermes-agent/
│
├── plugins/winpeek_rpa/                     Automation Backend
│   ├── plugin.yaml
│   ├── README.md                            Automation requirements + design
│   ├── mcp_server.py
│   ├── platforms/                           ← One directory per platform
│   │   ├── wechat/        (11 files ✅)     WeChat desktop automation + CRM
│   │   ├── douyin/        (1 file  🆕)     Douyin short-video automation
│   │   ├── kuaishou/      (1 file  🆕)     Kuaishou automation
│   │   ├── bilibili/      (1 file  🆕)     Bilibili video automation
│   │   ├── xiaohongshu/   (1 file  🆕)     Xiaohongshu note automation
│   │   └── shipinhao/     (1 file  🆕)     WeChat Channels automation
│   ├── shared/                              Shared RPA utils, scanners, schemas
│   └── skills/                              Per-platform skill loaders
│
├── gateway/winpeek_hub/                     MIM Messaging Backend
│   ├── README.md
│   ├── identity.py            ✅
│   ├── mqtt_adapter.py        ✅
│   ├── archive.py             ✅
│   ├── hub_bridge.py          ✅
│   ├── routing.py             ✅
│   ├── tenant.py              ✅
│   ├── chat.py                🆕 Message engine
│   ├── hub.py                 🆕 Node registry
│   ├── group.py               🆕 Group chat
│   ├── personas.py            🆕 Agent personas
│   ├── greeting.py            🆕 Online greeting
│   └── agent_launcher.py      🆕 Agent launcher
│
├── tools/
│   └── winpeek_tools.py                    All WinPeek Hermes tools
│       ├── winpeek_wechat_*   (4 ✅ + 11 🆕)
│       ├── winpeek_mim_*      (4 🆕)
│       ├── winpeek_assets_*   (5 🆕)
│       └── winpeek_{platform}_* (future: douyin, kuaishou, ...)
│
├── skills/                                  Agent Knowledge
│   ├── wechat-automation-rules/SKILL.md    ✅ WeChat operation rules
│   ├── trace-to-template/SKILL.md         ✅ Learn from traces
│   ├── software-self-learning/SKILL.md    ✅ Self-learn software ops
│   ├── software-assets/wechat.md          ✅ WeChat asset card
│   └── mim-guidelines/SKILL.md            🆕 MIM operation rules
│
├── apps/desktop/src/app/winpeek/           Desktop Frontend
│   ├── README.md                            ✅
│   ├── automation/                          Platform switcher (6 tabs)
│   │   └── index.tsx                        ← shared: tab bar + active panel
│   ├── wechat/                              WeChat CRM UI (most complex)
│   │   └── index.tsx
│   ├── mim/                                 MIM chat UI
│   │   └── index.tsx
│   ├── assets/                              Asset dashboard UI
│   │   └── index.tsx
│   └── components/                          Shared WinPeek components
│
├── scripts/
│   └── winpeek-quality-check.py            ✅ CI quality gate
│
├── .gitlab-ci.yml                           ✅ CI pipeline
│
└── website/docs/winpeek/                   User + Developer docs (Docusaurus)
    ├── index.mdx                       🆕 Landing page
    ├── quickstart.md                    🆕 5-min quickstart
    ├── _category_.json                  ✅
    │
    ├── developer-guide/
    │   ├── _category_.json              🆕
    │   ├── architecture.md              ✅ This document
    │   ├── automation-engine.md         🆕 UIA engine internals
    │   ├── automation-database.md       🆕 DB schemas (CRM + Hub)
    │   ├── mim-protocol.md              🆕 MQTT topics + message format
    │   └── quality-gate.md              🆕 CI/CD quality enforcement
    │
    ├── features/
    │   ├── _category_.json              🆕
    │   ├── overview.md                  🆕 Feature overview (all 3 modules)
    │   ├── automation/
    │   │   ├── _category_.json          🆕
    │   │   ├── overview.md              🆕 Automation overview
    │   │   ├── wechat.md                🆕 WeChat CRM user guide
    │   │   ├── douyin.md                🆕 Douyin placeholder
    │   │   ├── kuaishou.md              🆕 Kuaishou placeholder
    │   │   ├── bilibili.md              🆕 Bilibili placeholder
    │   │   ├── xiaohongshu.md           🆕 Xiaohongshu placeholder
    │   │   └── shipinhao.md             🆕 Shipinhao placeholder
    │   ├── mim-chat.md                  ✅ MIM chat user guide
    │   └── assets.md                    ✅ Asset dashboard user guide
    │
    └── reference/
        ├── _category_.json              🆕
        ├── tools.md                     🆕 All Hermes tools reference
        └── schemas.md                   🆕 DB schema reference
```

## Three Modules

| Module | Backend | Frontend | Tools | User Doc |
|--------|---------|----------|-------|----------|
| **Automation** | `plugins/winpeek_rpa/platforms/` | `apps/.../winpeek/automation/` + per-platform panels | `winpeek_{platform}_*` | `features/automation/{platform}.md` |
| **MIM** | `gateway/winpeek_hub/` | `apps/.../winpeek/mim/` | `winpeek_mim_*` | `features/mim-chat.md` |
| **Assets** | `plugins/winpeek_rpa/shared/` | `apps/.../winpeek/assets/` | `winpeek_assets_*` | `features/assets.md` |

## Automation Platforms

Each platform follows the same structure:

```
plugins/winpeek_rpa/platforms/{name}/
├── __init__.py
├── README.md          ← Requirements + technical design for this platform
├── uia.py             ← UIA driver (window/focus/nav/click/type)
├── db.py              ← Platform-specific data storage
├── api.py             ← Eyes/Hands/Engine 3-layer orchestrator
├── collect.py         ← Content collector
└── analyze.py         ← Content analyzer (if applicable)

tools/winpeek_tools.py ← Register winpeek_{name}_* tools
skills/{name}-automation/SKILL.md ← Agent operation knowledge
apps/desktop/.../automation/ ← Panel rendered when platform selected
website/.../features/automation/{name}.md ← User guide
```

| Platform | Status | Complexity | Notes |
|----------|--------|------------|-------|
| **WeChat** | ✅ 11 files | High | Full CRM: friends, groups, chat, portrait, sales |
| **Douyin** | 1 file (stub) | Medium | Short video publish, analytics |
| **Kuaishou** | 1 file (stub) | Medium | Content publish, live management |
| **Bilibili** | 1 file (stub) | Medium | Video upload, danmaku interaction |
| **Xiaohongshu** | 1 file (stub) | Medium | Note publish,种草 marketing |
| **Shipinhao** | 1 file (stub) | Medium | WeChat ecosystem, content ops |

**WeChat is by far the most complex platform** — it has a full CRM with 15 database tables, 8-dimension portrait scoring, 13-tree relationship classification, sales pipeline, and bulk messaging. Other platforms are primarily content publishing + analytics.

## How to Add a New Platform

1. `mkdir plugins/winpeek_rpa/platforms/{name}/`
2. Write `README.md` with requirements + design
3. Implement `uia.py` (UIA driver for that app)
4. Register `tools/winpeek_tools.py` with `winpeek_{name}_*` tools
5. Write `skills/{name}-automation/SKILL.md`
6. Add panel to `apps/desktop/src/app/winpeek/automation/index.tsx`
7. Write `website/docs/winpeek/features/automation/{name}.md`
8. Run `python scripts/winpeek-quality-check.py`
