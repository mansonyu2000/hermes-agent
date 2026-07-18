"""
MIM 功能清单管理工具
用法:
  python manage_features.py --init           # 建表 + 导入 JSON 数据
  python manage_features.py --query "status='todo' AND module LIKE '%群聊%'"   # 查询
  python manage_features.py --update F4.1 status=done                         # 更新
  python manage_features.py --done F4.1     # 快捷标记完成
"""
import json, os, sys, argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
from gateway.winpeek_hub.db import get_conn

JSON_PATH = os.path.join(os.path.dirname(__file__), '..', 'website', 'docs', 'winpeek', 'mim-design', 'feature-inventory.json')

def init():
    """建表 + 导入 JSON 数据"""
    conn = get_conn()
    if not conn:
        print("❌ MySQL 连接失败")
        return
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mim_feature_inventory (
                id VARCHAR(10) NOT NULL PRIMARY KEY,
                module VARCHAR(32) NOT NULL, feature VARCHAR(64) NOT NULL,
                sub TEXT NULL, deps VARCHAR(255) NULL,
                status ENUM('done','todo','skip') NOT NULL DEFAULT 'todo',
                priority ENUM('P0','P1','P2','P3') NOT NULL DEFAULT 'P3',
                decision VARCHAR(32) NULL, assignee VARCHAR(64) NULL,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_module(module), INDEX idx_status(status),
                INDEX idx_priority(priority), INDEX idx_decision(decision)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='MIM功能清单'
        """)
        conn.commit()

        with open(JSON_PATH, encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for item in data:
            prio = 'P3'
            dec = item.get('decision', '')
            if 'P0' in dec: prio = 'P0'
            elif 'P1' in dec: prio = 'P1'
            elif 'P2' in dec: prio = 'P2'

            cur.execute(
                "INSERT INTO mim_feature_inventory (id,module,feature,sub,deps,status,priority,decision,assignee) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE module=VALUES(module),feature=VALUES(feature),sub=VALUES(sub),"
                "deps=VALUES(deps),status=VALUES(status),priority=VALUES(priority),decision=VALUES(decision)",
                (item['id'], item['module'], item['feature'], item.get('sub', ''),
                 item.get('deps', ''), item.get('status', 'todo'), prio, dec, item.get('assignee', ''))
            )
            count += 1
        conn.commit()
        print(f"✅ 导入 {count} 条功能记录")
    conn.close()

def query(where=""):
    conn = get_conn()
    if not conn: return
    sql = f"SELECT id, module, feature, priority, status, decision, deps FROM mim_feature_inventory"
    if where: sql += f" WHERE {where}"
    sql += " ORDER BY module, id"
    with conn.cursor() as cur:
        cur.execute(sql)
        for row in cur.fetchall():
            print(f"{row['id']} [{row['priority']}] [{row['status'].upper():4}] {row['module']}/{row['feature']} | {row['decision']}")
        print(f"\n--- {cur.rowcount} results ---")
    conn.close()

def update(fid, **kwargs):
    conn = get_conn()
    if not conn: return
    sets = ", ".join(f"{k}=%s" for k in kwargs)
    cur = conn.cursor()
    cur.execute(f"UPDATE mim_feature_inventory SET {sets} WHERE id=%s", list(kwargs.values()) + [fid])
    conn.commit()
    print(f"✅ {fid} updated: {kwargs}")
    conn.close()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--init', action='store_true')
    p.add_argument('--query', type=str, default='')
    p.add_argument('--update', type=str)
    p.add_argument('--done', type=str, help='快捷标记完成')
    args = p.parse_args()

    if args.init:
        init()
    elif args.done:
        update(args.done, status='done')
    elif args.update:
        kv = dict(kv.split('=') for kv in args.update.split(','))
        # 需要 id 作为第一个参数
        fid = kv.pop('id', args.update.split(',')[0].split('=')[1])
        # 实际：--update "F4.1,status=done"
        parts = args.update.split(',')
        fid = parts[0]
        kvs = dict(p.split('=') for p in parts[1:])
        update(fid, **kvs)
    else:
        query(args.query)
