---
sidebar_position: 1
title: "WeChat CRM"
description: "AI-powered WeChat contact management — friend portrait, sales tracking, bulk messaging"
---

# WeChat CRM

AI-powered WeChat desktop client automation. Collect contacts and chat history via UIA, build multi-dimensional portraits, and manage customer relationships.

## Quick Start

```bash
# Collect all contacts from WeChat
python plugins/winpeek_rpa/platforms/wechat/contacts.py --collect

# Send a message
python plugins/winpeek_rpa/platforms/wechat/find.py --to "Name" --msg "Hello"
```

Or through Hermes Agent chat:

```
> Collect my WeChat contacts
> Send "Hello" to 许国勇
> Show me 许国勇's portrait
```

## Features

### Friend Management

Browse 2000+ contacts with search, multi-level filtering (A/B/C/D/blacklist), and sorting (by heat, activity, name). Click any contact to see 5 tabs:

- **Profile** — Basic info, contact details, tags, source
- **Portrait** — 8-dimension radar chart (closeness/trust/respect/affection/business value/growth value/credit/reciprocity), 13-tree relationship classification, AI-generated summary, key events timeline
- **Chat History** — Full message history with search, date filter, message type filter, and statistics
- **Sales** — Customer level (A/B/C/D), 7-stage pipeline (lead→close), visit log, sales targets
- **Notes** — Rich text notes with AI-generated summary

### Dashboard

Stats overview (total friends, groups, new this month, active), message trend chart, top 20 hot contacts, customer level distribution.

### Bulk Messaging

Select recipients by tag, level, or manually. Write message with {name}, {company} variables. AI generates multiple script candidates with tone options (friendly/formal/humorous). Send queue with 5-8s interval and 200/day cap.

### Data Sync

Full or incremental contact and chat history sync from WeChat PC client. Progress display with operation logging.

## Architecture

```
WeChat GUI ← UIA → WeChat Engine → WeChatDB → Hermes Tools → Desktop UI
```

See [Developer Guide](../developer-guide/architecture.md) for details.

## Related

- [Quickstart](../quickstart.md)
- [Hermes Tools Reference](../reference/tools.md)
- [Source: plugins/winpeek_rpa/](../../../plugins/winpeek_rpa/README.md)
