# 主人-好友画像系统 · 架构设计

> 每次聊天都是一次"关系事件"。不是简单地记录消息，而是从每条消息中提取：
> 这段对话拉近还是疏远了两人的关系？有没有商业机会？有没有成长机会？
> 谁是付出方？谁是收获方？
>
> 系统日积月累，最终帮主人打造完美人生。

---

## 一、核心理念：每一次互动都是一次事件

```
                     ┌─ 事件发生 ─┐
                     │  聊天/见面/转账/帮忙/冲突/…
                     └──┬──┬──┬──┘
                        │  │  │
          ┌─────────────┘  │  └─────────────┐
          ▼                ▼                ▼
    关系影响评估      机会识别          价值量化
    (拉近/疏远)    (商业/成长/付出)    (情感/金钱/时间)
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    更新双存储层
               MySQL ──── 个人文件(JSON/MD)
              (横向比较)    (纵向导出/便携)
```

---

## 二、双存储架构

```
UID 是一切的锚点。

┌──────────────────────────────────────────────────────────┐
│              MySQL (横向比较 · 多维度分析)                 │
│                                                          │
│  wechat_friend        ← 基础档案                          │
│  wechat_chat          ← 原始消息                          │
│  friend_event         ← 结构化事件                         │
│  friend_score_log     ← 关系分日志                         │
│  friend_opportunity   ← 机会识别                           │
│  wechat_friend_finance← 经济往来                           │
│  personal_refusal     ← 拒绝记录                            │
│  personal_decision    ← 重大决策                            │
│  personal_unfinished  ← 未完成清单                           │
│  personal_values_audit← 价值观审计                           │
│  sys_enum_definition  ← 自扩展枚举                           │
│  personal_*           ← 主人自身数据                         │
│                                                          │
│  用途: 所有人一起看、排名、统计、趋势、对比                   │
└──────────────────────────────────────────────────────────┘

                         ↕ 增量同步

┌──────────────────────────────────────────────────────────┐
│          个人文件 (纵向导出 · 便携 · 离线可用)              │
│                                                          │
│  ~/.hermes/people/<uid>/                                 │
│  ├─ portrait.json     ← 完整画像 (单文件快照)              │
│  ├─ events.jsonl      ← 事件流 (追加写入)                  │
│  ├─ scores.jsonl      ← 关系分时间序列                     │
│  ├─ finance.jsonl     ← 经济往来账                         │
│  ├─ chat_summary.json ← 聊天摘要 (AI 压缩)                 │
│  └─ portrait.md       ← Obsidian 可读卡片                  │
│                                                          │
│  用途: 单个人导出、分享、备份、Obsidian 打开                │
└──────────────────────────────────────────────────────────┘
```

### 同步策略

| 方向 | 时机 | 内容 |
|------|------|------|
| MySQL → 文件 | 每次画像更新 | 覆盖 portrait.json + portrait.md |
| MySQL → 文件 | 每次新事件 | 追加 events.jsonl + scores.jsonl |
| MySQL → 文件 | 每次交易 | 追加 finance.jsonl |
| 文件 → MySQL | 导入外部数据 | 批量 INSERT (去重) |
| 文件 → Obsidian | 文件更新时 | copy portrait.md → vault/人脉/ |

### 增量机制

```
每次变动 = 一个 delta event:

{
  "ts": "2025-01-15T14:32:00",
  "uid": "wxid_abc123",
  "type": "score_change",       // score_change | event_add | finance_add | profile_update
  "payload": {
    "dimension": "closeness",
    "old_value": 72,
    "new_value": 75,
    "delta": +3,
    "trigger": "chat_message",  // 触发源
    "trigger_id": "msg_xxx"     // 可追溯到原消息
  }
}
```

---

## 三、关系分模型 (Friend Score)

### 3.1 评分维度

每个好友在 8 个维度上被持续评分（0-100）：

```
       情感维度                    理性维度
   ┌─────────────┐          ┌─────────────┐
   │ 亲密度       │          │ 商业价值     │
   │ closeness    │          │ biz_value    │
   ├─────────────┤          ├─────────────┤
   │ 信任度       │          │ 成长价值     │
   │ trust        │          │ growth_value │
   ├─────────────┤          ├─────────────┤
   │ 尊重度       │          │ 经济信用     │
   │ respect      │          │ credit_score │
   ├─────────────┤          ├─────────────┤
   │ 好感度       │          │ 互惠度       │
   │ affection    │          │ reciprocity  │
   └─────────────┘          └─────────────┘
```

### 3.2 每个维度的含义

