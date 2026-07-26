---
sidebar_position: 3
title: "WeChat CRM 页面功能设计"
description: "微信营销管理系统的完整 UI/UX 设计：布局、导航、组件、交互流程"
---

# 微信营销管理系统 — 页面功能设计

## 整体布局

复用 Hermes 已有 `MasterDetail` 布局（与 Messaging 一致）：

```
┌─ 左侧导航 (260px) ─────┬── 右侧主内容区 (flex-1) ───────────┐
│                         │                                    │
│  🔍 搜索好友/群          │  根据左侧选中项动态渲染              │
│                         │                                    │
│  📊 仪表盘              │  ┌─ 详情面板 / 列表 / 聊天记录 ──┐  │
│  👤 我的好友 (3,847)    │  │                                │  │
│  👥 我的群聊 (412)      │  │                                │  │
│  ──────────────         │  │                                │  │
│  📨 群发消息             │  │                                │  │
│  📋 消息模板             │  │                                │  │
│  📈 数据统计             │  └────────────────────────────────┘  │
│  ──────────────         │                                    │
│  ⚙️ 微信管理             │                                    │
│  🔄 同步数据             │                                    │
└─────────────────────────┴────────────────────────────────────┘
```

---

## 一、左侧导航

### 1.1 搜索框 (顶部固定)
- 全局搜索：输入名称/备注/手机/微信号，实时过滤好友和群
- 搜索结果按匹配度排序，高亮命中关键词

### 1.2 仪表盘
- 总好友数 / 总群数 / 本月新增 / 活跃好友数
- 近7天消息量趋势图（柱状）
- Top 10 最热联系好友（按聊天次数）
- 最近操作日志摘要

### 1.3 我的好友 (左侧列表)
**列表项显示**：头像 + 昵称 + 备注名 + 最后消息摘要 + 时间

**好友详情面板（点击左侧好友后右侧展示）**：

#### Tab 1: 基本档案
A区 — 个人信息：
- 头像（大图） | 昵称 | 微信号(wxid) | 别名 | 备注名（可编辑）
- 地区 | 性别 | 签名
- 添加来源 (source / source_type) | 首次认识时间
- 共同群聊数

B区 — 联系方式：
- 手机号 | QQ | 邮箱（从聊天记录中提取）
- 企业微信关联

C区 — 来源与标签：
- 来源群 (source_group)
- 自定义 Tags（可编辑，AI 自动建议）
- 是否星标好友 / 黑名单

#### Tab 2: 人头画像 · 关系图谱（核心差异化功能）

> AI 自动分析 + 人工校准，持续完善每个好友的立体画像。
> 目的：帮主人记住"这人是谁、跟我什么关系、我该怎么对他"。

**A区 — 关系分类（结构化标签树）**

每个好友可被归入 **多棵分类树**（多对多），每棵树  级结构：`大类 → 子类 → 级别`。

级别统一用颜色驱动：

| 级别 | 含义 | 颜色 | 场景 |
|------|------|------|------|
| **1 级** | 好 / 亲近 / 重要 | 🔴 红色 | 挚友、直属领导、大客户 |
| **2 级** | 一般 / 普通 | ⚪ 默认色 | 普通同学、一面之交 |
| **3 级** | 不好 / 疏远 / 黑 | ⚫ 灰色 | 有过节、已拉黑、僵死 |

**分类树定义**：

```
1. 血缘关系
   ├─ 直系血亲 ─── 父/母/配偶/子女
   ├─ 旁系血亲 ─── 兄弟姐妹/叔伯/姑/舅/姨
   └─ 姻亲 ─────── 岳父母/公婆/姐夫/嫂子
   级别: 1=亲近 2=一般 3=冷淡

2. 亲戚
   └─ (自由填写: 堂兄/表妹/远房/…)  ← 按亲疏分 1/2/3 级

3. 同乡/老乡
   ├─ 同村
   ├─ 同镇
   ├─ 同县/区
   ├─ 同市
   └─ 同省
   级别: 1=常来往 2=偶尔联系 3=基本不联系

4. 同学  (按时间段 + 子级)
   ├─ 小学 ───── [级: 1/2/3]  [年份: 199x-200x]
   ├─ 初中 ───── 同上
   ├─ 高中 ───── 同上
   ├─ 中专/技校 ─ 同上
   ├─ 大专 ───── 同上
   ├─ 本科 ───── 同上  [校名: ____]
   ├─ 硕士 ───── 同上  [校名: ____]
   ├─ 博士 ───── 同上  [校名: ____]
   └─ 培训班/进修 ─ 同上  [名称: ____]
   级别: 1=铁哥们/闺蜜 2=普通同窗 3=几乎不联系

5. 战友
   ├─ 同年兵
   ├─ 同连队
   └─ 同部队(不同期)
   级别: 1=生死之交 2=战友情 3=一般

6. 同事  (按时间段/职位关系)
   ├─ 年份标签: "2000年同事" / "2018年同事" / …  ← 模糊年份即可
   ├─ 公司: [公司名]
   ├─ 职位关系:
   │   ├─ 领导/上级 (直属/隔级)
   │   ├─ 平级同事
   │   ├─ 下属 (直属/隔级)
   │   ├─ 跨部门同事
   │   └─ 前同事 (已离职)
   └─ 级别: 1=亦师亦友/铁杆 2=普通同事 3=有过节/不往来

7. 客户/生意伙伴
   ├─ A类客户 ─── 大单/长期 (红)
   ├─ B类客户 ─── 中等/活跃 (红)
   ├─ C类客户 ─── 小单/低频 (默认)
   ├─ D类客户 ─── 潜在/陌拜 (默认)
   └─ 流失客户 ─── 已断约 (灰)
   级别: 1=VIP 2=正常 3=僵死

8. 供应商
   ├─ 核心供应商
   ├─ 备选供应商
   └─ 曾合作/已停
   级别: 1=战略合作 2=正常采购 3=已终止

9. 同行/竞品
   ├─ 直接竞争
   ├─ 间接相关
   └─ 可合作/互补
   级别: 1=友好 2=中立 3=敌对

10. 供应链/上下游
    ├─ 上游 (原材料/零部件)
    ├─ 下游 (经销商/零售)
    ├─ 物流/仓储
    └─ 服务商 (设计/法务/代账/…)

11. 兴趣/圈子
    └─ (自由标签: 球友/牌友/钓鱼/读书会/教会/…)
    级别: 1=核心成员 2=参与者 3=边缘

12. 邻居
    ├─ 现邻居
    └─ 曾邻居 (年份: ____)

13. 其他/未分类
    └─ (待 AI 分析后自动归类)
```

**B区 — 一句话描述（AI 自动生成，人工可编辑）**

"跟老许是2015年在深圳坂田华为基地认识的，当时是同一个项目组的同事。他做后端我作前端，合作了3年多。人很靠谱技术好，现在已经跳到腾讯T9了。大概每半年见一次。老婆是湖南人。"

→ AI 从聊天记录中提取关键事件 + 时间 + 地点 + 关系变迁，生成**自然语言的人物速写**。每个被标注的好友都有一句话。

**C区 — 关键事件时间线（AI 提取）**

| 时间 | 事件 |
|------|------|
| 2015.03 | 初识：坂田华为基地，同项目组 |
| 2017.08 | 事件：一起加班赶 A项目上线 |
| 2018.12 | 变迁：老许离职去腾讯 |
| 2019.05 | 见面：深圳科技园吃饭 |
| 2023.01 | 最近：微信拜年，聊了小孩上学的事 |

→ 帮助主人下次聊天时能自然寒暄："你上次说的那个项目怎么样了？"

---

#### 数据库设计 — 关系分类存储

```sql
-- 关系分类定义表 (系统预置)
CREATE TABLE IF NOT EXISTS wechat_relation_tree (
    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
    tree_key    VARCHAR(32)  NOT NULL,          -- 大类: family/relative/hometown/classmate/...
    tree_name   VARCHAR(64)  NOT NULL,          -- 中文名: 血缘/亲戚/同乡/同学/同事/...
    parent_key  VARCHAR(32),                    -- 父节点 tree_key (NULL=顶层)
    level       INT DEFAULT 0,                  -- 树深度: 0=大类 1=子类 2=细类
    sort_order  INT DEFAULT 0
);

-- 好友关系标记 (多对多: 一个好友可属于多个分类)
CREATE TABLE IF NOT EXISTS wechat_friend_relation (
    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
    friend_id   INTEGER NOT NULL,               -- → wechat_friend.id
    tree_key    VARCHAR(32) NOT NULL,           -- → wechat_relation_tree.tree_key
    sub_key     VARCHAR(32),                    -- 子类 key (如 'colleague' → 'leader')
    relation_level TINYINT DEFAULT 2,           -- 1=红(好) 2=默认(一般) 3=灰(不好)
    time_label  VARCHAR(64),                    -- 时间标签: '2015-2018' / '小学' / ''
    org_label   VARCHAR(128),                   -- 组织标签: '华为' / '清华大学' / '3连'
    is_primary  TINYINT DEFAULT 0,              -- 是否主要关系
    notes       VARCHAR(256),                   -- 简短备注
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    INDEX idx_friend (friend_id),
    INDEX idx_tree (tree_key),
    UNIQUE KEY uk_friend_tree (friend_id, tree_key, sub_key)
);

-- 好友一句话描述
ALTER TABLE wechat_friend ADD COLUMN portrait_summary TEXT;
  -- AI 生成的 50~200 字人物速写

-- 好友关键事件
CREATE TABLE IF NOT EXISTS wechat_friend_event (
    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
    friend_id   INTEGER NOT NULL,
    event_date  VARCHAR(32),                    -- '2015-03' 或 '2015'
    event_type  VARCHAR(32) DEFAULT 'general',  -- first_met / milestone / reunion / life_change
    title       VARCHAR(256),
    detail      TEXT,
    source      VARCHAR(32) DEFAULT 'ai',       -- 'ai' / 'manual' / 'chat'
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    INDEX idx_friend_event (friend_id, event_date)
);
```

