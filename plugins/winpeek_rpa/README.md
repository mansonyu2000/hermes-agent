# WinPeek RPA — Multi-Platform Desktop Automation

Desktop automation engine for WeChat, Douyin, Kuaishou, Bilibili, Xiaohongshu, Shipinhao, and more. Each platform lives in `platforms/{name}/` with its own UIA driver, DB, and tools.

## Platforms

| Platform | Status | Features |
|----------|--------|----------|
| **WeChat** | ✅ 11 files, 4200+ lines | UIA engine, contact/chat collect, DB (SQLite/MySQL dual backend, 1962 contacts), CRM (portrait/sales/bulk), AI analysis (jieba + LLM) |
| Douyin | Stub | Short video publish, analytics |
| Kuaishou | Stub | Content publish, live management |
| Bilibili | Stub | Video upload, danmaku |
| Xiaohongshu | Stub | Note publish |
| Shipinhao | Stub | Content ops |

## Per-Platform Structure

```
platforms/{name}/
├── __init__.py
├── README.md          ← Requirements + technical design
├── uia.py             ← UIA driver
├── db.py              ← Data storage
├── api.py             ← Eyes/Hands/Engine orchestrator
├── collect.py         ← Content collector
└── analyze.py         ← Content analyzer
```

## WeChat Platform — Full Details

### Requirements

**V1.0 — Manual CRM**: Friend list (search/filter/sort, 2000+), 5-tab detail (Profile/Portrait/Chat History/Sales/Notes), dashboard, bulk messaging, sync, account management

**V2.0 — AI-Powered**: Auto portrait scoring (8-dim), insight engine (20+ rules), action loop (suggest → dispatch → feedback), economic ledger

### Architecture

```
WeChat GUI ← UIA → WeChatUIA (uia.py) → WeChatEngine (api.py) → WeChatDB (db.py)
                                     → Hermes Tools (tools/winpeek_tools.py) → Desktop UI
```

### Database (MySQL 192.168.3.23:3306/winpeek)

- **Existing** (8 tables, with data): wechat_friend (1962), wechat_group (180), wechat_chat (2262)
- **V1.0 New** (13 tables): CRM portrait + scoring + insight + sales + templates + enums
- **wechat_friend extensions** (15 columns): customer_level, sales_stage, heat_score, portrait_summary, ai_profile, is_blacklisted, remark, etc.
- **DDL**: `shared/crm_schema.sql`

### Hermes Tools (15 total)

| # | Tool | Phase |
|---|------|-------|
| 1-4 | winpeek_wechat_send, collect_msgs, collect_contacts, list_templates | ✅ V0 |
| 5-15 | winpeek_list_contacts, get_contact_detail, get_chat_history, get_portrait, update_portrait, list_groups, dashboard, crud_sales_log, bulk_send, ai_script, execute_insight | V1.0/V2.0 |

### Key Files (4200+ lines)

```
platforms/wechat/
├── uia.py (853)       UIA driver — window/focus/nav/click/send/memory
├── db.py (750)        Dual SQLite/MySQL backend, 8 tables, full CRUD
├── api.py (733)       3-layer engine (Eyes/Hands/Brain)
├── contacts.py (375)  Full contacts scanner + add friend
├── collect.py (396)   Profile + message collector
├── analyze.py (240)   jieba + LLM topic extraction
├── find.py (170)      Window find/search/send shortcuts
├── msg_collect.py (158) Single-session message collector
├── msg_traverse.py (249) Multi-session traverser
├── profile.py (261)   Deep profile reader
└── collect_contacts.py (325) Legacy contacts collector

shared/
├── crm_schema.sql     CRM 13 tables DDL
├── hub_schema.sql     Hub 4 tables DDL
├── software_scanner.py Installed software scanner
├── rpa_tools.py       UIA utilities + time parser
├── bg_input.py        Background input simulation
├── position_memory.py Bayesian position memory
└── config.py          Shared config
```
