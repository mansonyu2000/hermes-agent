-- MIM 功能清单表（替代 feature-inventory.md）
-- 执行：mysql -h 192.168.3.23 -u winpeek -p winpeek < this_file.sql

CREATE TABLE IF NOT EXISTS mim_feature_inventory (
    id          VARCHAR(10)  NOT NULL PRIMARY KEY COMMENT '功能ID, 如 F4.1',
    module      VARCHAR(32)  NOT NULL COMMENT '模块: 身份与登录/联系人/单聊消息/群聊/...',
    feature     VARCHAR(64)  NOT NULL COMMENT '功能名称',
    sub         TEXT         NULL     COMMENT '子功能/实现细节',
    deps        VARCHAR(255) NULL     COMMENT '依赖, 逗号分隔如 F1.7,F7.3',
    status      ENUM('done','todo','skip') NOT NULL DEFAULT 'todo' COMMENT '状态',
    priority    ENUM('P0','P1','P2','P3')  NOT NULL DEFAULT 'P3' COMMENT '优先级',
    decision    VARCHAR(32)  NULL     COMMENT '决策: V1/V1.5/V2/已完成',
    assignee    VARCHAR(64)  NULL     COMMENT '负责人/包名',
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_module (module),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_decision (decision)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='MIM功能清单（AI Agent可SQL查询）';

-- 导入初始数据（从 JSON 提取）
-- python -c "import json; data=json.load(open('feature-inventory.json')); ... "
