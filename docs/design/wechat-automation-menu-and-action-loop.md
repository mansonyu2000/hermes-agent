# 微信自动化软件 — 菜单/功能体系 + 画像驱动行动闭环

> **本文档三合一：**
> 1. 微信软件的完整菜单/子菜单 — 描述所有操作功能
> 2. 自动化行动闭环 — 画像→分析→决策→派遣→执行→反馈
> 3. 接受 Hermes 任务派遣 — 从"看清楚"到"做起来"

---

## 一、软件菜单体系

### 1.1 主菜单树

```
微信自动化 (WeChat Automation)
│
├── 📊 仪表盘                     → 全局总览 + AI 行动建议
│   ├── 今日快照                    总览卡片 + 今日推荐行动
│   ├── 关系健康度                  关系网络健康状态
│   └── 行动清单                    AI 生成的待执行行动列表
│
├── 👤 好友管理                   → 联系人的全生命周期
│   ├── 好友列表                   Master-Detail 列表
│   │   ├── 全部好友               按关系分级 (A/B/C/D)
│   │   ├── 按关系分类             13棵分类树筛选
│   │   ├── 按标签筛选             自定义标签
│   │   ├── 按热度排序             聊天频率/互动深度
│   │   ├── 按评分排序             8维度加权总分
│   │   └── 黑名单                 已拉黑/不联系
│   │
│   ├── 好友详情 (点击左侧好友)      → 5个Tab
│   │   ├── 📋 基本档案             个人信息/联系方式/标签/来源
│   │   ├── 🧠 画像·关系            8维雷达图/13树分类/AI总结/关键事件
│   │   ├── 💬 聊天记录             100%消息还原/搜索/统计
│   │   ├── 💼 销售管理             客户评级/拜访记录/目标/阶段/文档
│   │   └── 📄 备注·文档            富文本备注/附件/AI摘要
│   │
│   ├── 添加好友                   按微信号/手机号搜索添加
│   ├── 好友信息整理               → 批量编辑模式
│   │   ├── 批量设标签
│   │   ├── 批量改级别
│   │   ├── 批量加黑名单
│   │   └── 批量写备注
│   └── AI 画像分析                触发全量/增量 AI 画像重算
│
├── 👥 群管理                     → 群聊的运营管理
│   ├── 群列表                    按活跃度/成员数排序
│   ├── 群详情                    群名/群主/成员/公告/活跃度
│   ├── 成员导出                  群成员列表导出 CSⅤ
│   └── 群消息统计                群活跃时段/热门话题
│
├── 📨 群发消息                   → 营销消息批量发送
│   ├── 新建群发
│   │   ├── 选择收件人             按标签/级别/手动
│   │   ├── 编辑消息               富文本编辑器
│   │   ├── AI 生成话术           输入意图→多候选话术
│   │   ├── AI 情感设置            亲切/正式/幽默/关心
│   │   ├── 使用模板               从模板库选择
│   │   └── 预览·发送              变量替换预览→执行发送
│   ├── 发送历史                  已完成的群发任务+统计
│   └── 发送队列                  正在执行中的任务+进度
│
├── 📋 消息模板                   → 可复用的消息库
│   ├── 模板列表                  分类浏览 (初次/跟进/节日/催款/感谢/自定义)
│   ├── 新建模板                  标题/正文/分类/变量
│   ├── AI 优化模板               对现有模板润色/改进
│   └── 使用统计                  每个模板的使用次数/效果
│
├── 📈 数据统计                   → 多维度数据分析
│   ├── 好友总览                  数量/来源分布/分级分布
│   ├── 消息趋势                  按天/周/月的消息量折线图
│   ├── Top 排行榜                最热联系人/最活跃群/互动排名
│   ├── 销售漏斗                  客户阶段分布 (意向→成交)
│   ├── 关系网络图                好友群组关系可视化
│   └── 时间分布                  活跃时段热力图
│
├── ⚙️ 微信管理                   → 账号与连接
│   ├── 我的微信                  头像/昵称/微信号/在线状态
│   ├── 切换微信                  扫码切换账号
│   ├── 退出微信                  退出PC微信
│   └── 微信进程状态              Weixin.exe 运行状态
│
├── 🔄 数据同步                   → 数据采集与同步
│   ├── 好友同步                  全量/增量采集通讯录
│   ├── 聊天同步                  指定好友/全量采集聊天记录
│   ├── 群同步                    群列表+成员采集
│   ├── 同步日志                  每次同步的详细日志
│   └── 同步设置                  自动同步间隔/范围
│
└── 👤 个人助理 (主人画像)          → 360°自我管理
    ├── 日记                      日历视图 + Markdown 编辑器
    ├── 待办                      Kanban (todo→doing→done)
    ├── 项目                      项目+里程碑+子任务
    ├── 消费记账                  快速记账+月度统计
    ├── 学习                      学习计划+学习日志
    ├── 职业规划                  职业路线图
    ├── 健康                      健康档案+运动日志+身体数据
    ├── 爱好                      爱好清单+装备+心愿单
    ├── 阅读·影视·音乐            精神消费记录
    ├── 信仰                      宗教信仰档案
    ├── 投资                      投资习惯+持仓
    ├── 技能                      技能树+语言能力
    └── 360° 仪表盘               今日快照+AI关怀+消费预警
```

