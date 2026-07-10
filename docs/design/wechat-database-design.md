# 微信自动化 — 数据库设计

## 设计原则

每张表回答三个问题：
1. **上游数据从哪来** — 谁写入、什么时机写
2. **下游被谁消费** — 哪个 Tab / 哪个引擎 / 哪个工具读
3. **不做的影响** — 缺这张表，哪个功能直接报废

设计时全部表一次出完。实现分 V1.0 / V2.0，延期必须有原因。

---

## 一、完整数据链路

```
wechat_chat ─────────────────────────────────────────────────────────────┐
  (已有, 2262行)                                                         │
  │                                                                      │
  ├─→ [采集] 已有代码: msg_collect.py + msg_traverse.py                   │
  │                                                                      │
  ├─→ [展示] Tab 3 聊天记录 ── 直接读 wechat_chat                         │
  │                                                                      │
  └─→ [分析] AI 分析每条消息 ──→ friend_event ──→ friend_score_log        │
                                         │                                │
                                         └─→ friend_opportunity           │
                                                                         │
wechat_friend ───────────────────────────────────────────────────────────┐
  (已有, 1962行)                                                         │
  │                                                                      │
  ├─→ [采集] 已有代码: collect_contacts.py                               │
  ├─→ [展示] Tab 1 基本档案 ── 直接读 wechat_friend                       │
  ├─→ [扩展] 12 个新字段 ── 同一张表, AI/手动填充                         │
  │                                                                      │
  ├─→ wechat_friend_relation ── Tab 2 13树分类                            │
  ├─→ wechat_friend_event    ── Tab 2 关键事件时间线                       │
  ├─→ wechat_friend_finance  ── Tab 2 经济往来账簿                        │
  └─→ friend_sales_log       ── Tab 4 拜访记录                            │
                                                                         │
actionable_insight ──────────────────────────────────────────────────────┐
  │                                                                      │
  ├─→ 上游: friend_score_log + friend_opportunity + wechat_friend_event   │
  │         + 规则引擎 (定时扫描)                                         │
  │                                                                      │
  └─→ 下游: 仪表盘(TodayActionList) + Hermes 工具(winpeek_execute_insight)│
                                                                         │
action_template / automation_rule / message_template                      │
  └─→ 独立配置表, 上游是用户手动创建, 下游是群发/自动派遣                  │
                                                                         │
sys_enum_definition                                                       │
  └─→ 全局下拉数据源, 所有表单的枚举选项                                  │
```

---

## 二、逐表分析

### 第 1 层：已有表（不动）

| 表 | 行数 | 来源 | 消费者 |
|----|------|------|--------|
| wechat_friend | 1962 | collect_contacts.py → UIA 遍历通讯录 | Tab 1, Tab 2, 好友列表 |
| wechat_group | 180 | 同上 | 群列表, 群详情 |
| wechat_group_member | 0 | 同上（未采集） | 群成员列表 |
| wechat_chat | 2262 | msg_collect.py → UIA 滚动采集 | Tab 3, AI 分析管线 |
| wechat_moment | 0 | 未实现 | 朋友圈 Tab |
| wechat_moment_comment | 0 | 未实现 | 朋友圈互动 |
| wechat_video | 0 | 未实现 | 视频号 Tab |
| wechat_operation_log | 0 | 各操作自动写 | 同步日志 |

**不做的影响**：这 8 张表已经在生产环境。不动。

---

### 第 2 层：档案扩展（0 张新表，12 个字段加在 wechat_friend 上）

| 字段 | 上游来源 | 下游消费者 | 不做的影响 |
|------|---------|-----------|-----------|
| birthday | AI 从聊天提取 / 手动 | Tab 2 事件线、洞察引擎(生日提醒) | 生日提醒功能缺失 |
| gender | AI 推断 / 手动 | 画像展示 | 画像少一维 |
| email | AI 从聊天提取 | Tab 1 联系方式 | 联系方式不完整 |
| portrait_summary | AI 生成 50-200 字 | Tab 2 AI 速写卡片 | 核心差异化功能缺失 |
| ai_profile | AI 分析 JSON(职业/学历/爱好/性格/宗教/消费习惯) | Tab 2 画像详情 | 画像只剩人工填写 |
| customer_level | 手动 / AI 建议 | 好友列表级别筛选、仪表盘客户分布 | 客户分级无法运作 |
| sales_stage | 手动 | Tab 4 销售管线 | 销售漏斗图无法渲染 |
| estimated_amount | 手动 | Tab 4 目标追踪 | 销售预测缺失 |
| heat_score | 系统计算(聊天频次×互动深度) | 好友列表排序、仪表盘热度排行 | 热度排序和统计缺失 |
| is_blacklisted | 手动 | 好友列表筛选 | 黑名单过滤缺失 |
| remark | 手动富文本 | Tab 5 备注 | 备注功能缺失 |
| last_contact_at | 系统自动(每次新消息更新) | 洞察引擎(失联检测) | 失联检测规则报废 |

