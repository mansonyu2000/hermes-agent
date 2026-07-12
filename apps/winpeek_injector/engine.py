"""Agent Injector Engine — window activation + RPA message injection.

Migrated from PeekabooWin bridge-agent.py (979 lines).
Stripped: MQTT listener, ConPTY, WeChat bridge, stats reporter — those belong in their own modules.

Core kept: window find/activate (3 strategies), clipboard RPA inject, SendInput backend inject.
"""

import ctypes, time
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

import pyautogui
pyautogui.FAILSAFE = False
import pygetwindow as gw

try:
    from pywinauto import Desktop as UiaDesktop
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ═══════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════

CONFIG_DIR = Path.home() / ".hermes" / "winpeek" / "injector"
CONFIG_FILE = CONFIG_DIR / "agents.json"

def load_config() -> dict:
    if CONFIG_FILE.exists():
        import json
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}

def save_config(cfg: dict):
    import json
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

# ═══════════════════════════════════════════════
# Window discovery
# ═══════════════════════════════════════════════

def list_windows():
    """Enumerate visible windows. Terminal-type windows first."""
    TERMINAL_KW = ['powershell', 'cmd', 'terminal', 'claude', 'code', 'qoder',
                   'cursor', 'hermes', 'developer']
    wins = []
    for w in gw.getAllWindows():
        t = w.title.strip()
        if t:
            wins.append((t, w._hWnd))
    def _sort(item):
        t = item[0].lower()
        for i, kw in enumerate(TERMINAL_KW):
            if kw in t:
                return (0, i, t)
        return (1, 0, t)
    wins.sort(key=_sort)
    return wins

# ═══════════════════════════════════════════════
# Window activation (3 strategies)
# ═══════════════════════════════════════════════

def _focus_win32(hwnd: int):
    """Win32 ShowWindow + SetForegroundWindow + AttachThreadInput."""
    try:
        user32.ShowWindow(hwnd, 9)
    except Exception:
        pass
    try:
        fg = user32.GetForegroundWindow()
        cur_tid = kernel32.GetCurrentThreadId()
        fg_tid = user32.GetWindowThreadProcessId(fg, None)
        if cur_tid != fg_tid:
            user32.AttachThreadInput(cur_tid, fg_tid, True)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        if cur_tid != fg_tid:
            user32.AttachThreadInput(cur_tid, fg_tid, False)
    except Exception:
        pass

def activate_window(title_keyword: str, tab_index: int = None) -> bool:
    """Find and activate a window by title keyword. 3 strategies.

    Returns True if window was found and focused.
    """
    config = load_config()
    agent_names = list(config.keys())

    # Strategy 1: direct title match
    for win in gw.getAllWindows():
        try:
            if title_keyword.lower() in win.title.lower():
                hwnd = win._hWnd
                _focus_win32(hwnd)
                time.sleep(0.1)
                if tab_index:
                    pyautogui.hotkey("ctrl", "alt", str(tab_index))
                return True
        except Exception:
            continue

    # Strategy 2: find sibling window by other agent name + switch tab
    others = [a for a in agent_names if a != title_keyword]
    for win in gw.getAllWindows():
        try:
            t = win.title.lower()
            for other in others:
                if other.lower() in t:
                    hwnd = win._hWnd
                    _focus_win32(hwnd)
                    time.sleep(0.15)
                    if tab_index:
                        pyautogui.hotkey("ctrl", "alt", str(tab_index))
                        time.sleep(0.3)
                    return True
        except Exception:
            continue

    # Strategy 3: UIA search TabItem in all windows
    if HAS_PYWINAUTO:
        for win in gw.getAllWindows():
            try:
                hwnd = win._hWnd
                uia_win = UiaDesktop(backend="uia").window(handle=hwnd)
                tabs = list(uia_win.descendants(control_type="TabItem"))
                if not tabs:
                    continue
                for tab in tabs:
                    try:
                        tn = tab.window_text()
                        if tn and title_keyword.lower() in tn.lower():
                            uia_win.set_focus()
                            time.sleep(0.05)
                            tab.click_input()
                            time.sleep(0.1)
                            return True
                    except Exception:
                        continue
            except Exception:
                continue

    return False

# ═══════════════════════════════════════════════
# RPA injection (clipboard paste)
# ═══════════════════════════════════════════════

def inject_rpa(click_x: int, click_y: int, text: str):
    """Click input area → clear → paste → Enter. Blocks keyboard briefly."""
    pyautogui.click(click_x, click_y)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    pyautogui.press("delete")
    time.sleep(0.05)
    import pyperclip
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.1)
    pyautogui.press("enter")

