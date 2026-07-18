---
sidebar_position: 1
title: "MIM 知识库地图"
description: "MIM 全部 10 份设计文档的入口 — 阅读顺序、文档分类、健康状态、代码↔文档索引"
---

# MIM 知识库地图

> 最后更新：2026-07-18 · 状态：**文档补全完成，V1 可开工**

## 文档清单（10 份）

```
website/docs/winpeek/mim-design/
├── overview.md                    ← 📍 知识库地图（你在这里）
├── file-map.md                    ← 13 个核心文件关系图
├── ui-interaction-spec.md         ← UI 交互规格（登录/联系人/聊天/多身份）
├── test-plan.md                   ← 测试计划（单元 + E2E + 手工验收）
├── v1-acceptance-checklist.md     ← V1 集成验收 Checklist（10 类 45 项）
├── architecture.md                ← 中心化架构方案摘要
├── capability-audit.md            ← MIM vs Hermes 原生聊天功能差距
├── migration-audit.md             ← 旧版 winpeek-prod → 新版 功能遗漏盘点
└── group-chat-spec.md             ← 群聊功能规格（数据模型 + RPC + UI）

docs/
├── design/mim-centralized-runtime-architecture.md  ← 中心化架构方案 (Qoder, 最权威)
├── requirements/mim-prd.md                         ← 产品需求规格说明书
├── plan/mim-v1-expert-team-implementation.md       ← 专家团实施计划书 (Qoder本地)
└── plan/mim-idor-security-issues.md                ← 4 个 IDOR 安全漏洞 (待修复)

website/docs/winpeek/
├── mim-message-center-setup.md     ← 消息中心部署指南 (运维)
├── code-review-mim-db-refactor.md  ← DB 重构 Code Review 闭环
└── debug-vite-config-leva-zustand.md ← leva/zustand 调试复盘
```

## 阅读顺序（新 Agent 入职）

| 顺序 | 文档 | 读完后知道 |
|------|------|-----------|
| 1 | `docs/requirements/mim-prd.md` | 做什么 |
| 2 | `docs/design/mim-centralized-runtime-architecture.md` | 怎么做（最权威） |
| 3 | `docs/plan/mim-v1-expert-team-implementation.md` | 谁做哪块 |
| 4 | **ui-interaction-spec** | 界面长什么样 |
| 5 | **group-chat-spec** | 群聊怎么设计 |
| 6 | **capability-audit** | 现在差什么 |
| 7 | **migration-audit** | 旧版有什么，新版漏了什么 |
| 8 | **test-plan** | 怎么验证 |
| 9 | **v1-acceptance-checklist** | 做完的标准是什么 |
| 10 | `docs/plan/mim-idor-security-issues.md` | 有什么安全隐患 |

## 文档类型分类

| 类型 | 文档 | 用途 |
|------|------|------|
| **需求** | `mim-prd.md` | 产品定义 |
| **架构** | `architecture.md` + `mim-centralized-runtime-architecture.md` | 技术决策 |
| **计划** | `mim-v1-expert-team-implementation.md` | 任务拆分 |
| **规格** | `ui-interaction-spec` + `group-chat-spec` | 实现参照 |
| **审计** | `capability-audit` + `migration-audit` | 差距分析 |
| **测试** | `test-plan` | 测试用例 |
| **验收** | `v1-acceptance-checklist` | 完工标准 |
| **运维** | `mim-message-center-setup.md` | 部署操作 |
| **经验** | `code-review-mim-db-refactor.md` + `debug-vite-config-leva-zustand.md` | 避坑 |
| **安全** | `mim-idor-security-issues.md` | 漏洞跟踪 |

## 文档健康状态

| 文档 | 状态 | 说明 |
|------|:--:|------|
| `overview.md` | 🟢 | 本文，已更新 |
| `file-map.md` | 🟢 | 无问题 |
| `ui-interaction-spec.md` | 🟢 | 新创建 |
| `test-plan.md` | 🟢 | 新创建 |
| `v1-acceptance-checklist.md` | 🟢 | 新创建 |
| `architecture.md` | 🟢 | §12 开放问题待 CC 定案 |
| `capability-audit.md` | 🟢 | 无问题 |
| `migration-audit.md` | 🟢 | 无问题 |
| `group-chat-spec.md` | 🟢 | 从旧版 winpeek-prod 提取 |
| `mim-centralized-runtime-architecture.md` | 🟢 | 完整设计 |
| `mim-v1-expert-team-implementation.md` | 🔴 | **在 QODER 本地，未 push** |
| `mim-prd.md` | 🟡 | 2 个死链 |
| `mim-idor-security-issues.md` | 🟡 | 待 V1 实现时修复 |
| `docs/plan/README.md` | 🔴 | MIM 部分过时 |
| `mim-message-center-setup.md` | 🟢 | 无问题 |
| `code-review-mim-db-refactor.md` | 🟢 | 闭环已归档 |
| `debug-vite-config-leva-zustand.md` | 🟢 | 闭环已归档 |

## 代码 ↔ 文档 快速索引

| 要改的文件 | 先读文档 |
|-----------|---------|
| `gateway/winpeek_hub/hub_bridge.py` | architecture §5.1 + 实施计划书 包B |
| `tools/winpeek_tools.py` | architecture §4.1 + 实施计划书 包A + IDOR 文档 |
| `tui_gateway/server.py` | 实施计划书 包A |
| `apps/winpeek_injector/daemon.py` | architecture §5.2 + 实施计划书 包C |
| `apps/desktop/.../mim/index.tsx` | **ui-interaction-spec** + architecture §5.4 + 实施计划书 包D |
| `gateway/winpeek_hub/chat.py` | **group-chat-spec** §3 + PRD §4 |
| `gateway/winpeek_hub/identity.py` | PRD §3 + architecture §4.1 |
| 新群聊 DDL | **group-chat-spec** §2.1 |
| 测试编写 | **test-plan** + **v1-acceptance-checklist** |