### 1.2 快捷操作入口 (右键菜单 / 上下文菜单)

```
好友列表项右键:
  ├── 📝 写备注
  ├── 🏷️ 编辑标签
  ├── ⭐/☆ 置顶/取消置顶
  ├── 🚫 加黑名单
  ├── ✉️ 发消息
  ├── 📊 查看画像
  ├── 📈 查看统计
  ├── 🔄 更新聊天记录
  └── 🗑️ 删除好友

群列表项右键:
  ├── 📝 修群备注
  ├── 🔇 免打扰
  ├── 💾 保存到通讯录
  ├── 📊 群统计
  └── 👥 导出成员

消息列表中右键:
  ├── 💚 标记为 AI 生成
  ├── 📌 添加到关键事件
  ├── 🏷️ 提取为标签建议
  └── 📋 复制
```

---

## 二、画像系统 — 一切自动化的根基

### 2.1 两类画像

```
┌─────────────────────────────────────────────────────────────┐
│                    画像体系                                  │
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │   好友画像            │    │   主人自画像          │         │
│  │   (每人一份)          │    │   (唯一一份)          │         │
│  │                     │    │                     │         │
│  │ • 基础档案           │    │ • 性格 (MBTI/九型/DISC)│        │
│  │ • 8维关系分          │    │ • 投资习惯             │         │
│  │ • 13树关系分类        │    │ • 职业画像             │         │
│  │ • AI人物速写          │    │ • 消费偏好             │         │
│  │ • 关键事件时间线       │    │ • 技能·语言            │         │
│  │ • 经济往来账          │    │ • 爱好·信仰            │         │
│  │ • 客户阶段·级别       │    │ • 人生阶段             │         │
│  │ • 沟通风格·偏好       │    │ • 价值观               │         │
│  │ • 关键词·标签         │    │ • 未完成清单           │         │
│  └─────────────────────┘    └─────────────────────┘         │
│                                                             │
│  两者交叉 → 生成个性化互动策略                                  │
│  "对 INTJ 型领导应该直接点"                                   │
│  "对喜欢茶文化的客户投其所好"                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 画像构建方式 — AI 自动 + 人工校准

```
数据源                         画像产出
───────                       ────────
wechat_chat (原始消息)   →    关键词提取 (jieba + LLM)
                            →    话题分类
                            →    情感倾向分析
                            →    沟通风格识别
                            →    兴趣爱好抽取
                            →    职业/学历推测
                            →    消费习惯分析
                            →    生活状态推断
                            →    关键事件提取
                            →    关系演变追踪

