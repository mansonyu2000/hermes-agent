"""
wechat-find.py — 微信桌面操作：查找窗口、联系人、输入框

基于 uiautomation (Windows UIA COM) 直达微信 Qt 控件。
关键元素通过 AutomationId 精确定位，不依赖绝对坐标。

用法:
  python wechat-find.py                     # 侦察模式：列出关键 UIA 元素
  python wechat-find.py --find "联系人名"    # 搜索并打开联系人
  python wechat-find.py --send "消息内容"    # 向当前聊天窗口发消息
"""
import sys
import time
import argparse

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import uiautomation as auto
import pyautogui
pyautogui.FAILSAFE = False
import pyperclip


# ── 已知的微信 UIA AutomationId ──
AID_INPUT_BOX = "chat_input_field"
AID_CHAT_NAME = ("content_view.top_content_view.title_h_view.left_v_view"
                 ".left_content_v_view.left_ui_.big_title_line_h_view"
                 ".current_chat_name_label")
AID_CHAT_PAGE = "chat_message_page"
AID_NAV_TABBAR = "MainView.main_tabbar"
AID_SEARCH_BOX = "MainView.main_tabbar.search_edit"  # 可能不暴露


def find_wechat():
    """找到微信主窗口"""
    w = auto.WindowControl(Name="微信")
    if w.Exists(maxSearchSeconds=2):
        w.SetFocus()
        time.sleep(0.2)
        return w
    print("❌ 找不到微信窗口")
    return None


def get_rect(ctrl):
    """获取元素矩形"""
    r = ctrl.BoundingRectangle
    return r.left, r.top, r.width(), r.height()


def list_key_elements(wechat):
    """侦察模式：列出关键元素"""
    print(f"\n🔍 微信关键 UIA 元素 (窗口 {get_rect(wechat)[2]}x{get_rect(wechat)[3]}):\n")

    # 输入框
    inp = wechat.Control(AutomationId=AID_INPUT_BOX)
    if inp.Exists():
        x, y, w, h = get_rect(inp)
        print(f"  ✏️  输入框    ({x},{y}) {w}x{h}")

    # 聊天名
    name = wechat.Control(AutomationId=AID_CHAT_NAME)
    if name.Exists():
        print(f"  📇 聊天对象  「{name.Name}」 {get_rect(name)[2]}x{get_rect(name)[3]}")

    # 导航按钮
    navbar = wechat.Control(AutomationId=AID_NAV_TABBAR)
    if navbar.Exists():
        print(f"  🧭 导航栏")
        for btn in navbar.GetChildren():
            try:
                if btn.Name:
                    print(f"      [{btn.Name}]")
            except Exception:
                pass

    # 聊天页面
    chat = wechat.Control(AutomationId=AID_CHAT_PAGE)
    if chat.Exists():
        print(f"  💬 聊天区域  {get_rect(chat)[2]}x{get_rect(chat)[3]}")

    # 采样顶层元素
    print(f"\n  顶层结构:")
    for child in wechat.GetChildren():
        try:
            name = child.Name
            aid = child.AutomationId
            ct = child.ControlTypeName
            r = get_rect(child)
            print(f"  [{ct}] name={name!r} aid={aid!r} ({r[0]},{r[1]} {r[2]}x{r[3]})")
        except Exception:
            pass


def search_contact(wechat, contact_name):
    """搜索打开联系人：Ctrl+F → 粘贴 → Enter"""
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.3)
    pyperclip.copy(contact_name)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(0.5)

    name_ctrl = wechat.Control(AutomationId=AID_CHAT_NAME)
    if name_ctrl.Exists():
        print(f"   📇 当前聊天: {name_ctrl.Name}")
    return True


def send_message(wechat, text):
    """向当前聊天窗口发送消息 — UIA 直通输入框"""
    inp = wechat.Control(AutomationId=AID_INPUT_BOX)

    if inp.Exists():
        try:
            inp.Click()
            time.sleep(0.1)
            inp.SendKeys("{Ctrl}a{Delete}")
            inp.SendKeys(text)
            inp.SendKeys("{Enter}")
            print(f"   ✅ UIA 发送完成: {text[:50]}")
            return True
        except Exception as e:
            print(f"   ⚠️ UIA SendKeys 失败: {e}")

    # 回退：pyautogui + 剪贴板
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    pyautogui.press("delete")
    time.sleep(0.05)
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.1)
    pyautogui.press("enter")
    print(f"   ✅ 剪贴板发送完成: {text[:50]}")
    return True


def main():
    parser = argparse.ArgumentParser(description="微信桌面操作工具")
    parser.add_argument("--find", help="搜索并打开联系人")
    parser.add_argument("--send", help="向当前聊天发送消息")
    parser.add_argument("--list", action="store_true", help="列出关键 UIA 元素")
    args = parser.parse_args()

    if not any([args.find, args.send, args.list]):
        args.list = True

    wechat = find_wechat()
    if not wechat:
        return

    if args.list:
        list_key_elements(wechat)

    if args.find:
        print(f"\n🔍 搜索联系人: {args.find}")
        search_contact(wechat, args.find)

    if args.send:
        print(f"\n✉️ 发送消息: {args.send}")
        send_message(wechat, args.send)


if __name__ == "__main__":
    main()
