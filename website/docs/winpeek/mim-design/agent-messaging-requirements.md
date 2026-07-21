---
title: "MIM Agent-to-Agent 消息通道 — 需求分析"
status: draft
date: 2026-07-19
type: spec
origin: design-review
---

> **决策：MCP server 改造（包 F）降级为 V1.5。V1 先跑通消息管道主干（包 A-E）。**
> 本文档保留作为 V1.5 设计参考。

> 依据：[MIM V1 实施需求书](mim-v1-expert-team-implementation.md) · [feature-inventory](feature-inventory.md)
> 📍 [返回文档索引](overview.md) | 最后更新：2026-07-19

---

## 1. 目标一句话

让 Agent（Claude Code / Hermes / Qoder / Trae CLI）能通过 MIM 互相收发消息，
**每个 Agent 用自身 LLM + 自身环境 + 自身 MCP 工具回答问题**。
MIM 只做消息路由，不做推理。

## 2. 架构原则

```
┌─────────────────────────────────────────────────────┐
│                    MIM 中心（消息路由）               │
│  只管: 消息存储 / 转发 / 轮询                        │
│  不管: 推理 / 上下文 / 工具调用                       │
└──────┬──────────────────────────────┬───────────────┘
       │                              │
       ▼                              ▼
┌──────────────┐              ┌──────────────┐
│  Agent A     │              │  Agent B     │
│  (Claude)    │              │  (Hermes)    │
│              │              │              │
│  自身 LLM    │              │  自身 LLM    │
│  自身 MCP    │  ──消息──→   │  自身 MCP    │
│  自身环境    │  ←──回复──   │  自身环境    │
└──────────────┘              └──────────────┘
```

**核心结论**：MIM = 消息管道。Agent 的回答质量取决于 Agent 自身的 LLM + 环境 + 工具，不取决于 MIM。

## 3. 消息流

```
1. Agent A 调用 MCP 工具 mim_send(to_uid=2032, body="查 auth 模块")
2. MCP server → 本地 hermes serve → winpeek_mim_send RPC
3. MIM 中心 → 存储 + 路由到 B
4. Agent B 调用 MCP 工具 mim_poll()
5. MIM MCP server 返回:
   {
     messages: [
       {
         from_uid: 2031,
         from_name: "yu2-claude-1",
         from_role: "Agent",
         from_type: "claude-code",
         from_host: "yu2",
         from_title: "前端开发",
         from_skills: "React, TypeScript",
         content: "查 auth 模块"
       }
     ]
   }
6. Agent B (LLM) 用自身环境回答 → mim_send(to_uid=2031, body="auth 模块有3层...")
```

## 4. 收信人上下文设计

### 4.1 B 拿到什么

| 字段 | 来源 | 用途 |
|------|------|------|
| `from_uid` | 消息本身 | 回复时指定目标 |
| `from_name` | 消息本身 | 称呼对方 |
| `from_role` | `identity.get_by_uid(from_uid)` | 调整回答深度 |
| `from_type` | `identity.get_by_uid(from_uid)` | 知道对方是 AI，给结构化答案 |
| `from_host` | `identity.get_by_uid(from_uid)` | 同机器→路径可直引 |
| `from_title` | `identity.get_by_uid(from_uid)` | 了解对方专长 |
| `from_skills` | `identity.get_by_uid(from_uid)` | 了解对方能力域 |
| `content` | 消息本身 | 问题正文 |

全量来自已有数据（`identity` 表），MIM MCP server 在 `mim_poll` 时对每条消息调一次 `winpeek_mim_user_info` 拼上去。

### 4.2 B 不需要的（V1 不做）

- ❌ **对话历史** — A 问 B 就是当前问题，不需要"刚才说的那个"
- ❌ **A 的环境数据** — B 用自己的环境回答
- ❌ **幂等设计** — 同一问题不同时间问，B 的环境可能变了，答案不同
- ❌ **任务状态追踪** — V2

### 4.3 B 自身的上下文（Agent 自带，非 MIM 提供）

- 工作目录 / 项目代码
- MCP 工具清单（filesystem / git / DB / ...）
- 系统 prompt 中的角色定义

## 5. MCP Server 改造

[mcp_server.py](../../../../plugins/winpeek_rpa/mcp_server.py) 需新增 5 个 MIM 工具：

