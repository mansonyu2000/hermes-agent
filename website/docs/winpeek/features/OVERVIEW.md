---
sidebar_position: 5
title: "产品全景"
description: "WinPeek 各功能模块总览"
---

# WinPeek 产品全景

WinPeek 是构建在 Hermes Agent 之上的微信关系智能与自动化平台。核心能力：**从聊天中提取对人有用的决策信息，变成可行动的建议。**

## 产品愿景

把微信好友的几千条聊天记录，变成每天早上 5 条可行动的建议——该联系谁、该推进什么、什么逾期了、关系在降温还是在升温。

详见 [完整 PRD](../../../docs/requirements/wechat-prd.md)。

## 目标用户

| 角色 | 场景 | 好友规模 |
|------|------|----------|
| 销售/商务 | 客户关系管理、商机识别、群发营销 | 1000–5000 |
| 创业者/管理者 | 人脉维护、承诺追踪、经济往来 | 500–3000 |
| 个人用户 | 关系温度监控、关键事件提醒 | 200–2000 |

## 功能模块

### 已完成（Phase 0）

| 模块 | 说明 | 文档 |
|------|------|------|
| WinPeek RPA | 微信 UIA 自动化引擎（发消息/采集） | [Architecture](./ARCHITECTURE.md) |
| WinPeek Hub | 多 Agent MQTT 通信 + 消息归档 | [Hub API](./HUB-API.md) |
| MIM 协议 | 多 Hermes 实例互聊 | [Hub API → MQTT](./HUB-API.md#mqtt-topic-协议) |
| 桌面前端 | WinPeek 导航/视图（MIM/WeChat/Automation/Assets） | 代码：`apps/desktop/src/app/winpeek/` |

### 规划中（Phase 1+）

| 模块 | 优先级 | 设计文档 |
|------|--------|----------|
| 画像体系（8维评分） | P0 | [background/SUMMARY.md](../../../docs/design/background/SUMMARY.md) |
| CRM 系统（MasterDetail 布局） | P0 | [wechat-crm-design.md](../../../docs/design/wechat-crm-design.md) |
| 数据同步（自动采集） | P1 | [wechat-automation-menu.md](../../../docs/design/wechat-automation-menu-and-action-loop.md) |
| 行动闭环（洞察→执行） | P1 | 同上 |
| 消息模板/群发 | P2 | [CRM 设计](../../../docs/design/wechat-crm-design.md) |
| 数据统计/仪表盘 | P2 | 同上 |
| 主人自画像 | P3 | [画像哲学](../../../docs/design/background/philosophy-of-portrait.md) |

## 核心差异化

传统 CRM：
```
人手动录入 → 人手动分析 → 人手动行动
```

WinPeek：
```
AI 自动采集 → AI 自动画像 → AI 自动洞察 → AI 建议行动 → 人确认/自动执行
```

## 技术栈

| 层 | 技术 |
|------|------|
| Agent 框架 | Hermes Agent（Python） |
| 桌面自动化 | UIA (uiautomation) + pyautogui |
| Agent 通信 | MQTT (paho-mqtt) |
| 数据存储 | SQLite / MySQL |
| 前端 | React + Electron（Hermes Desktop） |
| AI 语义搜索 | agentmemory + bge-m3 (Ollama) |

---

参见：[架构详解](./ARCHITECTURE.md) · [快速上手](./QUICKSTART.md) · [完整 PRD](../../../docs/requirements/wechat-prd.md)
