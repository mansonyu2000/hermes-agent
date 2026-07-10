-- =============================================================================
-- WinPeek CRM 完整数据库设计 — MySQL
-- 基础: wechat_friend / wechat_group / wechat_chat (已有)
-- 新增: wechat_friend 扩展字段 + 14 张新表
-- =============================================================================

-- ① wechat_friend 扩展字段
-- =============================================================================
ALTER TABLE wechat_friend
    ADD COLUMN birthday          VARCHAR(16)  COMMENT '生日 MM-DD',
    ADD COLUMN gender            VARCHAR(4)   COMMENT '男/女/未知',
    ADD COLUMN email             VARCHAR(128) COMMENT 'AI从聊天提取',
    ADD COLUMN portrait_summary  TEXT         COMMENT 'AI人物速写 50-200字',
    ADD COLUMN ai_profile        JSON         COMMENT 'AI画像: 职业/学历/爱好/性格/宗教/消费习惯',
    ADD COLUMN customer_level    CHAR(1)      COMMENT 'A/B/C/D/NULL',
    ADD COLUMN sales_stage       VARCHAR(32)  COMMENT 'lead/intent/quote/negotiate/close/lost',
    ADD COLUMN estimated_amount  DECIMAL(12,2) COMMENT '预计成交金额',
    ADD COLUMN estimated_close   DATE         COMMENT '预计成交日期',
    ADD COLUMN win_probability   INT          COMMENT '成交概率 0-100',
    ADD COLUMN heat_score        INT DEFAULT 0 COMMENT '热度评分 0-100',
    ADD COLUMN is_blacklisted    INT DEFAULT 0 COMMENT '黑名单',
    ADD COLUMN remark            TEXT         COMMENT '富文本备注',
    ADD COLUMN obsidian_path     VARCHAR(512) COMMENT 'Obsidian卡片路径',
    ADD COLUMN last_contact_at   DATETIME     COMMENT '最后互动时间';


