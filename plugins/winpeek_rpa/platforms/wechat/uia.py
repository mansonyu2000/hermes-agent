"""
wechat-uia.py �?微信桌面 UIA 操作�?

基于 Windows UIA COM (uiautomation) 直达微信 Qt 控件�?
零坐标依赖，窗口缩放/移动不失效�?

用法:
  python wechat-uia.py                         # 侦察模式
  python wechat-uia.py --find "联系�?          # 搜索打开联系�?
  python wechat-uia.py --send "消息"            # 发消�?
  python wechat-uia.py --click-nav "通讯�?     # 点导航按�?
  python wechat-uia.py --read 10               # 读最近消�?
  python wechat-uia.py --contact               # 显示当前联系�?

作为库使�?
  from .uia import WeChatUIA
  w = WeChatUIA()
  w.send("hello")
  print(w.get_current_contact())
"""
import sys
import os
import json
import time
import argparse
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import uiautomation as auto
import pyautogui
pyautogui.FAILSAFE = False
import pyperclip

from ...shared.position_memory import PositionMemory


# ── 已知的微�?UIA AutomationId (稳定，跨版本不变) ──
AID = {
    "input_box":    "chat_input_field",
    "chat_page":    "chat_message_page",
    "nav_tabbar":   "MainView.main_tabbar",
    "chat_name":    ("content_view.top_content_view.title_h_view.left_v_view"
                     ".left_content_v_view.left_ui_.big_title_line_h_view"
                     ".current_chat_name_label"),
    "handoff":      "MainView.main_tabbar.tabbar_handoff",
    "setting":      "MainView.main_tabbar.tabbar_setting",
    "voip":         "voip_button",
    "more":         ("content_view.top_content_view.title_h_view.right_v_view"
                     ".right_content_h_view.right_content_v_view.right_ui_"
                     ".more_button"),
    "msg_list":     "chat_message_list",
    "msg_bubble":   "chat_message_list.qt_scrollarea_viewport.chat_bubble_item_view",
}

