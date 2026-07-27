"""MIM V1 E2E 验证 — 消息/历史/在线/搜索"""

import json, os, sys, time
# Ensure we load from hermes-agent-cc, not hermes-agent
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from datetime import datetime

def check(name, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f": {detail}" if detail else ""))
    return ok

def main():
    print("=" * 50)
    print("MIM V1 E2E Test")
    print("=" * 50)

    errors = 0

    # 1. from_name fix
    print("\n--- 1. Bugfix: from_name ---")
    from gateway.winpeek_hub.chat import get_history
    msgs = get_history(1, 2022, limit=5)
    has_name = any(m.get("from_name") and m["from_name"] != "uid_" for m in msgs)
    errors += 0 if check("from_name populated", has_name, msgs[-1].get("from_name","?") if msgs else "no msgs") else 1

    # 2. search_users
    print("\n--- 2. F1.2 search_users ---")
    from gateway.winpeek_hub.chat import search_users
    # Search by UID
    r = search_users("2022")
    errors += 0 if check("search by UID 2022", len(r) >= 1, f"found {len(r)} results") else 1
    # Search by nickname
    r = search_users("Hermes")
    errors += 0 if check("search by nickname", len(r) >= 1, str([u.get('nickname') for u in r[:3]])) else 1
    # Batch UID
    r = search_users("", {"uids": "2022,2034"})
    errors += 0 if check("batch UID search", len(r) >= 2, f"found {len(r)}") else 1

    # 3. online status (after nodes.json cleaned)
    print("\n--- 3. Online status ---")
    from gateway.winpeek_hub.hub import list_nodes
    nodes = list_nodes()
    online = [n for n in nodes if n.get("status") == "online"]
    offline = [n for n in nodes if n.get("status") != "online"]
    print(f"  total={len(nodes)} online={len(online)} offline={len(offline)}")
    errors += 0 if check("not all online", len(offline) > 0 or len(nodes) < 55,
        f"{len(online)}/{len(nodes)} online") else 1

    # 4. send → history round-trip
    print("\n--- 4. Send → History round-trip ---")
    from gateway.winpeek_hub.chat import send_message
    body = f"E2E-TEST-{int(time.time())}"
    send_message(1, "yuyangmin", 2022, body)
    time.sleep(0.5)
    msgs = get_history(1, 2022, limit=5)
    found = any(body in str(m.get("content", "")) for m in msgs)
    errors += 0 if check("send→history", found, body) else 1

    # 5. Summary
    print("\n" + "=" * 50)
    if errors == 0:
        print("ALL PASSED")
    else:
        print(f"{errors} FAILURES")
    print("=" * 50)
    return errors

if __name__ == "__main__":
    sys.exit(min(main(), 1))