wechat_friend (基础信息)  →    地区/性别/来源

wechat_moment (朋友圈)    →    生活方式/价值观

wechat_friend_finance     →    经济信用评估

friend_event (结构化事件)  →    8维评分计算
                            →    机会识别
                            →    关系趋势分析

主人手动输入              →    校准/补充 AI 盲区
```

### 2.3 画像更新的触发时机

| 触发条件 | 动作 |
|---------|------|
| 聊天记录增量同步完成 | 对该好友运行增量画像分析 |
| 手动点击"AI 画像分析" | 全量重新分析该好友 |
| 每天凌晨 2:00 (cron) | 对最近 7 天有过互动的好友运行批量增量分析 |
| 聊天中出现关键信号词 | 实时标记: "买房"/"升职"/"结婚"/"生病"/"借钱"/"换工作" |
| 8维分数任一维度变化 >10 分 | 触发警报 → 生成行动建议 |

---

## 三、自动化行动闭环 — 从"看清楚"到"做起来"

### 3.1 闭环全景图

```
                         ┌──────────────────────┐
                         │   1. 数据采集          │
                         │   UIA 采集聊天/通讯录   │
                         │   (已有: collect.py)   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   2. 画像构建          │
                         │   AI分析聊天→画像更新   │
                         │   (已有: analyze.py)   │
                         │   8维评分+13树分类     │
                         └──────────┬───────────┘
                                    │
                                    ▼
         ┌──────────────────────────────────────────────┐
         │         3. 洞察引擎 (Actionable Insights)      │
         │                                              │
         │  输入: 所有人的画像+评分+事件+主人画像           │
         │  输出: 结构化行动建议列表                        │
         │                                              │
         │  分析维度:                                     │
         │  ├─ 关系健康度扫描 (谁在疏远？谁在靠近？)         │
         │  ├─ 不对称关系检测 (谁付出多？谁拖累我？)         │
         │  ├─ 商业机会识别 (谁有采购意向？谁刚升职？)       │
         │  ├─ 信用风险评估 (谁该还钱了？)                  │
         │  ├─ 情感温度预警 (哪些重要关系在降温？)           │
         │  ├─ 承诺追踪 (我答应了谁什么事还没做？)           │
         │  ├─ 周期性提醒 (谁的生日/纪念日/跟进日到了？)     │
         │  └─ 自我成长建议 (根据主人画像推荐行动)          │
         └──────────────────┬───────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────────┐
         │        4. 行动计划生成 (Action Planner)        │
         │                                              │
         │  每条洞察 → 一条或多条可执行行动                  │
         │                                              │
         │  行动类型:                                     │
         │  ├─ SEND_MESSAGE    → 主动发消息              │
         │  ├─ FOLLOW_UP       → 跟进上次聊的话题          │
         │  ├─ REMIND_PAYMENT  → 催收/还款提醒            │
         │  ├─ CONGRATULATE    → 祝贺 (升职/生日/…)      │
         │  ├─ RE_CONNECT      → 重新联系 (太久没聊)      │
         │  ├─ CHECK_IN        → 关心问候 (对方有困难)     │
         │  ├─ SHARE_CONTENT   → 分享有价值的内容          │
         │  ├─ INVITE_MEETING  → 邀约见面                 │
         │  ├─ APOLOGIZE       → 道歉 (我失约了)          │
         │  ├─ THANK           → 感谢 (对方帮过我)         │
         │  ├─ SET_BOUNDARY    → 设边界 (单向消耗型关系)   │
         │  └─ SELF_IMPROVE    → 主人自身成长行动          │
         └──────────────────┬───────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────────┐
         │      5. Hermes 任务派遣 (Task Dispatch)        │
         │                                              │
         │  每条行动计划 → 一个 Hermes task/reminder      │
         │                                              │
         │  派遣方式:                                     │
         │  ├─ winpeek_wechat_send  → 直接执行发消息       │
         │  ├─ cron job             → 定时提醒             │
         │  ├─ todo create          → 加入待办列表          │
         │  ├─ say <uid> "..."      → 通知其他 Agent       │
         │  └─ dashboard alert      → 仪表盘推送            │
         └──────────────────┬───────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────────┐
         │        6. 执行与反馈 (Execution & Feedback)    │
         │                                              │
         │  执行: UIA 操作微信 / 生成话术 / 发送消息        │
         │  反馈: 对方是否回复？回复内容→新一轮画像更新        │
         │  效果: 行动是否达到预期？→ 调整策略               │
         │                                              │
         │  闭环: 每次互动 → 新的事件 → 画像更新             │
         │        → 新的洞察 → 新的行动 → ...               │
         └──────────────────────────────────────────────┘
