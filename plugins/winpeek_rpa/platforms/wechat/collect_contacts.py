"""
wechat_collect_contacts.py �?通讯录联系人/群采�?(Phase1/2/3)
�?op_panel.py _collect_contacts 提取, 独立可调用�?
"""
import time, re
import pyautogui
pyautogui.FAILSAFE = False

def collect_contacts(db, wx, w, enabled_types, limit=0,
                     log_func=None, set_step_func=None, running_check=None,
                     discover_func=None, update_counts_func=None):
    """采集通讯录联系人和群 �?入库 wechat_friend / wechat_group"""
    log = log_func or (lambda msg, level="INFO", ts=True: None)
    set_step = set_step_func or (lambda x: None)
    running = running_check or (lambda: True)
    discover = discover_func or (lambda msg, tag="": None)
    update_counts = update_counts_func or (lambda contacts=None: None)

    import uiautomation as auto, traceback
    from ...shared.bg_input import BGInput
    bg = BGInput("微信")

    # ── 资料读取 ──
    def read_full_profile():
        profile = {}
        nc = w.Control(AutomationId="right_v_view.nickname_button_view.display_name_text")
        if nc.Exists(): profile["nickname"] = nc.Name.strip()
        pv = w.Control(AutomationId="profile_view")
        if not pv.Exists(): return profile
        all_texts = []
        def walk(c, d=0):
            if d > 25: return
            try:
                for child in c.GetChildren():
                    n = (child.Name or "").strip()
                    ct = child.ControlTypeName or ""
                    if n and "Text" in ct: all_texts.append(n)
                    walk(child, d + 1)
            except Exception: pass
        walk(pv)
        SKIP = {"朋友资料","更多信息","朋友�?,"视频�?,"发消�?,"语音聊天","视频聊天",
                "备注","添加备注�?,"个性签�?,"来源","添加时间","共同群聊","微信号：","地区�?,}
        for i, t in enumerate(all_texts):
            nxt = all_texts[i+1] if i+1 < len(all_texts) else ""
            if "微信号：" in t and nxt: profile["wxid"] = nxt
            elif "地区�? in t and nxt: profile["region"] = nxt
            elif t == "个性签�? and nxt and nxt not in SKIP: profile["signature"] = nxt
            elif t == "来源" and nxt and nxt not in SKIP: profile["source"] = nxt
            elif t == "添加时间" and nxt and nxt not in SKIP: profile["first_met"] = nxt
            elif t == "共同群聊" and nxt and nxt not in SKIP:
                m = re.search(r'(\d+)', nxt)
                if m: profile["shared_groups"] = int(m.group(1))
        for i, t in enumerate(all_texts):
            if t == "备注" and i+1 < len(all_texts):
                v = all_texts[i+1]
                if v and v != "添加备注�?: profile["alias"] = v; break
        return profile

    if not wx.navigate_to('通讯�?):
        log("FATAL: Cannot reach Contacts page!", "ERR"); return

    # 分组配置
    groups_config = wx.get_page_groups()
    type_map = {}
    skip_groups = set()
    for group_name, ginfo in groups_config.items():
        ct = ginfo.get("contact_type", "friend")
        type_map[group_name] = ct
        if ginfo.get("skip_in_batch"): skip_groups.add(group_name)
    type_map.setdefault('新的朋友', 'new_friend')
    type_map.setdefault('群聊', 'group')
    type_map.setdefault('公众�?, 'official_account')
    type_map.setdefault('服务�?, 'service_account')
    type_map.setdefault('企业微信联系�?, 'enterprise_wechat')
    type_map.setdefault('我的企业', 'enterprise')
    type_map.setdefault('企业', 'enterprise')
    type_map.setdefault('联系�?, 'friend')
    skip_groups.add('我的企业')

    set_step("Scanning groups...")
    all_groups = wx.wait_visible_groups(timeout=2.0)
    if not all_groups:
        cl = w.Control(AutomationId='primary_table_.contact_list')
        if cl.Exists():
            clr = cl.BoundingRectangle
            pyautogui.click(clr.left+50, clr.top+30)
            for _ in range(15): bg.scroll(clr.left+50, clr.top+30, 2500, ticks=15, delay=0.03)
            all_groups = wx.wait_visible_groups(timeout=1.5)
    grp_names = [g['name'][:15] for g in all_groups]
    log(f"Groups: {len(all_groups)} ({', '.join(grp_names)}) | skip: {skip_groups}", ts=False)

    desired_groups = []
    for g in all_groups:
        if any(g['name'].startswith(s) for s in skip_groups): continue
        ctype = 'friend'
        for k, ct in type_map.items():
            if g['name'].startswith(k): ctype = ct; break
        if enabled_types.get(ctype, True): desired_groups.append(g['name'])

    opened, closed, found = wx.ensure_contact_groups(desired_groups,
        log_func=lambda msg: log(msg, ts=False))
    log(f"Door: {'ok' if found else 'FAIL'} opened={opened} closed={closed}", ts=False)

    # Door reset logic (same as original)
    if found and opened == 0:
        log("Door was already open, resetting...", "DIM", ts=False)
        cl = w.Control(AutomationId='primary_table_.contact_list')
        if cl.Exists():
            for item in cl.GetChildren():
                try:
                    gn = (item.Name or '')
                    if 'CellGroupView' in (item.ClassName or '') and gn:
                        if any(gn.startswith(d) or d.startswith(gn) for d in (desired_groups if desired_groups else ["联系�?])):
                            r = item.BoundingRectangle
                            if r.width() > 0: bg.click(r.left+40, r.top+r.height()//2); time.sleep(0.25); break
                except Exception: pass
        time.sleep(0.3)
        _o, _c, _f = wx.ensure_contact_groups(desired_groups if desired_groups else ["联系�?],
            log_func=lambda msg: log(msg, ts=False))
        log(f"Door reset: {'ok' if _f else 'FAIL'}", "OK" if _f else "WARN", ts=False)
    elif found and opened > 0:
        log("Door was closed, freshly opened", "DIM", ts=False)

    # Seen sets
    seen = set()
    seen_wxids = set()
    try:
        existing = db.list_friends()
        for f in existing:
            if f.get('nickname'): seen.add((f['nickname'].strip(), f.get('contact_type') or 'friend'))
            if f.get('wxid'): seen_wxids.add(f['wxid'])
    except Exception as e: log(f"DB pre-load failed: {e}", "WARN")
    log(f"DB: {len(existing) if 'existing' in dir() else '?'} known", ts=False)

    # FF alignment (simplified)
    total_in_group = 0
    for g in (all_groups if all_groups else []):
        gn = g.get('name', '')
        m = re.search(r'(\d+)', gn)
        if m: total_in_group = int(m.group(1)); break
    if total_in_group > 0: log(f"Group total: {total_in_group}", "DIM", ts=False)

    friend_count = sum(1 for s in seen if s[1] == 'friend')
    skip_ff = (opened > 0) or (total_in_group > 0 and total_in_group <= 30) or (friend_count >= total_in_group > 0)
    ff_scrolls = 0 if skip_ff else max(1, min(friend_count // 10, 25)) if friend_count >= 10 else 0

    # Main collection loop
    count, new_count, stall, total_pages = 0, 0, 0, 0
    current_type, watermark_name = 'friend', None
    pending_batch = []
    BATCH_SIZE = 10

    def flush_batch():
        nonlocal pending_batch
        if not pending_batch: return
        groups = [x for x in pending_batch if x[0] == 'group']
        friends = [x for x in pending_batch if x[0] != 'group']
        for _, data in groups: db.upsert_group(data)
        if friends:
            seen_in_batch = {}
            deduped = []
            for _, d in friends:
                wid = d.get('wxid', '')
                if wid and wid in seen_in_batch:
                    prev = seen_in_batch[wid]
                    log(f"  BATCH-DUP: {d.get('nickname','?')[:16]} wxid={wid} already as {prev[:16]}", "WARN", ts=False)
                    continue
                if wid: seen_in_batch[wid] = d.get('nickname', '?')
                deduped.append(d)
            ins, upd = db.batch_upsert_friends(deduped)
            grp_info = f" +{len(groups)}grp" if groups else ""
            log(f"+{ins} ins +{upd} upd{grp_info}", "BATCH")
        elif groups: log(f"+{len(groups)} groups", "BATCH")
        pending_batch = []

    # FF scrolls
    if ff_scrolls > 0:
        log(f"FF: {ff_scrolls} scrolls", "STEP", ts=False)
        cl_ff = w.Control(AutomationId='primary_table_.contact_list')
        if cl_ff.Exists():
            cr_ff = cl_ff.BoundingRectangle
            cx, cy = cr_ff.left+cr_ff.width()//2, cr_ff.top+cr_ff.height()//2
            for i in range(ff_scrolls):
                bg.scroll(cx, cy, -500, ticks=10, delay=0.04)
                time.sleep(1.5)
        time.sleep(3.0)

    for page in range(500):
        if not running(): break
        total_pages = page + 1
        set_step(f"P{page+1}")

        cl = w.Control(AutomationId='primary_table_.contact_list')
        if not cl.Exists():
            log(f"Page {page+1}: list lost", "WARN")
            if not wx.navigate_to('通讯�?): break
            time.sleep(0.5); continue

        clr = cl.BoundingRectangle
        watermark_y = 0
        if watermark_name:
            for wi in cl.GetChildren():
                try:
                    if (wi.Name or '').strip() == watermark_name:
                        wr = wi.BoundingRectangle
                        if wr.width() > 0 and wr.height() > 0: watermark_y = wr.bottom; break
                except Exception: pass

        # Phase 1: Discovery
        page_dedup = set()
        queue = []
        for item in cl.GetChildren():
            if not running(): break
            try:
                name = (item.Name or '').strip()
                cls = item.ClassName or ''
                if 'CellGroupView' in cls:
                    for k, ct in type_map.items():
                        if name.startswith(k): current_type = ct; break
                    continue
                if 'ClassifyView' in cls or 'MangerBtn' in cls or not name: continue
                if not enabled_types.get(current_type, True): continue
                r = item.BoundingRectangle
                for _ in range(5):
                    if r.width() > 0 and r.height() > 0: break
                    time.sleep(0.25); r = item.BoundingRectangle
                if r.width() == 0 or r.height() == 0: continue
                clr_page = cl.BoundingRectangle
                if r.bottom < clr_page.top or r.top > clr_page.bottom: continue
                dedup_key = (name, current_type)
                if dedup_key in seen: continue
                if r.top >= watermark_y:
                    if dedup_key not in page_dedup:
                        page_dedup.add(dedup_key); queue.append((name, current_type))
            except Exception as e: log(f"Discovery err: {e}", "ERR")

        if len(queue) > 1:
            _d = queue.pop()
            log(f"  defer last: {_d[0][:20]}", "DIM", ts=False)

        # Phase 2: Collection
        for name, ctype in queue:
            if not running(): break
            if ctype == 'group':
                pending_batch.append(('group', {'group_name': name}))
                log(f"  #{count} GROUP {name[:20]}", "OK", ts=False)
                seen.add((name, ctype)); watermark_name = name
                count += 1; new_count += 1
                if len(pending_batch) >= BATCH_SIZE: flush_batch()
                if limit > 0 and new_count >= limit: flush_batch(); update_counts(contacts=count); return
                continue

            # Friend: locate + click + read profile
            found_rect = None
            for _ in range(3):
                cl_cur = w.Control(AutomationId='primary_table_.contact_list')
                if not cl_cur.Exists(): time.sleep(0.3); continue
                for ci in cl_cur.GetChildren():
                    try:
                        if (ci.Name or '').strip() == name:
                            cr = ci.BoundingRectangle
                            if cr.width() > 0 and cr.height() > 0: found_rect = cr; break
                    except Exception: pass
                if found_rect: break
                time.sleep(0.3)
            if not found_rect: log(f"  {name[:20]} not in viewport, defer", "DIM", ts=False); continue

            bg.click(found_rect.left+30, found_rect.top+found_rect.height()//2)
            profile = {}
            poll_start = time.time()
            while True:
                profile = read_full_profile()
                if profile.get("wxid"): break
                if profile.get("nickname") == "已停用的微信用户": break
                time.sleep(0.2)
                if time.time() - poll_start > 10.0: log(f"  {name[:20]} no wxid", "WARN"); break
            if not profile.get("wxid"):
                if profile.get("nickname") == "已停用的微信用户":
                    log(f"  {name[:20]} deactivated, skip", "DIM", ts=False); seen.add((name, ctype))
                continue

            nickname = profile.get("nickname", name)
            wxid_str = profile.get("wxid", "")
            if wxid_str in seen_wxids: log(f"  #{count} {nickname[:20]} (wxid dup)", "DIM", ts=False); continue

            seen_wxids.add(wxid_str); count += 1; new_count += 1
            data = {'nickname': nickname, 'contact_type': ctype}
            if wxid_str: data['wxid'] = wxid_str
            for k in ['signature','region','phone','qq','source','first_met','alias','shared_groups']:
                if profile.get(k): data[k] = profile[k]
            pending_batch.append(('friend', data))
            log(f"  #{count} {nickname[:20]} -> {wxid_str}", "OK", ts=False)
            seen.add((name, ctype)); watermark_name = name
            if len(pending_batch) >= BATCH_SIZE: flush_batch()
            if limit > 0 and new_count >= limit: flush_batch(); update_counts(contacts=count); return
            if count % 20 == 0: update_counts(contacts=count)

        flush_batch(); update_counts(contacts=count)
        if limit > 0 and new_count >= limit: log(f"Limit reached: {new_count}", "OK"); break

        if not queue:
            stall += 1
            if stall >= 3: log(f"Bottom: 3x no new | {total_pages}p, {new_count} new", "OK"); break
            log(f"  Stall #{stall}/3...", "DIM", ts=False)
        else: stall = 0

        # Phase 3: Scroll
        cl3 = w.Control(AutomationId='primary_table_.contact_list')
        if not cl3.Exists(): continue
        clr3 = cl3.BoundingRectangle
        sx, sy = clr3.left+clr3.width()//2, clr3.top+clr3.height()//2
        set_step(f"Scroll... (new={new_count})")
        log(f"  scroll: ({sx},{sy}) -500x10", "DIM", ts=False)
        pyautogui.click(clr3.left+50, clr3.bottom-60)
        bg.scroll(sx, sy, -500, ticks=10, delay=0.03)
        for _ in range(30):
            cl_chk = w.Control(AutomationId='primary_table_.contact_list')
            if cl_chk.Exists():
                rendered = sum(1 for ci in cl_chk.GetChildren() if ci.BoundingRectangle.width() > 0)
                if rendered >= 3: break
            time.sleep(0.1)

    flush_batch()
    log(f"========== CONTACTS DONE: {count} total, {total_pages} pages ==========", "OK")
    update_counts(contacts=count)