**依赖关系**：12 个字段全部加在已有表上，不建新表。字段之间无依赖，加一个就多一个功能。

**分版本原因**：
- V1.0 必做：customer_level, sales_stage, heat_score, is_blacklisted, remark, last_contact_at → 好友列表筛选/排序/销售 Tab 直接依赖
- V1.0 必做：portrait_summary, ai_profile → 画像 Tab 核心展示
- V2.0 再做：birthday, gender, email → 需要 AI 提取管线先跑通

---

### 第 3 层：画像层（4 张新表）

#### ① wechat_relation_tree

| 项 | 内容 |
|----|------|
| 上游 | 手动维护（种子数据，13 棵树约 60 行） |
| 下游 | wechat_friend_relation → Tab 2 分类树选择器 |
| 不做的影响 | 分类树下拉为空，好友无法按关系归类 |

**13 棵树做 1 棵等于做全部**——同一套 INSERT + 同一套 SELECT + 同一套 UI，只是 label 不同。

#### ② wechat_friend_relation

| 项 | 内容 |
|----|------|
| 上游 | 用户手动标记 / AI 建议 → 写入 |
| 下游 | Tab 2 关系标签展示、好友列表左侧颜色标记(🔴🟡⚫) |
| 不做的影响 | 好友列表无法按关系级别筛选、Tab 2 关系分类 Tab 变空白 |
| 数据量 | 1962 好友 × 平均 2 条关系 ≈ 4000 行 |

#### ③ wechat_friend_event

| 项 | 内容 |
|----|------|
| 上游 | AI 从聊天提取 + 用户手动添加 |
| 下游 | Tab 2 关键事件时间线、洞察引擎(纪念日提醒) |
| 不做的影响 | Tab 2 的时间线组空白、AI 无法提醒纪念日/人生事件 |

#### ④ wechat_friend_finance

| 项 | 内容 |
|----|------|
| 上游 | AI 从聊天 OCR 提取 + 用户手动录入 |
| 下游 | Tab 2 经济往来账簿、洞察引擎(催收提醒) |
| 不做的影响 | 经济往来功能缺失、催收规则无数据源 |
| 延期原因 | 依赖 AI 金额提取管线，需先在 V1.0 验证 OCR+聊天分析准确率 |

**画像层依赖关系**：
```
wechat_relation_tree ──→ wechat_friend_relation
                              (独立, 不依赖其他 3 表)

wechat_friend_event ──→ 时间线 UI ──→ 洞察生日提醒
                              (独立)

wechat_friend_finance ──→ 经济账簿 UI ──→ 洞察催收提醒
                              (独立, 需 AI 金额提取)
```

画像层 4 张表互相独立。同时设计，可分阶段实现。

---

### 第 4 层：评分与洞察层（4 张新表）

#### ⑤ friend_event

| 项 | 内容 |
|----|------|
| 上游 | AI 分析 wechat_chat 每条消息 → 识别事件类型 → 计算 8 个 delta |
| 下游 | friend_score_log(评分变动) + friend_opportunity(机会创建) |
| 不做的影响 | 8 维评分无法自动计算、机会无法自动识别、整个智能层停摆 |

**这是系统从"静态 CRM"变成"动态 AI"的关节表。** 每一行代表一次互动对关系的影响。

数据量估算：2262 条聊天记录 × AI 分析 ≈ 可能产出 500-1000 条事件（合并同类消息后）。

#### ⑥ friend_score_log

| 项 | 内容 |
|----|------|
| 上游 | friend_event 触发 → 当前值 + delta = 新值 → 写一条日志 |
| 下游 | Tab 2 雷达图(当前分数)、Tab 2 趋势箭头(30天对比)、洞察引擎(降温检测) |
| 不做的影响 | 雷达图无数据源、趋势箭头无法计算、降温检测规则报废 |

衰减规则：30 天无互动 → 亲密度 -5 → 自动追加一条 decay 日志。

#### ⑦ friend_opportunity

| 项 | 内容 |
|----|------|
| 上游 | friend_event.is_*_opportunity = 1 → 创建一条机会 |
| 下游 | 仪表盘机会提醒、Tab 4 机会列表 |
| 不做的影响 | 机会漏斗功能缺失 |

#### ⑧ actionable_insight

| 项 | 内容 |
|----|------|
| 上游 | 规则引擎定期扫描 → friend_score_log(降温/升温) + friend_opportunity(机会跟进) + wechat_friend_event(生日) + wechat_friend_finance(催收) → 生成行动建议 |
| 下游 | 仪表盘(TodayActionList) + Hermes 工具(winpeek_execute_insight) → 执行 |
| 不做的影响 | 仪表盘的"今日行动清单"为空白、自动派遣功能报废 |

