-- =============================================================================
-- 014_winpeek_hub.sql — WinPeek Hub 数据库表 (MySQL)
-- 租户管理 + 用户平台绑定 + 消息归档
-- 复用已有 MySQL: 192.168.3.23:3306/winpeek
-- =============================================================================

-- 1. 租户表 (公司/团队)
CREATE TABLE IF NOT EXISTS hub_tenants (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL COMMENT '租户名称, 如"XX公司"',
    slug        VARCHAR(50)  NOT NULL UNIQUE COMMENT '唯一标识, 如 company_a',
    plan        VARCHAR(20)  DEFAULT 'free' COMMENT 'free/pro/enterprise',
    max_members INT          DEFAULT 10 COMMENT '最大成员数',
    is_active   TINYINT(1)   DEFAULT 1,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户表';

-- 2. 用户表 (含多平台绑定)
CREATE TABLE IF NOT EXISTS hub_users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id       INT          NOT NULL COMMENT '所属租户',
    display_name    VARCHAR(100) NOT NULL COMMENT '显示名',
    email           VARCHAR(200) COMMENT '邮箱',
    phone           VARCHAR(30)  COMMENT '手机号',
    role            VARCHAR(20)  DEFAULT 'member' COMMENT 'admin/manager/member',
    is_active       TINYINT(1)   DEFAULT 1,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES hub_tenants(id) ON DELETE CASCADE,
    INDEX idx_tenant (tenant_id),
    INDEX idx_display_name (display_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 3. 用户平台绑定表 (一个用户可绑定多个IM平台)
CREATE TABLE IF NOT EXISTS hub_user_platforms (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT          NOT NULL COMMENT '关联 hub_users.id',
    platform        VARCHAR(30)  NOT NULL COMMENT 'wechat/dingtalk/feishu/qq/telegram',
    platform_uid    VARCHAR(200) NOT NULL COMMENT '平台上的唯一ID, 如 wxid_xxx / dt_xxx',
    platform_name   VARCHAR(100) COMMENT '平台上的昵称',
    is_primary      TINYINT(1)   DEFAULT 0 COMMENT '是否为主要联系平台',
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES hub_users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_platform_uid (platform, platform_uid),
    INDEX idx_user (user_id),
    INDEX idx_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户平台绑定表';

-- 4. 消息归档表
CREATE TABLE IF NOT EXISTS hub_messages (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id       INT          NOT NULL COMMENT '所属租户',
    from_platform   VARCHAR(30)  NOT NULL COMMENT '来源平台',
    from_uid        VARCHAR(200) NOT NULL COMMENT '发送者平台UID',
    from_name       VARCHAR(100) COMMENT '发送者显示名',
    to_platform     VARCHAR(30)  COMMENT '目标平台 (跨平台时)',
    to_uid          VARCHAR(200) COMMENT '接收者平台UID',
    to_name         VARCHAR(100) COMMENT '接收者显示名',
    content         TEXT         NOT NULL COMMENT '消息内容',
    msg_type        VARCHAR(20)  DEFAULT 'text' COMMENT 'text/image/file/voice/system',
    direction       VARCHAR(10)  DEFAULT 'in' COMMENT 'in=用户→Agent, out=Agent→用户',
    is_cross_platform TINYINT(1) DEFAULT 0 COMMENT '是否跨平台消息',
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_time (tenant_id, created_at),
    INDEX idx_from (from_platform, from_uid),
    INDEX idx_to (to_platform, to_uid),
    INDEX idx_type (msg_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息归档表';

-- 5. 种子数据 (示例)
INSERT IGNORE INTO hub_tenants (name, slug, plan) VALUES ('默认团队', 'default', 'free');
