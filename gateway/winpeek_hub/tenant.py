"""
tenant.py — WinPeek Hub 多租户管理

每个"公司/团队"是一个 tenant。
用户在 Hermes Gateway 上通过某个 IM 平台发消息时，
Hub 根据用户的平台 ID (如微信 wxid) 查找其所属 tenant，
实现多租户数据隔离。

数据源: MySQL winpeek 库的 users 表
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# MySQL 连接配置（与 wechat_db.py 共用同一数据库）
_DB_CONFIG = {
    "host": os.getenv("WINPEEK_DB_HOST", "192.168.3.23"),
    "port": int(os.getenv("WINPEEK_DB_PORT", "3306")),
    "user": os.getenv("WINPEEK_DB_USER", "winpeek"),
    "password": os.getenv("WINPEEK_DB_PASS", ""),
    "database": os.getenv("WINPEEK_DB_NAME", "winpeek"),
}

def _get_conn():
    """惰性创建 MySQL 连接"""
    try:
        import mysql.connector
        return mysql.connector.connect(**_DB_CONFIG)
    except ImportError:
        logger.warning("mysql-connector-python not installed; tenant lookup disabled")
        return None
    except Exception as e:
        logger.warning(f"MySQL connection failed: {e}")
        return None


def get_tenant_for_user(platform: str, platform_uid: str) -> Optional[dict]:
    """
    根据用户在某个 IM 平台上的 ID，查找其所属租户。
    
    Args:
        platform: 平台名 (如 'wechat', 'dingtalk', 'feishu')
        platform_uid: 用户在平台上的唯一标识 (如微信号 wxid_xxx)
    
    Returns:
        {"tenant_id": "company_a", "tenant_name": "XX公司", "user_id": 42}
        或 None (未找到)
    """
    conn = _get_conn()
    if not conn:
        return None
    
    try:
        cur = conn.cursor(dictionary=True)
        # 从 users 表查找: platform + platform_uid → tenant
        cur.execute(
            """SELECT u.id as user_id, u.tenant_id, t.name as tenant_name
               FROM users u
               LEFT JOIN tenants t ON u.tenant_id = t.id
               WHERE u.platform_uid = %s AND u.platform = %s""",
            (platform_uid, platform)
        )
        row = cur.fetchone()
        if row:
            return {
                "tenant_id": row["tenant_id"],
                "tenant_name": row.get("tenant_name", ""),
                "user_id": row["user_id"],
            }
        return None
    except Exception as e:
        logger.debug(f"Tenant lookup failed: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def list_tenant_members(tenant_id: str) -> list:
    """
    列出某个租户下的所有成员及其在各平台的绑定关系。
    用于跨平台消息路由。
    
    Returns:
        [{"user_id": 1, "platform": "wechat", "platform_uid": "wxid_xxx"}, ...]
    """
    conn = _get_conn()
    if not conn:
        return []
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT id as user_id, platform, platform_uid, display_name
               FROM users WHERE tenant_id = %s""",
            (tenant_id,)
        )
        return cur.fetchall()
    except Exception:
        return []
    finally:
        cur.close()
        conn.close()