```

### 3.2 核心引擎: 洞察 → 行动 转换规则

这是最核心的部分。每一类洞察都有一条**可执行的转换规则**：

```
规则引擎: insight → action

┌─────────────────────────────────────────────────────────────────────┐
│ 洞察类型               触发条件                     行动              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 【关系维护类】                                                        │
│                                                                     │
│ 重要关系失联           亲密度>70 且 最后互动>30天    RE_CONNECT       │
│                        → "你跟XX已经30天没联系了"                      │
│                                                                     │
│ 重要关系降温           亲密度 30天下降>10分           CHECK_IN         │
│                        → "XX跟你的亲密度下降了12分"                    │
│                                                                     │
│ 新朋友跟进             添加好友后>7天未互动           FOLLOW_UP        │
│                        → "你加了XX一周了还没聊过天"                    │
│                                                                     │
│ 单向付出检测           互惠度<35 且 亲密度>60         SET_BOUNDARY    │
│                        → "你一直主动找XX, 对方几乎不找你"              │
│                                                                     │
│ 【商业机会类】                                                        │
│                                                                     │
│ 客户意向信号           聊天中出现 "报价"/"多少钱"     SEND_MESSAGE     │
│                        → "XX在询价, 该发报价单了"                      │
│                                                                     │
│ 客户决策权变更         好友画像职级变化(升职)         CONGRATULATE     │
│                        → "XX刚升职, 恭喜+趁热打铁"                    │
│                                                                     │
│ 客户沉睡唤醒           A级客户 60天无业务互动          SHARE_CONTENT   │
│                        → "给XX分享一条行业资讯"                        │
│                                                                     │
│ 竞品信号               聊天出现竞品名称               FOLLOW_UP        │
│                        → "XX提到了竞品, 该深入了解下"                   │
│                                                                     │
│ 【信用风险类】                                                        │
│                                                                     │
│ 借款逾期               约定还款日已过+未结清          REMIND_PAYMENT   │
│                        → "XX借的5000块逾期了"                          │
│                                                                     │
│ 借款将到期             约定还款日<7天                 REMIND_PAYMENT   │
│                        → "XX的借款3天后到期"                           │
│                                                                     │
│ 信用评分下降           经济信用 30天下降>10分          CHECK_IN         │
│                        → "注意: XX的信用分降了"                        │
│                                                                     │
│ 【情感人文类】                                                        │
│                                                                     │
│ 生日提醒               好友生日<3天                   CONGRATULATE     │
│                        → "明天是XX的生日"                              │
│                                                                     │
│ 对方有喜事             聊天中识别到 "结婚了"/"生娃了"  CONGRATULATE     │
│                        → "XX刚生了孩子, 祝贺一下"                      │
│                                                                     │
│ 对方有困难             聊天中识别到 "生病"/"失业"     CHECK_IN         │
│                        → "XX最近生病了, 关心一下"                      │
│                                                                     │
│ 感恩回报提醒           帮过我的人 90天未回报           THANK           │
│                        → "上次XX帮了你, 你还没表示"                    │
│                                                                     │
│ 【主人自身成长类】                                                    │
│                                                                     │
│ 承诺未兑现             聊天中 "我帮你..." 后未闭环     SELF_IMPROVE    │
│                        → "你答应帮XX做XX, 还没完成"                    │
│                                                                     │
│ 学习中断               学习计划连续N天未打卡           SELF_IMPROVE    │
│                        → "你3天没学TypeScript了"                       │
│                                                                     │
│ 消费超预算             当月某类消费>预算的120%         SELF_IMPROVE    │
│                        → "本月烟酒消费已超预算"                        │
│                                                                     │
│ 健康提醒               连续坐姿>4小时                  SELF_IMPROVE    │
│                        → "起来活动一下吧"                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 行动优先级算法

