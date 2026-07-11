# WinPeek 开发总体规划

> 版本: v2.0 · 日期: 2026-07-12 · 分支: DEV
>
> 4 Agent 分工，每人一个独立功能，端到端交付（需求→设计→实现→测试→文档）。

---

## 一、分支策略

**`DEV` 是唯一主干分支。**

| 分支 | 用途 | 状态 |
|------|------|------|
| `DEV` | 主开发分支（PRD、DB设计、CRM、文档、全部代码） | **当前** |
| `feat/winpeek` | 历史探索分支 | 过期，弃用 |
| `winpeek-H23-DOC` | CC-yu2 微信UI MR 所在分支 | 待合入 DEV |

规则：
- 所有人从 DEV 拉分支 → 开发 → MR 到 DEV
- Qoder 不提交业务代码，只评论 MR + 跑检查
- DEV 是唯一合入目标

---

## 二、Agent 分工

```
yu2 机器                              htubs24 机器
─────────                             ──────────
CC-yu2     → 微信自动化 CRM           Hermes-htubs24 → MIM 多平台聊天
Qoder-yu2  → 代码质量 + 全前端测试
待分配     → 电脑资产管理
```

| Agent | 功能 | 计划文件 | 代码范围 |
|-------|------|---------|---------|
| **CC-yu2** | 微信自动化 CRM | [agent-cc-wechat.md](agent-cc-wechat.md) | `wechat/` + `winpeek_rpa/` + `tools/` |
| **Hermes-htubs24** | MIM 聊天 | [agent-hermes-mim.md](agent-hermes-mim.md) | `mim/` + `winpeek_hub/` |
| **Qoder-yu2** | 质量 + 测试 | [agent-qoder-quality.md](agent-qoder-quality.md) | `scripts/` + `.gitlab-ci.yml` + `*.test.*` |
| **待分配** | 电脑资产 | [agent-assets.md](agent-assets.md) | `assets/` + `software_scanner.py` |

---

## 三、架构总览 (目标态)

```
Hermes Desktop (Electron + React + Vite)
  ├── Shell (titlebar + sidebar + statusbar)
  ├── Chat (核心对话界面)
  ├── WinPeek Module (新增)
  │   ├── MIM (多实例消息 — 聊天UI)
  │   ├── Automation (桌面自动化 — 平台选择 + WeChat面板)
  │   ├── Assets (电脑资产 — 软件发现 + 磁盘)
  │   └── Settings (个人身份 + 角色切换)
  └── Gateway (FastAPI + WebSocket)
      ├── Hub (winpeek_hub/)
      │   ├── tenant.py        — 租户/用户管理
      │   ├── identity.py      — 身份注册/登录 (JSONL)
      │   ├── archive.py       — 消息归档 (MySQL/JSONL)
      │   ├── routing.py       — 跨平台路由
      │   ├── mqtt_adapter.py  — MQTT 收发
      │   └── hub_bridge.py    — Gateway 钩子
      └── Plugins (winpeek_rpa/)
          ├── software_scanner.py — 软件资产扫描
          ├── wechat/*            — 微信自动化 (11个模块)
          └── mcp_server.py       — MCP 服务端
```

---

## 四、两套数据库设计

| 哪套 | 用途 | 表数 | 状态 |
|------|------|------|------|
| **CRM 表** (`crm_schema.sql`) | 微信好友画像、评分日志、可执行洞察 | 13 表 | 设计完成，待落地 |
| **Hub 表** (`hub_schema.sql`) | 租户、用户、消息归档、平台绑定 | 4 表 | SQL 已定义，DB 未建 |

**不是同一套表。** CRM 表归 CC-yu2（`wechat_friend_relation` / `friend_score_log` / `actionable_insight` ...），Hub 表归 Hermes-htubs24（`hub_tenants` / `hub_users` / `hub_user_platforms` / `hub_messages`）。

---

## 五、当前完成度

### 已完成

- [x] Desktop 左侧导航栏：Automation / MIM / Assets 三个入口
- [x] MIM 页面：微信风格双栏聊天UI
- [x] 身份系统：localStorage + JSONL 持久化，注册/登录/角色选择
- [x] Automation 页面：平台页签 + WeChat 面板
- [x] Assets 页面：软件列表 + 磁盘信息 (demo数据)
- [x] 路由系统：非 overlay 内联渲染，保留侧边栏
- [x] identity.py 后端 (JSONL存储)
- [x] MQTT通信：say命令 MQTT收发验证通过
- [x] 微信 CRM 数据库设计 (13 表)
- [x] WeChat CRM 原型 (MasterDetail+3Tab+画像雷达图)
- [x] 文档体系重组 (5层分离)
- [x] MIM 需求文档 (mim-prd.md)
- [x] 资产需求文档 (assets-prd.md)

