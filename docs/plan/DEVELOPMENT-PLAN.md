# WinPeek 开发总体规划

> 版本: v1.0 · 日期: 2026-07-12 · 分支: DEV
>
> 3 Agent 分工，每人一个独立功能，端到端交付（需求→设计→实现→测试→文档）。

---

## 一、Agent 分工

```
yu2 机器                              htubs24 机器
─────────                             ──────────
CC-yu2     → WeChat 自动化             Hermes-htubs24 → MIM 聊天
Qoder-yu2  → 代码质量 + 前端测试
```

| Agent | 功能 | 代码范围 | 产出 |
|-------|------|---------|------|
| **CC-yu2** | 微信自动化 CRM | `apps/desktop/.../winpeek/wechat/` + `plugins/winpeek_rpa/` + `tools/winpeek_tools.py` | PRD、DB 设计、后端工具、前端 UI、API 文档 |
| **Hermes-htubs24** | MIM 多平台即时通讯 | `apps/desktop/.../winpeek/mim/` + `gateway/winpeek_hub/` | 需求、后端 API、前端聊天 UI、MQTT 集成文档 |
| **Qoder-yu2** | 代码质量 + 前端测试 | 全局 lint/typecheck + 两个功能的前端组件测试 | CI 流水线、MR 质量报告、测试用例 |

---

## 二、分支策略

```
main (上游 Hermes)
  └── DEV (唯一开发主干)
        ├── feature/wechat-crm    ← CC-yu2 的工作分支
        ├── feature/mim-chat      ← Hermes-htubs24 的工作分支
        └── ci/qoder-gate         ← Qoder-yu2 的检查流水线（直接在 MR 上运行，无需独立分支）
```

规则：
- 所有人从 DEV 拉分支 → 开发 → MR 到 DEV
- Qoder 不提交代码，只评论 MR + 跑检查
- DEV 是唯一合入目标，不再有 feat/winpeek 等并行分支

---

## 三、功能拆解

### 功能 A：微信自动化 CRM — CC-yu2

**代码范围**：

| 层 | 文件 | 当前状态 | 目标 |
|----|------|---------|------|
| 前端 | `apps/desktop/src/app/winpeek/wechat/index.tsx` | CC 原型 (354行, 3 Tab, mock数据) | 5 Tab + 雷达图 + 真实数据 |
| 前端 | `.../wechat/components/*.tsx` | 空 | ChatTimeline, PortraitRadar, EventTimeline, SalesPanel |
| 后端 | `tools/winpeek_tools.py` | 4 工具 (send/collect/contacts/list) | +10 工具 (portrait, insight, stats, bulk...) |
| 后端 | `plugins/winpeek_rpa/platforms/wechat/db.py` | 8 表, 13 个 CRUD 方法 | +13 表建表, +20 个新 CRUD 方法 |
| 后端 | `plugins/winpeek_rpa/platforms/wechat/analyze.py` | jieba 分词+话题提取 | +8维评分+事件提取+画像生成 |
| 引擎 | `plugins/winpeek_rpa/shared/crm_schema.sql` | 已设计, 未执行 | MySQL 执行建表 |
| 设计 | `docs/design/wechat-*.md` | ✅ | 随实现更新 |
| 设计 | `docs/requirements/wechat-prd.md` | ✅ | 随发现补充 |

**版本计划**：

| 版本 | 内容 | 交付物 |
|------|------|--------|
| **V1.0** | 好友列表 + 5 Tab(档案/画像/聊天/销售/备注) + 数据统计 | 可用 CRM, 手动维护数据 |
| **V2.0** | AI 自动评分 + 洞察引擎 + 行动派遣 | 智能 CRM, AI 驱动 |

**V1.0 详细任务**：