不是所有行动都同等重要。优先级由**紧急度 × 重要度**决定：

```
优先级评分:

P = urgency_score × 0.4 + importance_score × 0.6

urgency_score (紧急度):
  逾期/即将到期                  → 1.0
  最后沟通>30天+重要关系          → 0.8
  生日/纪念日<3天                → 0.7
  商业信号 (询价/招标)            → 0.9
  一般周期性提醒                  → 0.4
  主人自身成长                    → 0.3

importance_score (重要度):
  直系血亲                        → 1.0
  A级客户                         → 0.9
  B级客户 / 领导                   → 0.7
  铁哥们 / 闺蜜                    → 0.6
  C级客户 / 普通好友               → 0.4
  D级 / 一面之交                   → 0.2
  黑名单 / 陌生人                  → 0.0

最终行动按 P 排序:
  P ≥ 0.8  → 🔴 今天必须做
  P ≥ 0.5  → 🟡 本周内做
  P ≥ 0.3  → ⚪ 有时间做
  P < 0.3  → 📋 存档备查
```

### 3.4 Hermes 任务派遣协议

当洞察引擎产出一条行动建议后，通过标准化协议派遣给 Hermes 执行：

```python
# 行动派遣数据包
action_packet = {
    "id": "act_20250115_001",
    "created_at": "2025-01-15T08:00:00",
    "priority": 0.85,                    # 优先级评分
    "level": "today",                    # today / week / leisure / archive
    "type": "SEND_MESSAGE",              # 行动类型枚举
    "target": {
        "wxid": "wxid_abc123",
        "nickname": "许国勇",
        "relation_level": 1,            # 1=红(亲近) 2=默认 3=灰(疏远)
        "customer_level": "A"
    },
    "insight": {
        "category": "重要关系失联",
        "description": "你跟许国勇已经35天没有互动了",
        "evidence": "最后消息时间: 2024-12-10, 亲密度从72降至65(-7分)",
        "urgency_reason": "超过30天阈值 + A级客户 + 关系在降温"
    },
    "action": {
        "instruction": "主动问候许国勇，询问最近情况",
        "suggested_script": "老许，好久没联系了，最近怎么样？上次你说的那个项目有进展吗？",
        "tone": "亲切自然",
        "template_id": "reconnect_001",
        "fallback_if_no_reply": "3天后如未回复，用更轻松的语气再发一次"
    },
    "dispatch": {
        "method": "winpeek_wechat_send",  # Hermes 工具名
        "params": {
            "wxid": "wxid_abc123",
            "message": "老许，好久没联系了，最近怎么样？上次你说的那个项目有进展吗？"
        },
        "schedule": None,                  # 立即执行; 或 "2025-01-16T09:00:00"
        "require_confirm": False,          # A级关系自动执行, 不需要确认
        "confirm_threshold": 0.7           # P>=0.7 的行动自动执行
    },
    "feedback": {
        "expected_outcome": "对方回复并继续对话",
        "success_criteria": "7天内对方有回复",
        "on_success": "更新亲密度+3, 记录成功互动",
        "on_failure": "3天后生成新的RE_CONNECT行动, 降低优先级"
    }
}
```

### 3.5 任务派遣的三条路径

