---
sidebar_position: 11
title: "Peeka V1 实施计划"
description: "任务分派、波次安排、接口契约 — 可执行计划"
---

# Peeka V1 实施计划

> 上游设计：[Peeka 消息分级处理方案](peeka-design)
> 本文性质：**任务分派 + 波次安排**——谁做什么、什么时候做、怎么做
> 当前状态：📋 已规划

---

## 0. 波次总览

```
波次 1（并行）           波次 2（并行）               收尾
┌─────────────────┐    ┌──────────────────────┐    ┌──────────┐
│ P1: Identity     │    │ P3: Peeka Router     │    │ P5: E2E  │
│ peeka_name 字段  │    │ 5类路由 + 三层决策    │    │ 主流程   │
│ 话术模板库       │    │                      │    │ 完整测试  │
├─────────────────┤    ├──────────────────────┤    └──────────┘
│ P2: MimView 整  │    │ P4: Ask/Response     │
│ 合(已有 包D)     │    │ 报文包装 + frontend  │
│                 │    │ peeka_name 展示      │
└─────────────────┘    └──────────────────────┘
```

---

## 1. 任务分派

### 包 P1 — Identity 扩展 + Daemon 话术模板

| 条目 | 文件 | 行数 | 说明 |
|------|------|:---:|------|
| P1.1 `identity._row_to_dict` 加 `peeka_name` | `gateway/winpeek_hub/identity.py` | ~10 | 新增 `_build_peeka_name()` + `_row_to_dict` 追加字段 |
| P1.2 daemon 注册时拼 peeka_name | `apps/winpeek_injector/daemon.py` | ~15 | `register_and_inject()` 里调用 `_build_peeka_name` |
| P1.3 daemon 话术模板库 | `apps/winpeek_injector/daemon.py` | ~15 | `GREETING_TEMPLATES` + `match_greeting()` |
| P1.4 daemon 礼貌交互计数器 | `apps/winpeek_injector/daemon.py` | ~10 | `_politeness_count` dict |

**负责人**: （我来实现）
**接口契约**:
- `_build_peeka_name(nickname, agent_type, hostname, ip="") → str`
- `match_greeting(body) → str | None`
- `record_politeness(from_uid, to_uid) → int` (返回当前计数)

---

### 包 P2 — 前端整合（包 D 已做）

包 D 已完成的工作不动。新增：

| 条目 | 文件 | 行数 | 说明 |
|------|------|:---:|------|
| P2.1 Profile 面板显示 peeka_name | `index.tsx` ProfilePanel | ~5 | 身份信息中加一行 PeekaName |

**负责人**: （我来实现）

---

### 包 P3 — Peeka Router（核心）

| 条目 | 文件 | 行数 | 说明 |
|------|------|:---:|------|
| P3.1 5 类消息分类器 | `gateway/winpeek_hub/peeka_router.py` | ~40 | 规则分类：greeting/notification/ad/request/other |
| P3.2 三层路由决策 | `gateway/winpeek_hub/peeka_router.py` | ~50 | 层1话术匹配 → 层2自答 → 层3转发 |
| P3.3 上下文拼接 | `gateway/winpeek_hub/peeka_router.py` | ~30 | 消息打包 + history + sender profile |

**负责人**: （我来实现）
**接口契约**:
- `route_incoming(from_uid, to_uid, body, sender_info) → dict` 返回路由决策
- `classify(body) → str` 返回 5 类 tag

---

### 包 P4 — Ask/Response 包装

| 条目 | 文件 | 行数 | 说明 |
|------|------|:---:|------|
| P4.1 `chat.py send_message` 调用 peeka_router | `gateway/winpeek_hub/chat.py` | ~20 | 新增路由调用 + 判断是否过滤/自答 |
| P4.2 `_handle_mim_send` 自动包装 body | `tools/winpeek_tools.py` | ~15 | `format="ask"`, `packed=True/False` |
| P4.3 poll 返回消息体含 peeka_name | `tools/winpeek_tools.py` | ~10 | `_handle_mim_poll` 拼接 sender peeka_name |