**D区 — 经济往来账簿（与个人财务打通）**

> 社会关系的本质不只是感情，还有"互相欠着的人情和钱"。
> 这部分量化记录与每个好友的经济往来，帮助主人随时知道：
> 「我欠谁多少钱 / 谁欠我多少钱 / 我们之间的经济来往有多深」。

| 字段 | 类型 | 说明 |
|------|------|------|
| 借款给TA | 金额 + 币种 + 时间 | 我借出 |
| 从TA借款 | 金额 + 币种 + 时间 | 我借入 |
| 应收款 | 金额 + 说明 | TA该付给我的（代购/垫付/投资） |
| 应付款 | 金额 + 说明 | 我该付给TA的 |
| 已结清 | ✓ 标记 | 是否已还清 |
| 约定还款日 | 日期 | 口头/书面约定 |
| 经济来往深度 | 0-100 | 综合评分：金额×频率×时效 |

**经济事件时间线**（AI 从聊天中提取 + 人工录入）：

| 时间 | 类型 | 金额 | 说明 | 状态 |
|------|------|------|------|------|
| 2024.03 | 借款出 | ¥5,000 | 说急用周转 | ✗ 未还 |
| 2024.06 | 代购垫付 | ¥320 | 帮买了个机械键盘 | ✓ 已还 |
| 2025.01 | 借款入 | ¥20,000 | 我买房周转，TA主动说"有需要说" | 约定2025.12还 |

**AI 自动提取规则**：
- 聊天中出现 "借" / "转你" / "你先帮我" / "回头给你" → 标记待确认
- 金额数字 + 支付宝/微信转账截图 → 自动记录
- 对方说 "还你" / "已转" → 自动标记为已结清
- 每条经济记录可绑定到聊天消息（跳转到原文核实）

```sql
-- 好友经济往来
CREATE TABLE IF NOT EXISTS wechat_friend_finance (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    friend_id       INTEGER NOT NULL,               -- → wechat_friend.id
    direction       VARCHAR(8)  NOT NULL,           -- 'out'=我借/付给TA  'in'=TA借/付给我
    finance_type    VARCHAR(16) NOT NULL,           -- 'loan'(借款) 'payment'(代付) 'investment'(投资) 'gift'(礼金)
    amount          DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(8) DEFAULT 'CNY',
    title           VARCHAR(256),                   -- 事由简述
    detail          TEXT,                            -- 详细说明
    due_date        DATE,                            -- 约定(还款)日期
    is_settled      TINYINT DEFAULT 0,              -- 0=未结清 1=已结清
    settled_at      DATETIME,
    chat_ref        VARCHAR(64),                    -- 来源聊天消息ID (可跳转)
    source          VARCHAR(16) DEFAULT 'manual',   -- 'manual' / 'ai_extracted'
    event_date      DATE,                            -- 发生日期
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    INDEX idx_friend_settled (friend_id, is_settled)
);
```

---

#### Tab 3: 聊天记录 (100% 还原)
- 消息时间线，支持日期跳转
- 消息类型标识：文字/图片/文件/语音/视频/系统消息
- 绿色标记 = AI 参与生成的消息
- 搜索：关键词 / 日期范围 / 消息类型
- 统计摘要：总消息数、文字/图片/文件占比

#### Tab 4: 销售跟进
- **拜访记录**：时间线，每次沟通摘要（AI 自动生成）
- **销售目标**：设定的目标 + 完成进度
- **客户分类**：A/B/C/D 级
- **客户备注**：自由文本（可编辑）
- **关联文档**：上传的合同/报价单等
- **热度评估**：综合评分 (0-100)
- **跟进提醒**：下次联系时间

### 1.4 我的群聊
**列表项显示**：群名 + 成员数 + 最后消息时间

**群详情**：
- 群名 | 群备注 | 群主 | 成员数
- 我的群昵称 | 是否免打扰 | 是否保存到通讯录
- **成员列表**（可展开，点击跳转到好友详情）
- 群活跃度评分
- 群消息统计

### 1.5 群发消息
- **选择目标**：全选 / 按标签 / 按分类 / 逐个勾选
- **消息编辑区**：
  - 模板选择器（下拉）
  - AI 智能话术生成（输入意图 → AI 生成多条候选）
  - 变量占位符：`{昵称}` `{备注}` `{日期}`
  - 情感设置：亲切/正式/活泼/幽默
  - 预览区（渲染后的效果）
- **发送控制**：
  - 间隔时间设置（防封号）
  - 发送进度条
  - 失败重试机制

### 1.6 消息模板
- 模板列表：标题 + 分类 + 创建时间
- 新建/编辑模板：标题、正文（支持变量）、分类
- AI 辅助优化模板

### 1.7 数据统计
- **总览**：好友数、群数、总消息量、活跃度
- **好友排行**：按聊天次数/时长/热度
- **时间趋势**：按天/周/月的消息量
- **关系图谱**：好友之间的共同群关系

### 1.8 微信管理
- 当前登录信息：头像 + 昵称 + 微信号
- **切换微信**：显示二维码 → 手机扫码登录
- **退出微信**：确认退出

### 1.9 同步数据
- **好友同步**：从微信客户端采集 → 写入 wechat_friend 表（已有功能）
- **聊天同步**：采集聊天记录 → 写入 wechat_chat 表（已有功能）
- 同步进度条 + 增量/全量选择
- 最后同步时间显示

---

## 二、右侧主内容：好友详情（核心页面）

### 布局：Tab 切换

```
┌──────────────────────────────────────────────────────┐
│ [基本档案] [人头画像👤] [聊天记录] [销售跟进]           │
├──────────────────────────────────────────────────────┤
│                                                        │
│   基本档案 = 头像/昵称/备注/手机/签名/来源/黑名单/置顶    │
│   人头画像 = 关系分类标签树 + 一句话描述 + 关键事件时间线  │
│   聊天记录 = 100% 消息还原 + 搜索 + AI 标记              │
│   销售跟进 = A/B/C/D客户评级 + 拜访记录 + 热度评分        │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 三、Obsidian 打通 — 个人知识库数据闭环

> 用户在 Obsidian 中维护自己的个人日志、日记、项目管理、财务记录。
> WinPeek CRM 作为"社交关系数据源"，与 Obsidian vault 双向打通，
> 让社交关系数据沉淀到用户的第二大脑中，形成"点滴有用"的长期积累。

### 3.1 打通架构

```
┌─────────────────────────────────────────────────────────┐
│                    WinPeek CRM                          │
│  wechat_friend │ finance │ event │ chat │ relation      │
└────────┬──────────────────────────────────┬─────────────┘
         │ 读取 Obsidian vault               │ 写入 Obsidian vault
         ▼                                    ▼
┌─────────────────────────────────────────────────────────┐
│              Obsidian Vault (本地文件夹)                   │
│                                                         │
│  📂 人脉/                     ← 每个好友一个 .md          │
│  │  ├─ 许国勇.md               ← 自动同步基本信息+画像      │
│  │  ├─ 于大海.md                                         │
│  │  └─ ...                                               │
│  │                                                       │
│  📂 财务/                     ← 经济往来汇总               │
│  │  ├─ 应收应付.md             ← 从 finance 表定期生成      │
│  │  └─ 借出记录.md                                       │
│  │                                                       │
│  📂 日记/                     ← 用户的日常记录             │
│  │  ├─ 2025-01-15.md          ← 可从聊天事件生成日记草稿    │
│  │  └─ ...                                               │
│  └─ 📂 模板/                   ← CRM 定义的模板            │
│     └─ 人脉卡片模板.md                                    │
└─────────────────────────────────────────────────────────┘
```

### 3.2 好友卡片自动同步 — 双向

每个好友在 Obsidian 中有一张 `.md` 卡片，由 CRM **自动生成并持续更新**。

**Obsidian 中的 `许国勇.md` 示例**：

```markdown
---
name: 许国勇
wxid: wxid_abc123
phone: 138xxxx1234
relation:
  - tree: 同事
  - sub: 领导
  - level: 1 (红)
  - time: 2015-2018
  - org: 华为
  - note: 深圳坂田基地项目组
  - tree: 同学
  - sub: 本科
  - level: 1 (红)
  - org: 华中科技大学
tags: [人脉, 重要, 华为, 前同事, 同学]
heat_score: 87
customer_level: A
portrait_summary: "跟老许是2015年在深圳坂田华为基地认识的..."
updated: 2025-01-15
---

# 许国勇

## 一句话速写
跟老许是2015年在深圳坂田华为基地认识的，当时是同一个项目组的同事。
他做后端我做前端，合作了3年多。人很靠谱技术好，现在已经跳到腾讯T9了。
大概每半年见一次。老婆是湖南人。

## 关系标签
- 🔴 [同事] 领导 · 2015-2018 · 华为 · 坂田基地项目组
- 🔴 [同学] 本科 · 华中科技大学

## 关键事件
| 时间 | 事件 |
|------|------|
| 2015.03 | 初识：坂田华为基地，同项目组 |
| 2017.08 | 一起加班赶 A项目上线 |
| 2018.12 | 老许离职去腾讯 |
| 2025.01 | 微信拜年，聊了小孩上学的事 |

## 经济往来
| 时间 | 类型 | 金额 | 状态 |
|------|------|------|------|
| 2024.06 | 代购垫付·机械键盘 | ¥320 | ✓ 已还 |

## 微信聊天统计
- 总消息: 2,847 条
- 首次聊天: 2018-03-15
- 最近聊天: 2025-01-20
- 热度: ████████░░ 87/100

