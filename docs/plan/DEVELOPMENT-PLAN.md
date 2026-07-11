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
| **Qoder-yu2** | 代码质量 + 全前端测试 | CI 流水线、typecheck、lint、CSS 检查、Vitest 组件测试、Playwright E2E | MR 门禁报告、测试套件 |
| **待分配** | 电脑资产管理 | `apps/desktop/.../winpeek/assets/` + `plugins/winpeek_rpa/shared/software_scanner.py` | PRD、后端工具、前端 UI |

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

### 功能 D：电脑资产管理 — 待分配

**代码范围**：

| 层 | 文件 | 当前状态 | 目标 |
|----|------|---------|------|
| 前端 | `apps/desktop/src/app/winpeek/assets/index.tsx` | 150行, 5 Tab, 11 mock软件 + 2假磁盘 | 5 Tab 全真实数据 |
| 后端 | `plugins/winpeek_rpa/shared/software_scanner.py` | 381行, 注册表+StartMenu | 注册为 Hermes 工具 |
| 工具 | `tools/winpeek_tools.py` | 4 微信工具 | +5 资产工具 |
| 设计 | `docs/requirements/assets-prd.md` | ✅ | 随实现更新 |

**版本计划**：

| 版本 | 内容 | 交付物 |
|------|------|--------|
| **V1.0** | 软件扫描+展示 + 磁盘信息 + CPU/内存 | 可用资产面板 (真实数据) |
| **V2.0** | 文件管理 + 进程管理 + GPU/网络 + 大文件扫描 | 完整运维面板 |

**V1.0 详细任务**：

| # | 任务 | 类型 | 依赖 |
|---|------|------|------|
| D1 | 注册 Hermes 工具：winpeek_scan_software | 后端 | - |
| D2 | 注册 Hermes 工具：winpeek_get_disk_info | 后端 | - |
| D3 | 注册 Hermes 工具：winpeek_get_hardware_info | 后端 | - |
| D4 | 前端：软件列表 Tab 对接真实扫描数据 (替换 mock) | 前端 | D1 |
| D5 | 前端：磁盘管理 Tab (真实 psutil 数据) | 前端 | D2 |
| D6 | 前端：硬件信息 Tab (CPU/内存) | 前端 | D3 |
| D7 | 前端："重新扫描"按钮对接后端 | 前端 | D1 |
| D8 | 前端：文件管理/进程管理 Tab 占位 | 前端 | - |

---

### 功能 C：代码质量 + 全前端测试 — Qoder-yu2

**Qoder 能力**：

| 能力 | 说明 |
|------|------|
| IDE (LSP/lint/format) | TypeScript strict、ESLint、未使用变量 |
| Browser | Playwright E2E、截图对比 |
| Node.js | Vitest、脚本 |

**测试分层**：

| 层级 | 工具 | 负责 | 说明 |
|------|------|------|------|
| 静态检查 | `pnpm typecheck` + `pnpm lint` | Qoder-yu2 | MR 自动触发 |
| CSS token 检查 | `scripts/check-css-tokens.mjs` | Qoder-yu2 | 扫描硬编码颜色 |
| 组件单元测试 | Vitest + React Testing Library | Qoder-yu2 | 渲染不崩溃、props 正确 |
| E2E | Playwright | Qoder-yu2 | 有 browser，可以做 |
| 肉眼验收 | Hermes Desktop 实际运行 | CC-yu2 | Electron 窗口截图/点击/滚动 |
| 后端 API 测试 | pytest | 各自 Agent | CC-yu2 测 winpeek_* 工具，Hermes-htubs24 测 Hub API |

**任务**：

| # | 任务 | 工具 | 依赖 |
|---|------|------|------|
| C1 | 搭建 Vitest 测试框架 | Vitest + RTL | - |
| C2 | CSS token 检查脚本 | grep + 正则 | - |
| C3 | `.gitlab-ci.yml` CI 流水线 | GitLab CI | C1, C2 (需要先有命令可跑) |
| C4 | CC-yu2 MR 门禁 | 每次 MR → typecheck + lint + CSS + Vitest → 评论报告 | C3 |
| C5 | Hermes-htubs24 MR 门禁 | 同上 | C3 |
| C6 | 组件测试：微信好友列表 | ContactRow, FriendListItem | 功能 A 前端代码合入 DEV 后 |
| C7 | 组件测试：好友详情 5 Tab | ProfileTab, PortraitTab, ChatTimeline | 同上 |
| C8 | 组件测试：画像雷达图 SVG | PortraitRadar (渲染+分数校验) | 同上 |
| C9 | E2E：好友列表 → 点击 → 右侧详情切换 | Playwright | 功能 A 前端代码合入 DEV 后 |
| C10 | 组件测试：MIM 聊天窗口 | ChatBubble, ContactList | 功能 B 前端代码合入 DEV 后 |
| C11 | E2E：MIM 联系人列表 → 聊天 → 发送消息 | Playwright | 功能 B 前端代码合入 DEV 后 |

