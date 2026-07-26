# WeChat RPA — 自动化桌面软件规格说明书

> **版本**: v1.0 · **日期**: 2026-07-22
> **关联文档**: [`website/docs/winpeek/wechat-automation/`](../website/docs/winpeek/wechat-automation/README.md) — 设计文档总索引
> **骨架来源**: [`wechat-automation-menu.md`](../website/docs/winpeek/wechat-automation/wechat-automation-menu.md) — 菜单体系 + 行动闭环
> **遵循**: `pipeline:spec` (`.agents/skills/spec-driven-development/SKILL.md`)

---

## 一、目标

把微信好友的几千条聊天记录变成每天早上 5 条可行动的建议——该联系谁、该推进什么、什么逾期了、关系在降温还是在升温。

**核心差异化**:
- 传统 CRM: 手动看 → 手动判断 → 手动操作
- 本系统: AI 持续看 → AI 自动判断 → AI 建议行动 → 用户确认/自动执行

---

## 二、目标用户

| 角色 | 典型场景 | 好友规模 |
|------|---------|---------|
| 销售/商务 | 客户关系管理、商机识别、群发营销 | 1000–5000 |
| 创业者/管理者 | 人脉维护、承诺追踪、经济往来 | 500–3000 |
| 个人用户 | 关系温度监控、关键事件提醒、消费记账 | 200–2000 |

---

## 三、功能范围

### 3.1 P0 — 基础数据层（必须交付）

| 模块 | 功能 | 验收标准 |
|------|------|---------|
| 账号管理 | 我的微信标识（头像/昵称/微信号/在线状态） | 显示正确，2s 轮询检测进程 |
| 数据同步 | 好友信息同步（全量/增量） | 采集完成率 >95%，去重正确 |
| 数据同步 | 聊天信息同步（全量/增量/指定好友） | 文本完整采集，时间戳准确，去重正确 |
| 好友管理 | 好友列表（筛选/排序/搜索/虚拟滚动） | 4000 条不卡顿，搜索 <200ms |
| 好友管理 | 好友详情 Tab1: 基本档案 | 可编辑字段保存到 DB |
| 群管理 | 群列表（活跃度排序） | 正确渲染 |
| 数据库 | 新增表建表 + wechat_friend 扩展字段 | SQL 迁移通过 |
| 数据库 | 13 棵分类树种子数据 | 可查询 |

### 3.2 P1 — 画像 + 洞察引擎（核心差异化）

| 模块 | 功能 | 验收标准 |
|------|------|---------|
| 仪表盘 | 今日快照（统计卡片 + 行动清单 + 温度预警） | 数字正确，加载 <2s |
| 好友详情 Tab2 | 8 维评分雷达图 | 正确渲染，悬停显示详情 |
| 好友详情 Tab2 | 13 树关系分类 | 可展开/折叠，多选标记 |
| 好友详情 Tab2 | AI 人物速写（50-200 字） | 可读准确，支持人工编辑 |
| 好友详情 Tab2 | 关键事件时间线 | 日期倒序，AI 提取+手动 |
| 好友详情 Tab3 | 聊天记录（消息时间线） | 日期分组，虚拟滚动 10000+ |
| 好友详情 Tab3 | 搜索与筛选 | 关键词搜索 <500ms，命中高亮 |
| 好友详情 Tab4 | 客户分级（A/B/C/D） | 下拉选择，保存正确 |
| 好友详情 Tab4 | 拜访/跟进记录 | CRUD，时间线展示 |
| 洞察引擎 | 规则匹配器 | 5 类洞察正确触发 |
| 洞察引擎 | 行动优先级算法 | P 值计算公式正确 |
| 洞察引擎 | 行动派遣（即时/cron/todo） | 3 条路径可执行 |
| 工具 API | winpeek_get_portrait / get_insights / execute_insight | 返回正确数据 |

### 3.3 P2 — 营销 + 个人助理

