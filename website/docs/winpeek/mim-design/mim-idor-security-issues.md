---
sidebar_position: 12
title: "安全漏洞：IDOR (uid 参数)"
description: "转发层 4 个 IDOR 安全漏洞记录 — 待 V1 实现时一并修复"
---

name: mim-idor-security-issues
description: QODER 转发层 4 个 IDOR 安全漏洞 — 待修复，勿遗忘
metadata:
  type: project
---

# MIM 转发层安全漏洞 (2026-07-18 安全审查)

**来源**: 自动化安全审查，针对 QODER 提交 `d20b4c0e6` 的 `tools/winpeek_tools.py`

**状态**: ⚠️ 已记录，待修复（user 说了"先记录下来"）

---

## 漏洞 1-3：IDOR — `uid` 参数信任客户端

`_handle_mim_send`、`_handle_mim_poll`、`_handle_mim_history` 三个函数里：

```python
uid = int(args.get("uid") or 0) or active_uid()
```

客户端传什么 uid 就用什么，无身份校验。攻击者可伪造 uid 以任何人身份发消息/收件/查历史。

**正确做法**：uid 应从 WebSocket 连接绑定的身份派生，或 login 返回 session token，后续请求传 token 反查 uid。

**位置**: `tools/winpeek_tools.py`
- `_handle_mim_send` (L360)
- `_handle_mim_poll` (L375)
- `_handle_mim_history` (L511)

---

## 漏洞 4：Token 走 URL 查询参数

```python
full_url = f"{ws_url}?token={token}" if token else ws_url
conn = websocket.create_connection(full_url, timeout=10)
```

Token 出现在 URL 里 → HTTP 代理日志/浏览器历史/中间人缓存可能泄露。

**正确做法**：改为自定义 HTTP header（`X-Hermes-Session-Token`），服务端 `_ws_auth_reason` 已在 `dashboard_auth/middleware.py` 支持该 header。

**位置**: `tools/winpeek_tools.py` L296

---

**修复时机**: 由 user 决定 — 可能在 V1 实现时一并修，或单独提交修复。
**如何修复**: 参见 [[mim-centralized-architecture]] 方案 §12。
