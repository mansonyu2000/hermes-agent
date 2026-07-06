"""
wechat_collect.py �?微信数据全量采集引擎

流程: 搜索联系�?�?打开对话 �?滚顶读资�?�?滚消�?�?入库

用法:
  python wechat_collect.py --name "于杨�? --full    # 全量采集
  python wechat_collect.py --name "于杨�? --inc      # 增量采集
  python wechat_collect.py --name "于杨�? --profile  # 只采资料
"""
import sys, os, time, re, json, argparse

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# (removed - now using package imports)
from .uia import WeChatUIA, AID
from .db import WeChatDB
import pyautogui
pyautogui.FAILSAFE = False
import pyperclip


# ══════════════════════════════════════════════════════�?
# 时间工具
# ══════════════════════════════════════════════════════�?

from ...shared.rpa_tools import parse_chat_time as _parse_msg_time


# ══════════════════════════════════════════════════════�?
# 资料卡解�?
# ══════════════════════════════════════════════════════�?

def parse_profile_text(raw_text):
    """�?朋友资料'或聊天系统消息中解析结构化字�?""
    info = {"profile_raw": raw_text}

    # 微信�?(字母数字下划线连字符)
    m = re.search(r'微信号[:：]\s*([a-zA-Z0-9_-]+)', raw_text)
    if m: info["wxid"] = m.group(1)

    # 地区
    m = re.search(r'地区[:：]\s*(.+?)(?:\n|$)', raw_text)
    if m: info["region"] = m.group(1).strip()

    # 手机�?(11位数�?
    m = re.search(r'手机号[:：]\s*(\d{11})', raw_text)
    if m: info["phone"] = m.group(1)

    # QQ (数字)
    m = re.search(r'[Qq][Qq][:：]\s*(\d{5,15})', raw_text)
    if m: info["qq"] = m.group(1)

    # 昵称：资料卡标题行（去掉"朋友资料"�?
    lines = raw_text.strip().split('\n')
    if lines:
        first = lines[0].replace("朋友资料", "").strip()
        if first and not first.startswith("微信�?):
            info["nickname"] = first

    # 个性签�?
    m = re.search(r'个性签名[:：]\s*(.+?)(?:\n|$)', raw_text)
    if m: info["signature"] = m.group(1).strip()

    # 共同群聊
    m = re.search(r'共同群聊\s*(\d+)', raw_text)
    if m: info["shared_groups"] = int(m.group(1))

    return info
    """�?朋友资料"系统消息中解析结构化字段"""
    info = {"profile_raw": raw_text}

    # 微信�?(匹配到下一个字段名或行�?
    m = re.search(r'微信号[:：]\s*([a-zA-Z0-9_-]+)', raw_text)
    if m: info["wxid"] = m.group(1)

    # 地区
    m = re.search(r'地区[:：]\s*(.+?)(?:\n|$)', raw_text)
    if m: info["region"] = m.group(1).strip()

    # 手机�?
    m = re.search(r'手机号[:：]\s*(\d+)', raw_text)
    if m: info["phone"] = m.group(1)

    # QQ
    m = re.search(r'[Qq][Qq][:：]\s*(\d+)', raw_text)
    if m: info["qq"] = m.group(1)

    # 昵称：资料卡标题行（第一行去�?朋友资料"�?
    lines = raw_text.strip().split('\n')
    if lines:
        first = lines[0].replace("朋友资料", "").strip()
        if first and not first.startswith("微信�?):
            info["nickname"] = first

    # 个性签�?
    m = re.search(r'个性签名[:：]\s*(.+?)(?:\n|$)', raw_text)
    if m: info["signature"] = m.group(1).strip()

    # 共同群聊
    m = re.search(r'共同群聊\s*(\d+)', raw_text)
    if m: info["shared_groups"] = int(m.group(1))

    return info


# ══════════════════════════════════════════════════════�?
# 全量采集
# ══════════════════════════════════════════════════════�?

def collect_profile(wx, db, contact_name):
    """搜索联系�?�?打开对话 �?滚到�?�?读资�?�?入库"""
    print(f"\n{'='*50}")
    print(f"采集资料: {contact_name}")
    print(f"{'='*50}")

    # Step 1: 搜索并打开
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.3)
    pyperclip.copy(contact_name)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.8)

    search_list = wx._win.Control(AutomationId="search_list")
    if not search_list.Exists():
        print("�?搜索列表未出�?)
        pyautogui.press("esc")
        return None

    # 找第一个匹配联系人
    clicked = False
    for item in search_list.GetChildren():
        try:
            aid = item.AutomationId or ""
            name = item.Name or ""
            if "search_item_" in aid and contact_name in name:
                print(f"   点击: {name[:40]}")
                item.Click()
                time.sleep(0.8)
                clicked = True
                break
        except Exception:
            pass

    if not clicked:
        print("�?未找到匹配联系人")
        pyautogui.press("esc")
        return None

    # Step 2: 滚到对话顶部 �?�?朋友资料"系统消息
    print("   滚动到对话顶部寻找资料卡...")
    profile_text = ""

    # 先定位消息区域并持续向上�?
    for _ in range(60):
        msg_list = wx._win.Control(AutomationId=AID["msg_list"])
        if not msg_list.Exists():
            break

        found_profile = False
        for item in msg_list.GetChildren():
            try:
                text = item.Name or ""
                if "朋友资料" in text:
                    profile_text = text
                    found_profile = True
                    print(f"   �?找到资料�?({len(text)} 字符)")
                    break
            except Exception:
                pass

        if found_profile:
            break

        # 鼠标定位消息区域向上�?
        mr = msg_list.BoundingRectangle
        pyautogui.moveTo(mr.left + mr.width() // 2, mr.top + mr.height() // 2)
        time.sleep(0.05)
        pyautogui.scroll(3000)
        time.sleep(0.4)

    if not profile_text:
        print("   ⚠️ 未找到资料卡（可能不是好友关系）")
        # 尝试从联系人名获取昵�?
        name_ctrl = wx._win.Control(AutomationId=AID["chat_name"])
        if name_ctrl.Exists():
            contact_name_from_ui = name_ctrl.Name
            if contact_name_from_ui:
                profile_text = f"昵称: {contact_name_from_ui}"

    # Step 3: 解析
    info = parse_profile_text(profile_text) if profile_text else {}
    if not info.get("nickname"):
        info["nickname"] = contact_name  # fallback

    # Step 4: 入库
    fid = db.upsert_friend(info)
    print(f"   💾 已入�?friend_id={fid}  wxid={info.get('wxid','?')}  nickname={info.get('nickname','?')[:30]}")
    if info.get("phone"):
        print(f"      手机={info['phone']}  QQ={info.get('qq','')}  地区={info.get('region','')}")

    return fid


def collect_messages(wx, db, friend_wxid, my_wxid=None, max_pages=80, incremental=True):
    """采集消息 �?入库

    算法:
      1. 查本地最新时�?T_local
      2. PageDown 到底 �?看最新时�?T_wechat
      3. PageUp 往上翻, 所有记录存缓存
      4. 遇到日期 < T_local �?停止 (已采集过)
      5. 缓存按时间正�?旧→�?批量写入本地�?
    """
    if my_wxid is None:
        my_wxid = db.wxid

    print(f"\n{'='*50}")
    print(f"采集消息: {friend_wxid}")
    print(f"{'='*50}")

    # Step 1: 本地最新时�?
    last_local_time = None
    if incremental:
        last_local_time = db.get_last_msg_time(from_uid=friend_wxid)
        if last_local_time:
            print(f"   本地最�? {last_local_time}")
        else:
            print(f"   本地无记录，全量采集")

    # Step 2: 先翻到底部看微信最新时�?
    print(f"   翻到底部...")
    msg_list = wx._win.Control(AutomationId=AID["msg_list"])
    if msg_list.Exists():
        mr = msg_list.BoundingRectangle
        pyautogui.moveTo(mr.left + mr.width() // 2, mr.top + mr.height() // 2)
        for _ in range(5):
            pyautogui.press("pagedown")
            time.sleep(0.3)

    # Step 3: 翻页采集 �?缓存
    buffer = []        # [(time_key, msg_data), ...]
    seen = set()
    current_time = ""
    stopped_by_time = False

    for page in range(max_pages):
        msg_list = wx._win.Control(AutomationId=AID["msg_list"])
        if not msg_list.Exists():
            break

        new_in_page = 0
        for item in msg_list.GetChildren():
            try:
                text = (item.Name or "").strip()
                aid = item.AutomationId or ""
                r = item.BoundingRectangle
                if not text:
                    continue

                is_date = not aid
                is_bubble = "chat_bubble_item_view" in aid

                # 去重
                key = (text[:60], r.top)
                if key in seen:
                    continue
                seen.add(key)

                # 时间继承
                if is_date:
                    current_time = text
                    # 停止条件: ISO 时间比对 (last_local_time �?ISO 格式)
                    if last_local_time:
                        iso = _parse_msg_time(text)
                        if iso and iso <= last_local_time:
                            stopped_by_time = True
                            break
                    continue  # 日期分隔符不存为消息

                # msg_ts: 从中文日期生�?ISO 时间�?(用于排序 + 增量比对)
                msg_ts = _parse_msg_time(current_time) if current_time else ""

                # 消息气泡/文件/图片
                msg_data = {
                    "from_uid": my_wxid if is_bubble else friend_wxid,
                    "to_uid": friend_wxid if is_bubble else my_wxid,
                    "sender_name": "�? if is_bubble else friend_wxid,
                    "is_from_me": 1 if is_bubble else 0,
                    "content": text,
                    "msg_type": "text",
                    "msg_time": current_time,
                    "msg_ts": msg_ts,
                    "is_date_sep": 0,
                    "time_key": msg_ts or current_time,  # ISO排序
                    "raw_json": json.dumps({"y": r.top, "aid": aid}, ensure_ascii=False),
                }

                if "图片" == text.strip():
                    msg_data["msg_type"] = "image"
                elif text.startswith("文件\n"):
                    msg_data["msg_type"] = "file"
                    lines = text.split("\n")
                    if len(lines) >= 2:
                        msg_data["file_name"] = lines[1]
                        msg_data["content"] = lines[1]
                elif "视频" in text and not is_bubble:
                    msg_data["msg_type"] = "video"

                buffer.append(msg_data)
                new_in_page += 1
            except Exception:
                pass

        if stopped_by_time:
            print(f"   [{page+1}] +{new_in_page} 条缓�?�?遇到已采集时�? 停止翻页")
            break

        print(f"   [{page+1}] +{new_in_page} 条缓�? 累计 {len(buffer)}, 时间: {current_time}")

        if new_in_page == 0:
            print(f"   无新内容，已到尽�?)
            break

        pyautogui.press("pageup")
        time.sleep(0.5)

    # Step 4: 缓存按时间正�?旧→�?批量写入
    if buffer:
        # 时间排序: 中文日期按字符序近似正确(�?�?�?
        buffer.sort(key=lambda m: m.get("time_key", ""))
        print(f"\n   正在写入 {len(buffer)} �?(时间正序)...")
        for msg_data in buffer:
            msg_data.pop("time_key", None)  # 移除排序临时字段
            db.insert_message(msg_data)
        print(f"   �?已入�?{len(buffer)} �?)

    return len(buffer)


def collect_all(wx, db, contact_name, incremental=False):
    """全量采集：资�?+ 消息"""
    fid = collect_profile(wx, db, contact_name)
    if fid is None:
        return

    friend = db.get_friend(contact_name)
    friend_wxid = friend.get("wxid") if friend else contact_name

    collect_messages(wx, db, friend_wxid, my_wxid=db.wxid, incremental=incremental)

    print(f"\n{'='*50}")
    s = db.stats()
    print(f"数据概况: {s['friends']}联系�?{s['messages']}消息 {s['files']}附件")
    print(f"数据�? {s['db_path']}")


# ══════════════════════════════════════════════════════�?
# CLI
# ══════════════════════════════════════════════════════�?

def main():
    parser = argparse.ArgumentParser(description="微信数据采集")
    parser.add_argument("--name", required=True, help="联系人名�?)
    parser.add_argument("--wxid", default="szyuyangmin", help="数据子目�?)
    parser.add_argument("--full", action="store_true", help="全量采集(资料+消息)")
    parser.add_argument("--inc", action="store_true", help="增量采集")
    parser.add_argument("--profile", action="store_true", help="只采集资�?)
    args = parser.parse_args()

    db = WeChatDB(wxid=args.wxid)
    db.init()

    wx = WeChatUIA()
    current = wx.get_current_contact()
    print(f"当前联系�? {current or '?'}")
    print(f"数据目录: {db.data_root}")

    try:
        if args.profile:
            collect_profile(wx, db, args.name)
        elif args.inc:
            collect_all(wx, db, args.name, incremental=True)
        else:
            collect_all(wx, db, args.name, incremental=False)
    except Exception as e:
        print(f"�?采集失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