```
洞察 → 行动 → 派遣

路径 1: 即时执行 (P ≥ 0.7)
  ┌──────┐     ┌──────────────┐     ┌─────────────────┐
  │ 洞察  │ →  │ AI 生成话术   │ →  │ winpeek_wechat_  │ → 微信发送
  │      │     │ 用户确认(可选) │     │ send 工具        │
  └──────┘     └──────────────┘     └─────────────────┘
  适用: 重要客户跟进、催款提醒、生日祝福

路径 2: 定时派遣
  ┌──────┐     ┌──────────────┐     ┌─────────────────┐
  │ 洞察  │ →  │ 创建 cron job │ →  │ 到期自动执行      │ → 微信发送
  │      │     │ 设定执行时间   │     │                 │
  └──────┘     └──────────────┘     └─────────────────┘
  适用: 周期性问候、定期维护、学习提醒

路径 3: 待办列队 (P < 0.7)
  ┌──────┐     ┌──────────────┐     ┌─────────────────┐
  │ 洞察  │ →  │ 加入 personal │ →  │ 用户在仪表盘看到   │
  │      │     │ _todo 表      │     │ 手动决定何时执行   │
  └──────┘     └──────────────┘     └─────────────────┘
  适用: 非紧急关系维护、自我成长行动

路径 4: 人工确认 (敏感操作)
  ┌──────┐     ┌──────────────┐     ┌─────────────────┐
  │ 洞察  │ →  │ 推送通知给主人  │ →  │ 主人审批         │ → 执行/放弃
  │      │     │ "是否允许?"    │     │                 │
  └──────┘     └──────────────┘     └─────────────────┘
  适用: 涉及金钱的提醒、敏感关系处理、大规模群发
```

### 3.6 执行反馈 → 画像更新 → 新一轮循环

```
执行一个行动之后:

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  Step 1: 执行                                                │
│  Hermes 通过 UIA 发送消息 "老许，最近怎么样？"                   │
│                                                              │
│  Step 2: 观察                                                │
│  等待对方回复 (下次聊天采集时获取)                               │
│                                                              │
│  Step 3: 分析                                                │
│  对方回复了 → AI 分析回复内容 → 提取情感/话题/意图               │
│  对方没回复 → 记录为 "跟进未成功"                               │
│                                                              │
│  Step 4: 更新                                                │
│  有回复:                                                      │
│    亲密度 +3 (因为互动了一次)                                   │
│    创建 friend_event: type=reconnect_result, outcome=positive │
│    更新 last_contact 时间                                      │
│  没回复:                                                      │
│    亲密度 -1 (单向互动)                                        │
│    降低此人的跟进优先级                                         │
│    3天后重新生成 RE_CONNECT 行动 (用不同话术)                   │
│                                                              │
│  Step 5: 新一轮循环                                           │
│  更新后的画像 → 重新评估 → 新的洞察 → 新的行动                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 四、日常自动化流程

### 4.1 每日自动流程 (cron: 每天 8:00)

```
1. 检查微信在线状态
2. 增量同步最近24小时的聊天记录
3. 对新消息运行增量画像分析
4. 运行洞察引擎 →
   - 扫描所有A/B级关系的最后互动时间
   - 检查是否有逾期借款
   - 检查是否有即将到期的提醒
   - 检测是否有新的商业信号
   - 检查主人的待办完成情况
5. 生成 "今日行动清单" →
   输出到仪表盘 + Hermes 通知
6. 对于 P≥0.8 的紧急行动 →
   自动派遣执行 (如需确认则推送通知)
```

### 4.2 每周自动流程 (cron: 每周一 9:00)

```
1. 运行全量关系健康度扫描
2. 生成 "本周关系周报":
   - 哪些关系在升温/降温？
   - 本周最活跃 Top 10
   - 本周该联系但没联系的人
   - 本周商业机会汇总
   - 主人学习/消费/健康统计
3. 生成 "本周推荐行动清单"
4. 对于周期性行动 (每周问候、每周学习目标) →
   创建定时任务
