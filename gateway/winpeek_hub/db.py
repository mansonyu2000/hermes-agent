"""
db.py — WinPeek MIM MySQL 连接管理

所有 MIM 模块通过此模块连接 htubs24 的 MySQL winpeek-db1。
配置方式（环境变量）:
  WINPEEK_DB_HOST  (默认 192.168.3.23)
  WINPEEK_DB_PORT  (默认 3306)
  WINPEEK_DB_USER  (默认 winpeek)
  WINPEEK_DB_PASS  (默认 Server33)
  WINPEEK_DB_NAME  (默认 winpeek-db1)
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
    "database": os.getenv("WINPEEK_DB_NAME", "winpeek-db1"),
    "charset": "utf8mb4",
}


def get_conn(database: str = None):
    """获取 MySQL 连接（DictCursor，所有调用方统一使用）。

    未安装 pymysql 或连接失败时返回 None — 调用方必须检查。
    """
    try:
        import pymysql
        from pymysql.cursors import DictCursor
        cfg = dict(_DB_CONFIG)
        if database:
            cfg["database"] = database
        return pymysql.connect(**cfg, cursorclass=DictCursor)
    except ImportError:
        logger.warning("pymysql not installed. Run: pip install pymysql")
        return None
    except Exception as e:
        logger.error(f"MySQL connection failed: {e}")
        return None


@lru_cache(maxsize=1)
def get_server_info() -> dict:
    """返回数据库连接信息（不含密码），用于日志/健康检查。"""
    return {k: v for k, v in _DB_CONFIG.items() if k != "password"}


# ---------------------------------------------------------------------------
# Context manager + decorator — 消除样板代码
# ---------------------------------------------------------------------------

from contextlib import contextmanager
import json


@contextmanager
def db_cursor(commit: bool = True):
    """上下文管理器：自动管理连接和游标生命周期。

    用法:
        with db_cursor() as cur:
            cur.execute("SELECT ...")
            return cur.fetchall()

    自动: 获取连接 → 创建游标 → commit/rollback → 关闭连接。
    """
    conn = get_conn()
    if conn is None:
        raise RuntimeError("Database unavailable")
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def with_db(handler):
    """装饰器：自动管理 winpeek_tools handler 的数据库连接和异常。

    用法:
        @with_db
        def _handle_xxx(args, cur):
            cur.execute("SELECT ...")
            return json.dumps({"ok": True, "data": cur.fetchall()})

    自动: 获取连接 → 创建游标 → 异常捕获 → commit → 关闭。
    要求 handler 签名: (args: dict, cur) -> str (JSON)
    """
    import functools

    @functools.wraps(handler)
    def wrapper(args):
        try:
            with db_cursor() as cur:
                return handler(args, cur)
        except Exception as e:
            return json.dumps({"error": str(e)})
    return wrapper
