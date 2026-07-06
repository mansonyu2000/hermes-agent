"""
wechat_contacts.py �?通讯录全量采�?

从微�?通讯�?tab采集所有联系人, 按类型分类入库�?

用法:
  python wechat_contacts.py --collect          # 全量采集
  python wechat_contacts.py --list             # 列出已采�?
"""
import sys, os, time, argparse
# (removed - now using package imports)
from .uia import WeChatUIA
from .db import WeChatDB
import uiautomation as auto
import pyautogui
pyautogui.FAILSAFE = False

# 分组�?�?contact_type 映射
GROUP_TYPE_MAP = {
    "新的朋友": "new_friend",
    "群聊": "group",
    "公众�?: "official_account",
    "服务�?: "service_account",
    "企业微信联系�?: "enterprise_wechat",
    "企业": "enterprise",
    "联系�?: "starred",  # 星标联系�?
}


def go_to_contacts(wx):
    """切换到通讯录tab (先回微信主tab再切, 确保UIA树完�?"""
    # 先确保微信主界面初始�?
    wx.click_nav("微信")
    time.sleep(0.8)
    wx.click_nav("通讯�?)
    time.sleep(1.0)


def read_contact_profile(wx):
    """读取右侧资料�?�?遍历 profile_view UIA 子树�?026-06-16 重写�?

    ⚠️ 易错: 深度必须 �?5（Qt CustomControl 嵌套深）
    ⚠️ 易错: ProfileTextView 存值，XTextView 存标签，都是 TextControl
    """
    import re
    profile = {}
    w = wx._win

    # 昵称 �?直接 AID
    nc = w.Control(AutomationId="right_v_view.nickname_button_view.display_name_text")
    if nc.Exists():
        profile["nickname"] = nc.Name.strip()

    # 遍历 profile_view 收集所�?TextControl（文档序�?
    pv = w.Control(AutomationId="profile_view")
    if not pv.Exists():
        return profile

    all_texts = []
    def collect(c, d=0):
        if d > 25: return  # ⚠️ 必须�?0，ProfileTextView 值在深度16+
        try:
            for child in c.GetChildren():
                n = (child.Name or "").strip()
                ct = child.ControlTypeName or ""
                if n and "Text" in ct:
                    all_texts.append(n)
                collect(child, d + 1)
        except Exception:
            pass
    collect(pv)

    SKIP = {
        "朋友资料", "更多信息", "朋友�?, "视频�?,
        "发消�?, "语音聊天", "视频聊天",
        "备注", "添加备注�?,
        "个性签�?, "来源", "添加时间", "共同群聊",
        "微信号：", "地区�?,
    }

    for i, t in enumerate(all_texts):
        nxt = all_texts[i + 1] if i + 1 < len(all_texts) else ""
        if "微信号：" in t and nxt:
            profile["wxid"] = nxt
        elif "地区�? in t and nxt:
            profile["region"] = nxt
        elif t == "个性签�? and nxt and nxt not in SKIP:
            profile["signature"] = nxt
        elif t == "来源" and nxt and nxt not in SKIP:
            profile["source"] = nxt
        elif t == "添加时间" and nxt and nxt not in SKIP:
            profile["first_met"] = nxt  # DB 字段�?
        elif t == "共同群聊" and nxt and nxt not in SKIP:
            m = re.search(r'(\d+)', nxt)
            if m:
                profile["shared_groups"] = int(m.group(1))

    # 备注
    for i, t in enumerate(all_texts):
        if t == "备注" and i + 1 < len(all_texts):
            v = all_texts[i + 1]
            if v and v != "添加备注�?:
                profile["alias"] = v
                break

    return profile


def collect_all_contacts(wx, db):
    """全量采集通讯�?""
    go_to_contacts(wx)
    print("通讯录已打开\n")

    contact_list = wx._win.Control(AutomationId="primary_table_.contact_list")
    if not contact_list.Exists():
        print("�?找不到通讯录列�?)
        return 0

    current_type = "friend"
    collected = 0
    total_items = 0

    # 先展开所有分�?(点击每个GroupView)
    print("展开分组...")
    for item in contact_list.GetChildren():
        try:
            name = item.Name or ""
            if "CellGroupView" in (item.ClassName or ""):
                r = item.BoundingRectangle
                pyautogui.click(r.left + 10, r.top + r.height()//2)
                time.sleep(0.3)
        except Exception:
            pass
    time.sleep(0.5)
    print("分组已展开\n")

    seen_names = set()
    cl_rect = contact_list.BoundingRectangle
    max_scrolls = 300  # 2027个联系人需要很多轮

    for scroll_round in range(max_scrolls):
        # 重新获取列表 (虚拟列表, 元素会回�?
        contact_list = wx._win.Control(AutomationId="primary_table_.contact_list")
        if not contact_list.Exists():
            break

        round_collected = 0
        for item in contact_list.GetChildren():
            try:
                name = item.Name or ""
                cls = item.ClassName or ""

                if "CellGroupView" in cls:
                    for key, ctype in GROUP_TYPE_MAP.items():
                        if name.startswith(key):
                            current_type = ctype
                            break
                    continue
                if "CellClassifyView" in cls:  # 字母索引�?A/B/C...
                    continue
                if "MangerBtn" in cls or not name.strip():
                    continue

                # 去重
                if name in seen_names:
                    continue
                seen_names.add(name)

                total_items += 1
                print(f"  [{total_items}] {name[:30]}", end="", flush=True)

                try:
                    r = item.BoundingRectangle
                    if r.width() == 0 or r.height() == 0:
                        print(" �?skip(offscreen)")
                        continue
                    pyautogui.click(r.left + 30, r.top + r.height()//2)
                except Exception:
                    continue
                time.sleep(0.25)

                profile = read_contact_profile(wx)
                if profile.get("nickname"):
                    data = {"nickname": profile["nickname"], "contact_type": current_type}
                    if profile.get("wxid"): data["wxid"] = profile["wxid"]
                    if profile.get("signature"): data["signature"] = profile["signature"]
                    if profile.get("region"): data["region"] = profile["region"]
                    if profile.get("source"): data["source"] = profile["source"]
                    if profile.get("add_time"): data["first_met"] = profile["add_time"]
                    fid = db.upsert_friend(data)
                    print(f"  �?{profile.get('wxid','?')}")
                    collected += 1
                    round_collected += 1
                else:
                    print(f"  �?(�?")
            except Exception as e:
                pass

        # 滚动加载更多 (大幅滚动 + 等待虚拟列表渲染)
        pyautogui.moveTo(cl_rect.left + 50, cl_rect.top + cl_rect.height() - 30)
        time.sleep(0.05)
        pyautogui.scroll(-2000)  # 大幅滚动
        time.sleep(0.6)

        if round_collected == 0 and scroll_round > 2:
            break

    print(f"\n�?共采�?{collected} 个联系人 ({scroll_round+1}轮滚�?")
    return collected


# ══════════════════════════════════════════════════════�?
# 添加好友
# ══════════════════════════════════════════════════════�?

def add_friend(wx, db, wxid_or_phone, verify_msg="你好，我是通过WinPeek添加�?):
    """搜索微信�?手机�?�?添加好友 �?发送验证消�?""
    import pyperclip

    print(f"添加好友: {wxid_or_phone}")

    # Step 1: 用搜索框搜微信号
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.3)
    pyperclip.copy(wxid_or_phone)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.8)

    # Step 2: 在搜索结果中�?添加到通讯�?
    search_list = wx._win.Control(AutomationId="search_list")
    if not search_list.Exists():
        print("�?搜索列表未出�?)
        pyautogui.press("esc")
        return False

    for item in search_list.GetChildren():
        try:
            name = item.Name or ""
            if "添加到通讯�? in name or "发消�? in name:
                item.Click()
                time.sleep(0.8)
                break
        except Exception:
            pass

    # Step 3: 查找"添加到通讯�?按钮 (可能已弹出验证页�?
    for _ in range(5):
        pyautogui.press("tab")
        time.sleep(0.1)

    pyautogui.press("enter")
    time.sleep(0.5)

    # Step 4: 如果有验证消息输入框，填�?
    try:
        pyperclip.copy(verify_msg)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        pyautogui.press("enter")
        print(f"   �?已发送好友申�? {verify_msg}")
    except Exception:
        pass

    # 入库：标记为待验�?
    db.upsert_friend({
        "wxid": wxid_or_phone,
        "nickname": wxid_or_phone,
        "contact_type": "new_friend",
        "source": "search_add",
    })
    pyautogui.press("esc")
    return True


def process_friend_requests(wx, db, auto_accept=True):
    """处理'新的朋友'中的好友申请"""
    import pyperclip

    go_to_contacts(wx)

    # 点击"新的朋友"
    contact_list = wx._win.Control(AutomationId="primary_table_.contact_list")
    if not contact_list.Exists():
        return 0

    processed = 0
    for item in contact_list.GetChildren():
        try:
            name = item.Name or ""
            if "新的朋友" in name:
                item.Click()
                time.sleep(1.0)
                break
        except Exception:
            pass

    # 现在�?新的朋友"页面，逐个处理申请
    corner = wx._win.Control(AutomationId="MainView.main_window_corner_view.MainView")
    if not corner.Exists():
        return 0

    # 找所�?接受"按钮
    for child in corner.GetChildren():
        try:
            _walk_accept_buttons(child, wx, db, auto_accept, processed)
        except Exception:
            pass

    pyautogui.press("esc")
    return processed


def _walk_accept_buttons(ctrl, wx, db, auto_accept, processed):
    """递归找接受按�?""
    try:
        name = ctrl.Name or ""
        aid = ctrl.AutomationId or ""
    except Exception:
        return

    if "接受" in name and "Button" in str(type(ctrl)):
        if auto_accept:
            ctrl.Click()
            time.sleep(0.5)
            processed += 1
            print(f"   �?已接受好友申�?)
        return

    try:
        for child in ctrl.GetChildren():
            _walk_accept_buttons(child, wx, db, auto_accept, processed)
    except Exception:
        pass


# ══════════════════════════════════════════════════════�?
# CLI
# ══════════════════════════════════════════════════════�?

def main():
    parser = argparse.ArgumentParser(description="通讯录管�?)
    parser.add_argument("--collect", action="store_true", help="全量采集通讯�?)
    parser.add_argument("--list", action="store_true", help="列出已采集联系人")
    parser.add_argument("--add", help="添加好友 (微信�?手机�?")
    parser.add_argument("--msg", default="你好，我是通过WinPeek添加�?, help="验证消息")
    parser.add_argument("--accept", action="store_true", help="处理好友申请")
    parser.add_argument("--wxid", default="szyuyangmin")
    args = parser.parse_args()

    db = WeChatDB(wxid=args.wxid)
    db.init()

    if args.collect:
        wx = WeChatUIA()
        n = collect_all_contacts(wx, db)
        s = db.stats()
        print(f"\n联系人总数: {s['friends']}  陌生�? {s['strangers']}")

    if args.add:
        wx = WeChatUIA()
        add_friend(wx, db, args.add, args.msg)

    if args.accept:
        wx = WeChatUIA()
        n = process_friend_requests(wx, db, auto_accept=True)
        print(f"处理完成: {n} 个申�?)

    if args.list:
        friends = db.list_friends()
        for f in friends:
            print(f"  [{f.get('contact_type','?')}] {f.get('nickname','')[:30]}  wxid={f.get('wxid','')}")


if __name__ == "__main__":
    main()
