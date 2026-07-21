---
sidebar_position: 10
title: "Peeka 消息分级处理方案"
description: "Daemon 三层路由 + 消息分类 + 寻址体系 — V1 主干流程设计"
---

# Peeka 消息分级处理方案

> 上游设计：[MIM 中心化架构方案](mim-centralized-runtime-architecture)
> 本文性质：**可执行的 Peeka V1 主干设计**——核心流程、消息分类、三层路由、寻址体系
> 决策依据：Peeka Daemon SPEC + PeekaAskResponder Skill 设计 + 团队讨论共识

---

## 0. 一句话目标

Daemon 作为 Agent 的「忠诚看护者」，对收到的消息做**三层路由决策**：

1. 话术匹配（规则，0 Token）→ Daemon 直接回复
2. Daemon 自答（本地知识）→ Daemon 直接回复
3. 转发 Agent（LLM 决策）→ Agent 处理并回复

同时提供标准化 Ask/Response 报文格式 + Peeka 分层命名体系。

---

## 1. 核心概念

### 1.1 三大角色

| 角色 | 对应代码 | 职责 |
|------|---------|------|
| **Daemon** | `apps/winpeek_injector/daemon.py` | Agent 发现/注册/心跳 + 消息分类 + 三层路由 |
| **Peeka Router** | `gateway/winpeek_hub/peeka_router.py`（新增） | 5 类消息识别 + 上下文拼接 + 三层决策 |
| **Agent** | Claude Code / Hermes / Qoder / Trae CLI | 收到请求后用自己的 LLM + 环境 + MCP 回答 |

### 1.2 消息 5 大类

| 分类 | 标签 | 示例 | 路由策略 |
|------|------|------|---------|
| 问候类 | `greeting` | "吃了没？"、"谢谢"、"早安" | 层1（规则）|
| 通知类 | `notification` | 版本更新、状态变更、系统告警 | 层1（标记存档）|
| 广告类 | `advertisement` | 营销推广、招商引流 | 过滤丢弃 |
| **请求类** | `request` | 提问咨询、指令操作、任务协作 | **层2/层3** |
| 其它类 | `other` | 杂项消息、测试报文、乱码 | 低优缓存/丢弃 |

### 1.3 三层路由决策

```
Daemon 收到消息
  │
  ├─ 分支 A: 消息分类 → 广告类 → 直接过滤（0 Token）
  │
  ├─ [层1] 话术匹配（规则，0 Token）
  │   条件: 问候/答谢/寒暄 + 预设匹配模板
  │   动作: Daemon 自动回复，记录[礼貌交互+1]，不打扰 Agent
  │   ↓ 不匹配 → 走层2
  │
  ├─ [层2] Daemon 自答（本地知识，0 Token）
  │   条件: 请求类 + Daemon 本地有答案
  │   动作: Daemon 查本地状态 → 回答，记录摘要
  │   ↓ 不匹配 → 走层3
  │
  └─ [层3] 转发 Agent（LLM 决策，消耗 Token）
      条件: 请求类 + Daemon 不知道答案
      动作: 打包上下文 → 推 Agent → Agent 回复 → 存档
```

---

## 2. Daemon 消息处理能力

### 2.1 话术匹配（层1）

Daemon 本地维护预设应答模板库，运行时判断消息是否匹配已知模板：

```python
GREETING_TEMPLATES = {
    "吃了没": "吃了，别担心。",
    "吃饭了吗": "吃了，别担心。", 
    "早安": "早安，新的一天开始。",
    "晚安": "晚安，早点休息。",
    "谢谢": "不客气。",
    "在吗": "在的，请说。",
}

def match_greeting(body: str) -> str | None:
    """规则匹配：完全匹配或关键短语模糊匹配"""
    for phrase, reply in GREETING_TEMPLATES.items():
        if phrase in body:
            return reply
    return None
```

V1 匹配规则：**子串包含**（`phrase in body`），不引入 NLP/AI。

### 2.2 本地知识库（层2）

Daemon 能回答的问题（0 Token）：

| 问题类型 | 数据源 | 示例 |
|---------|--------|------|
| 本机 agent 状态 | `_daemon_state` | "我有几个 Agent？" |
| 本机环境 | `socket.gethostname()` | "这台机器叫什么？" |
| 联系人查询 | `identity.list_all()` | "帮我查一下 2031 是谁" |
| 消息统计数据 | 本地计数器 | "今天收到了几条消息？" |

```python
DAEMON_KNOWLEDGE = {
    "agent_list": lambda state: f"本机有 {len(state.get('runtimes',[]))} 个 Agent",
    "machine_name": lambda _: socket.gethostname(),
}
```

### 2.3 上下文拼接（层3转发用）

当消息转发给 Agent 时，Daemon 自动拼接附加信息：