**负责人**: （我来实现）

---

### 包 P5 — E2E 验证

| 条目 | 说明 | 预期 |
|------|------|------|
| P5.1 daemon 注册含 peeka_name | 登录后 identity 返回 `peeka_name` | `pigCC-YU2-192.168.3.44-hotime.cn` |
| P5.2 问候消息自动回复 | 发"吃了没？"→ daemon 自动回"吃了，别担心。" | 0 Agent 介入 |
| P5.3 请求消息转发 | 发"帮我查 auth 模块"→ 转发给 Agent | 层3路由 |
| P5.4 广告过滤 | 发营销内容 → 不存档不转发 | 过滤 |
| P5.5 多 Agent A→B→回复 | 前端多身份切换 → 发消息 → 收到回复 | 全链路 |

---

## 2. 波次安排

| 波次 | 包含 | 时间 |
|:--:|------|:---:|
| **波次 1** | P1 (identity) + P2 (前端) | 当前 |
| **波次 2** | P3 (peeka_router) + P4 (包装) | 波次1之后 |
| **收尾** | P5 (E2E) | 波次2之后 |

---

## 3. V1 主干链路（可执行路径）

```
用户在前端发消息 "吃了没？" 给对方
  │
  ├─ 1. winpeek_mim_send → chat.py send_message
  │
  ├─ 2. peeka_router.classify("吃了没？") → "greeting"
  │
  ├─ 3. peeka_router.match_greeting("吃了没？") → "吃了，别担心。"
  │
  ├─ 4. Daemon 自动回复:
  │      peeka_router.auto_reply(from_uid, to_uid, "吃了，别担心。")
  │      → chat.py send_message（B→A 自动回复）
  │      → _politeness_count[(A, B)] += 1
  │      → 不打扰 Agent B（不推送到 B 的消息列表）
  │
  └─ 5. 前端 A 看到自动回复 "吃了，别担心。"（礼貌次数+1 仅在后台）

---
用户发请求 "帮我查 auth 模块" 给对方
  │
  ├─ 1. peeka_router.classify → "request"
  ├─ 2. peeka_router.daemon_known() → False（daemon 不知道 auth 模块）
  ├─ 3. peeka_router.assemble_context() → 打包上下文
  ├─ 4. 转发给 Agent B（入 B 的消息队列）
  ├─ 5. B 的前端轮询到新消息 → 显示
  └─ 6. B 的负责人回复 → 走正常 send_message → A 收到回复
```

---

## 4. 任务跟踪

每个子任务完成时更新状态。

| # | 任务 | 负责人 | 状态 | PR |
|:--:|------|:---:|:---:|:---:|
| P1.1 | identity peeka_name | 我 | 📋 | — |
| P1.2 | daemon 拼 peeka_name | 我 | 📋 | — |
| P1.3 | daemon 话术模板 | 我 | 📋 | — |
| P1.4 | daemon 礼貌计数器 | 我 | 📋 | — |
| P2.1 | 前端显示 peeka_name | 我 | 📋 | — |
| P3.1 | 5类消息分类器 | 我 | 📋 | — |
| P3.2 | 三层路由决策 | 我 | 📋 | — |
| P3.3 | 上下文拼接 | 我 | 📋 | — |
| P4.1 | chat.py 调 peeka_router | 我 | 📋 | — |
| P4.2 | send 自动包装 | 我 | 📋 | — |
| P4.3 | poll 含 peeka_name | 我 | 📋 | — |
| P5.1 | E2E daemon 注册含 peeka_name | 我 | 📋 | — |
| P5.2 | E2E 问候自动回复 | 我 | 📋 | — |
| P5.3 | E2E 请求转发 | 我 | 📋 | — |
| P5.4 | E2E 广告过滤 | 我 | 📋 | — |
| P5.5 | E2E 全链路 A→B→回复 | 我 | 📋 | — |
