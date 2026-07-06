"""
wechat_api.py �?微信自动化三层架�?

🧠 LLM �?👁�?eyes �?�?决策 �?🤖 hands 执行 �?💾 engine 入库
每层只做一件事。输入→输出，无副作用（�?hands 层）�?

参数约定:
  rect = (left, top, width, height)  �?UIA BoundingRectangle
  session = {name, aid, unread, is_pinned, is_muted, rect, raw}
"""
import time, re, json
import pyautogui
pyautogui.FAILSAFE = False
from ...shared.rpa_tools import parse_session_item
from ...shared.config import config as _cfg


# ══════════════════════════════════════════════════════�?
# 👁�?眼睛�?
# ══════════════════════════════════════════════════════�?

class WeChatEyes:
    """感知微信窗口。纯�? 不写, 不操作�?""

    def __init__(self, w):
        self.w = w

    def get_sessions(self):
        """�?[{name, aid, unread, is_pinned, rect:(l,t,w,h), raw}, ...] 按Y排序"""
        sl = self.w.Control(AutomationId='session_list')
        if not sl.Exists():
            return []
        out = []
        for item in sl.GetChildren():
            try:
                aid = item.AutomationId or ""
                if not aid.startswith('session_item_'): continue
                raw_name = (item.Name or "").strip()
                info = parse_session_item(aid, raw_name)
                if not info["name"] or info["name"] in ('群聊', '消息免打�?): continue
                r = item.BoundingRectangle
                if r.width() <= 0 or r.height() <= 0: continue
                info["aid"] = aid
                info["rect"] = (r.left, r.top, r.width(), r.height())
                info["raw"] = raw_name
                out.append(info)
            except Exception:
                pass
        out.sort(key=lambda x: x["rect"][1])  # �?Y 排序
        return out

    def get_messages(self):
        """�?[{content, msg_type, is_from_me, time, rect:(l,t,w,h)}, ...] 按Y排序"""
        import ctypes
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        ml = self.w.Control(AutomationId='chat_message_list')
        if not ml.Exists():
            return []
        items = []
        for item in ml.GetChildren():
            try:
                text = (item.Name or "").strip()
                if not text: continue
                aid = item.AutomationId or ""
                r = item.BoundingRectangle
                is_date = not aid
                is_bubble = "chat_bubble_item_view" in aid
                is_from_me = is_bubble and r.left > (screen_w - 100)
                items.append({
                    "content": text,
                    "msg_type": "text",
                    "is_from_me": is_from_me,
                    "is_date": is_date,
                    "is_bubble": is_bubble,
                    "aid": aid,
                    "rect": (r.left, r.top, r.width(), r.height()),
                })
            except Exception:
                pass
        items.sort(key=lambda x: x["rect"][1])
        return items

    def get_chat_title(self):
        """�?'张三' or None"""
        ctrl = self.w.Control(AutomationId=(
            "content_view.top_content_view.title_h_view.left_v_view"
            ".left_content_v_view.left_ui_.big_title_line_h_view"
            ".current_chat_name_label"))
        if ctrl.Exists():
            return (ctrl.Name or "").strip()
        return None

    # 🚪 门分�?�?点击可展开/折叠, 门内有子项可采集
    _DOORS_ENTER = {'服务�?, '群聊', '折叠的聊�?, '群助�?, '微信游戏'}  # 进门采集
    _DOORS_SKIP = {'公众�?}   # 公众号是文章链接, 暂不采集
    _WRONG_DOORS = _DOORS_ENTER | _DOORS_SKIP  # 兼容旧引�?

    def is_right_place(self):
        """验证在微信店(一级菜�?�?�?{ok, reason, door_sign, door_rect, first_names}

        ok=False: 在聊天窗�?/ session_list不存�?
        ok=True:  在微信店 (仅大厅OK)
        门头不在session_list中时无法检�? 靠调用方先点微信nav保证在大�?
        """
        sl = self.w.Control(AutomationId='session_list')
        if not sl.Exists():
            if self.w.Control(AutomationId='chat_message_list').Exists():
                return {"ok": False, "reason": "在聊天窗�?, "door_sign": None, "door_rect": None, "first_names": []}
            return {"ok": False, "reason": "session_list不存�?, "door_sign": None, "door_rect": None, "first_names": []}

        first_names, door_sign, door_rect = [], None, None
        for item in sl.GetChildren():
            aid = item.AutomationId or ""
            if not aid.startswith('session_item_'): continue
            name = aid.replace('session_item_', '', 1)
            if name == '消息免打�?: continue
            first_names.append(name)
            if name in self._WRONG_DOORS:
                door_sign = name
                try:
                    r = item.BoundingRectangle
                    if r.width() > 0:
                        door_rect = (r.left, r.top, r.width(), r.height())
                except Exception: pass
                break

        if not first_names:
            return {"ok": False, "reason": "无可见会�?, "door_sign": None, "door_rect": None, "first_names": []}

        if door_sign:
            return {"ok": True, "reason": f"微信店·门「{door_sign}�?, "door_sign": door_sign, "door_rect": door_rect, "first_names": first_names[:5]}
        return {"ok": True, "reason": "微信店·大�?, "door_sign": None, "door_rect": None, "first_names": first_names[:5]}

    def get_current_page(self):
        """�?'微信' | '通讯�? | '聊天' | None"""
        if self.w.Control(AutomationId='session_list').Exists():
            return '微信'
        if self.w.Control(AutomationId='primary_table_.contact_list').Exists():
            return '通讯�?
        if self.w.Control(AutomationId='chat_message_list').Exists():
            return '聊天'
        return None

    def find_session(self, name):
        """在可见列表中按名找会�?�?{name, aid, rect} or None"""
        for s in self.get_sessions():
            if s["name"] == name:
                return s
        return None

    def find_by_aid(self, aid):
        """�?AutomationId 在session_list中定�?�?rect or None"""
        sl = self.w.Control(AutomationId='session_list')
        if not sl.Exists(): return None
        for item in sl.GetChildren():
            try:
                if (item.AutomationId or "") == aid:
                    r = item.BoundingRectangle
                    if r.width() > 0 and r.height() > 0:
                        return (r.left, r.top, r.width(), r.height())
            except Exception:
                pass
        return None


# ══════════════════════════════════════════════════════�?
# 🤖 手层
# ══════════════════════════════════════════════════════�?

class WeChatHands:
    """操作微信。全�?bg_input 后台输入。返�?bool�?""

    def __init__(self, bg, wx, w):
        self.bg = bg
        self.wx = wx
        self.w = w

    # ── 启动自校�?(TECHNICAL.md §8.2) ──

    def calibrate(self, log_func=None):
        """启动自检: 测所有关键点�?�?{点位�? ok/fail, ...}"""
        log = log_func or (lambda m: None)
        wr = self.w.BoundingRectangle
        points = {
            "首行":    (wr.left + self._LIST_CX, self._list_top()),
            "尾行":    (wr.left + self._LIST_CX, self._list_bottom()),
            "搜索�?:  (wr.left + 190, wr.top + 60),
            "导航微信": (wr.left + 30, wr.top + 114),
            "导航通讯�?: (wr.left + 30, wr.top + 162),
            "最小化":  (wr.right - 100, wr.top + 16),
            "关闭":    (wr.right - 20, wr.top + 16),
            "消息�?:  (wr.left + wr.width() // 3, wr.bottom - 60),
            "发送键":  (wr.right - 50, wr.bottom - 35),
            "更多选项": (wr.right - 35, wr.top + 35),
        }
        # 中间�?
        usable_h = self._list_bottom() - self._list_top()
        mid_idx = max(0, usable_h // self._SESSION_H // 2)
        mid_y = self._list_top() + mid_idx * self._SESSION_H
        points[f"中间�?{mid_idx})"] = (wr.left + self._LIST_CX, mid_y)

        report = {}
        log("=== Calibration Start ===")
        for name, (cx, cy) in points.items():
            try:
                pyautogui.moveTo(cx, cy, duration=0.02)
                time.sleep(0.05)
                # 简单检�? 窗口还在�?
                ok = self.w.Exists()
                report[name] = {"pos": (cx, cy), "ok": ok}
                log(f"  {name}: ({cx},{cy}) �?{'OK' if ok else 'FAIL'}")
            except Exception as e:
                report[name] = {"pos": (cx, cy), "ok": False, "err": str(e)}
                log(f"  {name}: ({cx},{cy}) �?ERR {e}")
        log("=== Calibration Done ===")
        return report

    def _safe_center(self, rect, margin=15):
        """计算安全中心�?(远离边界 margin px) �?(x, y)"""
        x, y, w, h = rect
        cx = x + max(margin, min(w // 2, w - margin))
        cy = y + max(margin, min(h // 2, h - margin))
        return cx, cy

    def _in_bounds(self, rect, win_margin=20):
        """检查矩形是否在窗口安全区内"""
        wr = self.w.BoundingRectangle
        x, y, w, h = rect
        return (x >= wr.left + win_margin and
                y >= wr.top + win_margin and
                x + w <= wr.left + wr.width() - win_margin and
                y + h <= wr.top + wr.height() - win_margin)

    def click_rect(self, rect):
        """点击矩形安全中心 �?bool"""
        cx, cy = self._safe_center(rect)
        self.bg.click(cx, cy)
        time.sleep(0.15)
        return True

    def click_session(self, session):
        """点击会话 �?bool"""
        r = session["rect"]
        cx, cy = self._safe_center(r)
        self.bg.click(cx, cy)
        time.sleep(0.3)
        return True

    def click_nav(self, name):
        """点击左侧导航 �?bool"""
        self.wx.click_nav(name)
        time.sleep(0.3)
        return True

    def scroll_sessions(self, amount=-2000):
        """会话列表滚轮 �?鼠标移到列表�? 不点�? 直接�?(点中会话反而坏�?"""
        sl = self.w.Control(AutomationId='session_list')
        if not sl.Exists(): return False
        r = sl.BoundingRectangle
        pyautogui.moveTo(r.left + 100, r.top + r.height() // 2, duration=0.05)
        pyautogui.scroll(amount)
        time.sleep(0.2)
        return True

    # ── 活塞沉底 + 步进上翻 ──

    def scrollbar_sink(self, debug_func=None):
        """拖滑块匀速沉�?�?(ok, bottom_y)
        从轨道顶拖到轨道�? 一次到�? 不做预检, 直接�?
        """
        debug = debug_func or (lambda m: None)
        sl = self.w.Control(AutomationId='session_list')
        if not sl.Exists(): return False, 0
        r = sl.BoundingRectangle

        sb_x = r.right - 5
        track_top = r.top + 10
        track_bottom = r.bottom - 10
        debug(f"sink|drag|track=({sb_x},{track_top})�?{sb_x},{track_bottom})|1.2s")
        pyautogui.moveTo(sb_x, track_top, duration=0.05)
        time.sleep(0.05)
        pyautogui.mouseDown()
        pyautogui.moveTo(sb_x, track_bottom, duration=1.2)
        pyautogui.mouseUp()
        time.sleep(0.3)

        items = list(sl.GetChildren())
        new_bottom_y = max((it.BoundingRectangle.bottom for it in items if it.BoundingRectangle.bottom > 0), default=0)
        debug(f"sink|done|bottom_y={new_bottom_y}")
        return True, new_bottom_y

    def scrollbar_nudge_up(self, rows=5, debug_func=None):
        """拖滑块上�?~rows 行（活塞一步）�?(changed, before_top_y, after_top_y)
        �?session_list 控件内操�? 不碰窗口边界
        """
        debug = debug_func or (lambda m: None)
        sl = self.w.Control(AutomationId='session_list')
        if not sl.Exists(): return False, 0, 0
        r = sl.BoundingRectangle

        # 取当前可见首�?top
        items = list(sl.GetChildren())
        before_top_y = min((it.BoundingRectangle.top for it in items if it.BoundingRectangle.top > 0), default=0)

        # 计算拖拽距离: 轨道高的 rows/est_total 比例
        track_top = r.top + 10
        track_bottom = r.bottom - 10           # session_list 控件�? 不碰窗口
        track_height = track_bottom - track_top
        est_total = max(len(items), 14)
        drag_px = min(track_height * rows / est_total, track_height * 0.15)
        drag_px = max(drag_px, 10)
        duration = max(drag_px * 0.004, 0.1)

        sb_x = r.right - 5
        start_y = track_bottom                 # 沉底后滑块在轨道�?
        end_y = max(start_y - drag_px, track_top)

        debug(f"nudge_up|rows={rows}|drag={drag_px:.0f}px|dur={duration:.2f}s|{start_y}→{end_y}")
        pyautogui.moveTo(sb_x, start_y, duration=0.03)
        time.sleep(0.03)
        pyautogui.mouseDown()
        pyautogui.moveTo(sb_x, end_y, duration=duration)
        pyautogui.mouseUp()
        time.sleep(0.2)

        items2 = list(sl.GetChildren())
        after_top_y = min((it.BoundingRectangle.top for it in items2 if it.BoundingRectangle.top > 0), default=0)
        changed = abs(after_top_y - before_top_y) > 5 if before_top_y > 0 else False
        debug(f"nudge_up|result|before={before_top_y}|after={after_top_y}|changed={changed}")
        return changed, before_top_y, after_top_y

    # ── 校准辅助 ──
    _SESSION_H = 65
    _LIST_CX = 200

    def _list_top(self):
        """会话列表首行 Y"""
        sl = self.w.Control(AutomationId='session_list')
        if sl.Exists():
            return sl.BoundingRectangle.top + 15
        wr = self.w.BoundingRectangle
        return wr.top + 95

    def _list_bottom(self):
        """会话列表尾行 Y"""
        sl = self.w.Control(AutomationId='session_list')
        if sl.Exists():
            return sl.BoundingRectangle.bottom - self._SESSION_H
        wr = self.w.BoundingRectangle
        return wr.bottom - 60

    def page_up(self, times=1):
        """PageUp �?bool"""
        for _ in range(times):
            pyautogui.press("pageup")
            time.sleep(0.3)
        return True

    def focus_msg_area(self):
        """点聊天区获焦�? �?PageUp 生效 �?bool
        聊天区中�? (窗口�?�?2/3, 窗口�?60)  �?右侧聊天面板
        """
        wr = self.w.BoundingRectangle
        cx = wr.left + wr.width() * 2 // 3
        cy = wr.bottom - 60
        pyautogui.click(cx, cy)
        time.sleep(0.2)
        return True

    def click_send_button(self):
        """点发送按�?(窗口�?50, 窗口�?35) �?bool"""
        wr = self.w.BoundingRectangle
        pyautogui.click(wr.right - 50, wr.bottom - 35)
        time.sleep(0.1)
        return True

    def click_more_options(self):
        """点更多选项 (右上�? x-35, y+35) �?bool"""
        wr = self.w.BoundingRectangle
        pyautogui.click(wr.right - 35, wr.top + 35)
        time.sleep(0.1)
        return True

    def move_to(self, rect):
        """移动鼠标到指定位�?�?bool"""
        x, y, w, h = rect
        pyautogui.moveTo(x + w // 2, y + h // 2, duration=0.02)
        return True

    def right_click_menu(self, rect, menu_text, match_mode="contains"):
        """右键点击 �?弹出菜单 �?点击菜单�?�?bool
        rect: 右键点击位置 (x,y,w,h)
        menu_text: 菜单项文�? �?'移出「折叠的聊天�?
        """
        x, y, w, h = rect
        pyautogui.rightClick(x + w // 2, y + h // 2)
        time.sleep(0.3)
        # �?UIA 找弹出菜�?
        import uiautomation as auto
        menu = auto.MenuControl(Name='')
        found = None
        for _ in range(5):
            for m in auto.GetRootControl().GetChildren():
                try:
                    if m.ControlTypeName == 'MenuControl' or 'Menu' in (m.ClassName or ''):
                        for item in m.GetChildren():
                            name = (item.Name or '').strip()
                            if match_mode == 'contains' and menu_text in name:
                                found = item; break
                            elif match_mode == 'exact' and name == menu_text:
                                found = item; break
                    if found: break
                except: pass
            if found: break
            time.sleep(0.1)
        if found:
            try: found.Click(); time.sleep(0.2); return True
            except: pass
        # fallback: pyautogui 坐标估算
        pyautogui.click(x + w // 2 + 60, y + h // 2 + 30)
        time.sleep(0.2)
        return True


# ══════════════════════════════════════════════════════�?
# 💾 机械�?
# ══════════════════════════════════════════════════════�?

class WeChatEngine:
    """消息采集引擎。调 eyes+hands, �?db�?""

    def __init__(self, db, eyes, hands, w, log_func=print):
        self.db = db
        self.eyes = eyes
        self.hands = hands
        self.w = w
        self.log = log_func

    def is_group(self, name):
        """�?gid or None"""
        try:
            conn = self.db.connect()
            cur = self.db._exec(conn, "SELECT id FROM wechat_group WHERE group_name=?", (name,))
            row = cur.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception:
            return None

    def session_type(self, name):
        """�?'friend' | 'group' | None
        None = 公众�?服务�?未入�?�?跳过不采
        """
        if self.is_group(name):
            return 'group'
        f = self.db.get_friend(name)
        if f:
            return 'friend'
        return None  # 公众�?服务�?未入�?�?全部跳过

    def msg_count_db(self, name):
        """�?该会话已有消息数"""
        try:
            conn = self.db.connect()
            cur = self.db._exec(conn,
                "SELECT COUNT(*) FROM wechat_chat WHERE from_uid=? OR to_uid=? OR gid IN (SELECT id FROM wechat_group WHERE group_name=?)",
                (name, name, name))
            row = cur.fetchone()
            conn.close()
            return row[0] if row else 0
        except Exception:
            return 0

    def collect_msgs(self, session_name, max_pages=80, incremental=True):
        """爬楼梯式采集: 底部→点5行→采集→上翻→重复→到顶结�?""
        import ctypes
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        AID_MSG = 'chat_message_list'
        gid = self.is_group(session_name)

        last_local_time = None
        if incremental:
            if gid:
                last_local_time = self.db.get_last_msg_time(gid=gid)
            else:
                last_local_time = self.db.get_last_msg_time(from_uid=session_name)
            if last_local_time:
                self.log(f"    📅 local latest: {last_local_time}")

        # 获焦�?
        self.hands.focus_msg_area()

        buffer, seen, current_time = [], set(), ""
        prev_bottom_y = None
        stopped = False

        for pg in range(max_pages):
            ml = self.w.Control(AutomationId=AID_MSG)
            if not ml.Exists(): break
            mr = ml.BoundingRectangle

            # 读当前可见消�?�?按Y排序
            items = []
            for item in ml.GetChildren():
                try:
                    text = (item.Name or "").strip()
                    if not text: continue
                    aid = item.AutomationId or ""
                    r = item.BoundingRectangle
                    items.append((text, aid, r, not aid, "chat_bubble_item_view" in aid))
                except Exception: pass
            items.sort(key=lambda x: x[2].top)
            if not items: break

            # 🛑 到底检�? 底部Y没变 �?到顶�?
            bottom_y = items[-1][2].bottom
            if prev_bottom_y is not None and bottom_y == prev_bottom_y:
                break
            prev_bottom_y = bottom_y

            # 点底�?�?(激活消�? 确保加载)
            for _, _, r, _, _ in items[-5:]:
                pyautogui.click(r.left + 30, r.top + r.height() // 2)
                time.sleep(0.05)

            # 采集本页消息
            new_in_page = 0
            for text, aid, r, is_date, is_bubble in items:
                key = (text[:60], r.top)
                if key in seen: continue
                seen.add(key)

                if is_date:
                    current_time = text
                    if last_local_time:
                        iso = _parse_msg_time(text)
                        if iso and iso <= last_local_time:
                            stopped = True; break
                    continue

                is_from_me = is_bubble and r.left > (screen_w - 100)
                msg_ts = _parse_msg_time(current_time) if current_time else None

                md = {
                    "content": text, "msg_type": "text",
                    "msg_ts": msg_ts,
                    "is_date_sep": 0, "time_key": msg_ts or current_time,
                    "raw_json": json.dumps({"y": r.top, "aid": aid}, ensure_ascii=False),
                }
                if gid:
                    md.update({"gid": gid, "sender_name": "yuyangmin" if is_from_me else "",
                               "is_from_me": 1 if is_from_me else 0})
                else:
                    wxid = self.db.wxid
                    md.update({"from_uid": wxid if is_from_me else session_name,
                               "to_uid": session_name if is_from_me else wxid,
                               "sender_name": "yuyangmin" if is_from_me else session_name,
                               "is_from_me": 1 if is_from_me else 0})
                if "ChatBubbleReferItemView" in aid and "图片" in text:
                    md["msg_type"] = "image"
                elif text.startswith("文件\n"):
                    md["msg_type"] = "file"
                    ls = text.split("\n")
                    if len(ls) >= 2: md["file_name"] = ls[1]; md["content"] = ls[1]
                elif "[链接]" in text:
                    md["msg_type"] = "link"

                buffer.append(md)
                new_in_page += 1

            if stopped:
                self.log(f"    [p{pg+1}] +{new_in_page} �?hit local time")
                break

            # 🪜 上翻5�?(PageUp)
            self.hands.page_up()

        # 入库去重
        ins, dup = 0, 0
        if buffer:
            buffer.sort(key=lambda m: m.get("time_key", ""))
            for md in buffer:
                md.pop("time_key", None)
                c, t, gv, fu = md.get("content",""), md.get("msg_ts"), md.get("gid"), md.get("from_uid","")
                if t and self.db.message_exists(c, str(t), group_id=gv, friend_id=fu if not gv else None):
                    dup += 1; continue
                self.db.insert_message(md)
                ins += 1
            self.log(f"    💾 {ins} ins +{dup} dup �?wechat_chat")
        return ins, dup


from ...shared.rpa_tools import parse_chat_time as _parse_msg_time


# ══════════════════════════════════════════════════════�?
# 快捷工厂
# ══════════════════════════════════════════════════════�?

# ══════════════════════════════════════════════════════�?
# 🧠 大脑�?�?LLM 调用封装
# ══════════════════════════════════════════════════════�?

class Brain:
    """LLM 大脑调用。需要判断的事情发过�? 返回结构化答案�?

    LLM 选型原则:
      �?s 能搞定的 �?RPA 自己解决
      >2s 或不确定 �?LLM 兜底

    用法:
      brain = Brain(log_func=print)
      result = brain.ask('is_right_door', visible_items=str(names))
    """

    _OLLAMA_URL = _cfg.ollama_url
    _DEFAULT_MODEL = _cfg.default_model

    def __init__(self, log_func=print, prompts_path=None,
                 ollama_url=None, default_model=None):
        self.log = log_func
        self.ollama_url = ollama_url or self._OLLAMA_URL
        self.default_model = default_model or self._DEFAULT_MODEL
        self._timeout_s = _cfg.llm_timeout_s
        self._templates = self._load_templates(prompts_path)
        self._has_llm = self._probe_llm()

    def _load_templates(self, path=None):
        """�?brain_prompts.json 加载提示词模�?""
        if path is None:
            import os
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brain_prompts.json")
        try:
            import json
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 过滤掉以 _ 开头的元数�?
            return {k: v for k, v in data.items() if not k.startswith('_')}
        except Exception as e:
            self.log(f"  ⚠️ Failed to load prompts: {e}")
            return {}

    def _probe_llm(self):
        """快速探�?Ollama 是否可达 �?bool"""
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.ollama_url}/api/tags")
            urllib.request.urlopen(req, timeout=3)
            return True
        except Exception:
            return False

    @property
    def has_llm(self):
        """LLM 是否可用"""
        return self._has_llm

    def ask(self, template_name, **kwargs):
        """�?LLM �?返回结构化答案。无 LLM 时返回机械默认值�?
        template_name: 'is_right_door' | 'prioritize_sessions' | 'is_important' | ...
        kwargs: 填充模板中的 {变量}
        """
        tmpl = self._templates.get(template_name, {})
        prompt = tmpl.get("prompt", template_name)
        fmt = tmpl.get("format", "text")

        # 变量替换
        for k, v in kwargs.items():
            prompt = prompt.replace("{" + k + "}", str(v))

        if not self._has_llm:
            self.log(f"  �?[{template_name}] (no LLM) {prompt[:60]}...")
            return self._default_answer(template_name, fmt)

        self.log(f"  🧠 [{template_name}] {prompt[:80]}...")
        try:
            import urllib.request
            payload = json.dumps({
                "model": self.default_model,
                "prompt": prompt,
                "format": fmt if fmt == "json" else None,
                "stream": False,
            }).encode('utf-8')
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read().decode('utf-8')).get("response", "")
            if fmt == "json":
                try: return json.loads(result)
                except json.JSONDecodeError: return {}
            return result
        except Exception as e:
            self.log(f"  ⚠️ LLM failed: {e}")
            return self._default_answer(template_name, fmt)

    def _default_answer(self, template_name, answer_format):
        """机械默认答案 �?�?LLM 时的兜底"""
        if answer_format == "json":
            if template_name == 'is_right_door':
                return {"door": "不确�?, "action": "unsure", "reason": "无LLM"}
            return {}
        if answer_format == "yesno": return True
        return ""

    @property
    def templates(self):
        """对外暴露: 所有可用模板名 �?编辑/显示"""
        return list(self._templates.keys())

    def template_info(self, name):
        """对外暴露: 查看某个模板的完整内�?""
        return self._templates.get(name, {})

    def prioritize(self, sessions):
        """🎯 决策: 给定会话列表, 返回处理顺序�?
        当前用机械规�?免费). �?LLM: return self.ask('prioritize_sessions', sessions=str(sessions))"""
        # 机械规则: 未读>置顶>未读�?
        return sorted(sessions,
            key=lambda s: (s.get('unread', 0) > 0, s.get('is_pinned', False), s.get('unread', 0)),
            reverse=True)
        # �?LLM: return self.ask('prioritize_sessions', sessions=json.dumps(sessions, ensure_ascii=False))


def create(w, db, bg, wx, log_func=print):
    """一键创建四层对�?""
    eyes = WeChatEyes(w)
    hands = WeChatHands(bg, wx, w)
    engine = WeChatEngine(db, eyes, hands, w, log_func)
    brain = Brain(log_func)
    return eyes, hands, engine, brain
