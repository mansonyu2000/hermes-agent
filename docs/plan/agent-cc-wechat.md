# CC-yu2 — 微信自动化 CRM 开发计划

> 代码范围: `apps/desktop/.../winpeek/wechat/` + `plugins/winpeek_rpa/platforms/wechat/` + `tools/winpeek_tools.py`
>
> PRD: [docs/requirements/wechat-prd.md](../requirements/wechat-prd.md)
>
> DB设计: [docs/design/wechat-database-design.md](../design/wechat-database-design.md)

---

## 代码范围现状

| 层 | 文件 | 当前 | 目标 |
|----|------|------|------|
| 前端 | `wechat/index.tsx` | 354行, 3 Tab, mock数据 | 5 Tab + 雷达图 + 真实数据 |
| 前端 | `wechat/components/*.tsx` | 空 | ChatTimeline, PortraitRadar, EventTimeline, SalesPanel |
| 后端 | `tools/winpeek_tools.py` | 4 工具 | +10 工具 |
| 后端 | `plugins/.../db.py` | 8 表, 13 CRUD方法 | +13 表建表, +20 CRUD方法 |
| 后端 | `plugins/.../analyze.py` | jieba分词 | +8维评分+事件提取+画像生成 |
| 引擎 | `shared/crm_schema.sql` | 已设计 | MySQL 执行建表 |

---

## 版本计划

| 版本 | 内容 | 交付物 |
|------|------|--------|
| **V1.0** | 好友列表 + 5 Tab + 数据统计 | 可用 CRM, 手动维护数据 |
| **V2.0** | AI 自动评分 + 洞察引擎 + 行动派遣 | 智能 CRM, AI 驱动 |

---

## V1.0 任务

### DB 层

| # | 任务 | 依赖 |
|---|------|------|
| A1 | 建表：wechat_friend 扩展 15 字段 + 8 张新表 | - |
| A2 | 种子数据：wechat_relation_tree (13树, 60行) + sys_enum_definition | A1 |

### 后端工具

| # | 任务 | 依赖 |
|---|------|------|
| A3 | `winpeek_list_contacts` (分页/搜索/排序) | A1 |
| A4 | `winpeek_get_contact_detail` | A1 |
| A5 | `winpeek_get_chat_history` | - |
| A6 | `winpeek_get_portrait` + `winpeek_update_portrait` | A1 |
| A7 | `winpeek_list_groups` + `winpeek_get_group_detail` | - |
| A8 | `winpeek_dashboard` (聚合统计) | A1 |
| A9 | `winpeek_crud_sales_log` | A1 |

### 前端

| # | 任务 | 依赖 |
|---|------|------|
| A10 | 三层布局 (左侧功能导航 + 好友列表 + 右侧详情) | A3 |
| A11 | 好友列表 (筛选/排序/搜索/虚拟滚动) | A3 |
| A12 | Tab1 基本档案 (3 区) | A4 |
| A13 | Tab2 画像 (8维雷达图 + 13树分类 + 事件时间线) | A6 |
| A14 | Tab3 聊天记录 (消息时间线 + 搜索 + 统计) | A5 |
| A15 | Tab4 销售管理 (客户分级 + 拜访记录 + 目标) | A9 |
| A16 | Tab5 备注 (富文本 + AI 摘要) | A4 |
| A17 | 仪表盘 (统计卡片 + 图表) | A8 |
| A18 | 群发消息 + 消息模板 | A7 |
| A19 | 微信管理面板 (头像/切换/退出/同步) | - |

### 文档

| # | 任务 | 依赖 |
|---|------|------|
| A20 | API 文档：winpeek_* 工具使用文档 | A3-A9 |

---

## V2.0 任务

| # | 任务 | 延期原因 |
|---|------|---------|
| A21 | `wechat_friend_finance` 建表 + CRUD | 依赖 AI OCR + 金额提取管线 |
| A22 | `friend_event` 事件分析管线 | 依赖 AI 聊天分析管线 |
| A23 | `friend_opportunity` 机会识别 | 依赖 A22 |
| A24 | `actionable_insight` 洞察引擎 | 依赖 A21-A23 |
| A25 | `action_template` + `automation_rule` | 依赖 A24 |

---

## 当前阻塞

| # | 阻塞 | 状态 |
|---|------|------|
| 1 | winpeek-H23-DOC MR 修复 | 🔴 待重做 (需先 pull DEV) |
