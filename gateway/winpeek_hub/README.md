# WinPeek Hub

Multi-tenant message routing, archiving, and cross-platform delivery.
Runs inside Hermes Gateway as a zero-intrusion integration.

## Enable

```bash
export WINPEEK_HUB_ENABLED=1
hermes serve
```

## Components

| Module | File | Responsibility |
|--------|------|---------------|
| Bridge | `hub_bridge.py` | Zero-intrusion loader, hooks into gateway startup |
| Tenant | `tenant.py` | Multi-tenant management, MySQL-based |
| Routing | `routing.py` | Cross-platform message delivery |
| Archive | `archive.py` | Message archiving (MySQL / JSONL / off) |
| Identity | `identity.py` | MIM identity registration (JSONL) |
| MQTT | `mqtt_adapter.py` | MIM MQTT communication |

## Database

MySQL `winpeek` database with tables:
- `tenants` — tenant definitions
- `users` — tenant member bindings (platform → user)
- `hub_messages` — archived messages

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WINPEEK_HUB_ENABLED` | `0` | Set to `1` to enable |
| `WINPEEK_DB_HOST` | `192.168.3.23` | MySQL host |
| `WINPEEK_DB_PORT` | `3306` | MySQL port |
| `WINPEEK_DB_USER` | `winpeek` | MySQL user |
| `WINPEEK_DB_PASS` | `` | MySQL password |
| `WINPEEK_DB_NAME` | `winpeek` | MySQL database |
| `HUB_ARCHIVE_ENGINE` | `mysql` | Archive backend: `mysql` / `jsonl` / `off` |

## License

WinPeek Hub — part of the Hermes Agent WinPeek extension.
