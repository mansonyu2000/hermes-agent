# Implementation Plan: Peeka 身份系统 + MIM 聊天修复

> Phase 2 from spec-driven-development. 2026-07-26 session.

## Architecture Decision

Peeka 身份管理合并进 SettingsView（`/settings?tab=peeka:*`），不创建独立 overlay。

## Dependency Graph

```
types.ts → SettingsView Peeka integration → Tabs (Profile/Accounts/Password/Organization/Devices/Agents)
                                        → PeekaLoginPanel
                                        → PeekaPopup menu sync
MIM fixes (standalone): contacts parse + history params

Backend: _make_org_handler rewrite → CRUD handlers → auto-discover → logging
```

## Verification Checkpoints

1. `npx tsc --noEmit` — 2 pre-existing errors, 0 new
2. Python compile — all 3 files pass
3. E2E: 15/15 backend RPC flows pass
4. MIM: contacts + history verified
5. Cross-component sync: peeka-changed event chain verified