| # | 任务 | 类型 | 依赖 |
|---|------|------|------|
| A1 | 建表：wechat_friend 扩展 15 字段 + 8 张新表 | DB | - |
| A2 | 种子数据：wechat_relation_tree (13树, 60行) + sys_enum_definition | DB | A1 |
| A3 | 新增 Hermes 工具：winpeek_list_contacts (分页/搜索/排序) | 后端 | A1 |
| A4 | 新增 Hermes 工具：winpeek_get_contact_detail | 后端 | A1 |
| A5 | 新增 Hermes 工具：winpeek_get_chat_history | 后端 | - |
| A6 | 新增 Hermes 工具：winpeek_get_portrait + winpeek_update_portrait | 后端 | A1 |
| A7 | 新增 Hermes 工具：winpeek_list_groups + winpeek_get_group_detail | 后端 | - |
| A8 | 新增 Hermes 工具：winpeek_dashboard (聚合统计) | 后端 | A1 |
| A9 | 新增 Hermes 工具：winpeek_crud_sales_log | 后端 | A1 |
| A10 | 前端：三层布局 (左侧功能导航 + 好友列表 + 右侧详情) | 前端 | A3 |
| A11 | 前端：好友列表 (筛选/排序/搜索/虚拟滚动) | 前端 | A3 |
| A12 | 前端：Tab1 基本档案 (3 区) | 前端 | A4 |
| A13 | 前端：Tab2 画像 (8维雷达图 + 13树分类 + 事件时间线) | 前端 | A6 |
| A14 | 前端：Tab3 聊天记录 (消息时间线 + 搜索 + 统计) | 前端 | A5 |
| A15 | 前端：Tab4 销售管理 (客户分级 + 拜访记录 + 目标) | 前端 | A9 |
| A16 | 前端：Tab5 备注 (富文本 + AI 摘要) | 前端 | A4 |
| A17 | 前端：仪表盘 (统计卡片 + 图表) | 前端 | A8 |
| A18 | 前端：群发消息 + 消息模板 | 前端 | A7 |
| A19 | 前端：微信管理面板 (头像/切换/退出/同步) | 前端 | - |
| A20 | API 文档：winpeek_* 工具使用文档 | 文档 | A3-A9 |

---

### 功能 B：MIM 多平台即时通讯 — Hermes-htubs24

**代码范围**：

| 层 | 文件 | 当前状态 | 目标 |
|----|------|---------|------|
| 前端 | `apps/desktop/src/app/winpeek/mim/index.tsx` | 371 行, mock 数据 | 真实 MQTT 数据 + 多人聊天 |
| 后端 | `gateway/winpeek_hub/identity.py` | JSONL 本地存储 | HTTP API 暴露 |
| 后端 | `gateway/winpeek_hub/archive.py` | MySQL 归档 (未联通) | 联通 MySQL + 历史查询 API |
| 后端 | `gateway/winpeek_hub/mqtt_adapter.py` | 发送 say 命令 | 双向收发 + WebSocket 推送 |
| 后端 | `gateway/winpeek_hub/routing.py` | 跨平台路由 | 完善消息路由 |
| 后端 | `gateway/winpeek_hub/tenant.py` | 多租户 | HTTP API 暴露 |
| 设计 | MIM 需求文档 | ❌ 未写 | 需求规格 |
| API | MIM API 文档 | ❌ 未写 | API 参考 |

**版本计划**：

| 版本 | 内容 | 交付物 |
|------|------|--------|
| **V1.0** | MIM 实时聊天 (MQTT ↔ WebSocket ↔ 前端) + 身份系统 + 消息历史 | 可用聊天 |
| **V2.0** | 跨平台消息路由 + 文件传输 + 群聊 | 完整通讯 |

**V1.0 详细任务**：

| # | 任务 | 类型 | 依赖 |
|---|------|------|------|
| B1 | MIM 需求文档 | 设计 | - |
| B2 | 完善 Hub REST API：identity 注册/登录/查询端点 | 后端 | B1 |
| B3 | 完善 Hub REST API：contacts 列表端点 | 后端 | B1 |
| B4 | 完善 Hub REST API：messages 历史查询端点 (查 MySQL) | 后端 | B1 |
| B5 | MQTT → WebSocket 推送：实时消息到前端 | 后端 | - |
| B6 | 前端：联系人列表对接真实 API (替换 mock) | 前端 | B3 |
| B7 | 前端：聊天窗口对接真实消息 (MQTT 实时 + 历史) | 前端 | B4, B5 |
| B8 | 前端：身份注册/登录 UI 对接后端 API | 前端 | B2 |
| B9 | 前端：联系人列表显示在线状态 (Zustand + 心跳) | 前端 | B5 |
| B10 | 后端：消息已读/送达回执 | 后端 | B5 |
| B11 | MIM API 文档 | 文档 | B2-B5 |

