# WinPeek RPA — WeChat Automation & CRM

Desktop automation engine for WeChat. Provides UIA-based automation tools via Hermes tool system.

## Requirements

### V1.0 — Manual CRM

| Module | Features | Status |
|--------|----------|--------|
| Account | Display current WeChat identity, switch account, logout | P0 |
| Friend List | Search, filter (level A/B/C/D/blacklist), sort (activity/name/heat), virtual scroll for 2000+ contacts | P0 |
| Friend Detail | 5 Tabs: Profile (info/contact/tags), Portrait (8-dim radar + 13-tree class + AI summary + events timeline), Chat History (full timeline + search + stats), Sales (level/stage/visit log/targets), Notes (rich text) | P0 |
| Group List | Group list sorted by activity, group detail (members/notice/activity) | P0 |
| Dashboard | Stats cards (total friends/groups/new/active), activity trend chart, top 20 hot contacts | P1 |
| Bulk Messaging | Recipient selector (by tag/level/manual), message editor with {variables}, AI script generation, send queue (5-8s interval, 200/day cap) | P1 |
| Message Templates | CRUD + categories (first contact/follow-up/holiday/payment/thanks), AI optimize, use count stats | P1 |
| Data Sync | Full/incremental contacts sync, chat history sync, progress bar, operation log | P0 |
| Statistics | Source distribution pie, customer level bar, sales funnel, activity heatmap | P2 |

### V2.0 — AI-Powered

| Module | Features |
|--------|----------|
| Auto Portrait | AI 8-dimension scoring (closeness/trust/respect/affection/biz/growth/credit/reciprocity) from chat analysis, score decay on inactivity |
| Insight Engine | 20+ rules (drift alert, opportunity signal, payment overdue, birthday, reconnect), daily Top 5 action suggestions with AI scripts |
| Action Loop | Priority scoring (0-1), auto-dispatch or confirm, feedback loop (reply=success, no reply=retry with different script) |
| Economic Ledger | Auto-extract amounts from chat, track loan/payment/gift, due date reminder |

## Architecture

```
WeChat GUI
    ↑ UIA (Windows UI Automation)
WeChatUIA (uia.py)         ← Eyes: read / Hands: click+type / Brain: LLM routing
    ↓
WeChatEngine (api.py)       ← Orchestrator: collect contacts/messages, send
    ↓
WeChatDB (db.py)            ← Dual SQLite/MySQL backend, 8 tables (existing) + 13 new tables (V1.0)
    ↓
Hermes Tools (tools/winpeek_tools.py) ← 15 tools registered
    ↓
Desktop UI (apps/desktop/src/app/winpeek/wechat/) ← React frontend
```

## Database

**Existing** (8 tables, MySQL 192.168.3.23:3306/winpeek):

| Table | Rows | Purpose |
|-------|------|---------|
| wechat_friend | 1962 | Contact profiles |
| wechat_group | 180 | Groups |
| wechat_group_member | 0 | Group membership |
| wechat_chat | 2262 | Chat messages |
| wechat_moment | 0 | Moments |
| wechat_moment_comment | 0 | Moment comments |
| wechat_video | 0 | Videos |
| wechat_operation_log | 0 | Operation audit |

**V1.0 New** (13 tables): wechat_relation_tree, wechat_friend_relation, wechat_friend_event, wechat_friend_finance (V2.0), friend_event, friend_score_log, friend_opportunity, friend_sales_log, actionable_insight, action_template, automation_rule, message_template, sys_enum_definition

**wechat_friend extensions** (15 columns): customer_level (A/B/C/D), sales_stage (lead→close), heat_score (0-100), portrait_summary, ai_profile (JSON), is_blacklisted, remark, last_contact_at, birthday, gender, email, estimated_amount, estimated_close, win_probability, obsidian_path

See `shared/crm_schema.sql` for complete DDL.

## Hermes Tools

| Tool | Phase | Function |
|------|-------|----------|
| winpeek_wechat_send | ✅ V0 | Send message to contact |
| winpeek_wechat_collect_msgs | ✅ V0 | Collect chat messages |
| winpeek_wechat_collect_contacts | ✅ V0 | Collect all contacts |
| winpeek_list_templates | ✅ V0 | List learned templates |
| winpeek_list_contacts | V1.0 | Paginated friend list + search + sort |
| winpeek_get_contact_detail | V1.0 | Single friend full profile |
| winpeek_get_chat_history | V1.0 | Chat history + search + filter |
| winpeek_get_portrait | V1.0 | 8-dim scores + classification + events |
| winpeek_update_portrait | V1.0 | Manual score/category edit |
| winpeek_list_groups | V1.0 | Group list |
| winpeek_dashboard | V1.0 | Aggregated stats |
| winpeek_crud_sales_log | V1.0 | Sales visit log CRUD |
| winpeek_bulk_send | V1.0 | Batch messaging |
| winpeek_ai_script | V2.0 | AI-generated message scripts |
| winpeek_execute_insight | V2.0 | Execute action suggestion |

## Key Files

```
plugins/winpeek_rpa/
├── plugin.yaml              Plugin manifest
├── README.md                This document
├── mcp_server.py            MCP tools
├── platforms/wechat/
│   ├── uia.py (853 lines)   UIA driver — window/focus/nav/click/send
│   ├── db.py (750 lines)    Dual SQLite/MySQL backend
│   ├── api.py (733 lines)   3-layer engine (Eyes/Hands/Brain)
│   ├── contacts.py (375)    Full contacts scanner
│   ├── collect.py (396)     Profile + message collector
│   ├── analyze.py (240)     jieba + LLM topic extraction
│   ├── find.py (170)        Window find/search/send
│   ├── msg_collect.py (158) Single-session collector
│   ├── msg_traverse.py (249) Multi-session traverser
│   └── profile.py (261)     Deep profile reader
└── shared/
    ├── crm_schema.sql        CRM 13 tables DDL
    ├── hub_schema.sql        Hub 4 tables DDL
    ├── software_scanner.py   Installed software scanner
    ├── rpa_tools.py          UIA utilities
    ├── bg_input.py           Background input simulation
    ├── position_memory.py    Bayesian position memory
    └── config.py             Shared config
```