## 操作
- [ ] 下次联系时间: ___
- [ ] 跟进事项: ___
```

**同步策略**：

| 方向 | 触发条件 | 内容 |
|------|---------|------|
| CRM → Obsidian | 画像更新 | 覆盖 frontmatter + 一句话描述 + 关系标签 + 事件表 |
| CRM → Obsidian | 每次聊天分析 | 追加聊天统计 + 新提取事件 |
| Obsidian → CRM | 用户手动编辑 frontmatter | 更新 tags / 备注 / relation_level |
| Obsidian → CRM | 用户在日记中提到好友 | AI 提取关联事件写入 `wechat_friend_event` |

### 3.3 日记关联 — 从聊天到日记再到 CRM

用户每天在 Obsidian 写日记。CRM 可以：

1. **生成日记草稿**：根据当天的微信聊天摘要，自动生成日记条目
   ```
   ## 今日社交摘要 (2025-01-15)
   - 许国勇聊了小孩上学的事，他说在找学区房
   - 于大海发了个搞笑视频
   - 微信群里讨论了周末聚会地点
   ```

2. **从日记反向关联**：用户日记里写了 `[[许国勇]]` 或提到人名，
   → CRM 自动将相关内容作为"关键事件"记录到该好友

3. **日记中提到经济往来**：用户在日记写 "今天还了许国勇 320" 
   → 自动更新 `wechat_friend_finance` 标记已结清

### 3.4 财务汇总 — 定期同步到 Obsidian

每周/每月在 Obsidian 生成财务汇总：

```markdown
# 应收应付总览 (2025年1月)

## 借出未还
| 谁 | 金额 | 借出日期 | 约定还款 | 逾期 |
|------|------|---------|---------|------|
| 张三 | ¥5,000 | 2024-03 | 2024-06 | ✗ 7个月 |
| 李四 | ¥2,000 | 2025-01 | 2025-03 | - |

## 借入未还
| 谁 | 金额 | 借入日期 | 约定还款 |
|------|------|---------|---------|
| 许国勇 | ¥20,000 | 2025-01 | 2025-12 |

## 本月已结清
- 01-05 还许国勇代购款 ¥320 ✓
```

### 3.5 配置方式

```yaml
# ~/.hermes/config.yaml 或 plugin.yaml 中
winpeek:
  obsidian:
    enabled: true
    vault_path: "D:/Obsidian/我的知识库"      # Obsidian vault 根目录
    contact_folder: "人脉"                     # 好友卡片存放目录（相对于 vault）
    finance_folder: "财务"                     # 财务汇总目录
    diary_folder: "日记"                       # 日记目录
    auto_sync_interval: 3600                   # 自动同步间隔(秒), 0=仅手动
    sync_on_profile_update: true               # 画像更新时立即同步
    sync_on_finance_change: true               # 经济记录变更时立即同步
    extract_from_diary: true                   # 从日记反向提取事件
    generate_diary_draft: false                # 是否自动生成日记草稿
```

---

## 设计原则零：自扩展数据库

> **核心原则**：系统数据库不是写死的。任何新需求（新增分类、新增字段、新增品类）都应**动态扩展**，不需要改代码、不需要等发版。

### 工作流

```
用户说"我需要记录XXX" 
  → 系统检查当前表里有没有对应字段/枚举值
  → 没有？上网搜索相关知识 → AI 生成分类体系
  → 自动 ALTER TABLE / 插入枚举种子数据
  → 新版UI自动渲染新字段
  → 完成
```

### 三层扩展机制

| 层级 | 场景 | 实现 |
|------|------|------|
| **枚举扩展** | "电视剧类型里没有'纪录片'" | INSERT INTO 枚举表 / 前端下拉自动追加 |
| **字段扩展** | "好友表里我想记'星座'" | ALTER TABLE ADD COLUMN → AI 推荐字段类型/默认值 |
| **品类扩展** | "我要记'宠物用品消费'" | 网上搜常见宠物用品品牌/档次 → 批量入库 |

### AI 的职责

1. **上网搜索**：用户说 "增加 XX 分类" → 搜索 XX 的行业标准分类
2. **生成分类树**：输出结构化的父子层级
3. **入库**：写入枚举表 + 前端下拉自动渲染
4. **去重合并**：已有部分不重复建，只补没有的

### 枚举种子表设计

```sql
-- 系统所有下拉选项的元数据表
CREATE TABLE sys_enum_definition (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    enum_group      VARCHAR(64) NOT NULL,      -- 分组: 'industry' / 'religion' / 'tv_genre' / 'music_style' / 'exercise_type' / ...
    enum_key        VARCHAR(64) NOT NULL,      -- 键
    enum_value      VARCHAR(128) NOT NULL,     -- 显示值
    parent_key      VARCHAR(64),               -- 父级 (树形)
    icon            VARCHAR(8),                -- emoji
    description     VARCHAR(256),              -- 说明
    source          VARCHAR(16) DEFAULT 'system', -- 'system' / 'ai' / 'user' / 'web'
    search_query    VARCHAR(256),              -- 搜索关键词 (AI 用来上网查)
    sort_order      INT DEFAULT 0,
    is_active       TINYINT DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_enum (enum_group, enum_key)
);
```

### 用户触发方式

```
1. 前端下拉最后一项永远是 "+ 添加更多…"
2. 点击 → 弹窗："你想加什么？"
3. 输入 → 系统上网搜 → 返回候选项 → 用户确认/微调 → 入库
4. 下次打开下拉，新选项已在列表中
```

### 示例

```
用户: "宗教里没有'犹太教'"
  → AI搜索 "世界主要宗教分类"
  → 返回: 犹太教(Orthodox/Conservative/Reform) + 锡克教 + 巴哈伊教 + 耆那教 + 神道教 + …
  → 用户勾选要的 → 写入 sys_enum_definition
  → 下拉立即出现
```

---

## 四、个人助理系统 — 360° 主人关怀

> 在"管人"之外，加上"管自己"。
> 系统不只是 CRM，而是一个了解主人、主动关怀的个人助理。
> 所有数据可写入 Obsidian vault，形成主人专有的第二大脑。

### 4.1 模块全景

```
                    ┌────────────────────────┐
                    │     主人 (Self)         │
                    │  头像 / 昵称 / 简介      │
                    └───────┬────────────────┘
                            │
    ┌───────┬───────┬──────┼──────┬──────┬───────┬────────┐
    ▼       ▼       ▼      ▼      ▼      ▼       ▼        ▼
  记事    待办    任务   消费   学习   职业    模板     360°统计
 Journal  Todo   Task  Expense Study Career Templates  Dashboard
