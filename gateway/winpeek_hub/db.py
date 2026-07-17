"""
db.py — WinPeek MIM MySQL 连接管理

所有 MIM 模块通过此模块连接 htubs24 的 MySQL winpeek-db2。
配置方式（环境变量）:
  WINPEEK_DB_HOST  (默认 192.168.3.23)
  WINPEEK_DB_PORT  (默认 3306)
  WINPEEK_DB_USER  (默认 winpeek)
  WINPEEK_DB_PASS  (默认 Server33)
  WINPEEK_DB_NAME  (默认 winpeek-db2)
"""

import os
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_DB_CONFIG = {
    "host": os.getenv("WINPEEK_DB_HOST", "192.168.3.23"),
    "port": int(os.getenv("WINPEEK_DB_PORT", "3306")),
    "user": os.getenv("WINPEEK_DB_USER", "winpeek"),
    "password": os.getenv("WINPEEK_DB_PASS", "Server33"),
    "database": os.getenv("WINPEEK_DB_NAME", "winpeek-db2"),
    "charset": "utf8mb4",
}


def get_conn():
    """获取 MySQL 连接。"""
    try:
        import pymysql
        return pymysql.connect(**_DB_CONFIG)
    except ImportError:
        logger.error("pymysql not installed. Run: pip install pymysql")
        return None
    except Exception as e:
        logger.error(f"MySQL connection failed: {e}")
        return None


@lru_cache(maxsize=1)
def get_server_info() -> dict:
    """返回数据库连接信息（不含密码），用于日志/健康检查。"""
    return {k: v for k, v in _DB_CONFIG.items() if k != "password"}
