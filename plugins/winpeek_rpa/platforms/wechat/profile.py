"""
wechat_profile.py �?微信深度数据采集

已验证的 UIA 采集路径:
  1. 搜索 �?search_list (search_item_<�?)
  2. 资料�?�?点当前联系人�?�?�?Profile 面板
  3. 消息全量 �?chat_message_list 滚动 + 读取

用法:
  python wechat_profile.py                  # 侦察当前聊天
  python wechat_profile.py --search "于杨�?  # 搜索联系�?
  python wechat_profile.py --profile         # 打开资料�?
  python wechat_profile.py --messages 50     # 滚动读取消息
"""
import sys, time, os, argparse, json

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# (removed - now using package imports)
from .uia import WeChatUIA, AID


# ══════════════════════════════════════════════════════�?
# 搜索增强：分批展开、逐条匹配
# ══════════════════════════════════════════════════════�?

def search_deep(wx, keyword):
    """深度搜索：展开全部结果，分批返�?""
    import pyautogui, pyperclip

    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.3)
    pyperclip.copy(keyword)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.8)

    # 先展开所�?查看更多"按钮
    expanded = 0
    for _ in range(5):
        search_list = wx._win.Control(AutomationId="search_list")
        if not search_list.Exists():
            break
        found_expand = False
        for item in search_list.GetChildren():
            try:
                if "查看更多" in (item.Name or ""):
                    item.Click()
                    time.sleep(0.5)
                    found_expand = True
                    expanded += 1
            except Exception:
                pass
        if not found_expand:
            break

    # 收集全部结果
    results = {"contacts": [], "groups": [], "records": [], "favorites": []}
    section = "contacts"
    search_list = wx._win.Control(AutomationId="search_list")
    if search_list.Exists():
        for item in search_list.GetChildren():
            try:
                name = item.Name or ""
                aid = item.AutomationId or ""
                if not name.strip():
                    continue
                # 判断分区
                if "群聊" in name:
                    section = "groups"; continue
                if "聊天记录" in name:
                    section = "records"; continue
                if "收藏" in name:
                    section = "favorites"; continue
                if "常用" in name or "查看更多" in name:
                    continue

                entry = {"name": name, "aid": aid}
                if "search_item_" in aid:
                    results[section].append(entry)
            except Exception:
                pass

    pyautogui.press("esc")  # 关闭搜索
    return results


# ══════════════════════════════════════════════════════�?
# 资料卡采�?
# ══════════════════════════════════════════════════════�?

def open_and_read_profile(wx):
    """打开资料卡并读取信息 �?点联系人名字"""
    import pyautogui
    import uiautomation as auto

    # 点联系人头像区域 (标题栏左�?
    name_ctrl = wx._win.Control(AutomationId=AID["chat_name"])
    if not name_ctrl.Exists():
        return {"error": "找不到联系人标签"}

    # 双击名字区域（通常打开资料卡）
    name_ctrl.Click()
    time.sleep(0.8)

    # 检查是否出现了资料卡面�?
    profile = {}
    profile_panel = wx._win.Control(
        AutomationId="MainView.main_window_corner_view.MainView.main_window_main_splitter_view.main_window_sub_splitter_view.chat_message_page"
    )
    # 找新出现�?Profile 相关元素
    desktop = auto.GetRootControl()
    for c in desktop.GetChildren():
        try:
            cn = c.ClassName or ""
            if "Profile" in cn or "Contact" in cn or "profile" in cn.lower():
                r = c.BoundingRectangle
                profile["class"] = cn
                profile["bounds"] = f"{r.width()}x{r.height()}"
                # 读取面板内所有文�?
                texts = []
                for child in c.GetChildren():
                    try:
                        if child.Name:
                            texts.append(child.Name)
                    except Exception:
                        pass
                profile["texts"] = texts
        except Exception:
            pass

    # 回退：OCR 方式读取聊天窗口标题�?
    if not profile:
        # 直接�?UIA 树中与资料相关的元素
        texts = []
        for d in wx._win.GetChildren():
            try:
                _walk_text(d, texts, depth=0)
            except Exception:
                pass
        profile = {"method": "uia-tree", "texts": texts}

    pyautogui.press("esc")  # 关闭资料�?
    return profile


def _walk_text(ctrl, texts, depth):
    if depth > 4:
        return
    for child in ctrl.GetChildren():
        try:
            name = child.Name
            if name and name.strip():
                texts.append(name.strip())
        except Exception:
            pass
        _walk_text(child, texts, depth + 1)


# ══════════════════════════════════════════════════════�?
# 消息全量采集
# ══════════════════════════════════════════════════════�?

def collect_messages(wx, max_scrolls=20):
    """滚动读取全部消息，返回按时间排序的列�?""
    import pyautogui
    all_msgs = {}
    seen_keys = set()
    stall_count = 0

    for scroll_i in range(max_scrolls):
        # 读取当前可见消息
        msg_list = wx._win.Control(AutomationId=AID["msg_list"])
        if not msg_list.Exists():
            break

        new_in_round = 0
        for item in msg_list.GetChildren():
            try:
                name = item.Name or ""
                aid = item.AutomationId or ""
                r = item.BoundingRectangle
                if not name.strip():
                    continue

                key = (name[:40], r.top)  # 相同文本+相同Y = 同一�?
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                all_msgs[r.top] = {
                    "text": name,
                    "y": r.top,
                    "is_bubble": "chat_bubble_item_view" in aid,
                    "is_date": not aid,
                }
                new_in_round += 1
            except Exception:
                pass

        print(f"  [{scroll_i+1}] +{new_in_round} �? 累计 {len(all_msgs)}")

        if new_in_round == 0:
            stall_count += 1
            if stall_count >= 3:
                break
        else:
            stall_count = 0

        # 向上滚动
        pyautogui.scroll(800)
        time.sleep(0.4)

    # 排序
    return [all_msgs[k] for k in sorted(all_msgs.keys())]


# ══════════════════════════════════════════════════════�?
# CLI
# ══════════════════════════════════════════════════════�?

def main():
    parser = argparse.ArgumentParser(description="微信深度数据采集")
    parser.add_argument("--search", help="搜索关键�?)
    parser.add_argument("--profile", action="store_true", help="读取资料�?)
    parser.add_argument("--messages", type=int, default=0, help="读取消息（滚动次数）")
    args = parser.parse_args()

    wx = WeChatUIA()
    current = wx.get_current_contact()
    print(f"当前联系�? {current or '未知'}")
    print(f"窗口: {wx.get_bounds()[0]}x{wx.get_bounds()[1]}")
    print()

    if args.search:
        print(f"=== 搜索: {args.search} ===")
        results = search_deep(wx, args.search)
        for section, items in results.items():
            if items:
                print(f"\n[{section}] ({len(items)} �?:")
                for item in items:
                    print(f"  {item['name'][:50]}")

    if args.profile:
        print("\n=== 资料�?===")
        profile = open_and_read_profile(wx)
        print(json.dumps(profile, indent=2, ensure_ascii=False))

    if args.messages:
        print(f"\n=== 消息采集 (最�?{args.messages} 次滚�? ===")
        msgs = collect_messages(wx, max_scrolls=args.messages)
        print(f"\n�?{len(msgs)} 条消�?)
        for m in msgs[:20]:
            tag = "📅" if m.get("is_date") else "💬"
            print(f"  {tag} {m['text'][:80]}")


if __name__ == "__main__":
    main()
