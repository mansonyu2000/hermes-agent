---
sidebar_position: 1
title: "MIM 设计文档总览"
description: "MIM 知识库入口 — 文档体系、阅读顺序、健康状态"
---

# MIM 设计文档总览

> 最后更新：2026-07-18 · 状态：V1 开工前文档盘点

## 文档体系

```
docs/design/mim/README.md          ← 知识库地图（入口）
docs/design/mim-centralized-runtime-architecture.md  ← 中心化架构方案（权威）
docs/plan/mim-v1-expert-team-implementation.md       ← 专家团实施计划书
docs/requirements/mim-prd.md                         ← 产品需求规格说明书
docs/plan/mim-idor-security-issues.md                ← 安全漏洞记录
website/docs/winpeek/mim-message-center-setup.md     ← 部署指南
```

## 阅读顺序（新 Agent 入职）

| 顺序 | 文档 | 为什么 |
|------|------|--------|
| 1 | `mim-prd.md` | 先知道"做什么" |
| 2 | `mim-centralized-runtime-architecture.md` | 知道"怎么做"（最权威） |
| 3 | `mim-v1-expert-team-implementation.md` | 知道"谁做哪块" |
| 4 | `mim-message-center-setup.md` | 运维参考 |
| 5 | `code-review-mim-db-refactor.md` | 避坑经验 |
| 6 | `debug-vite-config-leva-zustand.md` | 避坑经验 |
| 7 | `mim-idor-security-issues.md` | 安全注意事项 |

## 文档健康检查

| 文档 | 状态 | 问题 |
|------|:--:|------|
| `mim-prd.md` | 🟡 | 时间戳 7-12，架构已演进；2 个死链 |
| `mim-centralized-runtime-architecture.md` | 🟢 | 内容准确，§12 开放问题待定 |
| `mim-v1-expert-team-implementation.md` | 🔴 | 仍在 QODER 本地，未 push |
| `mim-message-center-setup.md` | 🟢 | 无问题 |
| `code-review-mim-db-refactor.md` | 🟢 | 闭环已归档 |
| `debug-vite-config-leva-zustand.md` | 🟢 | 闭环已归档 |
| `mim-idor-security-issues.md` | 🟡 | 已记录，待修复时消耗 |

## 明显缺失

| 缺失项 | 优先级 |
|--------|:--:|
| 测试计划（单元/E2E/验收用例） | 🔴 |
| UI 交互规格（多身份切换、两步新建智能体） | 🔴 |
| 文件关系图（winpeek_hub 6 模块依赖） | 🟡 |
| V1 集成验收 Checklist | 🟡 |