---

### 功能 C：代码质量 + 前端测试 — Qoder-yu2

**范围**：

| 项 | 工具 | 目标 |
|----|------|------|
| TypeScript 类型检查 | `pnpm typecheck` | 0 error |
| ESLint | `pnpm lint` | 0 warning |
| 硬编码值检测 | grep + 规则 | 0 硬编码颜色/魔法数字 |
| CSS token 一致性 | 人工 + 正则 | 只用 `var(--ui-*)` |
| 组件命名规范 | 人工 | 符合项目惯例 |
| 前端组件测试 | Vitest + React Testing Library | 关键组件有测试 |

**任务**：

| # | 任务 | 说明 |
|---|------|------|
| C1 | 建立 MR 检查流水线 | MR 创建 → typecheck + lint → 评论贴结果 |
| C2 | 编写 CSS token 检查脚本 | 扫描 `apps/desktop/src/app/winpeek/` 下硬编码颜色 |
| C3 | 编写组件测试框架 | Vitest 配置 + 测试模板 |
| C4 | CC-yu2 MR 审查 | 每次 CC 的 MR 自动跑 C1 + C2 |
| C5 | Hermes-htubs24 MR 审查 | 每次 Hermes 的 MR 自动跑 C1 + C2 |
| C6 | 前端组件测试：微信好友列表 | ContactRow, FriendListItem |
| C7 | 前端组件测试：MIM 聊天窗口 | ChatBubble, ContactList |
| C8 | 前端组件测试：画像雷达图 | PortraitRadar (SVG 渲染校验) |
| C9 | 前端组件测试：聊天时间线 | ChatTimeline (消息分组/搜索) |

---

## 四、依赖关系

```
                    Qoder-yu2 (C1 建立检查流水线)  ← 最先
                         │
          ┌──────────────┴──────────────┐
          │                             │
     CC-yu2                         Hermes-htubs24
     A1-A2 (建表)                   B1 (MIM 需求)
     A3-A9 (后端工具)               B2-B5 (后端 API)
     A10-A19 (前端 UI)              B6-B10 (前端 UI)
     A20 (API 文档)                 B11 (API 文档)
          │                             │
          └──────────────┬──────────────┘
                         │
                    Qoder-yu2 (C4-C9 测试)
```

**两个功能完全独立，零依赖。** 微信 CRM 和 MIM 聊天没有共享代码，可以同时开发。

---

## 五、时间线

| 周 | CC-yu2 | Hermes-htubs24 | Qoder-yu2 |
|----|--------|---------------|-----------|
| W1 | A1-A2 建表 + A3-A9 后端工具 | B1 需求 + B2-B5 后端 API | C1 检查流水线 + C2 CSS 检查 |
| W2 | A10-A12 前端框架 + Tab1 | B6-B8 前端对接 | C3 测试框架 + C4/C5 首次 MR 审查 |
| W3 | A13-A15 Tab2/Tab3/Tab4 | B9-B10 在线状态 + 已读回执 | C6-C7 组件测试 |
| W4 | A16-A19 Tab5/仪表盘/群发/管理 | B11 文档 | C8-C9 组件测试 |

---

## 六、MR 工作流

```
1. Agent git pull DEV → git checkout -b feature/xxx → 开发 → commit → git push
2. GitLab 创建 MR (feature/xxx → DEV)
3. Qoder-yu2 自动运行 typecheck + lint + CSS 检查 → 评论贴质量报告
4. 另一方 Agent review 功能是否完整
5. 双方 approve → merge 到 DEV
```

---

## 七、当前阻塞项

| # | 阻塞 | 负责人 | 状态 |
|---|------|--------|------|
| 1 | CC-yu2 MR (winpeek-H23-DOC) 需修复后重新提交 | CC-yu2 | 🔴 待修复 |
| 2 | Qoder-yu2 检查流水线未建立 | Qoder-yu2 | 🔴 待建立 |
| 3 | MIM 需求文档未写 | Hermes-htubs24 | 🟡 待开始 |
| 4 | CRM 建表 SQL 未在 MySQL 执行 | CC-yu2 | 🟡 待 A1 |