```

### 4.3 事件驱动的实时触发

```
微信收到新消息 →
  ├─ 入库 (wechat_chat)
  ├─ 增量画像分析 (该好友)
  ├─ 检测关键信号词:
  │   ├─ "借钱"/"转你"/"急用" → 创建经济事件
  │   ├─ "报价"/"多少钱"/"预算" → 标记商业机会
  │   ├─ "生病"/"住院"/"去世" → 生成关心行动
  │   ├─ "升职"/"跳槽"/"换工作" → 更新职业画像+祝贺
  │   ├─ "结婚"/"生娃"/"买房" → 创建人生事件+祝贺
  │   └─ "好的"/"OK"/"收到" → 标记之前行动的"成功反馈"
  └─ 如触发关键信号 → 实时生成行动建议
```

---

## 五、技术实现要点

### 5.1 新增数据库表

```sql
-- 核心: 自动生成的行动建议表
CREATE TABLE actionable_insight (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    friend_id       INTEGER,                    -- → wechat_friend.id (NULL=主人自己的行动)
    insight_type    VARCHAR(32) NOT NULL,       -- relation_decay / biz_opportunity / payment_remind / birthday / self_growth / ...
    category        VARCHAR(32),                -- maintenance / commercial / risk / emotional / self
    title           VARCHAR(256) NOT NULL,      -- "跟许国勇已经35天没联系了"
    description     TEXT,                       -- 详细分析
    evidence        TEXT,                       -- 数据证据 (JSON: {closeness_before:72, closeness_after:65, ...})
    suggested_action VARCHAR(256),              -- AI生成的建议行动描述
    action_type     VARCHAR(32),                -- SEND_MESSAGE / FOLLOW_UP / RE_CONNECT / CONGRATULATE / ...
    action_payload  TEXT,                       -- JSON: 执行所需的完整参数
    priority_score  DECIMAL(3,2) DEFAULT 0,     -- 0.00-1.00
    priority_level  VARCHAR(8) DEFAULT 'leisure', -- today / week / leisure / archive
    status          VARCHAR(16) DEFAULT 'pending', -- pending / dispatched / executing / done / dismissed / failed
    dispatched_at   DATETIME,
    dispatched_to   VARCHAR(64),                -- 派遣目标: "winpeek_wechat_send" / "cron:job_id" / "todo:id"
    dispatch_method VARCHAR(16) DEFAULT 'auto', -- auto / scheduled / todo / manual_confirm
    executed_at     DATETIME,
    result          VARCHAR(16),                -- success / no_reply / failed / cancelled
    result_detail   TEXT,                       -- 执行结果详情
    feedback_ts     DATETIME,                   -- 收到反馈的时间
    feedback_score  TINYINT,                    -- 效果评分 1-5
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_priority (priority_score DESC),
    INDEX idx_friend_status (friend_id, status),
    INDEX idx_created (created_at)
);