**评分与洞察层依赖关系**：
```
wechat_chat ──→ friend_event ──→ friend_score_log
                     │
                     └──→ friend_opportunity
                              │
                              ▼
wechat_friend_event ──→ actionable_insight ←── wechat_friend_finance
friend_score_log ──────→                        friend_opportunity
```

`actionable_insight` 是最下游的表——它聚合前 7 张表的产出。只要上游缺一张，对应的洞察类型就空，但其他类型正常。

**全部延期到 V2.0 的原因**：这 4 张表的输入是 AI 分析管线的输出。管线需要真实聊天数据来验证准确率。V1.0 先把数据采集、展示、手动编辑做完；V2.0 接入 AI 管线，切换为自动。

---

### 第 5 层：营销与自动化层（3 张新表）

#### ⑨ friend_sales_log

| 项 | 内容 |
|----|------|
| 上游 | 用户手动录入 (Tab 4 拜访记录表单) |
| 下游 | Tab 4 时间线展示 |
| 不做的影响 | Tab 4 拜访记录变空白 |

**唯一的上游是手动输入，不依赖 AI 管线。** 所以 V1.0 就可以做。

#### ⑩ message_template

| 项 | 内容 |
|----|------|
| 上游 | 用户手动创建 (模板管理页面) |
| 下游 | 群发消息编辑器 → 选择模板 → 填充变量 → 发送 |
| 不做的影响 | 群发时无模板可选 |

#### ⑪ automation_rule

| 项 | 内容 |
|----|------|
| 上游 | 用户手动配置 |
| 下游 | 规则引擎 → 匹配条件 → 生成 actionable_insight |
| 不做的影响 | 只能使用系统预置规则，无法自定义 |

#### ⑫ action_template

| 项 | 内容 |
|----|------|
| 上游 | 手动维护（种子数据）+ 用户创建 |
| 下游 | automation_rule 引用 + actionable_insight 引用 |
| 不做的影响 | 行动类型无模板可用 |

**营销层依赖**：
```
message_template ──→ 群发功能（独立，V1 可做）
friend_sales_log  ──→ Tab 4    （独立，V1 可做）
action_template   ──→ automation_rule ──→ actionable_insight
                                           (V2)
```

---

### 第 6 层：系统层（1 张新表）

#### ⑬ sys_enum_definition

| 项 | 内容 |
|----|------|
| 上游 | 种子数据 + AI 上网搜索 + 用户手动添加 |
| 下游 | 所有表单的下拉选项（行业/宗教/爱好/消费类别…） |
| 不做的影响 | 下拉选项写死在代码里，加一个选项要改代码发版 |

**V1.0 做**——种子数据 60 行一次性写入即可，后续 AI 动态扩展。

---

## 三、版本划分

### V1.0 — 可用的 CRM（无 AI 自动分析）

| 表 | 原因 |
|----|------|
| wechat_friend (已有) | - |
| wechat_friend 扩展 12 字段 | 好友列表+详情+筛选的直接依赖 |
| wechat_group (已有) | - |
| wechat_chat (已有) | - |
| wechat_relation_tree | 种子数据一次写入 |
| wechat_friend_relation | 用户手动分类 |
| wechat_friend_event | 用户手动添加事件 |
| friend_sales_log | 用户手动记录拜访 |
| message_template | 用户手动创建模板 |
| sys_enum_definition | 种子数据一次写入 |

**V1.0 产出**：好友列表可以按级别/分类筛选，点击好友看到 5 个 Tab（档案/分类+事件/聊天记录/拜访/备注），所有数据手动维护。

---

### V2.0 — 智能 CRM（AI 分析全线接入）

| 表 | 原因 |
|----|------|
| wechat_friend_finance | 依赖 AI OCR + 金额提取管线 |
| friend_event | 依赖 AI 聊天分析管线 |
| friend_score_log | 依赖 friend_event |
| friend_opportunity | 依赖 friend_event |
| actionable_insight | 依赖上面 4 表全部 |
| action_template | 配合 actionable_insight |
| automation_rule | 配合 actionable_insight |

**延期原因不是"表太多"，是"上游管线还没跑"**。AI 分析管线需要 V1.0 积累的真实数据来验证准确率。如果 V1.0 期间 1962 个好友的聊天记录被大量采集，V2.0 的 AI 分析就有了充足的燃料。

---

## 四、总结

| | V1.0 | V2.0 |
|------|------|------|
| 扩展字段 | 12 | - |
| 新表 | 6 + 已扩展 | 7 |
| 依赖 | 全部手动输入 | 全部 AI 分析管线 |
| 交付物 | 完整的 5 Tab CRM + 手动画像 | 自动评分 + 洞察 + 行动闭环 |

**设计已完整。实现延后是因为 AI 管线需要真实数据，不是表太多。**
