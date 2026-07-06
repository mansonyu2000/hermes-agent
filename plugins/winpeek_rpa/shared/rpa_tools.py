"""
rpa_tools.py — RPA 原子工具集 (UIA定位 + OCR + VL 组件化)

每个函数只做一件事, 给参数→返回结果。无副作用。

用法:
  from rpa_tools import uia_find, parse_unread, ocr_region
"""
import re, time, json
import pyautogui
pyautogui.FAILSAFE = False


# ═══════════════════════════════════════════════════════
# UIA 工具
# ═══════════════════════════════════════════════════════

def uia_find(window, automation_id):
    """按 AutomationId 查找 UIA 元素 → {name, rect, class} or None"""
    ctrl = window.Control(AutomationId=automation_id)
    if not ctrl.Exists():
        return None
    r = ctrl.BoundingRectangle
    return {
        "name": (ctrl.Name or "").strip(),
        "class": ctrl.ClassName or "",
        "rect": (r.left, r.top, r.width(), r.height()),
        "control": ctrl,
    }


def uia_children(ctrl):
    """遍历 UIA 元素的直接子元素 → [(name, aid, class, rect), ...]"""
    out = []
    for item in ctrl.GetChildren():
        try:
            r = item.BoundingRectangle
            out.append((
                (item.Name or "").strip(),
                item.AutomationId or "",
                item.ClassName or "",
                (r.left, r.top, r.width(), r.height()),
                item,
            ))
        except Exception:
            pass
    return out


def uia_child_by_aid(ctrl, aid):
    """在ctrl子元素中按 AutomationId 精确匹配 → rect or None"""
    for item in ctrl.GetChildren():
        try:
            if (item.AutomationId or "") == aid:
                r = item.BoundingRectangle
                if r.width() > 0 and r.height() > 0:
                    return (r.left, r.top, r.width(), r.height())
        except Exception:
            pass
    return None


# ═══════════════════════════════════════════════════════
# 会话解析工具
# ═══════════════════════════════════════════════════════

def parse_session_item(aid, raw_name):
    """解析一个 session_list 项的完整信息 → dict.

    aid: AutomationId (session_item_<name>)
    raw_name: item.Name (多行文本)

    返回: {name, unread, is_pinned, is_muted, last_msg, last_time}
    """
    name = aid.replace('session_item_', '', 1) if aid.startswith('session_item_') else raw_name.split('\n')[0].strip()
    lines = raw_name.strip().split('\n')

    is_pinned = False
    is_muted = False
    unread = 0
    last_msg = ""
    last_time = ""

    for line in lines[1:]:  # 跳过首行(会话名)
        line = line.strip()
        if not line: continue
        if '已置顶' in line:
            is_pinned = True
        if '消息免打扰' in line:
            is_muted = True
        # 未读数: [N条] 或 [...]
        m = re.match(r'\[(\d+)条\]', line)
        if m:
            unread = int(m.group(1))
        elif '[...]' in line or '…' in line:
            unread = 100  # 超过100条

    # 最后一行通常是时间 (如 "08:42")
    last_line = lines[-1].strip() if len(lines) > 1 else ""
    if re.match(r'\d{2}:\d{2}', last_line):
        last_time = last_line
        # 倒数第二行是消息预览
        if len(lines) > 2:
            last_msg = lines[-2].strip()

    return {
        "name": name,
        "unread": unread,
        "is_pinned": is_pinned,
        "is_muted": is_muted,
        "last_msg": last_msg,
        "last_time": last_time,
    }


def has_unread(info):
    """有未读消息?"""
    return info["unread"] > 0


# ═══════════════════════════════════════════════════════
# 鼠标/键盘原子操作
# ═══════════════════════════════════════════════════════

def mouse_click(x, y, button="left"):
    """点击屏幕坐标"""
    pyautogui.click(x, y, button=button)


def mouse_scroll(x, y, amount, ticks=1):
    """在屏幕坐标滚轮。amount>0=上滚, <0=下滚"""
    pyautogui.moveTo(x, y)
    for _ in range(ticks):
        pyautogui.scroll(amount)


def key_press(key, times=1):
    """按键"""
    for _ in range(times):
        pyautogui.press(key)


# ═══════════════════════════════════════════════════════
# OCR 工具 (调用WinPeek MCP — 在Claude Code中可用)
# ═══════════════════════════════════════════════════════