-- 行动模板库 (可复用的行动策略)
CREATE TABLE action_template (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(128) NOT NULL,       -- "跟进话术-老客户"
    action_type     VARCHAR(32) NOT NULL,        -- SEND_MESSAGE / RE_CONNECT / ...
    category        VARCHAR(32),                 -- maintenance / commercial / risk / emotional / self
    trigger_rule    TEXT,                        -- JSON: 触发条件规则
    default_tone    VARCHAR(16) DEFAULT '亲切',   -- 默认语气
    template_text   TEXT NOT NULL,               -- 模板文本 (支持变量)
    variables       TEXT,                        -- JSON: [{name, description, default}]
    use_count       INT DEFAULT 0,              -- 使用次数
    success_rate    DECIMAL(4,3),                -- 成功率 (对方有回复的比例)
    is_active       TINYINT DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 自动化规则配置 (主人自定义自动化策略)
CREATE TABLE automation_rule (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(128) NOT NULL,
    description     TEXT,
    condition       TEXT NOT NULL,               -- JSON: 触发条件 {"closeness": {"<": 50}, "last_contact_days": {">": 30}}
    action_type     VARCHAR(32) NOT NULL,
    action_template_id INTEGER,                  -- → action_template.id
    priority_base   DECIMAL(3,2) DEFAULT 0.5,
    dispatch_method VARCHAR(16) DEFAULT 'auto',  -- auto / todo / confirm
    schedule        VARCHAR(64),                 -- cron 表达式 (空=事件驱动)
    is_active       TINYINT DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (action_template_id) REFERENCES action_template(id) ON DELETE SET NULL
);
```

### 5.2 Hermes 工具注册 (新增)

```python
# tools/winpeek_tools.py 中新增

# 画像相关
"winpeek_get_portrait"        # 获取好友画像 (8维分数+分类+AI总结)
"winpeek_analyze_portrait"    # 触发AI重算画像
"winpeek_list_portraits"      # 批量列出好友画像 (支持排序/筛选)

# 洞察引擎
"winpeek_get_insights"        # 获取当前所有行动建议
"winpeek_dismiss_insight"     # 忽略某条建议
"winpeek_execute_insight"     # 手动执行某条建议

# 自动化规则
"winpeek_list_automations"    # 列出所有自动化规则
"winpeek_toggle_automation"   # 启用/禁用规则

# 仪表盘
"winpeek_dashboard"           # 获取今日快照数据
"winpeek_weekly_report"       # 获取周报数据
```

### 5.3 前端新增页面

```
新增路由:
  /wechat-dashboard     → 仪表盘 (今日快照+行动清单+AI建议)
  /wechat-insights      → 洞察面板 (所有行动建议列表)
  /wechat-automation    → 自动化规则管理 (CRUD自动化规则)

新增组件:
  ActionCard             → 单条行动建议卡片 (含执行/推迟/忽略按钮)
  InsightFeed            → 洞察信息流 (按优先级排序的行动列表)
  PortraitRadar          → 8维评分雷达图
  PortraitTimeline       → 关键事件时间线
  AutomationRuleEditor   → 自动化规则编辑器 (可视化条件配置)
  TodaySnapshot          → 今日快照 (消费/待办/学习/互动汇总)
  PriorityBadge          → 优先级标签 (today/week/leisure)
```

---

## 六、实现路线图

| 阶段 | 内容 | 产出 | 优先级 |
|------|------|------|--------|
| **P0** | 建表: `actionable_insight` + `action_template` + `automation_rule` | SQL | 最高 |
| **P1** | 洞察引擎核心: 规则匹配器 + 优先级计算 | `insight_engine.py` | 最高 |
| **P2** | 行动生成器: insight → action_packet | `action_planner.py` | 高 |
| **P3** | 前端: 仪表盘 + 行动清单 + 洞察面板 | React 组件 | 高 |
| **P4** | Hermes 任务派遣: 即时执行 + cron + todo 三条路径 | 工具注册 | 高 |
| **P5** | 执行反馈闭环: 观察 → 分析 → 更新 | `feedback_loop.py` | 中 |
| **P6** | 种子模板 + 种子规则 (20+ 预置行动模板) | SQL 种子数据 | 中 |
| **P7** | 自动化规则 UI (用户自定义规则) | React 组件 | 低 |
| **P8** | 画像驱动的批量操作 (按画像维度筛选→群发) | UI + 后端 | 低 |

---

## 七、核心价值总结

```
传统 CRM:  你手动看 → 手动判断 → 手动操作
本系统:    AI 持续看 → AI 自动判断 → AI 建议行动 → 你确认/自动执行

关键差异:
  1. 不是"表格+搜索", 是"洞察+建议"
  2. 不是"你找事做", 是"事来找你"
  3. 不是"一次性分析", 是"持续追踪+趋势预警"
  4. 不是"独立工具", 是"Hermes 生态的一部分"—画像→洞察→派遣→执行→反馈→更新
```

---

*版本: v1.0 · 2025-01-15 · 与 `wechat-crm-design.md` + `master-friend-system-architecture.md` + `actionable-insights-engine.md` 互补*
