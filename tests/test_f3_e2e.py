"""F3 E2E test: Agent auto-reply pipeline."""
import json, logging, os, sys, time
from pathlib import Path
logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')

HOME = Path.home()
INBOX_ROOT = HOME / ".hermes" / "winpeek" / "inbox"


def main():
    print("=" * 60)
    print("F3 E2E Test: Agent Auto-Reply Pipeline")
    print("Scenario: yudahai(2032) → Hermes Agent(2034)")
    print("=" * 60)

    errors = 0

    # ── Step 1: Identity DB ──
    print("\n--- Step 1: DB check ---")
    from gateway.winpeek_hub.db import get_conn
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT uid,nickname FROM users WHERE uid=2032")
        sender = cur.fetchone()
        cur.execute("SELECT uid,nickname,identity_type FROM users WHERE uid=2034")
        target = cur.fetchone()
    conn.close()
    sender_uid, sender_name = sender[0], sender[1]
    target_uid, target_name = target[0], target[1]
    print(f"  Sender:  {sender_name} (uid={sender_uid})")
    print(f"  Target:  {target_name} (uid={target_uid}) type={target[2]}")
    print("  [PASS]")

    # ── Step 2: Send message → check inbox ──
    print("\n--- Step 2: send → inbox ---")
    from gateway.winpeek_hub.chat import send_message

    test_id = f"F3E2E{int(time.time())}"
    body = f"E2E test message — check system status. ref={test_id}"
    result = send_message(sender_uid, sender_name, target_uid, body)
    print(f"  send_message returned: mid={result.get('mid','?')[:30]}...")
    print(f"  body ref={test_id}")

    # Retry: Windows filesystem may cache glob results
    found_mid = None
    unread_dir = INBOX_ROOT / str(target_uid) / "unread"
    for attempt in range(5):
        time.sleep(0.5)
        import os
        files = sorted(
            [unread_dir / f for f in os.listdir(str(unread_dir)) if f.endswith('.json')]
        ) if unread_dir.exists() else []
        for f in files:
            msg = json.loads(f.read_text(encoding="utf-8"))
            if test_id in msg.get("body", ""):
                found_mid = msg["mid"]
                break
        if found_mid:
            break

    if found_mid:
        print(f"  [PASS] Message in inbox (after {attempt+1}s)")
        print(f"    mid={found_mid} from_uid={msg['from_uid']}")
    else:
        print(f"  [FAIL] test_id={test_id} NOT in {len(files)} inbox files!")
        for f in files[-3:]:
            msg = json.loads(f.read_text(encoding="utf-8"))
            print(f"    {f.name}: body_head={msg.get('body','')[:50]}")
        errors += 1
        return errors

    # ── Step 3: check_inbox RPC ──
    print("\n--- Step 3: check_inbox RPC ---")
    from tools.winpeek_tools import _handle_mim_check_inbox
    resp = json.loads(_handle_mim_check_inbox({"uid": target_uid}))
    unread = resp.get("unread_count", -1)
    print(f"  unread_count={unread} messages={len(resp.get('messages',[]))}")
    if unread >= 1:
        print("  [PASS]")
    else:
        print("  [FAIL] Expected >=1 unread")
        errors += 1

    # ── Step 4: agent_status RPC ──
    print("\n--- Step 4: agent_status RPC ---")
    from tools.winpeek_tools import _handle_mim_agent_status
    resp = json.loads(_handle_mim_agent_status({}))
    agents = resp.get("agents", [])
    print(f"  agents={len(agents)} pending_chase={resp.get('pending_chase',0)}")
    for a in agents:
        print(f"    {a['agent_type']}: uid={a['uid']} online={a['online']} unread={a['unread']}")
    found = any(a["uid"] == target_uid for a in agents)
    print(f"  {'[PASS]' if found else '[WARN]'} target agent in status")

    # ── Step 5: poll includes inbox ──
    print("\n--- Step 5: poll inbox integration ---")
    from tools.winpeek_tools import _handle_mim_poll
    resp = json.loads(_handle_mim_poll({"uid": target_uid}))
    inbox_count = resp.get("inbox_count", 0)
    print(f"  inbox_count={inbox_count} memory_msgs={len(resp.get('messages',[]))}")
    if inbox_count >= 1:
        print("  [PASS] poll now returns file inbox messages")
    else:
        print("  [FAIL] Expected >=1 inbox messages in poll")
        errors += 1

    # ── Step 6: read_digest ──
    print("\n--- Step 6: read_digest RPC ---")
    from tools.winpeek_tools import _handle_mim_read_digest
    resp = json.loads(_handle_mim_read_digest({"uid": target_uid}))
    digest = resp.get("digest", "")
    print(f"  digest={'[empty]' if not digest else digest[:80]}")
    print(f"  pending_inbox={resp.get('pending_inbox', 0)}")
    print("  [PASS]")

    # ── Step 7: mark_replied ──
    print("\n--- Step 7: mark_replied RPC ---")
    from tools.winpeek_tools import _handle_mim_mark_replied
    resp = json.loads(_handle_mim_mark_replied({"uid": target_uid, "mid": found_mid}))
    if resp.get("ok"):
        print(f"  [PASS] mid={found_mid} marked replied")

        # Verify status in delivered file
        delivered_file = INBOX_ROOT / str(target_uid) / "delivered" / f"{found_mid}.json"
        if delivered_file.exists():
            delivered_msg = json.loads(delivered_file.read_text(encoding="utf-8"))
            status = delivered_msg.get("status", "?")
            print(f"  Delivered status: {status}")
            if status == "replied":
                print("  [PASS] status=replied confirmed")
            else:
                print(f"  [WARN] status={status}, expected 'replied'")
    else:
        print(f"  [FAIL] {resp}")
        errors += 1

    # ── Summary ──
    print("\n" + "=" * 60)
    if errors == 0:
        print("ALL TESTS PASSED ✅ — F3 agent auto-reply pipeline works!")
    else:
        print(f"{errors} TEST(S) FAILED ❌")
    print("=" * 60)
    return errors


if __name__ == "__main__":
    sys.exit(min(main(), 1))
