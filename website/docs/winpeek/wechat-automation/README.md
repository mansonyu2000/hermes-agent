---
sidebar_position: 1
title: "WeChat RPA 设计文档总索引"
description: "WinPeek WeChat RPA 微信自动化模块的全部设计文档入口，包含 PRD、UI 设计、代码架构、数据库设计、背景哲学"
---

# WeChat RPA — 文档总索引

> **模块名称**：WinPeek RPA — WeChat Automation（微信桌面自动化）
> **代码位置**：`plugins/winpeek_rpa/`（25 个 Python 文件）
> **最后更新**：2026-07-18

---

## 文档地图

```
website/docs/winpeek/wechat-automation/
├── README.md                         ← 你在这里（总索引）
├── wechat-prd.md                     ← 产品需求规格（功能定义、验收标准）
├── wechat-crm-design.md              ← UI/UX 页面设计（布局、组件、交互）
├── wechat-automation-menu.md         ← 菜单体系 + 画像驱动行动闭环
├── wechat-database-design.md         ← 数据库设计（13 表、数据链路）
├── wechat-code-architecture.md       ← 代码架构地图（模块职责、调用关系）
├── wechat-background-philosophy.md   ← 背景哲学（8维评分、13树分类、行动闭环）
├── wechat-mcp-tools.md               ← MCP 工具清单（感知层 + 操作层）
├── wechat-uia-reference.md           ← UIA AutomationId 参考表
├── wechat-rpa-navigation.md          ← RPA 导航原理（三层定位、虚拟列表三戒）
└── wechat-development-standards.md   ← 开发规范（文件创建、Git 门禁）

↗ 关联规划文档
docs/plan/wechat-rpa-automation-spec.md  ← 规格说明书（P0-P3 分层、技术栈、路线图）
```

## 按角色推荐阅读顺序

### 产品 / 决策者

1. [wechat-prd](wechat-prd) — 理解产品愿景和功能清单
2. [wechat-background-philosophy](wechat-background-philosophy) — 理解设计哲学（为什么要 8 维评分）
3. [wechat-automation-menu](wechat-automation-menu) — 理解完整菜单体系

### 前端开发者

1. [wechat-crm-design](wechat-crm-design) — UI/UX 布局和组件规格
2. [wechat-automation-menu](wechat-automation-menu) — 菜单交互逻辑
3. [wechat-code-architecture](wechat-code-architecture) — 了解后端 API 调用

### 后端开发者

1. [wechat-code-architecture](wechat-code-architecture) — 代码地图和模块职责
2. [wechat-database-design](wechat-database-design) — 数据库 schema
3. [wechat-prd](wechat-prd) — 验收标准

### 新 Agent 上手

1. [README](README) (本文) — 定位文档
2. [wechat-code-architecture](wechat-code-architecture) — 找到对应代码文件
3. [wechat-background-philosophy](wechat-background-philosophy) — 理解设计意图
4. [wechat-rpa-navigation](wechat-rpa-navigation) — 理解 RPA 操作原理
5. [wechat-uia-reference](wechat-uia-reference) — 查阅 UIA AutomationId

## 核心概念速查

| 概念 | 定义 | 详见 |
|------|------|------|
| **UIA** | Windows UI Automation，通过 COM 接口直接操作微信 Qt 控件 | 代码架构 §核心层 |
| **Eyes/Hands/Engine** | 三层架构：感知 / 执行 / 编排 | 代码架构 §三层架构 |
| **8 维评分** | 亲密度/信任度/尊重度/喜爱度/商业价值/成长价值/信用度/互惠度 | 背景哲学 §八大维度 |
| **13 树分类** | 人际关系 7 大类 13 子类 | 背景哲学 §十三树 |
| **行动闭环** | 画像→分析→洞察→派遣→执行→反馈→更新画像 | 背景哲学 §行动闭环 |
| **每日 5 条建议** | AI 自动生成的可执行行动（关系升温/商机跟进/承诺追踪等） | 背景哲学 §行动建议 |

## 与 MIM 的关系

```
WeChat RPA（采集端）          MIM（通讯端）
─────────────────────        ─────────────
微信消息采集                   消息收发
  ↓                             ↓
wechat_chat 表                chat 表
  ↓                             ↓
画像分析 → 洞察                多 Agent 聊天
  ↓                             ↓
say 命令 ────────────▶    Hermes 收到消息
                           ↓
                      MIM 聊天窗口展示
```

两者通过 `say` 命令桥接。WeChat RPA 是数据采集和智能分析引擎，MIM 是多 Agent 消息通讯平台。

## 当前状态

| 文档 | 状态 |
|------|------|
| PRD | ✅ 已完成（CC-yu2 编写） |
| UI 设计 | ✅ 已完成 |
| 菜单体系 | ✅ 已完成 |
| 数据库设计 | ✅ 已完成 |
| 代码架构地图 | ✅ 本文档集 |
| 背景哲学 | ✅ 本文档集 |
| MCP 工具清单 | ✅ 本文档集 |
| UIA 参考表 | ✅ 本文档集 |
| RPA 导航原理 | ✅ 本文档集 |
| 开发规范 | ✅ 本文档集 |
| 规格说明书 | ✅ 已完成（docs/plan/wechat-rpa-automation-spec.md） |
| 测试计划 | 📋 待创建 |

**代码状态**：25 个 Python 文件已实现，`mcp_server.py` 对外暴露 10+ Hermes 工具。