### 未完成

| 层 | 模块 | 差距 |
|----|------|------|
| **后端** | Hub REST API | identity.py 无 HTTP 路由（Gateway auth 拦截） |
| **后端** | 消息历史API | 未实现 |
| **前端** | MIM 实时接收 | 未对接 MQTT → WebSocket |
| **前端** | Assets 真实数据 | 未对接 software_scanner.py |
| **前端** | WeChat CRM | 好友列表+5 Tab CC-yu2 开发中 |
| **数据** | CRM 13 表建表 | 未执行 |
| **数据** | Hub 4 表建表 | 未执行 |

---

## 六、依赖关系

```
Qoder-yu2 CI 流水线  ← 最先, 零依赖
    │
    │ CI 就绪后, 以下并行:
    │
    ├── CC-yu2 (微信CRM, 20任务)
    ├── Hermes-htubs24 (MIM, 11任务)
    └── 待分配 (Assets, 8任务)
          │
          │ 代码合入 DEV 后
          ▼
    Qoder-yu2 组件测试 + E2E

Hub REST API 打通
  ├── 前端 MIM 才能接真实数据
  ├── Assets 才能调 scanner API
  └── Automation 才能调操作执行 API

CC-yu2 MR 合入
  ├── CRM 前端才能继续迭代
  └── Phase 1 才能交付

MQTT → WebSocket 推送
  └── MIM 实时消息才能工作
```

---

## 七、时间线

| 周 | CC-yu2 | Hermes-htubs24 | Qoder-yu2 | 待分配 (Assets) |
|----|--------|---------------|-----------|-----------------|
| W1 | A1-A2 建表 + A3-A9 后端工具 | B1 需求 + B2-B5 后端 API | C1 测试框架 + C2 CSS检查 + C3 CI | D1-D3 后端工具 |
| W2 | A10-A12 前端框架 + Tab1 | B6-B8 前端对接 | C4/C5 MR 门禁 | D4-D6 前端对接 |
| W3 | A13-A15 Tab2/Tab3/Tab4 | B9-B10 在线状态 + 已读回执 | C6-C8 微信组件测试 | D7-D8 扫描按钮+Tab占位 |
| W4 | A16-A19 Tab5/仪表盘/群发/管理 | B11 文档 | C9-C11 E2E | - |

---

## 八、测试责任矩阵

| 测试类型 | CC-yu2 | Hermes-htubs24 | Qoder-yu2 |
|---------|--------|---------------|-----------|
| TypeScript typecheck | - | - | ✅ |
| ESLint | - | - | ✅ |
| CSS token 检查 | - | - | ✅ |
| Vitest 组件测试 | - | - | ✅ |
| Playwright E2E | - | - | ✅ |
| 后端 pytest (winpeek_* 工具) | ✅ | - | - |
| 后端 pytest (Hub API) | - | ✅ | - |
| 肉眼验收 (Electron) | ✅ | ❌ | - |

---

## 九、MR 工作流

```
1. Agent git pull DEV → git checkout -b feature/xxx → 开发 → commit → git push
2. GitLab 创建 MR (feature/xxx → DEV)
3. Qoder-yu2 自动运行 typecheck + lint + CSS 检查 → 评论贴质量报告
4. 另一方 Agent review 功能是否完整
5. 双方 approve → merge 到 DEV
```

---

## 十、当前阻塞项

| # | 阻塞 | 负责人 | 状态 |
|---|------|--------|------|
| 1 | CC-yu2 MR (winpeek-H23-DOC) 需修复后重新提交 | CC-yu2 | 🔴 待修复 |
| 2 | Qoder-yu2 CI 流水线未建立 | Qoder-yu2 | 🔴 待建立 |
| 3 | Hub REST API 被 Gateway auth 拦截 | Hermes-htubs24 | 🟡 待解决 |
| 4 | CRM 建表 + Hub 建表 未执行 | CC-yu2 / Hermes-htubs24 | 🟡 待执行 |
| 5 | Assets Agent 未分配 | - | ⚪ 待分配 |
