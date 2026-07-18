---
sidebar_position: 2
title: "中心化架构方案"
description: "MIM 中心化架构 + 运行时守护者方案 — 设计文档入口与摘要"
---

# MIM 中心化架构 + 运行时守护者

> 完整文档：[`docs/design/mim-centralized-runtime-architecture.md`](../../../docs/design/mim-centralized-runtime-architecture.md)
> 起草：Qoder Agent · 审核人：CC · 状态：待审核

## 目标一句话

Desktop 机器上只有一条对外连接——到 MIM 中心 serve 的 WebSocket。零 MySQL、零 MQTT 直连。

## 架构对比

```
❌ 现状（每台 Desktop 3 条连接）：
  Desktop → MySQL (凭据扩散)
  Desktop → MQTT  (8 台都连)
  Desktop → (无中心)

✅ 目标：
  Desktop → hermes serve ──WS──→ MIM 中心 → MySQL (唯一)
                                            → MQTT  (唯一)
```

## 核心决策（已拍板）

| # | 决策 | 结论 |
|---|------|------|
| D1 | Desktop 对外连接 | **MIM 中心 serve (WS)**，不是 MQTT |
| D2 | 降级策略 | **中心不可达直接报错**，不做本地缓存 |
| D3 | daemon 升级 | **运行时守护者**：发现→注册→心跳→上报 |
| D4 | swarm | 一机 N 智能体；动态 walk-in 自注册；批量心跳 |
| D5 | 设计参照 | 学习 Multica daemon/runtime 模型 |

## 5 个任务包

| 包 | 专家 | 文件 | 核心任务 |
|----|------|------|---------|
| A | 后端协议 | `winpeek_tools.py` + `server.py` | online 批量 uids、runtime_report、local_agents |
| B | 连接治理 | `hub_bridge.py` | center_url 感知，客户端模式跳过 MySQL/MQTT |
| C | daemon | `daemon.py` | 15 类检测、注册/心跳走转发入口 |
| D | 前端 | `mim/index.tsx` | 多身份切换、本机运行时、两步新建智能体 |
| E | 数据验证 | `tests/` + DDL | 双实例 E2E，断言零 3306/1883 出站 |

## 5 个开放问题（§12，待 CC 定案）

1. runtime 清单存哪里 → 倾向：中心内存 + nodes.json（不进 MySQL）
2. local_agents 不转发 → 倾向：本机答，无中心一致性需求
3. 心跳参数 → 倾向：维持 30s/120s
4. MCP_BLOCK 里删 MIM_BROKER → 倾向：删
5. hostname vs 新 machine 列 → 倾向：复用 hostname