| 模块 | 功能 |
|------|------|
| 群发消息 | 收件人选择（标签/级别/手动） |
| 群发消息 | 富文本编辑器 + 变量替换 |
| 群发消息 | AI 生成话术 + 情感设置 |
| 群发消息 | 发送控制（间隔/上限/时段） |
| 消息模板 | 模板 CRUD + AI 优化 |
| 数据统计 | 消息趋势/来源分布/Top 排行榜/销售漏斗 |
| 好友详情 Tab2 | 经济往来账簿 |
| 好友详情 Tab5 | 备注·文档（富文本 + AI 摘要） |
| 个人助理 | 日记/待办/消费记账 |
| 反馈闭环 | 执行 → 观察 → 分析 → 更新画像 |
| 种子数据 | 20+ 预置行动模板 |

### 3.4 P3 — 高级功能

| 模块 | 功能 |
|------|------|
| 自动化规则 UI | 可视化 IF-THEN 规则编辑器 |
| 主人自画像 | 性格/投资/职业/健康/信仰等 12 维度 |
| 画像驱动批量操作 | 按画像维度筛选 → 群发 |

---

## 四、技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | React + TypeScript + Vite | 现有 Hermes Web 架构 |
| 后端 | Python (Hermes Agent) | 现有 Hermes 架构 |
| 数据库 | SQLite（默认）/ MySQL（可选） | 通过 `DB_BACKEND` 环境变量切换 |
| 桌面交互 | Windows UIA (COM) | 通过 `uiautomation` 库操作微信 Qt 控件 |
| AI 分析 | Hermes LLM (Claude/Gemini) | 消息分析、画像生成、话术生成 |
| 同步 | Cron job | 每日 8:00 自动同步 + 增量 |

### 前端组件树

```
WechatCRM (顶层页面)
├── LeftNav (280px)
│   ├── GlobalSearch (好友/群搜索)
│   ├── NavItem: 仪表盘
│   ├── FriendList (虚拟滚动 + 筛选/排序)
│   ├── GroupList
│   ├── NavItem: 群发消息 / 消息模板 / 数据统计
│   └── NavItem: 微信管理 / 同步数据 (展开)
└── RightPanel
    ├── DashboardView (StatCards + TodayActionList + Alerts)
    ├── FriendDetailView (5 Tabs: 档案/画像/聊天/销售/备注)
    ├── BulkMessageView (收件人/编辑器/发送控制)
    ├── TemplateManagerView
    └── StatisticsView (6 种图表)
```

### 后端模块

```
plugins/winpeek_rpa/
├── mcp_server.py          ← MCP 服务端（工具暴露）
├── shared/                ← 共享基础设施
│   ├── rpa_tools.py       ← RPA 通用工具
│   ├── bg_input.py        ← 后台输入
│   └── config.py          ← 全局配置
├── platforms/wechat/      ← 微信平台（11 模块）
│   ├── uia.py             ← UIA 底层操作
│   ├── api.py             ← Eyes/Hands/Engine 三层架构
│   ├── db.py              ← 数据存储
│   ├── contacts.py        ← 联系人管理
│   ├── profile.py         ← 画像构建（8维 + 13树）
│   ├── analyze.py         ← AI 分析引擎
│   ├── collect.py         ← 数据采集编排
│   ├── collect_contacts.py ← 联系人采集
│   ├── msg_collect.py     ← 消息采集
│   ├── msg_traverse.py    ← 消息遍历
│   └── find.py            ← 搜索 + 发送
└── skills/wechat/         ← WeChat 技能
```

### 新增数据库表

| 表 | 用途 | 优先级 |
|----|------|--------|
| wechat_friend_relation | 好友↔关系 M:N 标记（13树） | P0 |
| friend_event | 结构化交互事件（评分+机会） | P1 |
| friend_score_log | 8 维评分时间序列 | P1 |
| friend_opportunity | 机会识别表 | P2 |
| friend_sales_log | 拜访/跟进记录 | P1 |
| actionable_insight | AI 行动建议 | P1 |
| action_template | 行动策略模板 | P2 |
| automation_rule | 用户自定义规则 | P3 |
| message_template | 群发消息模板 | P2 |
| sys_enum_definition | 自扩展枚举 | P2 |
| personal_* (17 表) | 主人 360° 数据 | P3 |

### Hermes 工具注册