| 工具 | 功能 |
|------|------|
| `mim_send_message(to_uid, body)` | 发消息给指定 agent |
| `mim_poll_messages()` | 拉取新消息（含 sender profile） |
| `mim_get_contacts()` | 获取联系人列表 |
| `mim_get_history(peer_uid, limit)` | 获取对话历史 |
| `mim_whoami()` | 返回当前 agent 身份 |

### 5.1 与本地 hermes serve 通信

MCP server 通过 HTTP/WS 调本地 `hermes serve` 的 `winpeek_mim_*` RPC。
复用现有 `_mim_center_call` 逻辑（已封装转发判断），MCP server 零模式感知。

### 5.2 Agent 身份注入

daemon 在 MCP_BLOCK 的 `env` 中注入：

```python
{
    "MIM_UID": "2032",
    "MIM_NAME": "yu2-hermes-1",
    "MIM_AGENT_TYPE": "hermes",
}
```

MCP server 启动时从环境变量读，后续 `mim_send` / `mim_poll` 自动带身份。

## 6. 与现有模块的关系

- 复用 F3.1（发消息）、F3.2（收消息）、F3.3（历史）
- 新增 F10.x（Agent 消息通道）
- **MQTT 不动** — MCP server 不感知传输层

## 7. 消息回复决策机制

### 7.1 核心原则

**完全由 LLM 自主判断，不做独立规则引擎。**

Agent 收到消息后，LLM 综合评估三个维度决定是否回复：

```
                    Agent B 收到消息
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      发信人评估      问题评估      自身能力评估
            │             │             │
            └─────────────┼─────────────┘
                          ▼
                    LLM 决策输出
                    ┌────┼────┐
                    ▼    ▼    ▼
                  回复  忽略  暂缓
```

### 7.2 三维评估

| 维度 | 依据字段 | 决策逻辑 |
|------|---------|---------|
| **发信人** | `from_role`, `from_type`, `from_skills` | Developer 问技术问题 → 认真答；PM 问 → 简化语言；同类型 agent → 结构化回复 |
| **问题** | `content` | 问题匹配自身领域 → 答；完全无关 → 忽略 |
| **自身能力** | Agent 自有的 MCP 工具 + 工作环境 | 有对应工具 → 执行后答；无能力 → 回复"无法操作" |

### 7.3 决策输出

```
回复:  用自身工具查/执行 → mim_send_message(to_uid, body="结果...")
忽略:  问题超出能力域、垃圾信息 → 不做任何操作
暂缓:  "收到，当前在忙，稍后回复" → 后续再查
```

### 7.4 触发时机

Agent 不是常驻进程。poll 触发有两种方式：

| 方式 | 实现 | V1 使用 |
|------|------|:---:|
| **用户指令** | 用户说"查下 MIM 消息"，Agent 调 `mim_poll_messages` | 是 |
| **系统 prompt 植入** | daemon 在 Agent 配置中写入 MIM 行为指令 | 是 |

### 7.5 系统 prompt 片段

Daemon 在注入 MCP 配置时，同步写入 Agent 的配置目录，告知 Agent MIM 能力：

```markdown
[MIM Network]
You are part of a multi-agent network. Other AI agents may send you messages.
Available tools:
- mim_poll_messages() — check for new messages
- mim_send_message(to_uid, body) — reply to an agent
- mim_get_contacts() — list all network agents

At the start of your response, check if any agent has messaged you.
If yes, evaluate whether the question is relevant to your expertise and tools.
Decide: reply with mim_send_message(), defer, or ignore.
```

### 7.6 不需要的（V1 不做）

- ❌ 规则引擎（if role==X then Y）
- ❌ 优先级队列
- ❌ 任务调度器
- ❌ 消息 ACK/确认

**LLM 就是决策者。**

## 8. 涉及文件清单

| 文件 | 改动内容 | 归属 |
|------|---------|:---:|
| `plugins/winpeek_rpa/mcp_server.py` | 新增 5 个 MIM MCP 工具 + sender profile 组装 | 包 F |
| `apps/winpeek_injector/daemon.py` | MCP_BLOCK env 注入 MIM_UID/MIM_NAME/MIM_AGENT_TYPE + 写入系统 prompt 片段 | 包 F |
| `tools/winpeek_tools.py` | `_handle_mim_poll` 返回结果附加 sender profile | 包 A |
| `gateway/winpeek_hub/identity.py` | 无需改动（已有 `get_by_uid`） | — |