# 导航按钮名称映射 (中文 �?�?tabbar 中的索引)
NAV_BUTTONS = ["微信", "通讯�?, "收藏", "朋友�?, "视频�?, "搜一�?, "游戏中心", "小程序面�?]


class WeChatUIA:
    """微信桌面 UIA 操作封装 �?含导航地�?+ 位置记忆"""

    def __init__(self, auto_focus=True, load_memory=True,
                 nav_map_path=None, wxid=None):
        self._win = None
        self._wxid = wxid or os.environ.get("WECHAT_WXID", "default")

        # 加载导航地图（声明式知识——理论）
        self.nav_map = self._load_nav_map(nav_map_path)

        # 动态构�?PAGE_MAP（兼容旧格式�?
        self.PAGE_MAP = self._build_page_map()

        # 加载像素锚点地图（兜底定位——布局规律�?
        self.pixel_anchors = self._load_pixel_anchors()

        # 加载位置记忆（经验知识——越用越准）
        self._memory = None
        if load_memory:
            try:
                self._memory = PositionMemory(wxid=self._wxid)
            except Exception:
                pass

        if auto_focus:
            self.focus()

    # ── 窗口管理 ──

    def focus(self):
        """找到微信窗口并激活，返回 self"""
        self._win = auto.WindowControl(Name="微信")
        if not self._win.Exists(maxSearchSeconds=3):
            raise RuntimeError("找不到微信窗口，请确认微信已打开")
        try:
            self._win.SetFocus()
            time.sleep(0.2)
        except Exception:
            pass
        return self

    def is_active(self):
        """检查微信窗口是否存�?""
        if self._win is None:
            self._win = auto.WindowControl(Name="微信")
        return self._win.Exists()

    def get_bounds(self):
        """获取窗口尺寸 (width, height)"""
        r = self._win.BoundingRectangle
        return r.width(), r.height()

    # ── 元素定位 ──

    def get_element(self, automation_id):
        """�?AutomationId 获取控件，找不到返回 None"""
        ctrl = self._win.Control(AutomationId=automation_id)
        if ctrl.Exists():
            return ctrl
        return None

    def wait_element(self, automation_id, timeout=5):
        """等待元素出现"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            ctrl = self.get_element(automation_id)
            if ctrl:
                return ctrl
            time.sleep(0.3)
        return None

    def list_elements(self):
        """侦察模式：列出所有关键元素及其状�?""
        bounds = self.get_bounds()
        print(f"🔍 微信 UIA 元素 (窗口 {bounds[0]}x{bounds[1]}):\n")

        items = [
            ("输入�?,       AID["input_box"]),
            ("聊天�?,       AID["chat_page"]),
            ("联系人标�?,   AID["chat_name"]),
            ("导航�?,       AID["nav_tabbar"]),
            ("语音通话",     AID["voip"]),
            ("更多按钮",     AID["more"]),
        ]
        for label, aid in items:
            ctrl = self.get_element(aid)
            if ctrl:
                try:
                    r = ctrl.BoundingRectangle
                    extra = f"「{ctrl.Name}�? if ctrl.Name else ""
                    print(f"  �?{label:<10} ({r.left},{r.top}) {r.width()}x{r.height()} {extra}")
                except Exception:
                    print(f"  �?{label:<10} (存在)")
            else:
                print(f"  �?{label:<10} 未找�?)

        # 导航按钮
        navbar = self.get_element(AID["nav_tabbar"])
        if navbar:
            print(f"\n  🧭 导航按钮:")
            for btn in navbar.GetChildren():
                try:
                    if btn.Name:
                        print(f"      [{btn.Name}]")
                except Exception:
                    pass

    # ── 消息操作 ──

    def send(self, text):
        """UIA 直通发送消息（不走剪贴板，不占焦点�?""
        inp = self.get_element(AID["input_box"])
        if not inp:
            print("�?找不到输入框")
            return False

        try:
            inp.Click()
            time.sleep(0.05)
            inp.SendKeys("{Ctrl}a{Delete}")
            time.sleep(0.05)
            inp.SendKeys(text)
            time.sleep(0.05)
            inp.SendKeys("{Enter}")
            return True
        except Exception as e:
            print(f"   ⚠️ UIA SendKeys 失败: {e}")

        return self.send_clipboard(text)

    def send_clipboard(self, text):
        """剪贴板回退方案：pyautogui + pyperclip"""
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.press("delete")
        time.sleep(0.05)
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)
        pyautogui.press("enter")
        return True

    # ── 联系�?──

    def get_current_contact(self):
        """获取当前聊天窗口的联系人名称"""
        ctrl = self.get_element(AID["chat_name"])
        if ctrl:
            return ctrl.Name
        return None

    def search_contact(self, name):
        """搜索并打开联系人：Ctrl+F �?粘贴 �?Enter"""
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.3)
        pyperclip.copy(name)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(0.5)

        current = self.get_current_contact()
        return current

    # ── 导航（状态感�?+ 地图 + 记忆）──

    def _load_nav_map(self, path=None):
        """加载 nav_map.json 导航地图�?""
        if path is None:
            path = Path(__file__).parent / "nav_map.json"
        if not Path(path).exists():
            # 退化为最小地图（只有已验证的两个页面�?
            return {
                "pages": {
                    "wechat_main": {"name": "微信", "nav_button": "微信",
                        "verify": {"uia": {"automation_id": "session_list"}}},
                    "contacts_main": {"name": "通讯�?, "nav_button": "通讯�?,
                        "verify": {"uia": {"automation_id": "primary_table_.contact_list"}}},
                },
                "contacts_groups": {},
            }
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_page_map(self):
        """�?nav_map 构建 PAGE_MAP dict（兼容旧格式）�?
        格式: {page_name: (nav_button, verify_aid)}
        """
        result = {}
        for page_id, info in self.nav_map.get("pages", {}).items():
            name = info.get("name", page_id)
            nav_btn = info.get("nav_button", name)
            verify = info.get("verify", {})
            uia = verify.get("uia", {}) if verify else {}
            verify_aid = uia.get("automation_id") if uia else None
            if verify_aid:
                result[name] = (nav_btn, verify_aid)
        return result

    def _load_pixel_anchors(self, path=None):
        """加载 pixel_anchors.json 像素锚点地图（兜底定位）�?""
        if path is None:
            path = Path(__file__).parent / "pixel_anchors.json"
        if not Path(path).exists():
            return {"nav_buttons": {"buttons": []}, "contacts_groups": {"groups": []}}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def click_nav(self, name):
        """点击导航栏按钮（底层点击，不验证�?""
        import pyautogui
        navbar = self.get_element(AID["nav_tabbar"])
        if not navbar:
            return False

        for btn in navbar.GetChildren():
            try:
                if btn.Name == name:
                    r = btn.BoundingRectangle
                    # 左偏10px防止点到右侧会话列表
                    pyautogui.click(r.left + r.width()//2 - 10, r.top + r.height()//2)
                    time.sleep(0.3)
                    return True
            except Exception:
                continue
        return False

    def get_current_page(self):
        """检测当前在哪个页面。UIA 优先，回退到记忆�?

        原理：检查各页面的特�?UIA 元素是否可见�?
        不和导航按钮状态耦合——按钮可能被遮挡/渲染延迟�?
        """
        # Tier 1: UIA 检测（快，可靠�?
        for page_name, (nav_btn, verify_aid) in self.PAGE_MAP.items():
            if verify_aid is None:
                continue
            try:
                el = self._win.Control(AutomationId=verify_aid)
                if el.Exists():
                    r = el.BoundingRectangle
                    if r.width() > 0 and r.height() > 0:
                        return page_name
            except Exception:
                continue

        # Tier 2: 位置记忆回退（中等速度�?
        if self._memory:
            self._memory.load()
            for page_id, info in self.nav_map.get("pages", {}).items():
                name = info.get("name", page_id)
                prefix = f"{page_id}::"
                for key in self._memory._records:
                    if key.startswith(prefix):
                        entries = self._memory._records[key]
                        if entries and any(
                            e.get("confidence", 0) > 0.5 for e in entries
                        ):
                            return name

        # Tier 3: 像素锚点兜底（UIA + 窗口区域检测）
        pixel_result = self.detect_by_pixel()
        if pixel_result:
            return pixel_result

        return None

    def navigate_to(self, target, max_retries=3):
        """导航到目标页面。知道当前在哪、要去哪、到了没�?

        成功后自动记录导航位置到记忆（自学习）�?
        """
        import pyautogui

        if target not in self.PAGE_MAP:
            return self.click_nav(target)

        for attempt in range(max_retries):
            current = self.get_current_page()
            if current == target:
                return True

            nav_btn, verify_aid = self.PAGE_MAP[target]

            # 尝试 UIA 点击，失败则像素锚点兜底
            clicked = self.click_nav(nav_btn)
            if not clicked:
                clicked = self.click_nav_by_pixel(nav_btn)
            if not clicked:
                time.sleep(0.5)
                continue

            # 验证到达
            time.sleep(0.5)
            for _ in range(10):
                if self.get_current_page() == target:
                    self._record_nav_success(target)
                    return True
                time.sleep(0.3)

        return self.get_current_page() == target

    def _record_nav_success(self, page_name):
        """记录导航成功位置到记忆（自学习）�?""
        if not self._memory:
            return
        try:
            page_id = self._page_name_to_id(page_name)
            nav_btn_name = self.PAGE_MAP.get(page_name, (page_name,))[0]
            navbar = self.get_element(AID["nav_tabbar"])
            if navbar:
                bw, bh = self.get_bounds()
                for btn in navbar.GetChildren():
                    try:
                        if btn.Name == nav_btn_name:
                            r = btn.BoundingRectangle
                            cx = r.left + r.width() // 2
                            cy = r.top + r.height() // 2
                            self._memory.remember(
                                page_id=page_id,
                                element_id=f"nav_button_{nav_btn_name}",
                                x=cx, y=cy,
                                window_w=bw, window_h=bh,
                                action="navigate_to",
                                automation_id=AID["nav_tabbar"]
                            )
                            break
                    except Exception:
                        continue
        except Exception:
            pass

    def record_click(self, page_name, element_id, x, y,
                     automation_id=None, fingerprint=None):
        """记录成功点击位置到记忆（�?op_panel 等调用）�?""
        if not self._memory:
            return
        try:
            bw, bh = self.get_bounds()
            page_id = self._page_name_to_id(page_name)
            self._memory.remember(
                page_id=page_id,
                element_id=element_id,
                x=x, y=y,
                window_w=bw, window_h=bh,
                action="click",
                automation_id=automation_id,
                fingerprint=fingerprint,
            )
        except Exception:
            pass

    def recall_position(self, page_name, element_id, min_confidence=0.3):
        """回忆已记住的元素位置。返�?{x, y, xPct, yPct, confidence, ...} �?None�?""
        if not self._memory:
            return None
        try:
            bw, bh = self.get_bounds()
            page_id = self._page_name_to_id(page_name)
            return self._memory.recall(
                page_id=page_id,
                element_id=element_id,
                window_w=bw, window_h=bh,
                min_confidence=min_confidence,
            )
        except Exception:
            return None

    def save_memory(self):
        """持久化位置记忆到磁盘。应在任务结束时调用�?""
        if self._memory:
            try:
                self._memory.save()
            except Exception:
                pass

    def get_page_groups(self):
        """�?nav_map 获取通讯录分组配置�?
        返回 {group_name: {contact_type, skip_in_batch, ...}}
        """
        return self.nav_map.get("contacts_groups", {})

    def _page_name_to_id(self, page_name):
        """中文页面�?�?nav_map page_id�?""
        for pid, info in self.nav_map.get("pages", {}).items():
            if info.get("name") == page_name:
                return pid
        return page_name

    # ── 像素锚点兜底（UIA 失败时的最后手段）──

    def click_nav_by_pixel(self, name):
        """像素坐标兜底点击导航按钮。不依赖 UIA，用锚点地图的已知坐标�?""
        import pyautogui
        buttons = self.pixel_anchors.get("nav_buttons", {}).get("buttons", [])
        for btn in buttons:
            if btn.get("name") == name:
                r = self._win.BoundingRectangle
                abs_x = r.left + btn["center_x"]
                abs_y = r.top + btn["center_y_rel"]
                pyautogui.click(abs_x, abs_y)
                time.sleep(0.3)
                return True
        return False

    def detect_by_pixel(self):
        """像素区域检测：判断 col2 区域（x=60-300）是否有通讯录列表或会话列表�?

        策略：检查窗口宽度——如�?col2 存在（w>=360），尝试检测其中内容�?
        这是 UIA 完全失效时的最后兜底方案�?
        返回页面名或 None�?
        """
        try:
            r = self._win.BoundingRectangle
            # col2 消失 = 窗口太窄，无法判�?
            if r.width() < 360:
                return None

            # col2 区域中心�?
            col2_cx = r.left + 60 + 120   # col2 x_start=60, half_width=120
            col2_cy = r.top + r.height() // 2

            # 检�?col2 区域是否�?UIA 元素（即�?get_element 失败，也可能有子元素�?
            # 实际�?UIA 再做一次轻量检测——这不是像素颜色检测，而是缩小范围�?UIA 检�?
            try:
                cl = self._win.Control(AutomationId='primary_table_.contact_list')
                if cl.Exists() and cl.BoundingRectangle.width() > 0:
                    return '通讯�?
            except Exception:
                pass
            try:
                sl = self._win.Control(AutomationId='session_list')
                if sl.Exists() and sl.BoundingRectangle.width() > 0:
                    return '微信'
            except Exception:
                pass
        except Exception:
            pass
        return None

    # ── 通讯录分组门检测（方法3：找联系人的根）──

    def get_expanded_groups(self):
        """检测通讯录中哪些分组是展开的�?

        方法3（人的方式）：遍�?contact_list 子元素，
        第一�?CellItemView 前面最近的 CellGroupView 就是打开的门�?
        同时记录每个分组后面是否有可见的联系人条目�?

        Returns:
            {group_name: {expanded: bool, item_count: int, first_item_name: str|None}}
        """
        w = self._win
        cl = w.Control(AutomationId='primary_table_.contact_list')
        if not cl.Exists():
            return {}

        result = {}
        last_group = None

        for item in cl.GetChildren():
            try:
                name = (item.Name or '').strip()
                cls = item.ClassName or ''
                br = item.BoundingRectangle

                if 'CellGroupView' in cls and name:
                    last_group = name
                    if name not in result:
                        result[name] = {'expanded': False, 'item_count': 0, 'first_item_name': None}
                    continue

                # 跳过分组标题和零尺寸元素
                if 'ClassifyView' in cls or 'MangerBtn' in cls or not name:
                    continue
                if br.width() == 0 or br.height() == 0:
                    continue

                # 这是一个可见的联系人条�?�?所属分组是展开�?
                if last_group and last_group in result:
                    if not result[last_group]['expanded']:
                        result[last_group]['expanded'] = True
                        result[last_group]['first_item_name'] = name
                    result[last_group]['item_count'] += 1

            except Exception:
                continue

        return result

    # ── 通讯录分组门管理 ──

    def _visible_groups(self):
        """获取当前 UIA 可见的所有分组（CellGroupView）�?
        Returns: [{name, x, y}, ...] �?Y 排序
        """
        w = self._win
        cl = w.Control(AutomationId='primary_table_.contact_list')
        if not cl.Exists():
            return []
        groups = []
        for item in cl.GetChildren():
            try:
                name = (item.Name or '').strip()
                cls = item.ClassName or ''
                if 'CellGroupView' in cls and name:
                    br = item.BoundingRectangle
                    if br.width() > 0:
                        groups.append({
                            'name': name,
                            'x': br.left + 40,
                            'y': br.top + br.height() // 2,
                            'top': br.top,
                        })
            except Exception:
                continue
        groups.sort(key=lambda g: g['top'])
        return groups

    def wait_visible_groups(self, timeout=3.0, poll=0.15):
        """轮询等待分组出现，一旦拿到立即返回——不浪费时间盲等�?

        Returns: [{name, x, y}, ...] 或超时返�?[]
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            groups = self._visible_groups()
            if groups:
                return groups
            time.sleep(poll)
        return []

    def _close_group(self, group_info, log_func=None):
        """点击一个分组标题来折叠它�?""
        import pyautogui
        if log_func:
            log_func(f"[Door] CLOSE: {group_info['name'][:25]}")
        pyautogui.click(group_info['x'], group_info['y'])
        time.sleep(0.15)

    def _open_group(self, group_info, log_func=None):
        """点击一个分组标题来展开它�?""
        import pyautogui
        if log_func:
            log_func(f"[Door] OPEN: {group_info['name'][:25]}")
        pyautogui.click(group_info['x'], group_info['y'])
        time.sleep(0.2)

    def ensure_contact_groups(self, desired_prefixes, log_func=None):
        """确保目标分组展开。极简算法�?
        1. 目标门在眼前？→ 开它（关掉其他展开的）
        2. 有展开的门挡着？→ 关掉它，腾空间，再看
        3. 没展开门但目标也不�?�?无能为力，报�?

        Args:
            desired_prefixes: 目标分组名前缀列表（如 ['联系�?]�?
            log_func: 可选日志回�?
        Returns:
            (opened, closed, found_target)
        """
        import pyautogui

        def log(msg):
            if log_func: log_func(msg)

        MAX_ROUNDS = 10

        # 等列表渲�?+ 滚到顶找分组标题
        for _ in range(5):
            if self._visible_groups():
                break
            time.sleep(0.3)
        if not self._visible_groups():
            # 列表滚到中间了，向上滚找分组标题
            cl = self._win.Control(AutomationId='primary_table_.contact_list')
            if cl.Exists():
                clr = cl.BoundingRectangle
                pyautogui.click(clr.left + 50, clr.top + 30)
                for _ in range(15):
                    pyautogui.scroll(2500)
                    time.sleep(0.02)
                time.sleep(0.5)

        for round_num in range(1, MAX_ROUNDS + 1):
            groups = self._visible_groups()
            expanded = self.get_expanded_groups()
            open_names = [k[:20] for k, v in expanded.items() if v.get('expanded')]

            # 步骤1: 找目标门
            target = None
            for g in groups:
                if any(g['name'].startswith(d) or d.startswith(g['name']) for d in desired_prefixes):
                    target = g
                    break

            if target:
                log(f"[Door] R{round_num}: target FOUND ({target['name'][:25]}). Open: {open_names}")
                # 关掉其他展开的门
                closed = 0
                for g in groups:
                    if g['name'] == target['name']:
                        continue
                    if expanded.get(g['name'], {}).get('expanded'):
                        self._close_group(g, log_func)
                        closed += 1
                time.sleep(0.2)
                # 目标已经开了？
                if expanded.get(target['name'], {}).get('expanded'):
                    return (0, closed, True)
                # 开目标
                self._open_group(target, log_func)
                return (1, closed, True)

            # 步骤2: 目标不在眼前，找展开的门关掉
            blocker = None
            for g in groups:
                if expanded.get(g['name'], {}).get('expanded'):
                    blocker = g
                    break

            if blocker:
                log(f"[Door] R{round_num}: no target. Closing: {blocker['name'][:25]} (open: {open_names})")
                self._close_group(blocker, log_func)
                time.sleep(0.4)
                continue  # 再看

            # 步骤3: 没有展开的门，目标也不在 �?没辙�?
            log(f"[Door] R{round_num}: no target, no blocker. Visible: {[g['name'][:20] for g in groups]}")
            break

        # 走投无路
        log(f"[Door] ⚠️ Cannot find target {desired_prefixes}. Recommend: scroll, re-navigate, or AI vision.")
        return (0, 0, False)

    def _click_group_header(self, item):
        """点击分组标题——UIA坐标优先，像素锚点兜底�?""
        import pyautogui
        name = (item.Name or '').strip()
        br = item.BoundingRectangle
        if br.width() > 0:
            pyautogui.click(br.left + 40, br.top + br.height() // 2)
        else:
            # 像素锚点兜底
            r = self._win.BoundingRectangle
            cg = self.pixel_anchors.get('contacts_groups', {})
            cx = cg.get('group_center_x', 180)
            for g in cg.get('groups', []):
                if name.startswith(g['name']):
                    pyautogui.click(r.left + cx,
                                   r.top + g['center_y_collapsed'])
                    return

    def reset_navigation(self, target='微信'):
        """导航到目标页面——仅使用像素锚点（一级导航永远可见，直接点即可）�?

        注意：绝对不使用 ESC 键（ESC = 隐藏微信窗口，不是返回！�?
        一级导航栏固定在窗口左侧，永远不会消失�?
        """
        import pyautogui

        for attempt in range(3):
            r = self._win.BoundingRectangle
            buttons = self.pixel_anchors.get("nav_buttons", {}).get("buttons", [])
            for btn in buttons:
                if btn.get("name") == target:
                    abs_x = r.left + btn["center_x"]
                    abs_y = r.top + btn["center_y_rel"]
                    pyautogui.click(abs_x, abs_y)
                    time.sleep(0.5)
                    if target in self.PAGE_MAP:
                        _, verify_aid = self.PAGE_MAP[target]
                        if verify_aid:
                            try:
                                el = self._win.Control(AutomationId=verify_aid)
                                if el.Exists() and el.BoundingRectangle.width() > 0:
                                    return True
                            except Exception:
                                pass
                    else:
                        return True
                    break
            time.sleep(0.3)

        return False

    # ── 消息读取 ──

    def read_messages(self, max_count=20):
        """读取聊天区消息：遍历 chat_message_list �?ListItem 子元�?""
        msg_list = self.get_element(AID["msg_list"])
        if not msg_list:
            return []

        messages = []
        try:
            for item in msg_list.GetChildren():
                try:
                    name = item.Name or ""
                    aid = item.AutomationId or ""
                    ct = item.ControlTypeName or ""
                    r = item.BoundingRectangle

                    # 消息气泡: automationId 包含 chat_bubble_item_view
                    # 日期分隔�? automationId 为空
                    if not name.strip():
                        continue

                    if "chat_bubble_item_view" in aid:
                        # 消息气泡 �?尝试区分自己/对方
                        is_self = "right" in name.lower() or r.left > 0  # TODO: 更精确的判断
                        messages.append({
                            "text": name.strip(),
                            "y": r.top,
                            "x": r.left,
                            "w": r.width(),
                            "bubble": True,
                        })
                    elif not aid:
                        # 日期分隔�?
                        messages.append({
                            "text": name.strip(),
                            "y": r.top,
                            "bubble": False,
                            "is_date": True,
                        })
                except Exception:
                    continue

            # �?Y 坐标排序
            messages.sort(key=lambda m: m.get("y", 0))
            return messages[-max_count:]

        except Exception as e:
            print(f"   ⚠️ read_messages 异常: {e}")
            return []

    def read_messages_ocr(self):
        """OCR 回退方案（暂不实现，保留接口�?""
        return []


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="微信 UIA 操作工具")
    parser.add_argument("--list", action="store_true", help="侦察模式: 列出所有元�?)
    parser.add_argument("--find", help="搜索并打开联系�?)
    parser.add_argument("--send", help="发送消�?)
    parser.add_argument("--click-nav", help="点击导航按钮")
    parser.add_argument("--read", type=int, help="读取最�?N 条消�?)
    parser.add_argument("--contact", action="store_true", help="显示当前联系�?)
    args = parser.parse_args()

    if not any([args.list, args.find, args.send, args.click_nav, args.read, args.contact]):
        args.list = True

    try:
        w = WeChatUIA()
    except RuntimeError as e:
        print(f"�?{e}")
        return

    if args.list:
        w.list_elements()

    if args.click_nav:
        ok = w.click_nav(args.click_nav)
        print(f"{'�? if ok else '�?} 导航 �?{args.click_nav}")

    if args.find:
        result = w.search_contact(args.find)
        print(f"🔍 搜索 '{args.find}' �?当前聊天: {result or '未知'}")

    if args.contact:
        name = w.get_current_contact()
        print(f"📇 当前联系�? {name or '未知'}")

    if args.read:
        msgs = w.read_messages(args.read)
        print(f"💬 最�?{len(msgs)} 条消�?")
        for i, m in enumerate(msgs):
            print(f"  [{i+1}] {m['text'][:80]}")

    if args.send:
        ok = w.send(args.send)
        print(f"{'�? if ok else '�?} 发�? {args.send[:50]}...")


if __name__ == "__main__":
    main()