| 工具名 | 优先级 | 状态 |
|--------|--------|------|
| winpeek_list_contacts | P0 | 已有 |
| winpeek_get_contact_detail | P0 | 已有 |
| winpeek_get_chat_history | P0 | 已有 |
| winpeek_wechat_send | P0 | 已有 |
| winpeek_wechat_collect_msgs | P0 | 已有 |
| winpeek_wechat_collect_contacts | P0 | 已有 |
| winpeek_get_portrait | P1 | 新增 |
| winpeek_analyze_portrait | P1 | 新增 |
| winpeek_get_insights | P1 | 新增 |
| winpeek_execute_insight | P1 | 新增 |
| winpeek_dashboard | P1 | 新增 |
| winpeek_weekly_report | P2 | 新增 |
| winpeek_bulk_send | P2 | 新增 |
| winpeek_ai_script | P2 | 新增 |

---

## 五、代码风格

### Python
- 类型注解（PEP 484）— 所有公共函数签名
- 文档字符串（PEP 257）— 模块级别 + 公共函数
- 遵循 `pyproject.toml` 现有 lint 配置
- 异常：自定义异常类，不抛裸 `Exception`

### TypeScript/React
- TypeScript strict 模式
- React 函数组件 + Hooks
- CSS Modules 或 Tailwind（遵循现有项目风格）
- 组件粒度：一个文件一个组件

---

## 六、测试策略

| 层级 | 覆盖范围 | 工具 |
|------|---------|------|
| 单元测试 | 工具函数、评分计算、优先级算法 | pytest |
| 集成测试 | API 端点、数据库读写 | pytest + SQLite in-memory |
| E2E | 前端组件渲染 | Vitest + Testing Library |
| 手动 | UIA 操作 | 人工验证 |

**验收方式**: 每条验收标准对应一个测试用例。P0 功能必须有测试覆盖。

---

## 七、边界（Boundaries）

### Always Do
- 所有用户输入做 HTML 转义（防 XSS）
- 聊天记录本地存储，不外传
- UIA 操作失败自动重试 3 次
- 关键操作（删除/退出/群发）提供确认弹窗
- 长时间操作显示进度条

### Ask First
- 涉及金钱相关的提醒（催款/借款）
- 批量群发（>50 人）
- 删除好友/退出微信
- 切换微信账号

### Never Do
- 不在日志中暴露微信登录凭据
- 不将聊天记录上传到外部 API
- 不绕过微信安全限制（发送频率、每日上限）
- 不修改微信安装目录或注入 DLL
- 不使用模拟点击之外的违规操作

---

## 八、实施路线图

| 阶段 | 内容 | 周期 |
|------|------|------|
| Phase 0 | 建表 + 扩展字段 + 种子数据 | 1 周 |
| Phase 1 | 前端页面框架（左导航+好友列表+基本档案） | 2 周 |
| Phase 2 | 聊天记录 Tab + 数据连接 | 1 周 |
| Phase 3 | 画像系统（雷达图+13树+速写+事件线） | 2 周 |
| Phase 4 | 洞察引擎 + 行动派遣 + 仪表盘 | 2 周 |
| Phase 5 | 营销功能（群发+模板+销售管理） | 2 周 |
| Phase 6 | 个人助理（日记+待办+记账） | 2 周 |

**总计**: 12 周（Phase 3+4 可并行，Phase 5+6 可并行）

---

## 九、参考文档

| 文档 | 路径 |
|------|------|
| 菜单体系+行动闭环 | `website/docs/winpeek/wechat-automation/wechat-automation-menu.md` |
| 产品需求规格 | `website/docs/winpeek/wechat-automation/wechat-prd.md` |
| UI 设计 | `website/docs/winpeek/wechat-automation/wechat-crm-design.md` |
| 数据库设计 | `website/docs/winpeek/wechat-automation/wechat-database-design.md` |
| 代码架构 | `website/docs/winpeek/wechat-automation/wechat-code-architecture.md` |
| 背景哲学 | `website/docs/winpeek/wechat-automation/wechat-background-philosophy.md` |
| MCP 工具清单 | `website/docs/winpeek/wechat-automation/wechat-mcp-tools.md` |
| 开发规范 | `website/docs/winpeek/wechat-automation/wechat-development-standards.md` |
