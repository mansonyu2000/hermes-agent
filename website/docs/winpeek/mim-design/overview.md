---
sidebar_position: 1
title: "MIM 知识库地图"
description: "MIM 全部 8 份设计文档入口 — feature-inventory 是唯一功能清单，其余为独立参考文档"
---

# MIM 知识库地图

> 最后更新：2026-07-18 · 状态：**文档整理完成，8 份文档无冗余**

## 文档清单（8 份）

```
website/docs/winpeek/mim-design/
├── overview.md                        ← 📍 知识库地图（你在这里）
├── feature-inventory.md               ← 📋 功能清单与实现决策（唯一事实来源）
├── file-map.md                        ← 13 个核心文件关系图
├── test-plan.md                       ← 测试计划
├── v1-acceptance-checklist.md         ← V1 验收 Checklist（10类45项）
├── mim-centralized-architecture.md    ← 中心化架构完整方案（QODER）
├── mim-prd.md                         ← 产品需求规格说明书
└── mim-idor-security-issues.md        ← 安全漏洞（待修复）

website/docs/winpeek/
├── mim-message-center-setup.md        ← 部署指南
├── code-review-mim-db-refactor.md     ← DB重构 Review 闭环
└── debug-vite-config-leva-zustand.md  ← 调试复盘
```

## 阅读顺序

| 顺序 | 文档 | 读完后知道 |
|------|------|-----------|
| 1 | **feature-inventory** | 全部功能的状态 + 每个功能的决策 |
| 2 | mim-centralized-architecture | 架构设计 |
| 3 | mim-prd | 产品需求背景 |
| 4 | file-map | 代码在哪、谁依赖谁 |
| 5 | test-plan | 怎么测试 |
| 6 | v1-acceptance-checklist | 做到什么程度算完成 |
| 7 | mim-idor-security-issues | 安全隐患 |

## 文档类型

| 类型 | 文档 | 用途 |
|------|------|------|
| **功能清单** | feature-inventory | **唯一事实来源** — 全部功能状态+决策 |
| **架构** | mim-centralized-architecture | 技术决策与设计 |
| **需求** | mim-prd | 产品定义 |
| **参考** | file-map | 代码导航 |
| **测试** | test-plan | 测试用例 |
| **验收** | v1-acceptance-checklist | 完工标准 |
| **安全** | mim-idor-security-issues | 漏洞跟踪 |
| **运维** | mim-message-center-setup | 部署操作 |
| **经验** | code-review-* / debug-* | 避坑 |

## 已合并删除（不再存在）

以下 9 份文档内容全部并入 `feature-inventory.md`：

- `capability-audit.md` — MIM vs Hermes 原生对比
- `migration-audit.md` — 旧版→新版功能遗漏
- `group-chat-spec.md` — 群聊功能规格
- `ui-interaction-spec.md` — UI 交互规格
- `architecture.md` — 架构摘要（完整版保留）
- `chat-features.md` (旧版) — 群聊增强
- `chat.md` (旧版) — 会话功能
- `messaging.md` (旧版) — 消息收发
- `group-chat-collaboration.md` (旧版) — 群聊协作

## 代码 ↔ 文档 快速索引

| 要改的文件 | 先读 |
|-----------|------|
| `hub_bridge.py` | feature-inventory §七 + 架构 §5.1 |
| `winpeek_tools.py` | feature-inventory §七 + IDOR文档 |
| `daemon.py` | feature-inventory §七 + 架构 §5.2 |
| `mim/index.tsx` | feature-inventory §九 + 架构 §5.4 |
| `chat.py` | feature-inventory §三 + §四 |
| `identity.py` | feature-inventory §一 |