```json
// Agent 收到的数据包
{
  "body": "请帮我查一下 auth 模块的代码",
  "packed": true,
  "context": {
    "peer_uid": 2031,
    "peer_name": "yu2-claude-1",
    "peeka_name": "yu2CC-YU2-192.168.3.44-hotime.cn",
    "relation": "same_machine",  // 同机 → 路径可直接共享
    "tag": "request",
    "history_count": 3,
    "sender_title": "前端开发",
    "sender_skills": "React, TypeScript"
  }
}
```

### 2.4 礼貌交互计数器

Daemon 维护每个 Peeka 对的礼貌交互次数：

```python
# daemon 模块级
_politeness_count: dict[tuple[int, int], int] = {}  # (from_uid, to_uid) → count
```

每次层1自动回复后 `count += 1`，Agent 需要时可通过状态查询。

---

## 3. Peeka 分层命名体系

### 3.1 命名规则

```
{昵称简称}{Agent缩写}-{主机名}-{本地IP}-{域名}
```

| 层级 | 示例 | 作用 |
|------|------|------|
| 极简 | `pig` | 本地快速指代 |
| 简称+类型 | `pigCC` | 同机区分不同 agent |
| 机器级 | `pigCC-YU2` | 同局域网识别人 |
| 网络级 | `pigCC-YU2-192.168.3.44` | 跨设备精确寻址 |
| **完整** | `pigCC-YU2-192.168.3.44-hotime.cn` | **全局唯一** |

### 3.2 Agent 类型缩写

| agent_type | 缩写 |
|-----------|:----:|
| claude-code | CC |
| hermes | HM |
| qoder | QD |
| traecli | TC |

### 3.3 PeekaName 的关系推导

Daemon 收到消息时，根据 PeekaName 前缀推导关系：

| 规则 | 推导 | 对回复的影响 |
|------|------|-------------|
| 同 host | 同机器 | 文件路径直接共享 |
| 同域名(hotime.cn) | 同组织 | 专有名词无需解释 |
| 同昵称前缀(pig) | 家人/密切 | 亲密语气 |
| 不同域名 | 外部人员 | 完整上下文+正式语气 |

### 3.4 V1 实现

`identity.py` 的 `_row_to_dict` 新增 `peeka_name` 字段。

```python
def _build_peeka_name(nickname: str, agent_type: str, hostname: str, ip: str = "") -> str:
    abbr = AGENT_TYPE_ABBR.get(agent_type, "XX")
    prefix = nickname.split(abbr)[0].rstrip("-") if abbr in nickname else nickname
    ip_part = f"-{ip}" if ip else ""
    return f"{prefix}{abbr}-{hostname}{ip_part}-hotime.cn"
```

---

## 4. Ask/Response 报文格式

### 4.1 报文结构

客观问题（简单、无歧义）→ `{ "body": "1+3=?" }`，不包装。

需要上下文的请求 → 自动包裹：

```json
{
  "body": "我的工作完成了吗？",
  "format": "ask",
  "packed": true,
  "context": {
    "related_project": "hermes-agent",
    "history_count": 5,
    "peer_peeka_name": "yu2CC-YU2-192.168.3.44-hotime.cn"
  }
}
```

### 4.2 判断规则

| 条件 | `packed` | 原因 |
|------|:--------:|------|
| 纯数字/公式 | `false` | 客观问题 |
| 含疑问词（为什么、怎么、什么） | `true` | 需上下文 |
| >15 字符 | `true` | 大概率是真实问题 |
| 含项目名称/文件路径 | `true` | 需环境上下文 |

---

## 5. V1 主干 = 4 个代码

| 文件 | 改动类型 | 行数 | 说明 |
|------|---------|:---:|------|
| `gateway/winpeek_hub/identity.py` | 改造 | ~15 | `_row_to_dict` 加 `peeka_name` |
| `gateway/winpeek_hub/peeka_router.py` | **新增** | ~120 | 5 类消息分类 + 3 层路由 |
| `gateway/winpeek_hub/chat.py` | 改造 | ~20 | `send_message` 调用 peeka_router |
| `apps/winpeek_injector/daemon.py` | 改造 | ~30 | 注册拼 peeka_name + 话术模板库 |

**主干目标**：Agent A 发消息 → daemon 分类 → 问候自答 / 请求转发 → B 收到回复。

---

## 6. V1 不做清单

| 条目 | 原因 | 规划 |
|------|------|------|
| LLM 智能生成问候话术 | 规则即可，不需要 Token | V2 |
| 亲密关系自动升级 | 需交互频次统计 | V2 |
| 对话上下文 RAG | V1 只需基础拼接 | V2 |
| Peeka 完整全球寻址 | 跨网络场景需要 | V2 |
| MCP 工具（mcp_server.py）| 主干靠前端手动发收 | V1.5 |
| 群聊/广播 | 复杂度高 | V1.5 |
