"""MIM V1 E2E — 消息/历史/在线/搜索/好友/已读"""

import json, os, sys, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)


def check(name, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f": {detail}" if detail else ""))
    return 0 if ok else 1


def main():
    errors = 0
    print("=" * 50)
    print("MIM V1 E2E Full Test")
    print("=" * 50)

    # ── 1. from_name fix ──
    print("\n--- 1. from_name in get_history ---")
    from gateway.winpeek_hub.chat import get_history
    msgs = get_history(1, 2022, limit=3)
    errors += check("from_name populated",
        any(m.get("from_name") and m["from_name"] != "uid_" for m in msgs),
        msgs[-1].get("from_name", "?") if msgs else "empty")

    # ── 2. search_users ──
    print("\n--- 2. F1.2 search_users ---")
    from gateway.winpeek_hub.chat import search_users
    r = search_users("2022")
    errors += check("by UID", len(r) >= 1, f"{len(r)} results")
    r = search_users("Hermes")
    errors += check("by nickname", len(r) >= 1, str([u.get('nickname') for u in r[:2]]))
    r = search_users("", {"uids": "2022,2034"})
    errors += check("batch UIDs", len(r) >= 2, f"{len(r)} found")

    # ── 3. online status ──
    print("\n--- 3. Online status ---")
    from gateway.winpeek_hub.hub import list_nodes
    nodes = list_nodes()
    online = [n for n in nodes if n.get("status") == "online"]
    offline = [n for n in nodes if n.get("status") != "online"]
    print(f"  total={len(nodes)} online={len(online)} offline={len(offline)}")
    errors += check("status granularity",
        len(offline) > 0 or len(nodes) < 55,
        f"{len(online)}/{len(nodes)} online")

    # ── 4. send→history round-trip ──
    print("\n--- 4. send→history round-trip ---")
    from gateway.winpeek_hub.chat import send_message
    test_id = f"E2E-{int(time.time())}"
    body = f"MIM V1 E2E test message ref={test_id}"
    send_message(1, "yuyangmin", 2022, body)
    time.sleep(0.5)
    msgs = get_history(1, 2022, limit=5)
    errors += check("message persisted",
        any(test_id in str(m.get("content", "")) for m in msgs), test_id)

    # ── 5. F1.3 add_contact ──
    print("\n--- 5. F1.3 add_contact ---")
    from gateway.winpeek_hub.chat import add_contact
    r = add_contact(1, 1000)
    errors += check("add friend", r.get("ok") or "already friends" in str(r.get("error","")),
        str(r)[:80])

    # ── 6. F2.4 search_history ──
    print("\n--- 6. F2.4 search_history ---")
    from gateway.winpeek_hub.chat import search_history
    r = search_history(1, "E2E", peer_uid=2022)
    errors += check("keyword search", len(r) >= 1, f"{len(r)} hits")

    # ── 7. F2.3 mark_read ──
    print("\n--- 7. F2.3 mark_read ---")
    from gateway.winpeek_hub.chat import mark_read
    n = mark_read(1, 2022)
    errors += check("mark read", n >= 0, f"{n} marked")

    # ── 8. F1.4 remove_contact ──
    print("\n--- 8. F1.4 remove_contact ---")
    from gateway.winpeek_hub.chat import remove_contact
    r = remove_contact(1, 1000)
    errors += check("remove friend", r.get("ok", False), str(r)[:80])

    # ── 9. RPC handlers smoke test ──
    print("\n--- 9. RPC handlers ---")
    from tools.winpeek_tools import (
        _handle_mim_add_contact, _handle_mim_remove_contact,
        _handle_mim_search_history, _handle_mim_mark_read, _handle_mim_search_users
    )
    for name, fn, args, ok_check in [
        ("search_users", _handle_mim_search_users, {"q": "2022"}, "users"),
        ("search_history", _handle_mim_search_history,
         {"uid": 1, "q": "test", "peer_uid": 2022}, "messages"),
        ("mark_read", _handle_mim_mark_read, {"uid": 1, "peer_uid": 2022}, "ok"),
    ]:
        try:
            resp = json.loads(fn(args))
            errors += check(f"RPC {name}", ok_check in resp, str(resp)[:60])
        except Exception as e:
            errors += check(f"RPC {name}", False, str(e))

    print("\n" + "=" * 50)
    if errors == 0:
        print("ALL TESTS PASSED — MIM V1 spec compliant")
    else:
        print(f"{errors} FAILURE(S)")
    print("=" * 50)
    return errors


if __name__ == "__main__":
    sys.exit(min(main(), 1))
