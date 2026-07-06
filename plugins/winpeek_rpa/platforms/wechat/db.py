r"""
wechat_db.py — 微信数据存储 (SQLite/MySQL 双后端, 开关切换)

数据目录: %USERPROFILE%\Documents\PeekabooWin\<platform>\<userid>\

聊天模式 (对齐 WinPeek chat 表):
  私聊: from_uid → to_uid  (uid=微信号或WinPeek uid)
  群聊: gid + from_uid

DB切换: 环境变量 DB_BACKEND=mysql 或 DB_BACKEND=sqlite(默认)
  MySQL: DB_HOST=192.168.3.23 DB_USER=winpeek DB_PASS=Server33 DB_NAME=winpeek
"""
import os, sys, json, sqlite3, argparse
from pathlib import Path
from datetime import datetime

# source → source_type 映射（"来源"字段正则归类）
SOURCE_TYPE_MAP = [
    ("card_share",   "名片分享"),
    ("phone_search", "手机号"),
    ("wxid_search",  "微信号"),
    ("group_chat",   "群聊"),
    ("qr_scan",      "扫一扫"),
]


def _infer_source_type(source):
    """从 '通过XXX添加' 中文文本推断 source_type"""
    if not source:
        return None
    for code, keyword in SOURCE_TYPE_MAP:
        if keyword in source:
            return code
    return "other"

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DATA_ROOT = Path(os.environ.get("PEEKABOO_DATA_ROOT",
    Path.home() / "Documents" / "PeekabooWin"))

# ═══════════════════════════════════════════════════════
# DB 后端抽象层
# ═══════════════════════════════════════════════════════

class _SQLiteBackend:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def placeholder(self):
        return "?"

    def last_rowid(self, conn):
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