-- ② 关系分类树定义 (系统预置13棵树)
-- =============================================================================
CREATE TABLE IF NOT EXISTS wechat_relation_tree (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    tree_key     VARCHAR(32)  NOT NULL COMMENT '大类key: family/relative/hometown/classmate/comrade/colleague/customer/supplier/competitor/supply_chain/interest/neighbor/other',
    tree_name    VARCHAR(64)  NOT NULL COMMENT '中文名: 血缘/亲戚/同乡/同学/战友/同事/客户/供应商/同行/供应链/兴趣/邻居/其他',
    parent_key   VARCHAR(32)  COMMENT '父节点key',
    level        INT DEFAULT 0 COMMENT '树深度: 0=大类 1=子类 2=细类',
    icon         VARCHAR(8)   COMMENT 'emoji',
    sort_order   INT DEFAULT 0,
    is_active    TINYINT DEFAULT 1,
    UNIQUE KEY uk_tree (tree_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='13棵关系分类树定义';


-- ③ 好友↔关系分类 M:N 标记
-- =============================================================================
CREATE TABLE IF NOT EXISTS wechat_friend_relation (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    friend_id       INT NOT NULL COMMENT '→ wechat_friend.id',
    tree_key        VARCHAR(32)  NOT NULL COMMENT '→ wechat_relation_tree.tree_key',
    sub_key         VARCHAR(32)  COMMENT '子类key',
    relation_level  TINYINT DEFAULT 2 COMMENT '1=红(近) 2=黄(一般) 3=灰(远)',
    time_label      VARCHAR(64)  COMMENT '时间标签: 2015-2018 / 小学',
    org_label       VARCHAR(128) COMMENT '组织标签: 华为 / 清华大学',
    is_primary      TINYINT DEFAULT 0 COMMENT '是否主要关系',
    notes           VARCHAR(256) COMMENT '短备注',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    UNIQUE KEY uk_friend_tree (friend_id, tree_key, sub_key),
    INDEX idx_tree (tree_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='好友↔关系分类 M:N';


-- ④ 关键事件时间线
-- =============================================================================
CREATE TABLE IF NOT EXISTS wechat_friend_event (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    friend_id    INT NOT NULL COMMENT '→ wechat_friend.id',
    event_date   VARCHAR(32)  COMMENT 'YYYY-MM 或 YYYY',
    event_type   VARCHAR(32)  DEFAULT 'general' COMMENT 'first_met/milestone/reunion/life_change/chat_extracted',
    title        VARCHAR(256),
    detail       TEXT,
    source       VARCHAR(16)  DEFAULT 'ai' COMMENT 'ai/manual/chat',
    confidence   TINYINT      DEFAULT 50 COMMENT 'AI置信度 0-100',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    INDEX idx_friend_date (friend_id, event_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='好友关键事件时间线';


-- ⑤ 经济往来账簿
-- =============================================================================
CREATE TABLE IF NOT EXISTS wechat_friend_finance (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    friend_id    INT NOT NULL COMMENT '→ wechat_friend.id',
    direction    VARCHAR(8)   NOT NULL COMMENT 'out=我借/付给TA in=TA借/付给我',
    finance_type VARCHAR(16)  NOT NULL COMMENT 'loan/payment/investment/gift',
    amount       DECIMAL(12,2) NOT NULL,
    currency     VARCHAR(8)   DEFAULT 'CNY',
    title        VARCHAR(256) COMMENT '事由',
    detail       TEXT,
    due_date     DATE         COMMENT '约定还款日',
    is_settled   TINYINT      DEFAULT 0 COMMENT '0=未结清 1=已结清',
    settled_at   DATETIME,
    chat_ref     VARCHAR(128) COMMENT '来源聊天消息ID',
    source       VARCHAR(16)  DEFAULT 'manual' COMMENT 'manual/ai_extracted',
    event_date   DATE         COMMENT '发生日期',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    INDEX idx_friend_settled (friend_id, is_settled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='好友经济往来账簿';


-- ⑥ 结构化交互事件 (聊天→关系分增减)
-- =============================================================================
CREATE TABLE IF NOT EXISTS friend_event (
    id                 BIGINT AUTO_INCREMENT PRIMARY KEY,
    friend_id          INT NOT NULL COMMENT '→ wechat_friend.id',
    event_type         VARCHAR(32)  NOT NULL COMMENT 'chat/money/meet/conflict/help/promise/refuse',
    event_subtype      VARCHAR(32)  COMMENT '子类型',
    event_ts           DATETIME NOT NULL COMMENT '发生时间',
    source             VARCHAR(16)  DEFAULT 'chat' COMMENT 'chat/manual/ocr/system',
    source_id          VARCHAR(128) COMMENT '来源消息ID',
    title              VARCHAR(256),
    summary            TEXT         COMMENT 'AI摘要 ≤200字',
    raw_text           TEXT         COMMENT '原始文本',
    -- 8维关系分增量
    closeness_delta    TINYINT DEFAULT 0,
    trust_delta        TINYINT DEFAULT 0,
    respect_delta      TINYINT DEFAULT 0,
    affection_delta    TINYINT DEFAULT 0,
    biz_delta          TINYINT DEFAULT 0,
    growth_delta       TINYINT DEFAULT 0,
    credit_delta       TINYINT DEFAULT 0,
    reciprocity_delta  TINYINT DEFAULT 0,
    -- 机会标记
    is_biz_opportunity      TINYINT DEFAULT 0,
    is_growth_opportunity   TINYINT DEFAULT 0,
    is_giving_opportunity   TINYINT DEFAULT 0,
    is_receiving_opportunity TINYINT DEFAULT 0,
    is_promise              TINYINT DEFAULT 0,
    is_refusal              TINYINT DEFAULT 0,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    INDEX idx_friend_ts (friend_id, event_ts),
    INDEX idx_type (event_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='结构化交互事件(聊天→评分+机会)';


-- ⑦ 8维评分时间序列
-- =============================================================================
CREATE TABLE IF NOT EXISTS friend_score_log (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    friend_id       INT NOT NULL,
    closeness       TINYINT DEFAULT 50 COMMENT '亲密度 0-100',
    trust           TINYINT DEFAULT 50 COMMENT '信任度',
    respect         TINYINT DEFAULT 50 COMMENT '尊重度',
    affection       TINYINT DEFAULT 50 COMMENT '好感度',
    biz_value       TINYINT DEFAULT 50 COMMENT '商业价值',
    growth_value    TINYINT DEFAULT 50 COMMENT '成长价值',
    credit_score    TINYINT DEFAULT 50 COMMENT '经济信用',
    reciprocity     TINYINT DEFAULT 50 COMMENT '互惠度',
    event_id        BIGINT       COMMENT '→ friend_event.id 触发事件',
    trigger_type    VARCHAR(32)  COMMENT 'chat/manual/decay/ai_recalc',
    summary         VARCHAR(256) COMMENT '评分变动原因简述',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    INDEX idx_friend (friend_id),
    INDEX idx_friend_ts (friend_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='8维关系评分时间序列';


-- ⑧ 机会识别
-- =============================================================================
CREATE TABLE IF NOT EXISTS friend_opportunity (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    friend_id       INT NOT NULL,
    opportunity_type VARCHAR(16) NOT NULL COMMENT 'biz/growth/giving/receiving',
    title           VARCHAR(256),
    description     TEXT,
    amount_estimate DECIMAL(12,2) COMMENT '预估金额',
    probability     TINYINT DEFAULT 50 COMMENT '概率 0-100',
    stage           VARCHAR(16) DEFAULT 'identified' COMMENT 'identified/evaluated/followed/won/lost',
    event_id        BIGINT       COMMENT '→ friend_event.id',
    next_action     VARCHAR(256) COMMENT '下一步行动',
    next_date       DATE,
    closed_at       DATETIME,
    result          VARCHAR(32)  COMMENT 'won/lost/expired',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    INDEX idx_friend_stage (friend_id, stage),
    INDEX idx_type (opportunity_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机会识别(从聊天提取的商业/成长机会)';


-- ⑨ 拜访/跟进记录 (销售管理)
-- =============================================================================
CREATE TABLE IF NOT EXISTS friend_sales_log (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    friend_id       INT NOT NULL,
    log_date        DATE NOT NULL,
    log_type        VARCHAR(16) DEFAULT 'wechat' COMMENT 'phone/wechat/meeting/email/other',
    content         TEXT  COMMENT '沟通内容摘要',
    result          VARCHAR(8)  COMMENT 'done/pending/failed',
    next_step       VARCHAR(256) COMMENT '下一步计划',
    next_date       DATE        COMMENT '下次跟进日期',
    related_chat_ids JSON       COMMENT '关联聊天消息ID数组',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE CASCADE,
    INDEX idx_friend_date (friend_id, log_date),
    INDEX idx_next (next_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='拜访/跟进记录';


-- ⑩ AI 行动建议
-- =============================================================================
CREATE TABLE IF NOT EXISTS actionable_insight (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    friend_id        INT          COMMENT '→ wechat_friend.id, NULL=主人自身',
    insight_type     VARCHAR(32)  NOT NULL COMMENT 'relation_decay/biz_opportunity/payment_remind/birthday/self_growth/reconnect/congratulate/check_in',
    category         VARCHAR(32)  COMMENT 'maintenance/commercial/risk/emotional/self',
    title            VARCHAR(256) NOT NULL,
    description      TEXT,
    evidence         JSON         COMMENT '数据证据',
    action_type      VARCHAR(32)  NOT NULL COMMENT 'SEND_MESSAGE/FOLLOW_UP/RE_CONNECT/CONGRATULATE/REMIND_PAYMENT/CHECK_IN/THANK/SET_BOUNDARY/SELF_IMPROVE',
    action_payload   JSON         COMMENT '执行参数: {wxid, message, tone, template_id}',
    suggested_script VARCHAR(1024) COMMENT 'AI生成的话术',
    priority_score   DECIMAL(3,2) DEFAULT 0 COMMENT '0.00-1.00',
    priority_level   VARCHAR(8)   DEFAULT 'leisure' COMMENT 'today/week/leisure/archive',
    status           VARCHAR(16)  DEFAULT 'pending' COMMENT 'pending/dispatched/executing/done/dismissed/failed',
    dispatch_method  VARCHAR(16)  DEFAULT 'auto' COMMENT 'auto/scheduled/todo/manual_confirm',
    dispatched_at    DATETIME,
    executed_at      DATETIME,
    result           VARCHAR(16)  COMMENT 'success/no_reply/failed/cancelled',
    result_detail    TEXT,
    feedback_score   TINYINT      COMMENT '效果评分 1-5',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (friend_id) REFERENCES wechat_friend(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_priority (priority_score DESC),
    INDEX idx_friend_status (friend_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI行动建议(洞察引擎输出)';


-- ⑪ 行动策略模板
-- =============================================================================
CREATE TABLE IF NOT EXISTS action_template (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(128) NOT NULL COMMENT '模板名',
    action_type   VARCHAR(32)  NOT NULL COMMENT 'SEND_MESSAGE/RE_CONNECT/CONGRATULATE/...',
    category      VARCHAR(32)  COMMENT 'maintenance/commercial/risk/emotional/self',
    trigger_rule  JSON         COMMENT '触发条件',
    default_tone  VARCHAR(16)  DEFAULT 'friendly' COMMENT 'friendly/formal/humorous/caring',
    template_text TEXT         NOT NULL COMMENT '模板文本, 支持{variable}',
    variables     JSON         COMMENT '[{name,description,default}]',
    use_count     INT DEFAULT 0,
    success_rate  DECIMAL(4,3) COMMENT '成功率(对方回复比例)',
    is_active     TINYINT DEFAULT 1,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行动策略模板(可复用)';


-- ⑫ 用户自动化规则
-- =============================================================================
CREATE TABLE IF NOT EXISTS automation_rule (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    name               VARCHAR(128) NOT NULL,
    description        TEXT,
    condition          JSON NOT NULL COMMENT '触发条件: {closeness:{"<":50}, last_contact_days:{">":30}}',
    action_type        VARCHAR(32)  NOT NULL,
    action_template_id INT          COMMENT '→ action_template.id',
    priority_base      DECIMAL(3,2) DEFAULT 0.5,
    dispatch_method    VARCHAR(16)  DEFAULT 'auto' COMMENT 'auto/todo/confirm',
    schedule           VARCHAR(64)  COMMENT 'cron表达式',
    is_active          TINYINT DEFAULT 1,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (action_template_id) REFERENCES action_template(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户自定义自动化规则';


-- ⑬ 群发消息模板
-- =============================================================================
CREATE TABLE IF NOT EXISTS message_template (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    title         VARCHAR(128) NOT NULL,
    category      VARCHAR(32)  COMMENT 'first_contact/product_recommend/holiday/follow_up/payment_remind/thanks/custom',
    template_text TEXT         NOT NULL COMMENT '支持{variable}占位符',
    variables     JSON         COMMENT '[{name,description}]',
    default_tone  VARCHAR(16)  DEFAULT 'friendly',
    use_count     INT DEFAULT 0,
    success_rate  DECIMAL(4,3),
    is_active     TINYINT DEFAULT 1,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='群发消息模板';


-- ⑭ 自扩展枚举
-- =============================================================================
CREATE TABLE IF NOT EXISTS sys_enum_definition (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    enum_group    VARCHAR(64)  NOT NULL COMMENT '分组: industry/religion/tv_genre/music_style/...',
    enum_key      VARCHAR(64)  NOT NULL,
    enum_value    VARCHAR(128) NOT NULL,
    parent_key    VARCHAR(64)  COMMENT '父级key(树形)',
    icon          VARCHAR(8)   COMMENT 'emoji',
    description   VARCHAR(256),
    source        VARCHAR(16)  DEFAULT 'system' COMMENT 'system/ai/user/web',
    search_query  VARCHAR(256) COMMENT 'AI搜索词',
    sort_order    INT DEFAULT 0,
    is_active     TINYINT DEFAULT 1,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_enum (enum_group, enum_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='自扩展枚举(动态分类/下拉选项)';