| 维度 | 含义 | 影响因素 |
|------|------|---------|
| **亲密度** | 有多亲近 | 聊天频率、内容深度、见面次数、称呼变化 |
| **信任度** | 有多信任 | 秘密分享、金钱来往、托付事项、守约记录 |
| **尊重度** | 有多尊重 | 语气、用词、是否倾听、是否轻视 |
| **好感度** | 喜不喜欢 | emoji使用、正向词汇、主动联系频率 |
| **商业价值** | 生意潜力 | 行业/职位/决策权/采购意向/合作历史 |
| **成长价值** | 能学到什么 | 对方专长、经验分享、指导机会 |
| **经济信用** | 借还记录 | 借款是否按时还、代付是否结清 |
| **互惠度** | 有来有往 | 一方付出 vs 双方付出、谁更主动 |

### 3.3 关系总分 (综合指标)

```
relation_total = closeness × 0.25
               + trust     × 0.20
               + respect   × 0.10
               + affection × 0.10
               + biz_value × 0.15
               + growth    × 0.10
               + credit    × 0.10

趋势箭头: ↗ 上升(近30天+5分) | → 持平 | ↘ 下降(近30天-5分)
```

### 3.4 趋势分析 — 时间维度

```
"你跟许国勇最近 30 天的亲密度从 72 降到了 68 (-4)，
 因为你们聊天频率从每天变成了每周。
 触发点: 2025-01-03 你说'最近太忙了'之后他没再主动找你。"
```

---

## 四、事件驱动模型

### 4.1 事件是万物的起点

每一条微信消息、每一次转账、每一次见面、每一次冲突——都是一个**结构化事件**。

```sql
CREATE TABLE friend_event (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    uid             VARCHAR(128) NOT NULL,       -- 好友 UID
    event_type      VARCHAR(32) NOT NULL,        -- 事件类型
    event_subtype   VARCHAR(32),                 -- 子类型
    event_ts        DATETIME NOT NULL,           -- 发生时间
    source          VARCHAR(16) DEFAULT 'chat',  -- chat/manual/ocr/system/finance
    source_id       VARCHAR(128),                -- 来源ID (消息ID/交易ID)
    
    -- 内容
    title           VARCHAR(256),
    summary         TEXT,                        -- AI 生成的摘要 (≤200字)
    raw_text        TEXT,                        -- 原始文本 (如有)
    
    -- 关系影响评估 (AI 分析)
    closeness_delta TINYINT DEFAULT 0,           -- 亲密度变化 (-10 ~ +10)
    trust_delta     TINYINT DEFAULT 0,
    respect_delta   TINYINT DEFAULT 0,
    affection_delta TINYINT DEFAULT 0,
    biz_delta       TINYINT DEFAULT 0,
    growth_delta    TINYINT DEFAULT 0,
    credit_delta    TINYINT DEFAULT 0,
    reciprocity_delta TINYINT DEFAULT 0,
    
    -- 机会标记
    is_biz_opportunity   TINYINT DEFAULT 0,     -- 商业机会？
    is_growth_opportunity TINYINT DEFAULT 0,    -- 成长机会？
    is_giving_opportunity TINYINT DEFAULT 0,    -- 付出机会？(帮TA)
    is_receiving_opportunity TINYINT DEFAULT 0,  -- 收获机会？(TA帮你)
    opportunity_detail   TEXT,                   -- AI 对机会的详细分析
    
    -- 情感分析
    my_emotion       VARCHAR(16),               -- 我的情绪: positive/neutral/negative
    their_emotion    VARCHAR(16),               -- TA的情绪
    emotion_intensity TINYINT DEFAULT 0,         -- 情绪强度 1-5
    
    -- 元数据
    analyzed_by      VARCHAR(16) DEFAULT 'ai',  -- ai/manual
    confidence       DECIMAL(3,2) DEFAULT 0.00, -- AI 置信度
    tags             TEXT,                       -- JSON array
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_uid_ts (uid, event_ts),
    INDEX idx_type (event_type),
    INDEX idx_opportunity (is_biz_opportunity, is_growth_opportunity)
);
```

### 4.2 事件类型体系

