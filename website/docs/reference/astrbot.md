---
sidebar_position: 6
title: "AstrBot 架构参考"
description: "AstrBot 开源多平台聊天机器人框架的架构分析，以及可借鉴到 MIM 的设计模式"
---

> 来源：[AstrBot 架构设计——消息处理篇](https://blog.soulter.top/posts/astrbot-arch-message-handle.html)
> 📍 [返回文档索引](README) | 最后更新：2026-07-18

---

## AstrBot 是什么

开源多平台 LLM 聊天机器人框架，支持 QQ/微信/Telegram + GPT/Gemini/Llama。从 1000 行单体演进到 16000 行模块化架构。

## 核心模式

### 事件总线

```
消息平台 → 统一消息格式 → asyncio.Queue → 事件总线 → Pipeline(Preprocess→LLM→Postprocess→Respond)
```

**对应 MIM**：MIM 中心已是事件总线；desktop 只调 RPC，不连 MySQL/MQTT（平台只上报）。

### 流水线

消息处理拆为 Stage 流水线，调度器按 `STAGES_ORDER` 执行。

**对应 MIM**：V2 可考虑将 `chat.py` 的线性处理改为 `Preprocess → Route → Persist → Deliver → Ack`。

### unique_msg_origin 寻址

`"平台:消息类型:session_id"` 一个字符串覆盖所有寻址场景。

**对应 MIM**：可引入 `"{machine}:{agent_type}:{uid}"` 替代多字段组合。

### Bootstrap 启动

按严格顺序加载 13 个组件，`asyncio.gather()` 并行长任务。

**对应 MIM**：`try_load_hub()` 可重构为显式阶段式加载。

## 建议采纳

| 优先级 | 借鉴点 | 应用 |
|--------|--------|------|
| 🔴 | 平台只上报（解耦） | V1 零直连 |
| 🔴 | unique_msg_origin | daemon 上报+路由 |
| 🟡 | Bootstrap 显式加载 | try_load_hub 重构 |
| 🟡 | Pipeline Stage | V2 chat.py |
