"""
wechat_msg_traverse.py �?遍历微信大厅+�? 活塞式采集所有会话消�?

调用�?
  op_panel.py �?collect_all_sessions() �?collect_chat_msgs()
"""

import time
import pyautogui
from .msg_collect import collect_chat_msgs


def collect_all_sessions(db, w, wx, eyes, hands, engine, brain,
                          limit=0, mode='all', log_func=None, set_step_func=None,
                          running_check=None, discover_func=None, debug_func=None):
    """遍历微信大厅+�? 活塞式从底到顶采集所有会话消息�?
    mode: 'all'|'today'|'7d'|'3h'|'incr'
    返回 (total_msgs, processed)
    """
    log = log_func or (lambda m, l="INFO", ts=True: None)
    set_step = set_step_func or (lambda s: None)
    running = running_check or (lambda: True)
    discover = discover_func or (lambda m, t="": None)
    debug = debug_func or (lambda m: None)

    t_start = time.time()
    log("========== MESSAGE COLLECTION START ==========", "STEP")

    # ── 1. 强制回微信大�? 先点微信nav退出任何门 ──
    wx.click_nav("微信"); time.sleep(0.3)
    if not wx.navigate_to('微信'):
        log("FATAL: Cannot reach WeChat", "ERR"); return 0, 0

    # ── 2. 进店验证: 确保在微信店 (3次重�? ──
    check = {}
    for retry in range(3):
        check = eyes.is_right_place()
        discover(f"Place: {check['reason']}", "DOOR")
        if check["ok"]: break
        if "聊天" in check["reason"]:
            wx.click_nav("微信"); time.sleep(0.5)
        else:
            wx.navigate_to('微信'); time.sleep(0.5)
    else:
        log(f"Not in WeChat store: {check.get('reason','?')}", "WARN"); return 0, 0

    # ── 3. 首次进店: 在门内则退出到大厅 (3次重�? ──
    for _ in range(3):
        if not check.get("door_sign"): break
        door = check["door_sign"]
        door_rect = check.get("door_rect")
        log(f"First entry in door '{door}', exit to 大厅", "DOOR")
        if door_rect:
            pyautogui.click(door_rect[0] + door_rect[2]//2, door_rect[1] + door_rect[3]//2)
            time.sleep(0.4)
        else:
            # 兜底: �?find_by_aid
            r = eyes.find_by_aid(f"session_item_{door}")
            if r: pyautogui.click(r[0]+50, r[1]+r[3]//2); time.sleep(0.4)
        check = eyes.is_right_place()
        discover(f"After exit: {check['reason']}", "DOOR")
    else:
        log("Still in door after 3 tries, re-navigate", "WARN")
        wx.navigate_to('微信'); time.sleep(0.5)

    t_verified = time.time()
    log(f"  verify: {t_verified - t_start:.1f}s", "STEP")

    # ── 4. 沉底: 一次性滑块拖到底 ──
    sl = w.Control(AutomationId='session_list')
    if not sl.Exists():
        log("session_list not found", "ERR"); return 0, 0

    ok, bottom_y = hands.scrollbar_sink(debug_func=debug)
    if ok:
        log(f"沉底: 尾行Y={bottom_y}", "OK")
    else:
        log("沉底失败", "WARN")

    t_scrolled = time.time()
    log(f"  scroll: {t_scrolled - t_verified:.1f}s", "STEP")

    # ── 5. 活塞窗口采集 ──
    total_msgs, processed, seen = 0, 0, set()
    discovered_doors = set()
    wr = w.BoundingRectangle
    CX = wr.left + 200
    PISTON_ROWS = 5
    stall = 0
    batch_num = 0

    while stall < 3:
        if not running() or (limit > 0 and processed >= limit):
            break

        batch_num += 1
        sessions = eyes.get_sessions()
        if not sessions:
            stall += 1
            log(f"[活塞 {batch_num}] 无可见会�?stall={stall}/3", "WARN")
            continue

        # 过滤已采集的
        new_items = [s for s in sessions if s['name'] not in seen]

        if not new_items:
            stall += 1
            debug(f"piston|batch={batch_num}|no_new|stall={stall}")
            log(f"[活塞 {batch_num}] 无新会话, 上翻{PISTON_ROWS}�?stall={stall}/3", "STEP")
            changed, _, _ = hands.scrollbar_nudge_up(rows=PISTON_ROWS, debug_func=debug)
            if not changed:
                debug(f"piston|batch={batch_num}|nudge_unchanged")
            time.sleep(0.15)
            continue

        stall = 0  # 有新内容 �?重置
        # �?Y 降序: 底→�?(最旧→最�?
        sorted_batch = sorted(new_items, key=lambda s: s['rect'][1] + s['rect'][3], reverse=True)
        log(f"[活塞 {batch_num}] {len(sorted_batch)}个新会话", "STEP")
        debug(f"piston|batch={batch_num}|new={len(sorted_batch)}|total_seen={len(seen)}")

        for s in sorted_batch:
            if not running() or (limit > 0 and processed >= limit):
                break
            name = s['name']
            if name in seen:
                continue

            r = s['rect']
            cy = r[1] + r[3] // 2

            is_enter_door = name in eyes._DOORS_ENTER or name in discovered_doors
            is_skip_door = name in eyes._DOORS_SKIP
            is_known_chat = engine.session_type(name) is not None

            # ── 跳过�?──
            if is_skip_door:
                log(f"  Skip door: {name}", "DOOR")
                seen.add(name); continue

            # ── 进门采集 ──
            if is_enter_door:
                log(f"  Enter door: {name}", "DOOR")
                pyautogui.click(CX, cy); time.sleep(0.4)
                door_sessions = eyes.get_sessions()
                for ds in sorted(door_sessions, key=lambda x: x['rect'][1] + x['rect'][3], reverse=True):
                    if not running() or (limit > 0 and processed >= limit): break
                    dn = ds['name']
                    if dn == name or dn in seen: continue
                    dr = ds['rect']; dcy = dr[1] + dr[3] // 2
                    set_step(f"[{processed+1}] {dn[:30]}")
                    pyautogui.click(CX, dcy); time.sleep(0.3)
                    if w.Control(AutomationId='chat_message_list').Exists():
                        contact = eyes.get_chat_title()
                        if contact and (dn[:2] == contact[:2] or dn in contact or contact in dn):
                            gid = engine.is_group(dn) if ds.get('is_group') else None
                            log(f"  [{processed+1}] {'GROUP' if gid else 'CHAT'} {dn[:25]}", "STEP", ts=False)
                            ins, dup = collect_chat_msgs(db, w, hands, dn, gid=gid, mode=mode, door=name, log_func=log, debug_func=debug)
                            total_msgs += ins; seen.add(dn); processed += 1
                    wx.click_nav("微信"); time.sleep(0.2)
                # 关门退�?
                door_r = eyes.find_by_aid(f"session_item_{name}")
                if door_r: pyautogui.click(door_r[0]+50, door_r[1]+door_r[3]//2); time.sleep(0.3)
                seen.add(name)
                continue

            # ── 已知聊天 ──
            if is_known_chat:
                t0 = time.time()
                set_step(f"[{processed+1}] {name[:30]}")
                pyautogui.click(CX, cy); time.sleep(0.3)
                contact = eyes.get_chat_title()
                if not contact or (name[:2] != contact[:2] and name not in contact and contact not in name):
                    continue
                t1 = time.time()
                gid = engine.is_group(name) if s.get('is_group') else None
                log(f"  [{processed+1}] {'GROUP' if gid else 'CHAT'} {name[:25]}", "STEP", ts=False)
                ins, dup = collect_chat_msgs(db, w, hands, name, gid=gid, mode=mode, log_func=log, debug_func=debug)
                t2 = time.time()
                total_msgs += ins; seen.add(name); processed += 1
                log(f"  open={t1-t0:.1f}s read={t2-t1:.1f}s", "STEP")
                continue

            # ── 未知: 点击试探 ──
            t0 = time.time()
            pyautogui.click(CX, cy); time.sleep(0.3)
            if w.Control(AutomationId='chat_message_list').Exists():
                contact = eyes.get_chat_title()
                if contact and (name[:2] == contact[:2] or name in contact or contact in name):
                    log(f"  [{processed+1}] CHAT {name[:25]} (new)", "STEP", ts=False)
                    ins, dup = collect_chat_msgs(db, w, hands, name, mode=mode, log_func=log, debug_func=debug)
                    total_msgs += ins; seen.add(name); processed += 1
            else:
                discovered_doors.add(name)
                seen.add(name)
                log(f"  New door discovered: {name}", "DOOR")
                wx.click_nav("微信"); time.sleep(0.2)

        # 采完一�?�?活塞上翻
        changed, _, _ = hands.scrollbar_nudge_up(rows=PISTON_ROWS, debug_func=debug)
        if not changed:
            stall += 1
            debug(f"piston|batch={batch_num}|nudge_unchanged|stall={stall}")
        time.sleep(0.15)

    # ── 6. 到顶: 把剩余到首行的全采完 ──
    sessions = eyes.get_sessions()
    remaining = [s for s in sessions if s['name'] not in seen]
    if remaining:
        log(f"到顶: {len(remaining)}个剩余会�? 补采", "STEP")
        sorted_rem = sorted(remaining, key=lambda s: s['rect'][1] + s['rect'][3], reverse=True)
        for s in sorted_rem:
            if not running() or (limit > 0 and processed >= limit): break
            name = s['name']
            if name in seen or name in eyes._DOORS_SKIP: continue
            r = s['rect']; cy = r[1] + r[3] // 2
            is_door = name in eyes._DOORS_ENTER or name in discovered_doors

            if is_door:
                pyautogui.click(CX, cy); time.sleep(0.4)
                door_sessions = eyes.get_sessions()
                for ds in sorted(door_sessions, key=lambda x: x['rect'][1] + x['rect'][3], reverse=True):
                    dn = ds['name']
                    if dn == name or dn in seen: continue
                    dr = ds['rect']; dcy = dr[1] + dr[3] // 2
                    pyautogui.click(CX, dcy); time.sleep(0.3)
                    if w.Control(AutomationId='chat_message_list').Exists():
                        contact = eyes.get_chat_title()
                        if contact and (dn[:2] == contact[:2] or dn in contact or contact in dn):
                            gid = engine.is_group(dn) if ds.get('is_group') else None
                            ins, dup = collect_chat_msgs(db, w, hands, dn, gid=gid, mode=mode, door=name, log_func=log, debug_func=debug)
                            total_msgs += ins; seen.add(dn); processed += 1
                    wx.click_nav("微信"); time.sleep(0.2)
                door_r = eyes.find_by_aid(f"session_item_{name}")
                if door_r: pyautogui.click(door_r[0]+50, door_r[1]+door_r[3]//2); time.sleep(0.3)
            else:
                pyautogui.click(CX, cy); time.sleep(0.3)
                if w.Control(AutomationId='chat_message_list').Exists():
                    contact = eyes.get_chat_title()
                    if contact and (name[:2] == contact[:2] or name in contact or contact in name):
                        ins, dup = collect_chat_msgs(db, w, hands, name, mode=mode, log_func=log, debug_func=debug)
                        total_msgs += ins; seen.add(name); processed += 1
            seen.add(name)

    t_done = time.time()
    log(f"  climb: {t_done - t_scrolled:.1f}s | total: {t_done - t_start:.1f}s", "STEP")
    log(f"========== DONE: {total_msgs} msgs from {processed} sessions ==========", "OK")
    discover(f"Done: {total_msgs} msgs from {processed} sessions", "DONE")
    return total_msgs, processed