```
事件大类:
├── social (社交)
│   ├── first_contact        ← 首次认识
│   ├── chat_session         ← 一次聊天会话
│   ├── meet_in_person       ← 线下见面
│   ├── voice_call           ← 语音通话
│   ├── video_call           ← 视频通话
│   ├── group_interaction    ← 群内互动
│   ├── introduced_to_other  ← 介绍给别人
│   ├── conflict             ← 冲突/争执
│   ├── apology              ← 道歉/和解
│   ├── compliment           ← 夸奖/赞美
│   └── complain             ← 抱怨/吐槽
│
├── finance (经济)
│   ├── loan_out             ← 我借出
│   ├── loan_in              ← 我借入
│   ├── loan_repaid          ← 还款
│   ├── gift_given           ← 送礼(我→TA)
│   ├── gift_received        ← 收礼(TA→我)
│   ├── treat_invited        ← 请客(我→TA)
│   ├── treat_received       ← 被请(TA→我)
│   ├── payment_proxy        ← 代付
│   └── red_envelope         ← 红包
│
├── career (职业)
│   ├── job_referral         ← 内推/介绍工作
│   ├── biz_collaboration    ← 商业合作
│   ├── deal_closed          ← 成交
│   ├── client_referral      ← 介绍客户
│   ├── mentor_advice        ← 指导建议(TA→我)
│   └── mentored_them        ← 我指导TA
│
├── knowledge (知识)
│   ├── learned_from         ← 从TA学到
│   ├── taught_to            ← 教给TA
│   ├── resource_shared      ← 分享资源/文章
│   └── book_recommended     ← 推荐书/课程
│
├── life (生活)
│   ├── helped_them          ← 帮了TA
│   ├── helped_by_them       ← TA帮我
│   ├── celebrated_together  ← 一起庆祝
│   ├── condolence           ← 慰问/安慰
│   └── traveled_together    ← 一起旅行
│
└── risk (风险)
    ├── trust_broken         ← 失信
    ├── lied_to              ← 被欺骗
    ├── ghosted              ← 被冷落
    └── boundary_violated    ← 边界被侵犯
```

---

## 五、关系分计算引擎

### 5.1 每次事件 → 分数更新

```
[事件] chat_session: 聊了30分钟, 讨论买房, 情绪愉快
       │
       ▼ AI 分析
       closeness_delta = +2   (深度话题)
       trust_delta     = +1   (分享了个人财务状况)
       biz_delta       = +3   (TA说有个楼盘资源)
       is_biz_opportunity = 1 (可能合作看房)
       
       → 写入 friend_event
       → 更新 friend_score_log
       → 触发 delta 同步到个人文件
```

### 5.2 分数日志表

```sql
CREATE TABLE friend_score_log (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    uid         VARCHAR(128) NOT NULL,
    event_id    BIGINT,                        -- → friend_event.id
    score_date  DATE NOT NULL,
    
    closeness   TINYINT DEFAULT 50,
    trust       TINYINT DEFAULT 50,
    respect     TINYINT DEFAULT 50,
    affection   TINYINT DEFAULT 50,
    biz_value   TINYINT DEFAULT 30,
    growth_value TINYINT DEFAULT 30,
    credit_score TINYINT DEFAULT 70,
    reciprocity TINYINT DEFAULT 50,
    relation_total TINYINT DEFAULT 50,
    
    trend_30d   VARCHAR(4),                    -- up/down/flat
    
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_uid_date (uid, score_date)
);
```

### 5.3 衰减机制

```
分数不是只涨不跌的。如果没有互动，关系自然冷淡：

衰减规则 (每30天无互动):
  closeness  -3
  affection  -2
  biz_value  -1   (商业价值不太会因疏远而降)
  trust      -1   (信任比较稳定)
  
最低衰减到基线值 (初始分)，不会降到负数。
```

---

## 六、机会识别引擎

每次事件都可能隐藏着机会。AI 负责把它找出来。

### 6.1 机会类型

| 类型 | 识别信号 | 示例 |
|------|---------|------|
| **商业机会** | 提到采购/招标/换供应商/预算/"找谁做" | "我们公司最近在找CRM" |
| **成长机会** | 提到培训/考证/跳槽/涨薪/新技能 | "我在学K8s，你也应该学" |
| **付出机会** | TA遇到困难/求助/生病/搬家 | "最近手头紧" → 主动问要不要帮忙 |
| **收获机会** | TA主动提出帮忙/介绍资源/分享渠道 | "我认识一个人可以做这个" |
| **情感机会** | 生日/升职/结婚/生娃 → 该送礼祝福了 | "下周我女儿满月" |

### 6.2 机会表

