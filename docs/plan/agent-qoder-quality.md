# Qoder-yu2 — 代码质量 + 全前端测试 开发计划

> 范围: `.gitlab-ci.yml` + `scripts/check-css-tokens.mjs` + `*.test.*` + MR 门禁
>
> **不写业务代码。只读、只检查、只评论 MR。**

---

## 能力边界

| 能力 | 说明 |
|------|------|
| IDE (LSP/lint/format) | TypeScript strict、ESLint、未使用变量 |
| Browser | Playwright E2E、截图对比 |
| Node.js | Vitest、脚本 |

---

## 测试分层

| 层级 | 工具 | 说明 |
|------|------|------|
| 静态检查 | `pnpm typecheck` + `pnpm lint` | MR 自动触发 |
| CSS token 检查 | `scripts/check-css-tokens.mjs` | 扫描硬编码颜色 |
| 组件单元测试 | Vitest + React Testing Library | 渲染不崩溃、props 正确 |
| E2E | Playwright | 端到端流程 |
| 肉眼验收 | Hermes Desktop | CC-yu2 负责，Qoder 不做 |

---

## 任务

### 阶段 1：零依赖先行

| # | 任务 | 工具 | 依赖 |
|---|------|------|------|
| C1 | 搭建 Vitest 测试框架 + 示例测试 | Vitest + RTL | - |
| C2 | CSS token 检查脚本 (扫描硬编码颜色/魔法数字) | grep + 正则 | - |
| C3 | `.gitlab-ci.yml` CI 流水线 (typecheck+lint+CSS) | GitLab CI | C1, C2 |

### 阶段 2：MR 门禁

| # | 任务 | 说明 |
|---|------|------|
| C4 | CC-yu2 MR 门禁 | 每次 MR → typecheck + lint + CSS + Vitest → 评论 |
| C5 | Hermes-htubs24 MR 门禁 | 同上 |
| C6 | 待分配 Agent MR 门禁 | 同上（Agent 分配后生效） |

### 阶段 3：组件测试 (等功能合入 DEV 后)

| # | 任务 | 测试对象 |
|---|------|---------|
| C7 | 微信好友列表 | ContactRow, FriendListItem |
| C8 | 好友详情 5 Tab | ProfileTab, PortraitTab, ChatTimeline |
| C9 | 画像雷达图 SVG | PortraitRadar (渲染+分数校验) |
| C10 | 微信 CRM E2E | 好友列表 → 点击 → 详情切换 |
| C11 | MIM 聊天窗口 | ChatBubble, ContactList |
| C12 | MIM E2E | 联系人 → 聊天 → 发送 |
| C13 | Assets 组件测试 | SoftwarePanel, DiskPanel, HardwarePanel |
| C14 | Assets E2E | 页面切换 + 扫描按钮 |

---

## 执行顺序

```
C1 → C2 → C3  (零依赖     W1)
C4 + C5 + C6  (首次 MR    W2)
C7-C14        (代码合入后  W3-W4)
```

## 检查项清单

| 检查项 | 工具 | 目标 |
|--------|------|------|
| TypeScript strict | `pnpm typecheck` | 0 error |
| ESLint | `pnpm lint` | 0 warning |
| 硬编码颜色 | C2 脚本 | 只用 `var(--ui-*)` |
| 未使用 import/变量 | LSP diagnostics | 0 |
| 组件命名 | 人工 | 匹配项目惯例 |
| useEffect cleanup | 人工嗅探 | 每个 effect 有 return |
| 长函数 | 人工 | >100 行标记 |
| 重复逻辑 | 人工 | 标记提取建议 |
