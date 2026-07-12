# WinPeek — Desktop Frontend

WinPeek module views under Hermes Desktop Electron app.

## Views

| View | Route | Component | Status |
|------|-------|-----------|--------|
| **Automation** | `/automation` | `automation/index.tsx` | Platform switcher (6 tabs) + per-platform panel |
| **MIM Chat** | `/mim` | `mim/index.tsx` | Multi-agent messaging (371 lines) |
| **Assets** | `/assets` | `assets/index.tsx` | Computer asset dashboard (150 lines) |
| **WeChat CRM** | panel in Automation | `wechat/index.tsx` | CRM master-detail (354 lines) |

## Automation Platform Switcher

`automation/index.tsx` renders a tab bar (6 platforms) + the active platform's panel. WeChat is currently the only implemented panel. Other platforms are placeholders.

Each new platform needs its own panel component — either as a sub-page under `automation/` or as a dedicated component file loaded by platform key.

## Current State

| View | Real Data | Mock Data |
|------|-----------|-----------|
| Automation (WeChat) | 8 contact mock, local send | ✅ partial |
| MIM | localStorage identity, 8 contact mock | ✅ all mock |
| Assets | 11 software mock, 2 disk mock | ❌ all mock |

## Pending Work

- WeChat: 5 Tab detail, dashboard, bulk messaging, sync (see `plugins/winpeek_rpa/README.md` for full requirements)
- MIM: Replace mock with real API (see `gateway/winpeek_hub/README.md`)
- Assets: Connect to `software_scanner.py` (see `website/docs/winpeek/features/assets.md`)

## Tech Stack

- React 19 + TypeScript (strict)
- Vite 6
- nanostores (state)
- Tailwind CSS + shadcn/ui
- `useGatewayRequest()` → Hermes IPC bridge