```sql
CREATE TABLE friend_opportunity (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    uid         VARCHAR(128) NOT NULL,
    event_id    BIGINT,                        -- 触发事件
    opp_type    VARCHAR(16) NOT NULL,          -- biz/growth/giving/receiving/emotional
    title       VARCHAR(256),
    detail      TEXT,                          -- AI 分析详情
    urgency     TINYINT DEFAULT 1,             -- 1-5 (多紧急)
    value_est   VARCHAR(64),                   -- 预估价值
    action_suggested TEXT,                     -- AI 建议的行动
    status      VARCHAR(16) DEFAULT 'open',    -- open/taken/missed/dismissed
    taken_at    DATETIME,
    result      TEXT,                          -- 行动结果
    remind_at   DATETIME,                      -- 提醒时间
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_uid_status (uid, status),
    INDEX idx_remind (remind_at)
);
```

---

## 七、双存储实现细节

### 7.1 UID 体系

```
每个人的 UID 是全局唯一标识，贯穿 MySQL 和个人文件:

UID = wxid_<微信号>          ← 微信好友
    | uid_<自增>              ← 非微信联系人  
    | dt_<钉钉ID>             ← 钉钉好友
    | tg_<Telegram ID>        ← Telegram好友

所有表、所有文件都用这个 UID 做 key。
```

### 7.2 个人文件格式

**portrait.json** — 完整画像快照：

```json
{
  "uid": "wxid_abc123",
  "version": 173,
  "updated_at": "2025-01-15T14:32:00Z",
  "basic": {
    "nickname": "许国勇",
    "alias": "老许",
    "remark": "前同事-华为",
    "wxid": "wxid_abc123",
    "avatar_url": "http://...",
    "phone": "138xxxx1234",
    "region": "广东 深圳",
    "signature": "但行好事莫问前程",
    "source": "通过群聊添加",
    "source_type": "group_chat"
  },
  "portrait": {
    "summary": "跟老许是2015年在坂田华为认识的，合作3年。现在腾讯T9。半年见一次。",
    "personality": {
      "mbti": "ISTJ",
      "communication": "直接",
      "decision": "理性分析"
    }
  },
  "relations": [
    {"tree": "同事", "sub": "平级同事", "level": 1, "time": "2015-2018", "org": "华为"},
    {"tree": "同学", "sub": "本科", "level": 1, "org": "华中科技大学"}
  ],
  "scores": {
    "closeness": 72, "trust": 85, "respect": 80,
    "affection": 68, "biz_value": 55, "growth_value": 70,
    "credit_score": 95, "reciprocity": 60,
    "relation_total": 72, "trend_30d": "up"
  },
  "finance": {
    "total_lent": 5000, "total_borrowed": 20000,
    "outstanding_in": 0, "outstanding_out": 0,
    "net_position": -15000
  },
  "events_count": 247,
  "opportunities_open": 1,
  "last_contact": "2025-01-15T10:30:00Z",
  "next_reminder": "2025-01-20T09:00:00Z"
}
```

**events.jsonl** — 事件流 (追加):

```jsonl
{"ts":"2025-01-15T10:30","type":"chat_session","closeness_delta":2,"summary":"讨论了买房，TA说有个楼盘资源"}
{"ts":"2025-01-10T15:00","type":"red_envelope","amount":88,"summary":"TA发来拜年红包"}
```

**scores.jsonl** — 分数时间序列:

```jsonl
{"date":"2025-01-15","closeness":72,"trust":85,"relation_total":72}
{"date":"2025-01-01","closeness":70,"trust":84,"relation_total":71}
{"date":"2024-12-15","closeness":73,"trust":84,"relation_total":73}
```

### 7.3 增量同步

```
每次 MySQL 写入 → 触发同步检查:

if (portrait字段变更):
    → 覆盖 portrait.json
    → 写 portrait.md (obsidian)

if (有新事件):
    → 追加 events.jsonl

if (分数变化 >= 2分):
    → 追加 scores.jsonl

if (有新的经济记录):
    → 追加 finance.jsonl
```

同步通过文件系统的 `mtime` 做去重——比上次更新晚的文件才覆盖。

---

## 八、横向分析 (MySQL 的强项)

### 8.1 全量对比查询

```sql
-- 谁是我最亲近的 10 个人？
SELECT uid, closeness, relation_total FROM friend_score_log
WHERE score_date = CURDATE() ORDER BY closeness DESC LIMIT 10;

-- 谁的商业价值最高但亲密度低？(该维护的关系)
SELECT uid, biz_value, closeness, (biz_value - closeness) AS gap
FROM friend_score_log WHERE score_date = CURDATE()
HAVING gap > 20 ORDER BY gap DESC;

-- 谁的经济信用最差？(该催款的)
SELECT uid, credit_score FROM friend_score_log
WHERE score_date = CURDATE() AND credit_score < 50 ORDER BY credit_score;

-- 过去 30 天亲密度下降最快的人？(关系在流失)
SELECT a.uid, a.closeness - b.closeness AS drop
FROM friend_score_log a JOIN friend_score_log b
WHERE a.score_date = CURDATE() AND b.score_date = DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY drop;

-- 谁给了我最多商业机会？
SELECT uid, COUNT(*) AS opp_count FROM friend_opportunity
WHERE opp_type = 'biz' AND status = 'taken'
GROUP BY uid ORDER BY opp_count DESC;

-- 我对谁的付出多于收获？(单向关系)
SELECT uid, reciprocity FROM friend_score_log
WHERE score_date = CURDATE() AND reciprocity < 40 ORDER BY reciprocity;
```

