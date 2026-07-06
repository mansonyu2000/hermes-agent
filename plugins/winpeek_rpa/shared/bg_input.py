"""
bg_input.py — 后台输入，不抢占用户鼠标键盘

点击: PostMessage (WM_LBUTTONDOWN/UP → 目标窗口)
滚动: SendInput 绝对坐标 (MOUSEEVENTF_WHEEL + MOUSEEVENTF_ABSOLUTE)
      指定屏幕坐标，不移动鼠标光标

用法:
  from bg_input import BGInput
  bg = BGInput("微信")
  bg.click(100, 200)         # 后台点击（不抢鼠标）
  bg.scroll(100, 200, -120)  # 后台滚动（不抢鼠标）
"""
import time, ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

# ── PostMessage（点击）──
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
MK_LBUTTON     = 0x0001

# ── SendInput（滚动）──
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

class SENDINPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("mi", MOUSEINPUT)]

INPUT_MOUSE = 0
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000
WHEEL_DELTA = 120


class BGInput:
    def __init__(self, window_title="微信"):
        self.hwnd = None
        self._sw = user32.GetSystemMetrics(0)  # 屏幕宽
        self._sh = user32.GetSystemMetrics(1)  # 屏幕高
        self._find(window_title)

    def _find(self, title):
        h = user32.FindWindowW(None, title)
        if not h:
            h = user32.FindWindowW(None, "WeChat")
        if not h:
            raise RuntimeError(f"Window '{title}' not found")
        self.hwnd = h

    def _screen_to_client(self, x, y):
        """屏幕坐标 → 窗口客户区坐标"""
        pt = wintypes.POINT(int(x), int(y))
        user32.ScreenToClient(self.hwnd, ctypes.byref(pt))
        return (pt.x, pt.y)

    def refresh(self):
        self._find("微信")

    # ═══════════════════════════════════════════════
    # 点击 — PostMessage（可靠）
    # ═══════════════════════════════════════════════

    def click(self, x, y, delay=0.03):
        """后台点击——传入屏幕坐标，不移动鼠标"""
        cx, cy = self._screen_to_client(x, y)
        lp = (cy << 16) | (cx & 0xFFFF)
        user32.PostMessageW(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
        time.sleep(delay)
        user32.PostMessageW(self.hwnd, WM_LBUTTONUP, 0, lp)

    # ═══════════════════════════════════════════════
    # 滚动 — SetCursorPos + SendInput(WHEEL)
    # ═══════════════════════════════════════════════
    #
    # 2026-06-17 诊断结论:
    #   SendInput(MOUSEEVENTF_WHEEL | MOUSEEVENTF_ABSOLUTE) 不定位滚轮!
    #   滚轮事件总是投递到当前光标位置，dx/dy 被忽略。
    #   正确做法: SetCursorPos(屏幕坐标) → SendInput(WHEEL)
    #   光标瞬移 <2ms，用户无感。多屏无需坐标换算。

    def scroll(self, x, y, delta=-120, ticks=5, delay=0.03):
        """后台滚动——传入屏幕坐标，SetCursorPos定位光标后SendInput滚轮。

        delta: 滚动量（负=向下，正=向上），WHEEL_DELTA(120) 为单位
        """
        user32.SetCursorPos(int(x), int(y))
        for _ in range(ticks):
            inp = SENDINPUT()
            inp.type = INPUT_MOUSE
            inp.mi.mouseData = delta
            inp.mi.dwFlags = MOUSEEVENTF_WHEEL
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
            time.sleep(delay)

    def scroll_by(self, x, y, total_delta, delay=0.03):
        """按总滚动量自动拆分为多次 WHEEL_DELTA 单位"""
        ticks = abs(total_delta) // WHEEL_DELTA
        sign = 1 if total_delta > 0 else -1
        self.scroll(x, y, delta=sign * WHEEL_DELTA, ticks=ticks, delay=delay)

    # ═══════════════════════════════════════════════
    # 滚动 — SetCursorPos + SendInput(WHEEL)
    # ═══════════════════════════════════════════════
    #
    # 2026-06-17 诊断结论:
    #   SendInput(MOUSEEVENTF_WHEEL | MOUSEEVENTF_ABSOLUTE) 不定位滚轮!
    #   PostMessage(WM_MOUSEWHEEL) Qt控件不响应!
    #   唯一可靠方案: SetCursorPos(屏幕坐标) → SendInput(WHEEL)
    #   光标瞬移 <2ms，用户基本无感。

    def scroll(self, x, y, delta=-120, ticks=5, delay=0.03):
        """后台滚动 — SetCursorPos定位光标后SendInput滚轮。
        光标瞬移 <2ms，用户基本无感。

        x, y: 屏幕坐标
        delta: WHEEL_DELTA(120) 为单位
        """
        user32.SetCursorPos(int(x), int(y))
        for _ in range(ticks):
            inp = SENDINPUT()
            inp.type = INPUT_MOUSE
            inp.mi.mouseData = delta
            inp.mi.dwFlags = MOUSEEVENTF_WHEEL
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
            time.sleep(delay)
