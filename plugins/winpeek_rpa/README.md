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

### Hermes Tools

| Tool | Phase | Function |
|------|-------|----------|
| `winpeek_wechat_send` | ✅ V0 | Send message to contact |
| `winpeek_wechat_collect_msgs` | ✅ V0 | Collect chat messages |
| `winpeek_wechat_collect_contacts` | ✅ V0 | Collect all contacts |
| `winpeek_list_templates` | ✅ V0 | List learned templates |
| `winpeek_list_contacts` | V1.0 | Paginated friend list + search + sort |
| `winpeek_get_contact_detail` | V1.0 | Single friend full profile |
| `winpeek_get_chat_history` | V1.0 | Chat history + search + filter |
| `winpeek_get_portrait` | V1.0 | 8-dim scores + classification + events |
| `winpeek_update_portrait` | V1.0 | Manual score/category edit |
| `winpeek_list_groups` | V1.0 | Group list |
| `winpeek_dashboard` | V1.0 | Aggregated stats |
| `winpeek_crud_sales_log` | V1.0 | Sales visit log CRUD |
| `winpeek_bulk_send` | V1.0 | Batch messaging |
| `winpeek_ai_script` | V2.0 | AI-generated message scripts |
| `winpeek_execute_insight` | V2.0 | Execute action suggestion |

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
