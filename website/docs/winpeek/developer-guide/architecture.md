---
sidebar_position: 1
title: "WinPeek Architecture"
description: "WinPeek module design — how WeChat CRM, MIM, and Assets extend Hermes Agent following upstream plugin/tool/skill conventions"
---

# WinPeek Architecture

WinPeek is a Hermes Agent extension module providing three capabilities: WeChat CRM, multi-agent instant messaging, and computer asset management.

## Design Principle

Follow Hermes upstream: **Plugin** for backend + **Tool** for agent interface + **Skill** for agent knowledge + **website/docs** for user docs.

Each feature = one self-contained directory. No separate `docs/design/` / `docs/requirements/` / `docs/plan/` layers — those live in the plugin's `README.md` and `website/docs/`.

## Module Map

```
hermes-agent/
│
├── plugins/winpeek_rpa/                    Feature 1: WeChat CRM
│   ├── plugin.yaml                        Plugin manifest
│   ├── README.md                          Design + requirements (single source of truth)
│   ├── platforms/wechat/                  11 files — UIA engine, DB, analyze, collect
│   ├── shared/                            crm_schema.sql, software_scanner, RPA utils
│   ├── skills/wechat/__init__.py          Agent skill loader
│   └── mcp_server.py                      MCP server
│
├── gateway/winpeek_hub/                    Feature 2: MIM Chat
│   ├── README.md                          Design + requirements
│   ├── identity.py                        Identity register/login
│   ├── mqtt_adapter.py                    MQTT send/receive
│   ├── archive.py                         Message archive
│   ├── routing.py                         Cross-platform routing
│   ├── tenant.py                          Multi-tenant
│   └── hub_bridge.py                      Gateway integration
│
├── skills/
│   ├── wechat-automation-rules/SKILL.md   Agent: WeChat operation rules
│   ├── trace-to-template/SKILL.md         Agent: learn from traces
│   ├── software-self-learning/SKILL.md    Agent: self-learn software ops
│   └── software-assets/wechat.md          Agent: WeChat asset card
│
├── tools/
│   └── winpeek_tools.py                   All WinPeek Hermes tools
│
├── apps/desktop/src/app/winpeek/          Desktop frontend
│   ├── wechat/                             WeChat CRM UI
│   ├── mim/                                MIM chat UI
│   ├── assets/                             Asset dashboard UI
│   └── automation/                         Platform switcher
│
└── website/docs/winpeek/                   User + Developer docs (Docusaurus)
    ├── index.mdx                           Landing page
    ├── quickstart.md                       Get started
    ├── features/
    │   ├── wechat-crm.md                   WeChat CRM user guide
    │   ├── mim-chat.md                     MIM user guide
    │   └── assets.md                       Asset user guide
    ├── developer-guide/
    │   ├── architecture.md                 This document
    │   ├── wechat-database.md              DB schema reference
    │   ├── wechat-engine.md                UIA automation engine
    │   ├── mim-mqtt.md                     MQTT protocol
    │   └── quality-gate.md                 Quality CI/CD
    └── reference/
        ├── tools.md                        All Hermes tools
        └── schemas.md                      DB schemas
```

## How to Add a Feature

1. Create the backend in `plugins/<name>/` or `gateway/<name>/`
2. Write a `README.md` containing both requirements and technical design
3. Register Hermes tools in `tools/winpeek_tools.py`
4. Write Agent knowledge as `skills/<name>/SKILL.md`
5. Build the frontend in `apps/desktop/src/app/winpeek/<name>/`
6. Write user docs in `website/docs/winpeek/features/<name>.md`
7. Run `python scripts/winpeek-quality-check.py` before commit

## Feature Details

| Feature | Backend | Frontend | Skill | User Doc |
|---------|---------|----------|-------|----------|
| WeChat CRM | `plugins/winpeek_rpa/` | `apps/.../wechat/` | `skills/wechat-automation-rules/` | `features/wechat-crm.md` |
| MIM Chat | `gateway/winpeek_hub/` | `apps/.../mim/` | — | `features/mim-chat.md` |
| Assets | `plugins/winpeek_rpa/shared/` | `apps/.../assets/` | `skills/software-assets/` | `features/assets.md` |