**执行顺序**：C1 → C2 → C3（零依赖，先行）。C4/C5 第一次 MR 来时即生效。C6-C11 等功能代码合入 DEV 后分批补。

---

## 四、依赖关系

```
  ┌─────────────── Qoder-yu2 ──────────────┐
  │  C1 测试框架 → C2 CSS检查 → C3 CI      │  ← 先行, 零依赖
  └──────────────────┬─────────────────────┘
                     │ CI 就绪后, 以下并行:
                     │
  ┌──────────────────┼──────────────────────────────┐
  │                  │                              │
  ▼                  ▼                              ▼
CC-yu2           Hermes-htubs24                 待分配(Assets)
A1-A2 (建表)     B1 (MIM需求)                  D1-D3 (后端工具)
A3-A9 (后端)     B2-B5 (后端API)               D4-D6 (前端对接)
A10-A19 (前端)   B6-B10 (前端)                 D7-D8 (扫描按钮+占位)
A20 (文档)       B11 (文档)
  │                  │                              │
  └────────┬─────────┴──────────────────────────────┘
           │ 代码合入 DEV 后
           ▼
  ┌────────────── Qoder-yu2 ──────────────┐
  │  C6-C8 组件测试 (微信CRM)              │
  │  C9     E2E (微信CRM)                  │
  │  C10    组件测试 (MIM)                 │
  │  C11    E2E (MIM)                      │
  │  C12    组件测试 (Assets) ← 新增       │
  └───────────────────────────────────────┘

每轮 MR: Qoder-yu2 自动运行 C4/C5 门禁 → 评论报告
肉眼验收: CC-yu2 在 yu2 机器启动 Hermes Desktop 验证
```

**两个功能完全独立，零依赖。** 微信 CRM 和 MIM 聊天没有共享代码，可以同时开发。Qoder 的 C1-C3 也不依赖任何人。

---

## 五、时间线

| 周 | CC-yu2 | Hermes-htubs24 | Qoder-yu2 | 待分配 (Assets) |
|----|--------|---------------|-----------|-----------------|
| W1 | A1-A2 建表 + A3-A9 后端工具 | B1 需求 + B2-B5 后端 API | C1 测试框架 + C2 CSS 检查 + C3 CI 流水线 | D1-D3 后端工具 |
| W2 | A10-A12 前端框架 + Tab1 | B6-B8 前端对接 | C4/C5 MR 门禁 | D4-D6 前端对接 |
| W3 | A13-A15 Tab2/Tab3/Tab4 | B9-B10 在线状态 + 已读回执 | C6-C8 微信组件测试 | D7-D8 扫描按钮+Tab占位 |
| W4 | A16-A19 Tab5/仪表盘/群发/管理 | B11 文档 | C9 微信 E2E + C10-C11 MIM 测试 | — |

---

## 六、测试责任矩阵

| 测试类型 | CC-yu2 | Hermes-htubs24 | Qoder-yu2 |
|---------|--------|---------------|-----------|
| TypeScript typecheck | - | - | ✅ `pnpm typecheck` |
| ESLint | - | - | ✅ `pnpm lint` |
| CSS token 检查 | - | - | ✅ `check-css-tokens.mjs` |
| Vitest 组件测试 | - | - | ✅ 全部前端组件 |
| Playwright E2E | - | - | ✅ 有 browser |
| 后端 pytest (winpeek_* 工具) | ✅ | - | - |
| 后端 pytest (Hub API) | - | ✅ | - |
| 肉眼验收 (Electron 实际运行) | ✅ | ❌ Ubuntu 无桌面 | - |

**结论**：前端测试全部由 Qoder-yu2 承担（类型/组件/E2E/截图）。CC-yu2 负责微信后端工具测试 + 肉眼验收。Hermes-htubs24 负责 Hub API 测试，不参与前端测试。

## 七、MR 工作流

```
1. Agent git pull DEV → git checkout -b feature/xxx → 开发 → commit → git push
2. GitLab 创建 MR (feature/xxx → DEV)
3. Qoder-yu2 自动运行 typecheck + lint + CSS 检查 → 评论贴质量报告
4. 另一方 Agent review 功能是否完整
5. 双方 approve → merge 到 DEV
```

---

## 八、当前阻塞项

| # | 阻塞 | 负责人 | 状态 |
|---|------|--------|------|
| 1 | CC-yu2 MR (winpeek-H23-DOC) 需修复后重新提交 | CC-yu2 | 🔴 待修复 |
| 2 | Qoder-yu2 检查流水线未建立 | Qoder-yu2 | 🔴 待建立 |
| 3 | MIM 需求文档未写 | Hermes-htubs24 | 🟡 待开始 |
| 4 | CRM 建表 SQL 未在 MySQL 执行 | CC-yu2 | 🟡 待 A1 |
