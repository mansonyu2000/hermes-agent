---
sidebar_position: 0
title: "WinPeek 知识库总索引"
description: "AI Agent 友好的软件研发知识管理体系：产品、入门、使用、参考、设计、开发、治理七大板块"
type: index
role: ["product", "architect", "developer", "tester", "devops"]
---

# WinPeek 知识库

> **框架**：Diátaxis 四象限 × CRMEB 实用分类 × AI Agent 元数据
> **最后更新**：2026-07-18

---

## 文档导航

```
website/docs/
│
├── product/                         ← 🆕 产品（序言/路线图/更新记录）
│   └── README
│
├── getting-started/                 ← 安装/快速开始/更新（已有 8 篇）
│
├── user-guide/                      ← How-To（功能使用/FAQ）
│   ├── features/                    ← 已有：mim-chat, automation-wechat, assets
│   └── README
│
├── reference/                       ← 参考资料库（学习/借鉴/素材/模板/案例/样例）
│   ├── README
│   ├── astrbot.md
│   ├── templates/
│   ├── cases/
│   └── examples/
│
├── api/                             ← API 接口文档（功能实现，非参考素材）
│   └── README
│
├── design/                          ← Explanation（架构/设计文档）
│   └── winpeek/
│       ├── mim-design/              ← MIM 设计：9 篇
│       ├── wechat-automation/       ← WeChat RPA 设计：11 篇
│       └── README
│
├── development/                     ← 🆕 开发（标准/工作流/二开）
│   ├── workflows/
│   ├── guides/
│   └── README
│
├── governance/                      ← 🆕 治理（ADR/Review/复盘）
│   ├── decisions/
│   ├── reviews/
│   ├── retrospectives/
│   └── README
│
└── templates/                       ← 🆕 文档模板
```

## 按角色推荐入口

| 角色 | 第一份要读的 | 快速链接 |
|------|------------|:--:|
| 🆕 新手 | get-started | [安装指南](get-started/README) |
| 🏗 架构师 | design | [MIM 设计](design/winpeek/mim-design/README) |
| 👨‍💻 开发者 | development + design | [WeChat RPA](design/winpeek/wechat-automation/README) |
| 🧪 测试 | design/test-plan | [MIM 测试计划](design/winpeek/mim-design/test-plan) |
| 🚀 运维 | get-started + user-guide | [部署指南](design/winpeek/mim-message-center-setup) |
| 🤖 AI Agent | 本文 + design | [代码地图](design/winpeek/wechat-automation/wechat-code-architecture) |

## 文档统计

| 板块 | 文档数 | 状态 |
|------|:--:|:--:|
| product | 0 | 🆕 待建 |
| getting-started | 8 | ✅ 已有 |
| user-guide | 3 | ✅ |
| reference | 3 | 🆕 模板已有，待充实 |
| api | 0 | 🆕 待建 |
| design | 20 | ✅ 完整 |
| development | 0 | 🆕 待建 |
| governance | 0 | 🆕 待建 |

## AI Agent 文档元数据规范

所有文档头部须包含以下 frontmatter：

```yaml
---
title: "标题"
description: "一句话描述"
sidebar_position: N
type: tutorial|how-to|reference|explanation|governance|product
role: [architect, developer, tester, devops, product]
module: mim|wechat-rpa|assets|shared
status: draft|review|approved|archived
---
```