# ═══════════════════════════════════════════════
# Backend injection (SendInput, non-blocking)
# ═══════════════════════════════════════════════

INPUT_KEYBOARD = 1
INPUT_MOUSE = 0
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
VK_RETURN = 0x0D
VK_CONTROL = 0x11

class _KBINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG)]

class _MOUINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", wintypes.ULONG)]

class _IN_UNION(ctypes.Union):
    _fields_ = [("ki", _KBINPUT), ("mi", _MOUINPUT)]

class _WIN_INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _IN_UNION)]

def _kb(vk=0, scan=0, flags=0):
    inp = _WIN_INPUT(type=INPUT_KEYBOARD)
    inp.u.ki.wVk = vk
    inp.u.ki.wScan = scan
    inp.u.ki.dwFlags = flags
    return inp

def _mouse_click(x, y):
    user32 = ctypes.windll.user32
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    down = _WIN_INPUT(type=INPUT_MOUSE)
    down.u.mi.dx = int(x * 65535 / sw)
    down.u.mi.dy = int(y * 65535 / sh)
    down.u.mi.dwFlags = MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE
    up = _WIN_INPUT(type=INPUT_MOUSE)
    up.u.mi.dx = down.u.mi.dx
    up.u.mi.dy = down.u.mi.dy
    up.u.mi.dwFlags = MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE
    return [down, up]

def inject_backend(title_keyword: str, click_x: int, click_y: int, text: str) -> bool:
    """SendInput batch — all events in one system call. Doesn't block user keyboard."""
    user32 = ctypes.windll.user32

    hwnd = None
    def _enum(h, _):
        nonlocal hwnd
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(h, buf, 256)
        if title_keyword.lower() in buf.value.lower():
            hwnd = h
            return False
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(_enum), 0)

    if not hwnd:
        return False

    user32.SetForegroundWindow(hwnd)
    time.sleep(0.15)

    events = _mouse_click(click_x, click_y)
    events += [_kb(vk=VK_CONTROL), _kb(vk=0x41),
               _kb(vk=0x41, flags=KEYEVENTF_KEYUP),
               _kb(vk=VK_CONTROL, flags=KEYEVENTF_KEYUP),
               _kb(vk=0x2E), _kb(vk=0x2E, flags=KEYEVENTF_KEYUP)]

    if any(ord(c) > 127 for c in text):
        import pyperclip
        pyperclip.copy(text)
        events += [_kb(vk=VK_CONTROL), _kb(vk=0x56),
                   _kb(vk=0x56, flags=KEYEVENTF_KEYUP),
                   _kb(vk=VK_CONTROL, flags=KEYEVENTF_KEYUP)]
    else:
        for ch in text:
            if ch == '\n':
                events += [_kb(vk=VK_RETURN), _kb(vk=VK_RETURN, flags=KEYEVENTF_KEYUP)]
            else:
                events += [_kb(scan=ord(ch), flags=KEYEVENTF_UNICODE),
                           _kb(scan=ord(ch), flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)]

    events += [_kb(vk=VK_RETURN), _kb(vk=VK_RETURN, flags=KEYEVENTF_KEYUP)]

    arr = (_WIN_INPUT * len(events))(*events)
    result = user32.SendInput(len(events), arr, ctypes.sizeof(_WIN_INPUT))
    return result > 0

# ═══════════════════════════════════════════════
# High-level: deliver MIM message to an agent window
# ═══════════════════════════════════════════════

def deliver_to_agent(agent_name: str, text: str, mode: str = "rpa") -> bool:
    """Find agent window, inject message. Returns success.

    mode: 'rpa' (click+paste), 'backend' (SendInput batch), 'conpty' (ConPTY, no focus)
    """
    config = load_config()
    agent_cfg = config.get(agent_name, {})
    if not agent_cfg:
        return False

    title = agent_cfg.get("window_title", agent_name)
    cx = agent_cfg.get("click_x", 0)
    cy = agent_cfg.get("click_y", 0)
    tab_index = agent_cfg.get("tab_index")

    # ConPTY — no window activation needed
    if mode == "conpty":
        try:
            from .conpty_inject import inject_cc
            return inject_cc(text + "\n", window_title=title)
        except ImportError:
            pass  # Fallback to RPA

    # RPA/Backend — need window activation
    if not activate_window(title, tab_index=tab_index):
        return False

    if mode == "backend":
        return inject_backend(title, cx, cy, text)
    else:
        inject_rpa(cx, cy, text)
        return True
