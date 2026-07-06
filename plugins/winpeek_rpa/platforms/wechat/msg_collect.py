"""
wechat_msg_collect.py �?读单个微信会话的消息 (时间分组)

规则:
  1. 每个时间行作为段落起�? 后续非时间行属于同一时间�?
  2. 同组多段落用 \n 拼接 �?一条DB记录
  3. PageDown到底 �?PageUp翻到�?(底部Y不变=到顶)
  4. 去重: (�?时间) 唯一
  5. 老时间先入库 (时间正序)

collect_chat_msgs() �?独立功能: 给参数就读取
"""

import time, re, json
import pyautogui
pyautogui.FAILSAFE = False
from ...shared.rpa_tools import parse_chat_time


def collect_chat_msgs(db, w, hands, session_name, gid=None, max_pages=80,
                      mode='all', door=None, log_func=None, debug_func=None):
    """读单个会话消�?�?入库 wechat_chat�?
    WeChat 打开聊天即在最新消�?�?PageUp 采集旧消息�?

    mode:
      'all'    �?全量 (一�?PageUp 到顶)
      'today'  �?当天
      '7d'     �?最�?�?
      '3h'     �?最�?小时
      'incr'   �?增量 (从DB取上次最后时�?
    door: 所属门, None=大厅
    返回 (inserted, skipped_dup)
    """
    import ctypes
    from datetime import datetime, timedelta
    log = log_func or (lambda m, l="INFO": None)
    debug = debug_func or (lambda m: None)
    t0 = time.time()

    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    AID_MSG = 'chat_message_list'

    # ── 截止时间 ──
    now = datetime.now()
    if mode == 'today':
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif mode == '7d':
        cutoff = now - timedelta(days=7)
    elif mode == '3h':
        cutoff = now - timedelta(hours=3)
    elif mode == 'incr':
        last = db.get_last_msg_time(gid=gid) if gid else db.get_last_msg_time(from_uid=session_name)
        cutoff = datetime.fromisoformat(last) if last else None
    else:  # 'all'
        cutoff = None

    # ── 翻页: WeChat打开在最新消�? PageUp逐页上翻采集旧消�?──
    hands.focus_msg_area()

    # ── 采集所有消�?�?时间分组 ──
    groups = []       # [{time, iso, texts:[str], is_from_me}, ...]
    seen = set()
    current_group = None
    stopped = False
    pages_read = 0
    prev_bottom = None

    for pg in range(max_pages):
        ml = w.Control(AutomationId=AID_MSG)
        if not ml.Exists(): break

        items = []
        page_bottom = 0
        for item in ml.GetChildren():
            try:
                text = (item.Name or "").strip()
                if not text: continue
                r = item.BoundingRectangle
                aid = item.AutomationId or ""
                items.append({"text": text, "aid": aid, "y": r.top, "bottom": r.bottom,
                              "left": r.left, "is_date": not aid,
                              "is_bubble": "chat_bubble_item_view" in aid})
                if r.bottom > page_bottom:
                    page_bottom = r.bottom
            except Exception: pass

        # ── 到顶判断: Y不同=有新内容, Y相同才比内容 ──
        if prev_bottom is not None and page_bottom == prev_bottom:
            new_on_page = sum(1 for it in items if it["text"] not in seen)
            if new_on_page == 0: break
        prev_bottom = page_bottom

        for it in items:
            if it["text"] in seen: continue
            seen.add(it["text"])

            parsed = parse_chat_time(it["text"])
            if parsed:
                # 非全量模�? 碰到超时日期 �?停止翻页
                if cutoff and parsed < cutoff:
                    stopped = True; break
                if current_group and current_group["texts"]:
                    groups.append(current_group)
                current_group = {"time": it["text"], "iso": parsed, "texts": [], "y": it["y"]}
                continue

            if current_group is None:
                current_group = {"time": "", "iso": None, "texts": [], "y": it["y"]}
            is_from_me = it["is_bubble"] and it["left"] > (screen_w - 100)
            current_group["is_from_me"] = is_from_me
            current_group["texts"].append(it["text"])

        pages_read += 1
        if stopped: break
        hands.page_up()

    # 提交最后一�?
    if current_group and current_group["texts"]:
        groups.append(current_group)

    # ── 入库: 时间正序, 去重 ──
    groups.sort(key=lambda g: g.get("iso") or g.get("time", ""))
    ins, dup = 0, 0
    for g in groups:
        iso = g["iso"] or parse_chat_time(g["time"])
        content = "\n".join(g["texts"])
        if not content.strip(): continue

        is_mine = g.get("is_from_me", False)
        md = {
            "content": content, "msg_type": "text",
            "msg_ts": iso, "is_date_sep": 0,
            "raw_json": json.dumps({"group_time": g["time"], "segments": len(g["texts"])}, ensure_ascii=False),
        }
        if door:
            md["door"] = door
        if gid:
            md["gid"] = gid
            md["sender_name"] = "yuyangmin" if is_mine else ""
            md["is_from_me"] = 1 if is_mine else 0
        else:
            wxid = db.wxid
            md["from_uid"] = wxid if is_mine else session_name
            md["to_uid"] = session_name if is_mine else wxid
            md["sender_name"] = "yuyangmin" if is_mine else session_name
            md["is_from_me"] = 1 if is_mine else 0

        if iso and db.message_exists(content[:100], str(iso),
                group_id=gid, friend_id=md.get("from_uid","") if not gid else None):
            dup += 1; continue
        db.insert_message(md)
        ins += 1

    elapsed = time.time() - t0
    log(f"  done {ins}msgs {dup}dup {pages_read}pages in {elapsed:.1f}s", "STEP")
    return ins, dup


