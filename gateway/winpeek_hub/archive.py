"""
archive.py — WinPeek Hub 消息归档

所有通过 Hub 的消息（跨平台或同平台）都写入 MySQL，
用于审计、合规和多端同步。

表结构（复用 WinPeek 现有设计）:
  hub_messages:
    - id, tenant_id, from_platform, from_uid, to_platform, to_uid
    - content, msg_type, created_at
"""

import os
import logging
import json
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_DB_CONFIG = {
    "host": os.getenv("WINPEEK_DB_HOST", "192.168.3.23"),
    "port": int(os.getenv("WINPEEK_DB_PORT", "3306")),
    "user": os.getenv("WINPEEK_DB_USER", "winpeek"),
    "password": os.getenv("WINPEEK_DB_PASS", ""),
    "database": os.getenv("WINPEEK_DB_NAME", "winpeek"),
}

def _get_conn():
    try:
        import mysql.connector
        return mysql.connector.connect(**_DB_CONFIG)
    except ImportError:
        return None
    except Exception:
        return None

_ENGINE = os.getenv("HUB_ARCHIVE_ENGINE", "mysql")  # mysql | jsonl | off


def archive_message(
    tenant_id: str,
    from_platform: str,
    from_uid: str,
    to_platform: str,
    to_uid: str,
    content: str,
    msg_type: str = "text",
) -> bool:
    """
    归档一条消息。
    
    支持三种存储引擎（通过 HUB_ARCHIVE_ENGINE 环境变量切换）:
      - mysql: 写入 MySQL hub_messages 表
      - jsonl: 追加到 ~/.hermes/winpeek/archive/messages.jsonl
      - off: 不归档
    """
    if _ENGINE == "off":
        return True
    
    if _ENGINE == "jsonl":
        return _archive_jsonl(tenant_id, from_platform, from_uid,
                              to_platform, to_uid, content, msg_type)
    
    # 默认 mysql
    return _archive_mysql(tenant_id, from_platform, from_uid,
                          to_platform, to_uid, content, msg_type)


def _archive_mysql(tenant_id, from_platform, from_uid,
                   to_platform, to_uid, content, msg_type) -> bool:
    conn = _get_conn()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO hub_messages
               (tenant_id, from_platform, from_uid, to_platform, to_uid,
                content, msg_type, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (tenant_id, from_platform, from_uid, to_platform, to_uid,
             content, msg_type, datetime.now())
        )
        conn.commit()
        return True
    except Exception as e:
        logger.debug(f"Archive failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def _archive_jsonl(tenant_id, from_platform, from_uid,
                   to_platform, to_uid, content, msg_type) -> bool:
    try:
        import os as _os
        log_dir = _os.path.expanduser("~/.hermes/winpeek/archive")
        _os.makedirs(log_dir, exist_ok=True)
        log_path = _os.path.join(log_dir, "messages.jsonl")
        entry = json.dumps({
            "tenant_id": tenant_id,
            "from": f"{from_uid}@{from_platform}",
            "to": f"{to_uid}@{to_platform}",
            "content": content,
            "type": msg_type,
            "ts": datetime.now().isoformat(),
        }, ensure_ascii=False)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
        return True
    except Exception:
        return False