def ocr_region_mcp(region=None):
    """OCR 指定区域。region=(left,top,width,height) or None=全窗口。

    ⚠️ 此函数在 Claude Code 中通过 MCP 调用。
    在 Python 脚本中返回占位符 — 实际调用请用 mcp__peekaboo-win__window_capture。
    """
    return {"note": "ocr_region — call via MCP in Claude Code", "region": region}


# ═══════════════════════════════════════════════════════
# VL 视觉分析工具
# ═══════════════════════════════════════════════════════

def vl_analyze_mcp(image_path, prompt):
    """VL 视觉分析 — Qwen2.5VL 看图理解。

    ⚠️ 此函数在 Claude Code 中通过 MCP 调用。
    """
    return {"note": "vl_analyze — call via MCP in Claude Code", "image": image_path, "prompt": prompt}


# ═══════════════════════════════════════════════════════
# 调试/自检
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    # 测试 parse_session_item
    test_aid = "session_item_观澜宣教馆工作群"
    test_raw = "观澜宣教馆工作群.，-\n已置顶\n[2条] \n甄雪珍: [小程序] 中国主裁来了！\n08:42\n"
    info = parse_session_item(test_aid, test_raw)
    print(f"parse: {json.dumps(info, ensure_ascii=False, indent=2)}")

    test_aid2 = "session_item_养生干货大本营随问随答"
    test_raw2 = "养生干货大本营随问随答\n[108条] \n[有人@我]\nKH3-倪主任: 儒医曹彦强老师...\n09:26\n"
    info2 = parse_session_item(test_aid2, test_raw2)
    print(f"parse: {json.dumps(info2, ensure_ascii=False, indent=2)}")
    print("rpa_tools OK")


# ═══════════════════════════════════════════════════════
# 时间解析 (WeChat 相对日期 → ISO)
# ═══════════════════════════════════════════════════════

_WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
_NON_DATE_KEYWORDS = ["打招呼", "以上是", "以下是", "聊天记录", "系统消息"]

def parse_chat_time(text):
    """WeChat消息时间 → ISO 字符串 '2026-06-18T18:52:00'

    支持:
      '2025年12月8日 10:33'            → ISO (绝对日期)
      '2025年11月29日 星期六 14:07'     → ISO (忽略星期, 用绝对日期)
      '6月18日 18:52' / '4月14日 17:53' → ISO (今年)
      '星期二 18:52' / '星期一 12:47'   → ISO (本周X)
      '昨天 18:03'                      → ISO (昨天)
      '今天 18:52' / '18:52'            → ISO (今天)
      '以上是打招呼的消息'               → ''  (非日期, 跳过)
      无法解析的时间字符串               → ''  (返回空, 外部可调LLM)
    """
    if not text or not text.strip():
        return ""
    text = text.strip()

    # 过滤非日期内容
    for kw in _NON_DATE_KEYWORDS:
        if kw in text:
            return ""

    # 绝对日期(可能带星期): 2025年12月8日 10:33 或 2025年11月29日 星期六 14:07
    m = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日.*?(\d{1,2}):(\d{2})', text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}T{int(m.group(4)):02d}:{m.group(5)}:00"

    # 今年月日: 6月18日 18:52 / 4月14日 17:53
    m = re.match(r'(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})', text)
    if m:
        from datetime import datetime
        y = datetime.now().year
        return f"{y}-{int(m.group(1)):02d}-{int(m.group(2)):02d}T{int(m.group(3)):02d}:{m.group(4)}:00"

    from datetime import datetime, timedelta
    now = datetime.now()
    today = now.date()

    time_match = re.search(r'(\d{1,2}):(\d{2})', text)
    hh, mm = (int(time_match.group(1)), int(time_match.group(2))) if time_match else (0, 0)

    # 今天 / 仅时间
    if '今天' in text or (time_match and not any(w in text for w in _WEEKDAYS + ['昨天'])):
        d = today
    elif '昨天' in text:
        d = today - timedelta(days=1)
    else:
        for i, wd in enumerate(_WEEKDAYS):
            if wd in text:
                today_wd = today.weekday()
                d = today + timedelta(days=(i - today_wd))
                break
        else:
            # 无法解析 — 返回空 (外部可调 LLM)
            if time_match:
                return ""  # 有时钟但格式未知 → 让 LLM 处理
            return ""  # 无法识别

    return f"{d.isoformat()}T{hh:02d}:{mm:02d}:00" if time_match else d.isoformat()