```

**核心理念**：助理比主人更了解主人自己——知道主人今天花了多少钱、下一步职业目标是什么、这周该学什么、还有哪些事没做。

### 4.2 记事 (Journal / 日记)

时间线上的个人记录。与 Obsidian 日记互相同步。

**字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| 日期 | DATE | 记录的日期（可以是过去某天） |
| 时间 | TIME | 具体时间（可选） |
| 类型 | enum | 日记/备忘/灵感/心情/总结 |
| 标题 | VARCHAR(256) | 可选 |
| 正文 | TEXT | 自由文本 (Markdown) |
| 心情 | enum | 😊😐😢😡😰 (5 档) |
| 天气 | VARCHAR(32) | 晴/阴/雨/雪/… (AI 可自动填) |
| 地点 | VARCHAR(128) | GPS 或手动 |
| 标签 | JSON array | 自由标签 |
| 关联好友 | JSON array | 关联的联系人 ID |
| 关联消费 | JSON array | 关联的消费记录 ID |
| 来源 | enum | manual / ai_draft / obsidian_import |
| obsidian_path | TEXT | Obsidian 日记文件路径 |

**AI 辅助**：
- 每天晚上 22:00 自动生成当日日记草稿（今天聊了谁、花了什么钱、完成了什么任务）
- 从聊天中提取值得记录的事件（"今天许国勇跟我说…"）

### 4.3 待办 (Todo)

轻量级任务卡片，Kanban 式管理。

| 字段 | 类型 | 说明 |
|------|------|------|
| 标题 | VARCHAR(256) | 必填 |
| 描述 | TEXT | 详情 |
| 状态 | enum | todo→doing→done→cancelled |
| 优先级 | enum | P0(紧急) P1(重要) P2(一般) P3(低) |
| 截止日期 | DATE | 可选 |
| 提醒时间 | DATETIME | 到时通知 |
| 标签 | JSON array | 分类标签 |
| 关联好友 | JSON array | 这是个"给谁做的事" |
| 来源 | enum | manual / ai_extracted / from_chat |
| 重复规则 | VARCHAR(64) | daily/weekly/monthly/… cron 表达式 |
| 估计耗时 | INT | 分钟 |
| 实际耗时 | INT | 分钟 (完成时填写) |

**AI 辅助**：
- 聊天中出现 "我明天…" / "你记得…" / "别忘了…" → 自动创建待办
- 每天早 8:00 推送今日待办摘要
- 逾期待办自动提醒 + 重新排期建议

### 4.4 任务/项目 (Task / Project)

比 Todo 更重：有子任务、有里程碑、有进度。

| 字段 | 类型 | 说明 |
|------|------|------|
| 名称 | VARCHAR(256) | 必填 |
| 描述 | TEXT | |
| 类型 | enum | personal / work / study / finance / health |
| 状态 | enum | planning→active→paused→done→archived |
| 进度 | INT | 0-100 (%)，可自动根据子任务计算 |
| 开始日期 | DATE | |
| 目标完成 | DATE | |
| 实际完成 | DATE | |
| 里程碑 | JSON array | `[{title, due, done}]` |
| 子任务 | → `personal_task_item` 表 | 树形结构 |
| 关联好友 | JSON array | 涉及的联系人 |
| 笔记 | TEXT | Markdown 关联笔记 |

### 4.5 个人消费记账 (Personal Expense)

每一笔消费都被记录、分类、统计。

| 字段 | 类型 | 说明 |
|------|------|------|
| 日期 | DATE | 消费日期 |
| 时间 | TIME | 具体时间 |
| 金额 | DECIMAL(10,2) | |
| 币种 | VARCHAR(8) | CNY/USD/… 默认 CNY |
| 大类 | enum | 饮食/交通/住房/购物/娱乐/医疗/教育/人情/捐赠/烟酒/其他 |
| 子类 | VARCHAR(64) | 细分类目 |
| 具体描述 | VARCHAR(256) | "买了一包芙蓉王" / "捐了水滴筹" |
| 支付方式 | enum | 微信/支付宝/现金/银行卡/信用卡/其他 |
| 是否必要 | enum | need(必需) / want(想要) / impulse(冲动) |
| 心情关联 | enum | 消费时的心情 |
| 地点 | VARCHAR(128) | |
| 关联好友 | JSON array | "和谁一起吃的饭" |
| 收据/小票 | TEXT | 图片路径或 OCR 文本 |
| 标签 | JSON array | |
| 来源 | enum | manual / ai_auto / chat_extracted |

**示例数据**：

| 日期 | 大类 | 描述 | 金额 | 心情 |
|------|------|------|------|------|
| 2025-01-15 | 烟酒 | 芙蓉王 (硬) | ¥25 | 😐 |
| 2025-01-15 | 饮食 | 矿泉水×1 | ¥2 | 😐 |
| 2025-01-14 | 捐赠 | 水滴筹-同事父亲生病 | ¥200 | 😢 |
| 2025-01-14 | 饮食 | 请许国勇吃饭 | ¥180 | 😊 |
| 2025-01-13 | 交通 | 打车去高铁站 | ¥56 | 😐 |

**AI 辅助**：
- 微信支付/支付宝截图 → OCR + 自动分类 + 创建消费记录
- 月底自动生成消费报告：按大类饼图 + 同比环比 + 预算预警
- "烟"类别超过预算 → 主动提醒："主人，这个月烟钱已经 ¥750 了，比上月多了 15%。"
- 在日记里写"今天买了两包烟" → 自动识别为消费记录

### 4.6 学习笔记 + 学习计划

| 子模块 | 说明 |
|------|------|
| 学习笔记 | Markdown 笔记，标签化，可关联到知识领域树 |
| 学习计划 | 目标课程/书籍 + 计划完成日期 + 每日学习时长 |
| 学习进度 | 按知识领域的完成度 % |
| 学习日志 | 每天学了什么、学了多久（自动从 Obsidian 日记提取） |
| 知识地图 | 已掌握 vs 待学习的技能树可视化 |

**字段**：

```sql
-- 学习计划
CREATE TABLE personal_study_plan (
    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
    title       VARCHAR(256) NOT NULL,
    domain      VARCHAR(64),           -- 领域: programming/design/language/finance/health/…
    sub_domain  VARCHAR(64),           -- 子领域
    goal        TEXT,                  -- 学习目标
    target_date DATE,
    status      VARCHAR(16) DEFAULT 'planning',  -- planning/active/paused/done
    daily_min   INT DEFAULT 30,        -- 每日最低学习时间(分钟)
    total_hours DECIMAL(8,1) DEFAULT 0, -- 累计学习时长
    progress    INT DEFAULT 0,         -- 0-100
    notes       TEXT,                  -- Markdown
    resource_url TEXT,                 -- 课程链接/书单
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 学习日志
CREATE TABLE personal_study_log (
    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
    plan_id     INTEGER,
    log_date    DATE NOT NULL,
    duration    INT NOT NULL,           -- 分钟
    content     TEXT,                   -- 学什么了
    notes       TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES personal_study_plan(id) ON DELETE SET NULL
);
```

### 4.7 职业规划

| 字段 | 说明 |
|------|------|
| 当前职位 | 公司 / 职位 / 行业 / 入职日期 |
| 目标职位 | 期望职位 / 期望行业 / 期望薪资 |
| 技能差距 | 当前 vs 目标之间的技能差异（列表） |
| 里程碑 | 考证/跳槽/晋升/转行 等关键节点 |
| 行动计划 | 关联的学习计划 + 任务 |
| 简历版本 | 关联的 Obsidian 简历 `.md` 路径 |
| 面试记录 | 面试公司/时间/结果/反思 |

### 4.8 模板系统

用户可在"模板市场"中选择预置模板，一键创建对应模块的结构。

**模板列表**：

| 模板 | 用途 |
|------|------|
| 日记模板 | 每日复盘 (今日完成/今日感悟/明日计划) |
| 周报模板 | 本周工作/学习/社交/财务总结 |
| 月报模板 | 月度深度复盘 |
| 学习计划模板 | 编程/英语/考证/… |
| 职业规划模板 | 5年职业路线图 |
| 消费预算模板 | 月度预算分配 (50%必需/30%想要/20%储蓄) |
| 项目模板 | 个人项目 (含里程碑) |
| 人脉维护模板 | 定期联系计划 |

### 4.9 360° 统计仪表盘

一张综合视图，让主人一目了然：

```
┌──────────────────────────────────────────────────────┐
│          主人关怀 · 今日快照 (2025-01-15)              │
├─────────────┬──────────┬──────────┬──────────────────┤
│  💰 今日消费 │ 📝 待办  │ 📖 学习  │ 👥 今日互动       │
│  ¥207       │ 3 待完成 │ 45 分钟  │ 许国勇、于大海     │
├─────────────┴──────────┴──────────┴──────────────────┤
│                                                        │
│  📈 本月消费趋势 (折线图)     📊 消费分类饼图              │
│                                                        │
│  📚 学习进度                    📋 逾期待办               │
│  React 入门  ████████░░ 80%     ⚠ 还许国勇钱 (逾期3天)   │
│  TypeScript  ████░░░░░░ 40%     ⚠ 续保车险 (明天截止)    │
│                                                        │
│  🔥 近期重点 (AI 推荐)                                  │
│  • 许国勇的借款快到期了，准备好还款了吗？                   │
│  • 你连续3天没学 TypeScript 了                           │
│  • 本周消费超出预算 ¥320，主要在"餐饮"                    │
│                                                        │
└──────────────────────────────────────────────────────┘
```

### 4.10 个人助理数据库

```sql
-- 日记/记事
CREATE TABLE personal_journal (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    log_date        DATE NOT NULL,
    log_time        TIME,
    entry_type      VARCHAR(16) DEFAULT 'diary',   -- diary/memo/inspiration/mood/summary
    title           VARCHAR(256),
    body            TEXT,
    mood            VARCHAR(4),                     -- great/good/neutral/sad/angry
    weather         VARCHAR(32),
    location        VARCHAR(128),
    tags            TEXT,                           -- JSON array
    related_friends TEXT,                           -- JSON array of friend IDs
    related_expense  TEXT,                          -- JSON array of expense IDs
    source          VARCHAR(16) DEFAULT 'manual',
    obsidian_path   VARCHAR(512),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_date (log_date)
);

-- 待办
CREATE TABLE personal_todo (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    title           VARCHAR(256) NOT NULL,
    description     TEXT,
    status          VARCHAR(16) DEFAULT 'todo',     -- todo/doing/done/cancelled
    priority        VARCHAR(4) DEFAULT 'P2',        -- P0/P1/P2/P3
    due_date        DATE,
    remind_at       DATETIME,
    tags            TEXT,                            -- JSON array
    related_friends TEXT,                            -- JSON array
    source          VARCHAR(16) DEFAULT 'manual',
    recurrence      VARCHAR(64),                     -- cron or 'daily'/'weekly'/'monthly'
    est_minutes     INT,
    actual_minutes  INT,
    completed_at    DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    obsidian_path   VARCHAR(512),
    INDEX idx_status (status),
    INDEX idx_due (due_date)
);

-- 任务/项目
CREATE TABLE personal_project (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    title           VARCHAR(256) NOT NULL,
    description     TEXT,
    project_type    VARCHAR(16) DEFAULT 'personal',  -- personal/work/study/finance/health
    status          VARCHAR(16) DEFAULT 'planning',   -- planning/active/paused/done/archived
    progress        INT DEFAULT 0,
    start_date      DATE,
    target_date     DATE,
    completed_at    DATE,
    milestones      TEXT,                             -- JSON: [{title, due, done}]
    related_friends TEXT,                             -- JSON
    notes           TEXT,
    obsidian_path   VARCHAR(512),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 项目子任务
CREATE TABLE personal_project_item (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id      INTEGER NOT NULL,
    parent_id       INTEGER,                          -- 树形父节点
    title           VARCHAR(256) NOT NULL,
    status          VARCHAR(16) DEFAULT 'todo',
    sort_order      INT DEFAULT 0,
    due_date        DATE,
    completed_at    DATETIME,
    FOREIGN KEY (project_id) REFERENCES personal_project(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES personal_project_item(id) ON DELETE CASCADE,
    INDEX idx_project (project_id)
);

-- 个人消费
CREATE TABLE personal_expense (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    expense_date    DATE NOT NULL,
    expense_time    TIME,
    amount          DECIMAL(10,2) NOT NULL,
    currency        VARCHAR(8) DEFAULT 'CNY',
    category        VARCHAR(16) NOT NULL,              -- food/transport/housing/shopping/entertain/medical/edu/favor/donate/smoke_drink/other
    sub_category    VARCHAR(64),
    description     VARCHAR(256),
    payment_method  VARCHAR(16),                       -- wechat/alipay/cash/bank_card/credit_card/other
    necessity       VARCHAR(8),                        -- need/want/impulse
    mood            VARCHAR(4),
    location        VARCHAR(128),
    related_friends TEXT,                              -- JSON
    receipt_path    VARCHAR(512),
    tags            TEXT,                              -- JSON
    source          VARCHAR(16) DEFAULT 'manual',
    obsidian_path   VARCHAR(512),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (expense_date),
    INDEX idx_category (category)
);
```

### 4.11 Obsidian 目录结构扩展

```
📂 Obsidian Vault/
├── 📂 人脉/                   ← 好友卡片 (已设计)
├── 📂 日记/
│   ├── 2025-01-15.md
│   └── …
├── 📂 财务/
│   ├── 应收应付.md
│   ├── 消费记录.md             ← 每月自动汇总
│   └── 预算.md                 ← 月度预算 vs 实际
├── 📂 学习/
│   ├── 学习计划.md
│   ├── 学习日志.md
│   └── 📂 笔记/
│       ├── React入门笔记.md
│       └── …
├── 📂 职业/
│   ├── 职业规划.md
│   ├── 简历.md
│   └── 面试记录.md
├── 📂 项目/
│   ├── 项目A.md
│   └── …
├── 📂 模板/
│   ├── 日记模板.md
│   ├── 周报模板.md
│   └── …
└── 📂 仪表盘/
    └── 每日快照.md              ← 每天自动生成
```

### 4.12 Obsidian 配置扩展

```yaml
winpeek:
  obsidian:
    enabled: true
    vault_path: "D:/Obsidian/我的知识库"
    # 目录映射
    contact_folder: "人脉"
    diary_folder: "日记"
    finance_folder: "财务"
    study_folder: "学习"
    notes_folder: "学习/笔记"
    career_folder: "职业"
    project_folder: "项目"
    template_folder: "模板"
    dashboard_folder: "仪表盘"
    # 同步策略
    auto_sync_interval: 3600
    sync_journal: true            # 日记双向同步
    sync_expense: true            # 消费记录同步
    sync_todo: true               # 待办双向同步
    sync_study: true              # 学习记录同步
    # AI 辅助
    generate_diary_draft: true    # 每日日记草稿
    generate_daily_snapshot: true # 每日快照
    generate_weekly_report: true  # 周报
    generate_monthly_report: true # 月报
    expense_budget_warn: true     # 预算预警
    todo_reminder: true           # 待办提醒
```

### 4.13 健康档案 + 运动 + 身体数据

> 主人到底过得怎样？不只是心理（心情日记），还有身体。
> 一份持续更新的健康档案，AI 比主人更清楚主人的身体数据。

**A区 — 健康档案 (Personal Health Profile)**

| 字段 | 类型 | 说明 |
|------|------|------|
| 出生日期 | DATE | |
| 性别 | VARCHAR(4) | |
| 身高 | DECIMAL(5,1) | cm |
| 体重 | DECIMAL(5,1) | kg (可记录历史变化) |
| 血型 | VARCHAR(4) | A/B/AB/O/未知 |
| 过敏史 | TEXT | 药物/食物/花粉/… |
| 既往病史 | TEXT | 手术/住院/慢性病 |
| 家族病史 | TEXT | 父母/祖辈 |
| 视力 | VARCHAR(32) | 左/右 |
| 静息心率 | INT | bpm |
| 血压 | VARCHAR(16) | 收缩压/舒张压 |
| 睡眠质量 | 1-5 评分 | 可每日记录 |

**B区 — 运动日志**

| 字段 | 类型 | 说明 |
|------|------|------|
| 日期 | DATE | |
| 运动类型 | enum | 跑步/游泳/健身/骑行/瑜伽/球类/散步/登山/拳击/其他 |
| 时长 | INT | 分钟 |
| 强度 | 1-5 评分 | 轻松/中等/剧烈/极限/受伤 |
| 距离 | DECIMAL(6,2) | km (如有) |
| 卡路里估算 | INT | kcal |
| 心率区间 | VARCHAR(32) | 有氧/无氧/燃脂 |
| 地点 | VARCHAR(128) | 健身房/公园/家里 |
| 心情 | VARCHAR(4) | |
| 备注 | TEXT | |

**C区 — 身体数据日志 (每日/每周打卡)**

| 字段 | 类型 | 说明 |
|------|------|------|
| 日期 | DATE | |
| 体重 | DECIMAL(5,1) | kg |
| 腰围 | DECIMAL(5,1) | cm |
| BMI | DECIMAL(4,1) | 自动计算 |
| 体脂率 | DECIMAL(4,1) | % (如有体脂秤) |
| 饮水量 | INT | ml (估计或实际) |
| 步数 | INT | |
| 坐姿时间 | INT | 小时 (静坐提醒) |
| 是否抽烟 | INT | 支数 |
| 是否喝酒 | VARCHAR(64) | 类型+量 |

**AI 关怀示例**：
- "主人，你这个月只运动了 2 天，体重涨了 1.5kg。"
- "你连续坐了 4 小时了，起来走走吧。"
- "BMI 已经 26.3 了，属于超重区间。需要制定减重计划吗？"

### 4.14 爱好清单

| 字段 | 类型 | 说明 |
|------|------|------|
| 爱好名称 | VARCHAR(64) | 钓鱼/摄影/烹饪/骑行/园艺/… |
| 类别 | enum | 运动/艺术/收藏/户外/手工/音乐/阅读/游戏/宠物/其他 |
| 投入程度 | 1-5 | 偶尔→狂热 |
| 每月预算 | DECIMAL(8,2) | |
| 月均耗时 | INT | 小时 |
| 关联好友 | TEXT | "和谁一起玩这个" → 自动关联到人脉 |
| 相关群组 | TEXT | 加入的群/社区 |
| 装备清单 | TEXT | 拥有的设备/工具 |
| 心愿清单 | TEXT | 想买的装备/想去的地方 |
| 最近活动 | DATE | 最近一次进行的时间 |

### 4.15 主人自画像 — 性格 / 投资 / 职业 / 人生阶段

> 这部分是主人自己对自己的认知 + AI 辅助完善。
> 目的不是给别人看，而是让助理"真正了解主人是谁"。

**A区 — 性格画像**

| 维度 | 类型 | 说明 |
|------|------|------|
| MBTI | VARCHAR(8) | INTJ / ENFP / … (可自测或 AI 从聊天风格推断) |
| 九型人格 | INT | 1-9 |
| DISC | VARCHAR(4) | D/I/S/C 主导型 |
| 沟通风格 | VARCHAR(16) | 直接/委婉/幽默/严肃/热情/冷感 |
| 决策偏好 | VARCHAR(16) | 理性分析/直觉判断/从众/独立 |
| 风险偏好 | enum | 保守(1) → 激进(5) |
| 社交能量 | enum | 外向(充电) / 内向(耗电) / 混合 |
| 压力反应 | VARCHAR(32) | 战斗/逃避/僵住/找人倾诉 |
| 核心价值观 | TEXT | 自由/家庭/成就/安全/健康/… |
| 座右铭 | VARCHAR(256) | |
| 害怕什么 | TEXT | AI 从日记/聊天中分析 |
| 追求什么 | TEXT | AI 从长期行为中推断 |

**B区 — 投资习惯**

| 字段 | 类型 | 说明 |
|------|------|------|
| 投资类型 | JSON array | 股票/基金/房产/加密货币/黄金/外汇/理财/收藏品/股权投资 |
| 投资年限 | INT | 年 |
| 投资金额 | VARCHAR(32) | 总投 + 月投额度 |
| 风险等级 | 1-5 | 保守 ↔ 激进 |
| 偏好行业 | VARCHAR(128) | 科技/消费/医疗/新能源/… |
| 证券账户 | JSON array | 券商APP/账号(脱敏) |
| 投资目标 | TEXT | 养老/买房/财务自由/子女教育/… |
| 止盈止损 | TEXT | 个人纪律描述 |
| 投资笔记 | → Obsidian | 关联的投资日记/研究笔记路径 |
| 持仓汇总 | JSON | 定期快照 |
| 年度收益 | DECIMAL(6,2) | % |

**C区 — 职业画像**

| 字段 | 类型 | 说明 |
|------|------|------|
| 当前状态 | enum | 在职/自由职业/创业/待业/退休/学生 |
| 行业 | VARCHAR(64) | |
| 职级 | VARCHAR(64) | 初级/中级/高级/总监/VP/CXO/创始人 |
| 公司规模 | VARCHAR(32) | 初创/中小/大厂/国企/外企 |
| 入职日期 | DATE | |
| 税前年薪 | VARCHAR(32) | 区间或具体数 |
| 社保公积金 | VARCHAR(64) | 缴纳城市+基数 |
| 上一份工作 | VARCHAR(128) | 公司+职位+时间 |
| 跳槽频率 | VARCHAR(32) | 平均几年一跳 |
| 职业优势 | TEXT | 最擅长的技能/优势 |
| 职业短板 | TEXT | 需要提升的能力 |
| 职业目标 | 1年/3年/5年 | 三个时间维度的目标 |
| 理想工作 | TEXT | 钱多/事少/离家近/有意义/… |
| 是否考虑副业 | TINYINT | 0/1 |
| 副业方向 | TEXT | |
| 简历 | → Obsidian | 简历文件路径 |

**D区 — 人生阶段**

| 字段 | 类型 | 说明 |
|------|------|------|
| 年龄 | INT | |
| 婚姻状况 | enum | 单身/恋爱/已婚/离异/丧偶 |
| 子女 | INT | 数量 + 年龄 |
| 居住城市 | VARCHAR(64) | |
| 居住状态 | enum | 自有/租房/父母同住/公司宿舍 |
| 车辆 | VARCHAR(64) | 品牌+型号 |
| 宠物 | TEXT | 猫/狗/鱼/鹦鹉/无 |
| 生活阶段 | enum | 学生期/奋斗期/稳定期/育儿期/空巢期/退休期 |

**AI 洞察示例**：
- "根据你的聊天风格，MBTI 倾向于 INTJ。建议的沟通策略：直接、有逻辑、少废话。"
- "你的投资组合过于集中在科技股(75%)，建议分散风险。"
- "以你目前的储蓄率，按年化 6% 计算，10 年后可达到 300 万目标。"
- "你的 5 年职业目标是 CTO，但核心短板是管理经验。建议: 先争取带 2-3 人小团队的机会。"

```sql
-- 主人自画像
CREATE TABLE personal_self_profile (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    -- 性格
    mbti            VARCHAR(8),
    enneagram       TINYINT,
    disc_style      VARCHAR(4),
    communication   VARCHAR(16),
    decision_style  VARCHAR(16),
    risk_tolerance  TINYINT DEFAULT 3,           -- 1-5
    social_energy   VARCHAR(8),
    stress_response VARCHAR(32),
    core_values     TEXT,
    motto           VARCHAR(256),
    fears           TEXT,
    aspirations     TEXT,
    -- 投资
    invest_types     TEXT,                        -- JSON array
    invest_years     INT,
    invest_amount    VARCHAR(32),
    risk_level       TINYINT DEFAULT 3,           -- 1-5
    prefer_industry  VARCHAR(128),
    broker_accounts  TEXT,                        -- JSON (脱敏)
    invest_goals     TEXT,
    stop_loss_rules  TEXT,
    annual_return    DECIMAL(6,2),
    -- 职业
    work_status      VARCHAR(16),                 -- employed/freelance/startup/unemployed/retired/student
    industry         VARCHAR(64),                 -- internet/finance/manufacture/medical/edu/realestate/retail/logistics/energy/agri/media/gov/military/consult/legal/npo/other
    industry_detail  VARCHAR(64),                 -- 细分子行业
    company_name     VARCHAR(128),                -- (加密存储)
    company_scale    VARCHAR(16),                 -- 1-10/11-50/51-200/201-1000/1001-10000/10000+
    company_type     VARCHAR(16),                 -- startup/private/foreign/soe/central_soe/public/gov/ngo/freelance
    department       VARCHAR(64),                 -- rd/product/design/ops/marketing/sales/hr/finance/legal/admin/management
    job_title        VARCHAR(128),
    position_level   VARCHAR(32),                 -- intern/junior/mid/senior/lead/manager/director/vp/cxo/founder
    reports_to       VARCHAR(128),                -- 汇报给谁(职位)
    subordinate_count INT DEFAULT 0,              -- 管理多少人
    join_date        DATE,
    contract_end     DATE,                        -- 合同到期日
    probation_end    DATE,                        -- 转正日期
    salary_range     VARCHAR(32),
    salary_exact     VARCHAR(32),                 -- (加密) 精确月薪
    bonus            VARCHAR(64),                 -- 年终/项目奖/期权/股票
    social_insurance VARCHAR(128),
    work_location    VARCHAR(128),                -- 城市+通勤
    remote_ratio     VARCHAR(16),                 -- full_remote/hybrid/onsite
    work_hours       VARCHAR(16),                 -- 955/965/996/007/flex
    prev_job         TEXT,                        -- JSON: [{company,title,from,to}]
    job_hop_freq     VARCHAR(32),
    career_strengths TEXT,
    career_gaps      TEXT,
    skill_matrix     TEXT,                        -- JSON: [{skill,level(1-5),years,last_used}]
    cert_list        TEXT,                        -- JSON: [{name,date,expire}]
    career_goal_1y   TEXT,
    career_goal_3y   TEXT,
    career_goal_5y   TEXT,
    ideal_job        TEXT,
    has_side_hustle  TINYINT DEFAULT 0,
    side_hustle_dir  TEXT,
    resume_path      VARCHAR(512),
    -- 人生
    age              INT,
    marital_status   VARCHAR(8),
    children_count   INT DEFAULT 0,
    children_age     VARCHAR(64),
    city             VARCHAR(64),
    housing_status   VARCHAR(16),
    vehicle          VARCHAR(64),
    pets             VARCHAR(128),
    life_stage       VARCHAR(16),                 -- student/striving/stable/parenting/empty_nest/retired
    -- 一句话自我介绍
    self_summary     TEXT,                        -- AI 生成 + 人工校准
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 4.16 语言/技能档案

**语言能力**：

| 字段 | 类型 | 说明 |
|------|------|------|
| 母语 | VARCHAR(32) | |
| 第二语言 | VARCHAR(32) | 英语/日语/韩语/… |
| 水平等级 | VARCHAR(16) | 母语/A1/A2/B1/B2/C1/C2 |
| 考试证书 | VARCHAR(128) | CET-6 / IELTS 7.5 / N2 / TOPIK 5 |
| 考试日期 | DATE | |
| 目前状态 | enum | 维持/学习中/退化中/已荒废 |
| 学习计划 | → `personal_study_plan` 关联 | |

**专业技能**：

| 字段 | 类型 | 说明 |
|------|------|------|
| 技能名 | VARCHAR(64) | Python / 焊接 / 摄影后期 / 厨师 / … |
| 类别 | enum | 编程/设计/语言/手工艺/烹饪/驾驶/乐器/其他 |
| 熟练度 | 1-5 | 入门→专家 |
| 使用年限 | DECIMAL(3,1) | 年 |
| 是否认证 | VARCHAR(128) | 证书名称 |
| 目前在用 | TINYINT | 当前职业/日常是否使用 |
| 愿意教人 | TINYINT | 是否愿意教别人（技能交换） |

### 4.17 阅读 / 观影 / 娱乐追踪

> 每个人关注的东西不同，读书、看剧、看电影、
> 听音乐、打游戏、看综艺——记录下来，AI 帮你发现偏好。

**A区 — 阅读记录**

| 字段 | 类型 | 说明 |
|------|------|------|
| 书名 | VARCHAR(256) | |
| 作者 | VARCHAR(128) | |
| 类型 | enum | 小说/历史/哲学/科技/商业/心理/传记/科幻/武侠/言情/推理/诗歌/其他 |
| 介质 | enum | 纸质/电子(Kindle/微信读书)/有声 |
| 状态 | enum | 想读/在读/已读/弃读 |
| 开始日期 | DATE | |
| 读完日期 | DATE | |
| 评分 | 1-5 | |
| 笔记 | TEXT | 关联 Obsidian 读书笔记 |
| 一句话总结 | VARCHAR(512) | AI 可从笔记中提取 |
| 是否推荐 | TINYINT | 0/1 |

**B区 — 电影记录**

| 字段 | 类型 | 说明 |
|------|------|------|
| 片名 | VARCHAR(256) | |
| 年份 | INT | |
| 导演 | VARCHAR(128) | |
| 类型 | enum | 动作/喜剧/科幻/恐怖/悬疑/爱情/动画/纪录片/战争/犯罪/奇幻/文艺/其他 |
| 来源 | enum | 院线/Netflix/B站/网盘/电视/其他 |
| 观看日期 | DATE | |
| 评分 | 1-5 | |
| 和谁看 | TEXT | 关联好友 (自动记录社交) |
| 一句话影评 | VARCHAR(512) | |
| 是否二刷 | TINYINT | |

**C区 — 电视剧/网剧记录**

| 字段 | 类型 | 说明 |
|------|------|------|
| 剧名 | VARCHAR(256) | |
| 类型 | enum | 国产剧/美剧/韩剧/日剧/英剧/泰剧/动漫/网剧/短剧 |
| 题材 | enum | 古装/都市/悬疑/谍战/青春/家庭/职场/宫斗/武侠/仙侠/历史/科幻/甜宠/刑侦/战争/其他 |
| 季数 | VARCHAR(16) | "第1季" / "全3季" / "追到第5季" |
| 状态 | enum | 想看/在追/弃剧/已追完 |
| 平台 | VARCHAR(64) | 腾讯/爱奇艺/优酷/B站/Netflix/… |
| 开始追 | DATE | |
| 追完/弃剧 | DATE | |
| 评分 | 1-5 | |
| 一句话评价 | VARCHAR(512) | |
| 和谁讨论 | TEXT | 关联好友 |

**D区 — 综艺/音乐/游戏**

| 子类 | 字段 |
|------|------|
| 综艺 | 节目名、类型(真人秀/脱口秀/选秀/竞技/访谈/旅行)、平台、评分 |
| 音乐 | 歌手/乐队名、风格(流行/摇滚/民谣/电子/古典/说唱/爵士/…)、常听APP、歌单链接 |
| 游戏 | 游戏名、平台(Steam/手游/PS5/Switch)、类型(RPG/FPS/MOBA/策略/休闲/…)、时长、段位、是否弃坑 |

**E区 — 数据库**

```sql
CREATE TABLE personal_reading (
    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
    title       VARCHAR(256) NOT NULL,
    author      VARCHAR(128),
    genre       VARCHAR(16),
    medium      VARCHAR(16),        -- paper/ebook/audio
    status      VARCHAR(8) DEFAULT 'want',  -- want/reading/done/dropped
    start_date  DATE,
    end_date    DATE,
    rating      TINYINT,            -- 1-5
    summary     VARCHAR(512),
    recommend   TINYINT DEFAULT 0,
    obsidian_note VARCHAR(512),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE personal_movie (
    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
    title       VARCHAR(256) NOT NULL,
    movie_year  INT,
    director    VARCHAR(128),
    genre       VARCHAR(16),        -- action/comedy/scifi/horror/suspense/romance/animation/docu/war/crime/fantasy/arthouse/other
    source      VARCHAR(16),        -- cinema/netflix/bilibili/disk/tv/other
    watch_date  DATE,
    rating      TINYINT,
    watched_with TEXT,              -- JSON friend IDs
    review      VARCHAR(512),
    rewatch     TINYINT DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE personal_tv_show (
    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
    title       VARCHAR(256) NOT NULL,
    show_type   VARCHAR(16),        -- cn/us/kr/jp/uk/th/anime/short/other
    genre       VARCHAR(16),        -- costume/urban/suspense/spy/youth/family/workplace/palace/martial/fantasy/history/scifi/romance/crime/war/other
    season      VARCHAR(16),
    status      VARCHAR(8) DEFAULT 'want',  -- want/watching/dropped/done
    platform    VARCHAR(64),
    start_date  DATE,
    end_date    DATE,
    rating      TINYINT,
    review      VARCHAR(512),
    discussed_with TEXT,            -- JSON friend IDs
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.18 信仰 / 精神世界

| 字段 | 类型 | 说明 |
|------|------|------|
| 宗教信仰 | enum | 无/佛教/基督教(新教)/天主教/伊斯兰教/道教/印度教/民间信仰/其他 |
| 具体派别 | VARCHAR(64) | 净土宗/禅宗/长老会/浸信会/逊尼派/什叶派/… |
| 信仰程度 | 1-5 | 名义→虔诚 |
| 是否素食 | TINYINT | 0=否 1=全素 2=部分素食 |
| 是否持戒 | TEXT | 不杀生/不饮酒/守斋/… |
| 修行习惯 | TEXT | 念经/祷告/打坐/冥想/礼拜/放生/… |
| 频率 | VARCHAR(32) | 每日/每周/每月/节日/偶尔 |
| 宗教场所 | VARCHAR(128) | 常去的寺庙/教堂/清真寺 |
| 精神导师 | VARCHAR(64) | 法师/牧师/阿訇/… |
| 相关社群 | TEXT | 共修群/聚会点/团契 |
| 可分享 | TINYINT | 是否愿意跟人聊信仰 |
| 备注 | TEXT | |

```sql
CREATE TABLE personal_belief (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    religion        VARCHAR(32),
    denomination    VARCHAR(64),
    devotion        TINYINT DEFAULT 1,
    vegetarian      TINYINT DEFAULT 0,
    precepts        TEXT,
    practice        TEXT,
    frequency       VARCHAR(32),
    place           VARCHAR(128),
    mentor          VARCHAR(64),
    community       TEXT,
    shareable       TINYINT DEFAULT 1,
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 4.19 购物偏好 / 品牌消费档案

> 从"买了什么品牌"到"为什么买"，了解主人的消费决策模式。
> 数据来源：微信支付截图 OCR、手动录入、AI 从聊天提取。

**A区 — 偏好品牌库**

| 字段 | 类型 | 说明 |
|------|------|------|
| 品类 | enum | 服装/鞋/包/护肤/彩妆/数码/家电/汽车/食品/饮料/烟酒/母婴/运动/家居/办公/宠物/手表/饰品/其他 |
| 品牌 | VARCHAR(64) | |
| 档次 | enum | 平价/中端/高端/奢侈 |
| 常用渠道 | VARCHAR(128) | 淘宝/京东/拼多多/抖音/线下专柜/代购/海淘/闲鱼 |
| 月均消费 | DECIMAL(8,2) | 该品类月均花多少 |
| 忠诚度 | 1-5 | 是否首选该品牌 |
| 复购频率 | VARCHAR(32) | 每周/每月/每季/每年/偶尔 |
| 首次购买 | DATE | |
| 最近购买 | DATE | |
| 备注 | VARCHAR(256) | "因为是某某推荐的" / "性价比高" |

**B区 — 消费决策倾向**

| 维度 | 选项 |
|------|------|
| 价格敏感度 | 极度在意 → 毫不在意 (1-5) |
| 品牌敏感度 | 无所谓 → 非品牌不买 (1-5) |
| 决策速度 | 冲动→理性 (1-5) |
| 信息来源 | 朋友推荐/小红书/抖音/B站测评/知乎/广告/店员推荐/自行研究 |
| 偏好折扣 | 从不/偶尔/经常/只买打折的 |
| 退货习惯 | 从不/偶尔/经常 |

**C区 — 大型消费记录**

| 字段 | 类型 | 说明 |
|------|------|------|
| 品类 | VARCHAR(32) | 房产/汽车/家电/珠宝/教育/医疗/装修/旅游/其他 |
| 名称 | VARCHAR(128) | |
| 品牌 | VARCHAR(64) | |
| 金额 | DECIMAL(12,2) | |
| 日期 | DATE | |
| 购买动机 | TEXT | "为什么买这个" |
| 满意程度 | 1-5 | AI 可从后续聊天分析 |
| 是否后悔 | TINYINT | 0=不后悔 1=有点 2=很后悔 |
| 下次换什么 | VARCHAR(128) | 替代选择 |

**AI 洞察示例**：
- "主人偏好苹果生态，近 3 年购买了 iPhone/MacBook/AirPods/Apple Watch。"
- "你的护肤品月均消费 ¥680，集中在 SK-II 和 Lancôme。"
- "汽车消费偏向日系品牌，注重省油和保值率。"

```sql
CREATE TABLE personal_brand_pref (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    category        VARCHAR(16) NOT NULL,       -- clothing/shoes/bags/skincare/makeup/digital/appliance/car/food/beverage/smoke_drink/baby/sport/home/office/pet/watch/jewelry/other
    brand           VARCHAR(64) NOT NULL,
    tier            VARCHAR(8),                 -- budget/mid/high/luxury
    channel         VARCHAR(128),
    monthly_spend   DECIMAL(8,2),
    loyalty         TINYINT DEFAULT 3,          -- 1-5
    repurchase_freq VARCHAR(16),                -- weekly/monthly/quarterly/yearly/occasional
    first_buy       DATE,
    last_buy        DATE,
    notes           VARCHAR(256),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE personal_big_purchase (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    category        VARCHAR(16) NOT NULL,       -- house/car/appliance/jewelry/edu/medical/renovation/travel/other
    name            VARCHAR(128),
    brand           VARCHAR(64),
    amount          DECIMAL(12,2),
    purchase_date   DATE,
    motivation      TEXT,
    satisfaction    TINYINT,                    -- 1-5
    regret          TINYINT DEFAULT 0,          -- 0/1/2
    next_choice     VARCHAR(128),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE personal_consume_style (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    price_sensitivity   TINYINT DEFAULT 3,      -- 1-5
    brand_sensitivity   TINYINT DEFAULT 3,
    decision_speed      TINYINT DEFAULT 3,      -- 1=impulse 5=rational
    info_source         VARCHAR(128),            -- friend_share/xiaohongshu/douyin/bilibili/zhihu/ads/clerk/self_research
    discount_habit      VARCHAR(16),             -- never/rare/often/only_discount
    return_habit        VARCHAR(16),             -- never/rare/often
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.20 数据库（补充 — SQL）

```sql
CREATE TABLE personal_health_profile (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    birth_date      DATE,
    gender          VARCHAR(4),
    height_cm       DECIMAL(5,1),
    blood_type      VARCHAR(4),
    allergies       TEXT,
    medical_history  TEXT,
    family_history  TEXT,
    vision_left     VARCHAR(16),
    vision_right    VARCHAR(16),
    resting_hr      INT,
    blood_pressure  VARCHAR(16),
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 运动日志
CREATE TABLE personal_exercise_log (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    log_date        DATE NOT NULL,
    exercise_type   VARCHAR(16) NOT NULL,      -- run/swim/gym/cycle/yoga/ball/walk/hike/boxing/other
    duration_min    INT NOT NULL,
    intensity       TINYINT DEFAULT 3,          -- 1-5
    distance_km     DECIMAL(6,2),
    calories_kcal   INT,
    heart_rate_zone VARCHAR(32),
    location        VARCHAR(128),
    mood            VARCHAR(4),
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (log_date)
);

-- 身体数据日志
CREATE TABLE personal_body_log (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    log_date        DATE NOT NULL,
    weight_kg       DECIMAL(5,1),
    waist_cm        DECIMAL(5,1),
    bmi             DECIMAL(4,1),
    body_fat_pct    DECIMAL(4,1),
    water_ml        INT,
    steps           INT,
    sit_hours       DECIMAL(4,1),
    cigarettes      INT DEFAULT 0,
    alcohol         VARCHAR(64),
    sleep_quality   TINYINT,                    -- 1-5
    sleep_hours     DECIMAL(3,1),
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (log_date)
);

-- 爱好清单
CREATE TABLE personal_hobby (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(64) NOT NULL,
    category        VARCHAR(16),                -- sport/art/collect/outdoor/craft/music/read/game/pet/other
    devotion        TINYINT DEFAULT 1,          -- 1-5
    monthly_budget  DECIMAL(8,2),
    monthly_hours   INT,
    related_friends TEXT,                        -- JSON
    related_groups  TEXT,
    equipment       TEXT,
    wishlist        TEXT,
    last_activity   DATE,
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 语言能力
CREATE TABLE personal_language (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    language        VARCHAR(32) NOT NULL,
    is_native       TINYINT DEFAULT 0,
    level           VARCHAR(8),                  -- A1/A2/B1/B2/C1/C2
    certificate     VARCHAR(128),
    cert_date       DATE,
    status          VARCHAR(16) DEFAULT 'maintain',  -- maintain/learning/declining/lost
    study_plan_id   INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 专业技能
CREATE TABLE personal_skill (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(64) NOT NULL,
    category        VARCHAR(16),                -- coding/design/language/craft/cook/drive/instrument/other
    proficiency     TINYINT DEFAULT 1,          -- 1-5
    years_used      DECIMAL(3,1),
    certification   VARCHAR(128),
    currently_used  TINYINT DEFAULT 0,
    willing_to_teach TINYINT DEFAULT 0,
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.21 扩展模板

| 新增模板 | 用途 |
|---------|------|
| 健康档案模板 | 一次性填写个人健康基线 |
| 运动日志模板 | 每日运动打卡记录 |
| 身体数据模板 | 每周/每月身体指标跟踪 |
| 爱好清单模板 | 系统整理个人爱好 |
| 语言学习模板 | 语言学习路线图 (听说读写) |

### 4.22 Obsidian 目录补充

```
📂 Obsidian Vault/
├── 📂 健康/
│   ├── 健康档案.md
│   ├── 运动日志.md          ← 每周汇总
│   └── 身体数据.md          ← BMI/体重趋势图
├── 📂 爱好/
│   ├── 爱好清单.md
│   └── 📂 摄影/
│       ├── 装备清单.md
│       └── 拍摄计划.md
├── 📂 技能/
│   ├── 语言能力.md
│   └── 技能树.md
```

### 4.23 配置扩展

```yaml
winpeek:
  personal_assistant:
    health:
      enabled: true
      sedentary_remind: true       # 久坐提醒 (每60分钟)
      sedentary_threshold: 60       # 分钟
      weekly_exercise_goal: 150     # 每周运动目标(分钟)
      weight_alert: true            # 体重异常提醒
    hobby:
      enabled: true
      inactivity_remind: true       # 爱好荒废提醒
    skill:
      enabled: true
  obsidian:
    health_folder: "健康"
    hobby_folder: "爱好"
    skill_folder: "技能"
```

---

## 五、数据库总览

| 模块 | 数据来源表 |
|------|-----------|
| **好友基础档案** | `wechat_friend` + `wechat_friend_relation` + `wechat_relation_tree` |
| **好友关键事件** | `wechat_friend_event` |
| **好友经济往来** | `wechat_friend_finance` |
| **结构化交互事件** | `friend_event` (每次聊天/交易的事件化+评分) |
| **关系评分日志** | `friend_score_log` (8维度分数时间序列) |
| **机会识别** | `friend_opportunity` |
| **群管理** | `wechat_group` + `wechat_group_member` |
| **聊天记录** | `wechat_chat` |
| **主人自画像** | `personal_self_profile` |
| **日记/记事** | `personal_journal` |
| **待办** | `personal_todo` |
| **项目/任务** | `personal_project` + `personal_project_item` |
| **消费记账** | `personal_expense` |
| **拒绝记录** | `personal_refusal` (借钱/帮忙/投资/… 的拒绝+事后反思) |
| **重大决策** | `personal_decision` (职业/财务/人生选择 + 事后复盘) |
| **未完成清单** | `personal_unfinished` (承诺/借款/学习/关系/未了结) |
| **价值观审计** | `personal_values_audit` (仁/义/礼/智/信 + 言行一致性) |
| **消费品牌偏好** | `personal_brand_pref` + `personal_big_purchase` + `personal_consume_style` |
| **学习** | `personal_study_plan` + `personal_study_log` |
| **健康+运动** | `personal_health_profile` + `personal_exercise_log` + `personal_body_log` |
| **爱好** | `personal_hobby` |
| **语言+技能** | `personal_language` + `personal_skill` |
| **阅读/电影/剧** | `personal_reading` + `personal_movie` + `personal_tv_show` |
| **信仰** | `personal_belief` |
| **自扩展枚举** | `sys_enum_definition` |
| **朋友圈** | `wechat_moment` + `wechat_moment_comment` |
| **操作日志** | `wechat_operation_log` |
| **个人文件导出** | `~/.hermes/people/<uid>/portrait.json` + `.md` |
| **Obsidian 导出** | 以上所有表 → `.md` 文件到 vault |

> 注: `wechat_friend_event` 是好友的人生的关键事件（初识/纪念日/人生变迁），
> `friend_event` 是结构化交互事件（每次聊天/交易，含关系分增减和机会标记）。
> 两者是不同粒度的表，互不冲突。

### `wechat_friend` 新增字段

```sql
ALTER TABLE wechat_friend ADD COLUMN ai_profile TEXT;          -- JSON: 职业/学历/爱好/性格/宗教/购买意向/…
ALTER TABLE wechat_friend ADD COLUMN portrait_summary TEXT;    -- 一句话人物速写
ALTER TABLE wechat_friend ADD COLUMN sales_stage VARCHAR(32) DEFAULT 'lead';
ALTER TABLE wechat_friend ADD COLUMN customer_level CHAR(1) DEFAULT 'D';
ALTER TABLE wechat_friend ADD COLUMN heat_score INT DEFAULT 0;
ALTER TABLE wechat_friend ADD COLUMN is_blacklisted INT DEFAULT 0;
ALTER TABLE wechat_friend ADD COLUMN remark TEXT;
ALTER TABLE wechat_friend ADD COLUMN obsidian_path TEXT;       -- Obsidian 卡片路径
```

### 新增独立表

```sql
-- (已在上文展开)
CREATE TABLE wechat_relation_tree (…);   -- 13 棵分类树种子数据
CREATE TABLE wechat_friend_relation (…); -- 好友↔关系标记(多对多)
CREATE TABLE wechat_friend_event (…);    -- 关键事件时间线
CREATE TABLE wechat_friend_finance (…);  -- 经济往来账簿
```

---

## 六、实现路径

| 阶段 | 内容 | 依赖 |
|------|------|------|
| P0 | 全部新表建表 + 种子数据 + Obsidian 配置骨架 | 现有 DB |
| P1 | 好友列表 + 群列表 + 按关系分类筛选 + 搜索 | P0 |
| P2 | 好友详情页: 基本档案 + 人头画像 + 经济往来 + 聊天记录 | P1 |
| P3 | `friend_event` 事件分析管线 (聊天→事件) + 基础评分 | P0 + LLM |
| P4 | 8 维度评分计算 + 衰减机制 + `friend_score_log` | P3 |
| P5 | AI 机会识别 + `friend_opportunity` | P3 |
| P6 | 个人助理模块: 日记 + 待办 + 消费记账 | P0 |
| P7 | 个人助理模块: 项目 + 学习 + 健康档案 + 爱好 + 技能 | P6 |
| P8 | 主人自画像 (`personal_self_profile`) 全字段 CRUD | P7 |
| P9 | AI 画像: 自动归类 + 一句话描述 + 事件提取 + 经济提取 | 需 LLM |
| P10 | 双存储: MySQL → 个人文件增量同步 | P4 |
| P11 | Obsidian 双向全量同步 (卡片/日记/财务) | P2-P10 |
| P12 | 360° 仪表盘: 每日快照 + 关系健康度 + 消费统计 + AI 关怀 | P4-P11 |
| P13 | 自扩展枚举系统 (`sys_enum_definition`) | P0 |
| P14 | 群发消息 + 消息模板 | P2 |

**可并行**: P3+P6 可同时开工; P7+P8 可同时开工; P13 随时可做。

---

## 七、前端组件树

```
AutomationView
 └─ PlatformTabBar (微信/抖音/快手/视频号/小红书/B站)
     └─ WechatCRM
         ├─ LeftNav
         │   ├─ SearchBar
         │   ├─ DashboardNav("仪表盘")
         │   ├─ SectionHeader("我的好友")  ← 可折叠, FilterChips
         │   │   └─ ContactListItem[]
         │   ├─ SectionHeader("我的群聊")
         │   │   └─ GroupListItem[]
         │   ├─ Divider
         │   ├─ NavItem("📝 日记")
         │   ├─ NavItem("✅ 待办")
         │   ├─ NavItem("📋 项目")
         │   ├─ NavItem("💰 消费")
         │   ├─ NavItem("📚 学习")
         │   ├─ NavItem("🚀 职业规划")
         │   ├─ Divider
         │   ├─ NavItem("📨 群发消息")
         │   ├─ NavItem("📋 消息模板")
         │   ├─ NavItem("📊 360° 统计")
         │   ├─ Divider
         │   └─ AccountSection
         │       ├─ 微信头像+昵称
         │       ├─ "切换微信"
         │       ├─ "退出微信"
         │       └─ "同步数据"
         └─ RightPanel (MasterDetail)
             ├─ DashboardView              ← 今日快照
             ├─ ContactDetailView          ← 5 个 Tab (档案/画像/聊天/销售)
             ├─ GroupDetailView
             ├─ JournalView                ← 日记列表 (日历视图) + Markdown 编辑器
             ├─ TodoView                   ← Kanban 看板 (todo/doing/done)
             ├─ ProjectView                ← 项目列表 + 详情 + 子任务
             ├─ ExpenseView                ← 消费记录 + 快速记账 + 月度统计图表
             ├─ StudyView                  ← 学习计划 + 学习日志 + 知识地图
             ├─ CareerView                 ← 职业规划路线图
             ├─ BulkMessageView
             ├─ TemplateView               ← 模板市场/选择器
             ├─ Statistics360View          ← 360° 仪表盘
             └─ AccountView
```

---

## 八、API 需求

| 端点 | 方法 | 用途 |
|------|------|------|
| `mcp_winpeek_contacts_list` | GET | 好友列表（分页+排序+搜索） |
| `mcp_winpeek_contacts_get` | GET | 单个好友详情 |
| `mcp_winpeek_contacts_update` | PUT | 更新备注/tags/分类 |
| `mcp_winpeek_groups_list` | GET | 群列表 |
| `mcp_winpeek_chat_history` | GET | 按好友/群的聊天记录 |
| `mcp_winpeek_ai_profile` | POST | 触发 AI 画像分析 |
| `mcp_winpeek_sync` | POST | 触发同步 |
| `mcp_winpeek_send_message` | POST | 发送消息 |
| `mcp_winpeek_bulk_send` | POST | 群发 |
| `mcp_winpeek_stats` | GET | 统计数据 |
| **日记** | | |
| `mcp_journal_list` | GET | 日记列表 (按日期范围/类型过滤) |
| `mcp_journal_create` | POST | 新建日记 |
| `mcp_journal_update` | PUT | 编辑日记 |
| `mcp_journal_delete` | DELETE | 删除日记 |
| **待办** | | |
| `mcp_todo_list` | GET | 待办列表 (按状态/优先级过滤) |
| `mcp_todo_create` | POST | 创建待办 |
| `mcp_todo_update` | PUT | 更新状态/内容 |
| `mcp_todo_delete` | DELETE | 删除 |
| **项目** | | |
| `mcp_project_list` | GET | 项目列表 |
| `mcp_project_get` | GET | 项目详情 (含子任务) |
| `mcp_project_create` | POST | 创建项目 |
| `mcp_project_update` | PUT | 更新项目/子任务 |
| **消费** | | |
| `mcp_expense_list` | GET | 消费列表 (按月/分类/…过滤) |
| `mcp_expense_create` | POST | 快速记账 |
| `mcp_expense_stats` | GET | 消费统计 (按月的分类饼图/趋势) |
| `mcp_expense_budget` | GET/PUT | 预算设置/查看 |
| **学习** | | |
| `mcp_study_plan_list` | GET | 学习计划列表 |
| `mcp_study_log_create` | POST | 记录学习时间 |
| **仪表盘** | | |
| `mcp_dashboard_today` | GET | 今日快照 (消费/待办/学习/互动汇总) |
| `mcp_dashboard_weekly` | GET | 周报数据 |

这些 API 在 `plugins/winpeek_rpa/mcp_server.py` 和 `tools/winpeek_tools.py` 中注册。