### 8.2 仪表盘

```
┌────────────────────────────────────────────────────┐
│              主人关系健康度总览                       │
│                                                    │
│  总人脉: 3,847  活跃(30天): 847  沉睡: 2,100        │
│                                                    │
│  关系分分布:          机会分布:       情感分布:       │
│  80-100  ████ 12%    商业  23 ↑      积极 847       │
│  60-80   ████████ 35% 成长  15 ↑      中性 1,200     │
│  40-60   ██████ 28%   付出  8  ↑      消极 34        │
│  20-40   ███ 18%      收获  3  →                     │
│  0-20    ██ 7%                                       │
│                                                    │
│  ⚠ 关注: 许国勇(亲密度↓) 李四(信用↓)                  │
│  🔥 机会: 张三(商业) 王五(成长)                        │
│  💰 催款: 赵六(¥5000 逾期3月)                         │
│  🎂 生日: 钱七(明天)                                  │
└────────────────────────────────────────────────────┘
```

---

## 九、数据流转全景

```
    微信消息 ──→ AI 分析 ──→ 结构化事件 ──→ 分数计算 ──→ MySQL
                                        │               │
                                        │  机会识别 ────┤
                                        │               │
                                        └──→ 个人文件 ──→ Obsidian
                                               │
                                          JSON + MD
                                         (单文件可导出)
                                         
    主人手动输入 ──→ friend_event (source=manual)
    
    转账/红包 ──→ wechat_friend_finance + friend_event (source=finance)
    
    OCR 截图 ──→ 消费记录 / 经济事件
    
    Obsidian 日记 ──→ 反向提取 ──→ friend_event
```

---

## 十、表结构总览

```
MySQL 数据库 (共享 · 横向分析):

  [核心关系]
  wechat_friend              好友基础档案
  wechat_friend_relation     关系分类标记 (多对多)
  
  [事件驱动]
  friend_event               结构化事件 (核心表)
  friend_score_log           关系分时间序列
  friend_opportunity         机会识别
  
  [经济]
  wechat_friend_finance             经济往来账簿
  
  [聊天]
  wechat_chat                原始消息
  
  [主人]
  personal_self_profile      主人自画像
  personal_journal           日记
  personal_todo              待办
  personal_project           项目
  personal_expense           消费
  personal_study_plan        学习
  personal_health_profile    健康
  personal_exercise_log      运动
  personal_body_log          身体数据
  personal_hobby             爱好
  personal_language          语言
  personal_skill             技能
  personal_reading           阅读
  personal_movie             电影
  personal_tv_show           电视剧
  personal_belief            信仰
  personal_brand_pref        品牌偏好
  personal_big_purchase      大额消费
  personal_consume_style     消费风格

  [自我认知]
  personal_refusal           拒绝记录 (边界/原则)
  personal_decision          重大决策 (事后复盘)
  personal_unfinished        未完成清单
  personal_values_audit      价值观一致性审计

  [系统]
  sys_enum_definition        自扩展枚举


个人文件 (UID · 纵向导出):

  ~/.hermes/people/<uid>/
  ├─ portrait.json          画像快照
  ├─ portrait.md            Obsidian 卡片
  ├─ events.jsonl           事件流
  ├─ scores.jsonl           分数序列
  └─ finance.jsonl          经济账
```

---

## 十一、可实现优先级

| Phase | 内容 |
|------|------|
| **P0** | `friend_event` 表 + `friend_score_log` 表 + 基础评分写入 |
| **P1** | 每个 chat_session 自动触发事件分析 |
| **P2** | 8 维度评分计算 + 衰减机制 |
| **P3** | AI 机会识别 + `friend_opportunity` |
| **P4** | 双存储: MySQL → 个人文件自动同步 |
| **P5** | 横向分析仪表盘 (SQL 统计查询) |
| **P6** | Obsidian 卡片自动更新 |
| **P7** | 自扩展枚举系统 |
| **P8** | 从日记/消费反向提取事件 |