class _MySQLBackend:
    def __init__(self, host, user, password, database, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port

    def connect(self):
        import pymysql
        conn = pymysql.connect(
            host=self.host, user=self.user, password=self.password,
            database=self.database, port=self.port,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor)
        return conn

    def placeholder(self):
        return "%s"

    def last_rowid(self, conn):
        cur = conn.cursor()
        cur.execute("SELECT LAST_INSERT_ID()")
        return cur.fetchone()["LAST_INSERT_ID()"]


def _get_backend():
    """根据环境变量选择后端"""
    backend = os.environ.get("DB_BACKEND", "sqlite").lower()
    if backend == "mysql":
        return _MySQLBackend(
            host=os.environ.get("DB_HOST", "192.168.3.23"),
            user=os.environ.get("DB_USER", "winpeek"),
            password=os.environ.get("DB_PASS", "Server33"),
            database=os.environ.get("DB_NAME", "winpeek"),
            port=int(os.environ.get("DB_PORT", "3306")))
    return None  # None = SQLite (路径由 WeChatDB 决定)


# ═══════════════════════════════════════════════════════
# WeChatDB
# ═══════════════════════════════════════════════════════

class WeChatDB:
    def __init__(self, wxid="default", platform="wechat", mysql_backend=None):
        self.wxid = wxid
        self.platform = platform
        self._mysql = mysql_backend or _get_backend()

        if self._mysql:
            self.backend = self._mysql
            self.db_path = f"mysql://{self._mysql.host}/{self._mysql.database}"
        else:
            self.backend = _SQLiteBackend(DATA_ROOT / platform / wxid / "db" / f"{platform}.db")
            self.db_path = self.backend.db_path

        # 文件存储 (始终本地)
        self.data_root = DATA_ROOT / platform / wxid
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.file_dir = self.data_root / "file"
        self.attach_dir = self.data_root / "attach"
        self.file_dir.mkdir(parents=True, exist_ok=True)
        self.attach_dir.mkdir(parents=True, exist_ok=True)

    def connect(self):
        return self.backend.connect()

    def _ph(self):
        return self.backend.placeholder()

    def _last_id(self, conn):
        return self.backend.last_rowid(conn)

    def _exec(self, conn, sql, params=None):
        """兼容 SQLite(?) 和 MySQL(%s) 的占位符"""
        ph = self._ph()
        if ph != "?":
            sql = sql.replace("?", ph)
        cur = conn.cursor()
        cur.execute(sql, params or ())
        return cur

    # ═══════════════════════════════════════════════════
    # 建表
    # ═══════════════════════════════════════════════════

    def init(self):
        conn = self.connect()
        ph = self._ph()
        is_mysql = isinstance(self.backend, _MySQLBackend)

        auto = "AUTO_INCREMENT" if is_mysql else "AUTOINCREMENT"
        engine = " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4" if is_mysql else ""
        now = "CURRENT_TIMESTAMP" if is_mysql else "datetime('now','localtime')"

        sql = f"""
        CREATE TABLE IF NOT EXISTS wechat_friend (
            id          INTEGER PRIMARY KEY {auto},
            wxid        VARCHAR(128),
            nickname    VARCHAR(256) NOT NULL,
            alias       VARCHAR(256),
            contact_type VARCHAR(32) DEFAULT 'friend',
            -- friend/new_friend/group/official_account/service_account/enterprise_wechat/enterprise/starred
            is_friend   INTEGER DEFAULT 1,
            source_group VARCHAR(256),
            region      VARCHAR(128),
            phone       VARCHAR(64),
            qq          VARCHAR(64),
            avatar_url  TEXT,
            signature   TEXT,
            source      VARCHAR(64),
            source_type VARCHAR(32),
            profile_raw TEXT,
            shared_groups INTEGER DEFAULT 0,
            is_starred  INTEGER DEFAULT 0,
            tags        TEXT,
            winpeek_uid INTEGER,
            first_met   TEXT,
            updated_at  TEXT,
            created_at  TEXT DEFAULT ({now}),
            UNIQUE(wxid)
        ){engine};

        CREATE TABLE IF NOT EXISTS wechat_group (
            id          INTEGER PRIMARY KEY {auto},
            group_name  VARCHAR(256) NOT NULL,
            group_remark VARCHAR(256),
            owner_wxid  VARCHAR(128),
            member_count INTEGER DEFAULT 0,
            notice      TEXT,
            is_muted    INTEGER DEFAULT 0,
            is_saved    INTEGER DEFAULT 0,
            my_alias    VARCHAR(256),
            tags        TEXT,
            activity_score REAL DEFAULT 0,
            last_msg_time TEXT,
            created_at  TEXT DEFAULT ({now}),
            UNIQUE(group_name)
        ){engine};

        CREATE TABLE IF NOT EXISTS wechat_group_member (
            id          INTEGER PRIMARY KEY {auto},
            group_id    INTEGER,
            friend_id   INTEGER,
            nickname    VARCHAR(256),
            role        VARCHAR(32) DEFAULT 'member',
            joined_at   TEXT
        ){engine};

        CREATE TABLE IF NOT EXISTS wechat_chat (
            id          INTEGER PRIMARY KEY {auto},
            from_uid    VARCHAR(128),
            to_uid      VARCHAR(128),
            gid         VARCHAR(128),
            sender_name VARCHAR(256),
            is_from_me  INTEGER DEFAULT 0,
            msg_type    VARCHAR(32) DEFAULT 'text',
            content     TEXT,
            file_path   TEXT,
            file_name   VARCHAR(512),
            file_size   INTEGER,
            file_md5    VARCHAR(64),
            msg_ts      DATETIME,
            raw_json    TEXT,
            is_date_sep INTEGER DEFAULT 0,
            door        VARCHAR(64),
            collected_at TEXT DEFAULT ({now})
        ){engine};

        CREATE TABLE IF NOT EXISTS wechat_moment (
            id          INTEGER PRIMARY KEY {auto},
            friend_id   INTEGER,
            author_name VARCHAR(256),
            author_wxid VARCHAR(128),
            content     TEXT,
            media_type  VARCHAR(32) DEFAULT 'text',
            media_path  TEXT,
            media_urls  TEXT,
            location    VARCHAR(256),
            like_count  INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            post_time   VARCHAR(64),
            post_ts     TEXT,
            raw_json    TEXT,
            collected_at TEXT DEFAULT ({now})
        ){engine};

        CREATE TABLE IF NOT EXISTS wechat_moment_comment (
            id          INTEGER PRIMARY KEY {auto},
            moment_id   INTEGER,
            commenter   VARCHAR(256),
            content     TEXT,
            is_my_reply INTEGER DEFAULT 0,
            comment_time VARCHAR(64),
            collected_at TEXT DEFAULT ({now})
        ){engine};

        CREATE TABLE IF NOT EXISTS wechat_video (
            id          INTEGER PRIMARY KEY {auto},
            author_name VARCHAR(256),
            author_wxid VARCHAR(128),
            title       VARCHAR(512),
            description TEXT,
            video_path  TEXT,
            cover_path  TEXT,
            like_count  INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            share_count INTEGER DEFAULT 0,
            topics      TEXT,
            post_time   VARCHAR(64),
            raw_json    TEXT,
            collected_at TEXT DEFAULT ({now})
        ){engine};

        CREATE TABLE IF NOT EXISTS wechat_operation_log (
            id          INTEGER PRIMARY KEY {auto},
            operation   VARCHAR(64),
            target      VARCHAR(256),
            result      VARCHAR(32),
            detail      TEXT,
            duration_ms INTEGER,
            created_at  TEXT DEFAULT ({now})
        ){engine};
        """

        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    self._exec(conn, stmt)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"  [warn] {str(e)[:80]}")

        # 迁移：存量表可能缺少 source_type 列
        try:
            self._exec(conn,
                "ALTER TABLE wechat_friend ADD COLUMN source_type VARCHAR(32)")
        except Exception:
            pass  # 列已存在

        # 迁移：存量表可能缺少 door 列
        try:
            self._exec(conn,
                "ALTER TABLE wechat_chat ADD COLUMN door VARCHAR(64)")
        except Exception:
            pass  # 列已存在

        # 索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_friend_wxid ON wechat_friend(wxid)",
            "CREATE INDEX IF NOT EXISTS idx_friend_nick ON wechat_friend(nickname)",
            "CREATE INDEX IF NOT EXISTS idx_friend_isfriend ON wechat_friend(is_friend)",
            "CREATE INDEX IF NOT EXISTS idx_chat_from ON wechat_chat(from_uid)",
            "CREATE INDEX IF NOT EXISTS idx_chat_to ON wechat_chat(to_uid)",
            "CREATE INDEX IF NOT EXISTS idx_chat_gid ON wechat_chat(gid)",
            "CREATE INDEX IF NOT EXISTS idx_chat_type ON wechat_chat(msg_type)",
            "CREATE INDEX IF NOT EXISTS idx_groupmember_gid ON wechat_group_member(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_moment_friend ON wechat_moment(friend_id)",
            "CREATE INDEX IF NOT EXISTS idx_moment_author ON wechat_moment(author_wxid)",
            "CREATE INDEX IF NOT EXISTS idx_video_author ON wechat_video(author_wxid)",
        ]
        if isinstance(self.backend, _MySQLBackend):
            indexes = [i.replace("IF NOT EXISTS", "") for i in indexes]

        for idx_sql in indexes:
            try:
                self._exec(conn, idx_sql)
            except Exception:
                pass

        conn.commit()
        conn.close()
        return True

    # ═══════════════════════════════════════════════════
    # CRUD: 联系人 (is_friend)
    # ═══════════════════════════════════════════════════

    def upsert_friend(self, data):
        # 自动推断 source_type
        if data.get("source"):
            data["source_type"] = _infer_source_type(data["source"])

        conn = self.connect()
        existing = None
        if data.get("wxid"):
            cur = self._exec(conn, "SELECT id FROM wechat_friend WHERE wxid=?", (data["wxid"],))
            existing = cur.fetchone()

        if existing:
            fid = existing["id"] if isinstance(existing, dict) else existing[0]
            fields = ["nickname","contact_type","alias","region","phone","qq","avatar_url",
                      "signature","source","source_type","profile_raw","shared_groups",
                      "is_starred","tags","is_friend","first_met","source_group","winpeek_uid"]
            sets = [f"{f}=?" for f in fields if f in data]
            vals = [data[f] for f in fields if f in data]
            if vals:
                vals.append(datetime.now().isoformat())
                sets.append("updated_at=?")
                vals.append(fid)
                self._exec(conn, f"UPDATE wechat_friend SET {','.join(sets)} WHERE id=?", vals)
                conn.commit()
            conn.close()
            return fid

        fields = ["wxid","nickname","contact_type","alias","region","phone","qq","avatar_url",
                  "signature","source","source_type","profile_raw","shared_groups",
                  "is_starred","tags","is_friend","source_group","winpeek_uid","first_met"]
        available = {f: data[f] for f in fields if f in data}
        available.setdefault("is_friend", 1)
        available.setdefault("first_met", datetime.now().isoformat())
        available.setdefault("updated_at", datetime.now().isoformat())

        cols = ",".join(available.keys())
        phs = ",".join(["?"] * len(available))
        self._exec(conn,
            f"INSERT INTO wechat_friend ({cols}) VALUES ({phs})",
            list(available.values()))
        conn.commit()
        fid = self._last_id(conn)
        conn.close()
        return fid

    def batch_upsert_friends(self, friends_list):
        """批量写入联系人 — 单事务，避免每条 connect+commit。

        Args:
            friends_list: list of dict，每条同 upsert_friend 的 data 格式
        Returns:
            (inserted_count, updated_count)
        """
        if not friends_list:
            return (0, 0)
        conn = self.connect()
        inserted, updated = 0, 0
        now = datetime.now().isoformat()
        try:
            for data in friends_list:
                # 自动推断 source_type
                if data.get("source"):
                    data["source_type"] = _infer_source_type(data["source"])

                existing = None
                if data.get("wxid"):
                    cur = self._exec(conn,
                        "SELECT id FROM wechat_friend WHERE wxid=?", (data["wxid"],))
                    existing = cur.fetchone()

                if existing:
                    fid = existing["id"] if isinstance(existing, dict) else existing[0]
                    fields = ["nickname","contact_type","alias","region","phone","qq",
                              "avatar_url","signature","source","source_type","profile_raw",
                              "shared_groups","is_starred","tags","is_friend",
                              "first_met","source_group","winpeek_uid"]
                    sets = [f"{f}=?" for f in fields if f in data]
                    vals = [data[f] for f in fields if f in data]
                    if vals:
                        vals.append(now)
                        sets.append("updated_at=?")
                        vals.append(fid)
                        self._exec(conn,
                            f"UPDATE wechat_friend SET {','.join(sets)} WHERE id=?", vals)
                    updated += 1
                else:
                    fields = ["wxid","nickname","contact_type","alias","region","phone",
                              "qq","avatar_url","signature","source","source_type","profile_raw",
                              "shared_groups","is_starred","tags","is_friend",
                              "source_group","winpeek_uid","first_met"]
                    available = {f: data[f] for f in fields if f in data}
                    available.setdefault("is_friend", 1)
                    available.setdefault("first_met", now)
                    available.setdefault("updated_at", now)
                    cols = ",".join(available.keys())
                    phs = ",".join(["?"] * len(available))
                    self._exec(conn,
                        f"INSERT INTO wechat_friend ({cols}) VALUES ({phs})",
                        list(available.values()))
                    inserted += 1
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return (inserted, updated)

    def get_last_collected(self, limit=1):
        """获取最后采集的N个联系人 — 用于接力插入。

        返回最近采集的 friend 类型联系人的 nickname 列表 (最新在前)。
        过滤 fallback 脏数据（如 "昵称: XXX"）。
        """
        conn = self.connect()
        cur = self._exec(conn,
            f"SELECT nickname FROM wechat_friend WHERE nickname IS NOT NULL "
            "AND contact_type = 'friend' "
            "AND nickname NOT LIKE ? AND nickname NOT LIKE ? "
            f"ORDER BY id DESC LIMIT {int(limit)}",
            ('昵称:%', 'nickname:%'))
        rows = cur.fetchall()
        conn.close()
        names = [r["nickname"] for r in rows]
        if limit == 1:
            return names[0] if names else None
        return names

    def get_friend(self, wxid_or_name):
        conn = self.connect()
        cur = self._exec(conn,
            "SELECT * FROM wechat_friend WHERE wxid=? OR nickname=? OR alias=? LIMIT 1",
            (wxid_or_name, wxid_or_name, wxid_or_name))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_friends(self, is_friend=None):
        conn = self.connect()
        if is_friend is not None:
            cur = self._exec(conn,
                "SELECT id,wxid,nickname,is_friend,region,phone,source_group,shared_groups,winpeek_uid,updated_at FROM wechat_friend WHERE is_friend=? ORDER BY updated_at DESC",
                (is_friend,))
        else:
            cur = self._exec(conn,
                "SELECT id,wxid,nickname,is_friend,region,phone,source_group,shared_groups,winpeek_uid,updated_at FROM wechat_friend ORDER BY is_friend DESC, updated_at DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    # ═══════════════════════════════════════════════════
    # CRUD: 群
    # ═══════════════════════════════════════════════════

    def upsert_group(self, data):
        conn = self.connect()
        cur = self._exec(conn, "SELECT id FROM wechat_group WHERE group_name=?", (data["group_name"],))
        existing = cur.fetchone()

        if existing:
            gid = existing["id"] if isinstance(existing, dict) else existing[0]
            fields = ["group_remark","owner_wxid","member_count","notice",
                      "is_muted","is_saved","my_alias","tags","activity_score","last_msg_time"]
            sets = [f"{f}=?" for f in fields if f in data]
            vals = [data[f] for f in fields if f in data]
            if vals:
                vals.append(gid)
                self._exec(conn, f"UPDATE wechat_group SET {','.join(sets)} WHERE id=?", vals)
                conn.commit()
        else:
            fields = ["group_name","group_remark","owner_wxid","member_count",
                      "notice","is_muted","is_saved","my_alias","tags","activity_score","last_msg_time"]
            available = {f: data[f] for f in fields if f in data}
            cols = ",".join(available.keys())
            phs = ",".join(["?"] * len(available))
            self._exec(conn,
                f"INSERT INTO wechat_group ({cols}) VALUES ({phs})",
                list(available.values()))
            conn.commit()
            gid = self._last_id(conn)
        conn.close()
        return gid

    # ═══════════════════════════════════════════════════
    # CRUD: 消息 (from_uid → to_uid | gid)
    # ═══════════════════════════════════════════════════

    def insert_message(self, data):
        conn = self.connect()
        fields = ["from_uid","to_uid","gid","sender_name","is_from_me","msg_type",
                  "content","file_path","file_name","file_size","file_md5",
                  "msg_ts","raw_json","is_date_sep","door"]
        # DATETIME 不接受空串 → None
        if data.get('msg_ts') == '':
            data['msg_ts'] = None
        available = {f: data[f] for f in fields if f in data}
        cols = ",".join(available.keys())
        phs = ",".join(["?"] * len(available))
        self._exec(conn,
            f"INSERT INTO wechat_chat ({cols}) VALUES ({phs})",
            list(available.values()))
        conn.commit()
        conn.close()

    def get_last_msg_time(self, from_uid=None, gid=None):
        """获取最新消息时间 (msg_ts DATETIME)"""
        conn = self.connect()
        if from_uid:
            cur = self._exec(conn,
                "SELECT MAX(msg_ts) as ts FROM wechat_chat WHERE (from_uid=? OR to_uid=?) AND is_date_sep=1 AND msg_ts IS NOT NULL",
                (from_uid, from_uid))
        elif gid:
            cur = self._exec(conn,
                "SELECT MAX(msg_ts) as ts FROM wechat_chat WHERE gid=? AND is_date_sep=1 AND msg_ts IS NOT NULL",
                (gid,))
        else:
            conn.close(); return None
        row = cur.fetchone()
        conn.close()
        if row and row['ts']:
            t = row['ts']
            return t.isoformat() if hasattr(t, 'isoformat') else str(t)
        return None

    def get_last_msg_ts(self, from_uid=None, gid=None):
        conn = self.connect()
        if from_uid:
            cur = self._exec(conn,
                "SELECT msg_ts FROM wechat_chat WHERE (from_uid=? OR to_uid=?) AND is_date_sep=0 ORDER BY id DESC LIMIT 1",
                (from_uid, from_uid))
        elif gid:
            cur = self._exec(conn,
                "SELECT msg_ts FROM wechat_chat WHERE gid=? AND is_date_sep=0 ORDER BY id DESC LIMIT 1",
                (gid,))
        else:
            conn.close(); return None
        row = cur.fetchone()
        conn.close()
        return row["msg_ts"] if row else None

    def message_exists(self, content, msg_ts, friend_id=None, group_id=None):
        conn = self.connect()
        if friend_id:
            cur = self._exec(conn,
                "SELECT 1 FROM wechat_chat WHERE content=? AND msg_ts=? AND (from_uid=? OR to_uid=?) LIMIT 1",
                (content, msg_ts, friend_id, friend_id))
        elif group_id:
            cur = self._exec(conn,
                "SELECT 1 FROM wechat_chat WHERE content=? AND msg_ts=? AND gid=? LIMIT 1",
                (content, msg_ts, group_id))
        else:
            conn.close(); return False
        exists = cur.fetchone() is not None
        conn.close()
        return exists

    def list_messages(self, from_uid=None, gid=None, limit=50, offset=0):
        conn = self.connect()
        if from_uid:
            cur = self._exec(conn,
                "SELECT * FROM wechat_chat WHERE from_uid=? OR to_uid=? ORDER BY id ASC LIMIT ? OFFSET ?",
                (from_uid, from_uid, limit, offset))
        elif gid:
            cur = self._exec(conn,
                "SELECT * FROM wechat_chat WHERE gid=? ORDER BY id ASC LIMIT ? OFFSET ?",
                (gid, limit, offset))
        else:
            conn.close(); return []
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    # ═══════════════════════════════════════════════════
    # 朋友圈/视频号
    # ═══════════════════════════════════════════════════

    def insert_moment(self, data):
        conn = self.connect()
        cur = self._exec(conn,
            "SELECT 1 FROM wechat_moment WHERE author_wxid=? AND content LIKE ? AND post_time=? LIMIT 1",
            (data.get("author_wxid",""), (data.get("content","")[:60] + "%"), data.get("post_time","")))
        if cur.fetchone():
            conn.close(); return None

        fields = ["friend_id","author_name","author_wxid","content","media_type",
                  "media_path","media_urls","location","like_count","comment_count",
                  "post_time","post_ts","raw_json"]
        available = {f: data[f] for f in fields if f in data}
        cols = ",".join(available.keys())
        phs = ",".join(["?"] * len(available))
        self._exec(conn,
            f"INSERT INTO wechat_moment ({cols}) VALUES ({phs})",
            list(available.values()))
        conn.commit()
        mid = self._last_id(conn)
        conn.close()
        return mid

    def insert_video(self, data):
        conn = self.connect()
        cur = self._exec(conn,
            "SELECT 1 FROM wechat_video WHERE author_wxid=? AND title=? LIMIT 1",
            (data.get("author_wxid",""), data.get("title","")))
        if cur.fetchone():
            conn.close(); return None

        fields = ["author_name","author_wxid","title","description","video_path",
                  "cover_path","like_count","comment_count","share_count","topics",
                  "post_time","raw_json"]
        available = {f: data[f] for f in fields if f in data}
        cols = ",".join(available.keys())
        phs = ",".join(["?"] * len(available))
        self._exec(conn,
            f"INSERT INTO wechat_video ({cols}) VALUES ({phs})",
            list(available.values()))
        conn.commit()
        vid = self._last_id(conn)
        conn.close()
        return vid

    # ═══════════════════════════════════════════════════
    # 统计
    # ═══════════════════════════════════════════════════

    def stats(self):
        conn = self.connect()
        def q(sql):
            cur = self._exec(conn, sql)
            row = cur.fetchone()
            if isinstance(row, dict):
                return list(row.values())[0]
            return row[0]
        friends = q("SELECT COUNT(*) FROM wechat_friend WHERE is_friend=1")
        strangers = q("SELECT COUNT(*) FROM wechat_friend WHERE is_friend=0")
        groups = q("SELECT COUNT(*) FROM wechat_group")
        chats = q("SELECT COUNT(*) FROM wechat_chat")
        moments = q("SELECT COUNT(*) FROM wechat_moment")
        videos = q("SELECT COUNT(*) FROM wechat_video")
        files = q("SELECT COUNT(*) FROM wechat_chat WHERE file_path IS NOT NULL")
        conn.close()
        return {
            "platform": self.platform,
            "backend": "mysql" if self._mysql else "sqlite",
            "db_path": str(self.db_path),
            "friends": friends, "strangers": strangers, "groups": groups,
            "messages": chats, "moments": moments, "videos": videos, "files": files,
            "data_root": str(self.data_root),
        }


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="微信数据管理 (SQLite/MySQL)")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--wxid", default="szyuyangmin")
    parser.add_argument("--platform", default="wechat")
    parser.add_argument("--backend", choices=["sqlite","mysql"], default=None)
    parser.add_argument("--list-friends", action="store_true")
    parser.add_argument("--list-messages", action="store_true")
    parser.add_argument("--friend", help="联系人过滤")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    if args.backend == "mysql":
        os.environ["DB_BACKEND"] = "mysql"

    db = WeChatDB(wxid=args.wxid, platform=args.platform)

    if args.init:
        db.init()
        print(f"✅ 数据库已初始化: {db.db_path}")
        return

    if args.list_friends:
        friends = db.list_friends()
        print(f"联系人 ({len(friends)}):")
        for f in friends:
            tag = "👤好友" if f.get("is_friend") else "👽陌生人"
            print(f"  {tag} {f.get('nickname','')[:30]}  wxid={f.get('wxid','')}  群={f.get('source_group','')}")

    if args.list_messages:
        fid = None
        if args.friend:
            friend = db.get_friend(args.friend)
            if friend:
                fid = friend.get("wxid")
        msgs = db.list_messages(from_uid=fid, limit=args.limit)
        for m in msgs:
            tag = "📅" if m.get("is_date_sep") else "💬"
            print(f"  {tag} [{m.get('msg_time','')}] {m.get('sender_name','')}: {(m.get('content') or '')[:80]}")

    if args.stats:
        s = db.stats()
        print(f"后端: {s['backend']}  数据库: {s['db_path']}")
        print(f"好友: {s['friends']}  陌生人: {s['strangers']}  群聊: {s['groups']}")
        print(f"消息: {s['messages']}  朋友圈: {s['moments']}  视频号: {s['videos']}  附件: {s['files']}")
        print(f"数据目录: {s['data_root']}")


if __name__ == "__main__":
    main()
