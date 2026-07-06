"""
software_scanner.py — Windows 软件资产自动扫描器

自动发现本机已安装的软件，输出结构化 JSON。

扫描来源:
  1. 注册表 Uninstall (HKLM + HKCU)
  2. Start Menu 快捷方式
  3. 常见便携软件目录
  
输出格式:
  {
    "scanned_at": "2026-07-07T...",
    "total": 120,
    "apps": [
      {
        "name": "微信",
        "category": "IM",
        "publisher": "Tencent",
        "version": "4.1.11.24",
        "install_path": "D:\\Program Files\\Weixin\\",
        "exe_path": "D:\\Program Files\\Weixin\\Weixin.exe",
        "launch_args": "",
        "process_name": "Weixin.exe",
        "description": "微信桌面客户端"
      },
      ...
    ]
  }

用法:
  python software_scanner.py                 # 扫描并打印 JSON
  python software_scanner.py --output xxx    # 保存到文件
  python software_scanner.py --category IM   # 只扫描 IM 类软件
"""

import json
import os
import sys
import winreg
from datetime import datetime
from pathlib import Path
from typing import Optional

# ═══════════════════════════════════════════════════════
# 分类规则
# ═══════════════════════════════════════════════════════

CATEGORY_RULES = {
    "IM":       ["微信", "WeChat", "Weixin", "QQ", "钉钉", "DingTalk", "飞书", "Feishu", "Telegram", "Discord", "Slack", "Skype", "Line", "Signal", "WhatsApp"],
    "浏览器":    ["Chrome", "Edge", "Firefox", "Brave", "Opera", "Safari", "Chromium", "Vivaldi", "Arc"],
    "办公":      ["Office", "Word", "Excel", "PowerPoint", "WPS", "Notion", "Obsidian", "Evernote", "Typora", "Xmind", "Adobe Acrobat", "PDF", "福昕"],
    "开发":      ["VS Code", "Visual Studio", "JetBrains", "PyCharm", "IntelliJ", "WebStorm", "GoLand", "Sublime", "Notepad++", "Vim", "Cursor", "Git", "Node.js", "Python"],
    "设计":      ["Photoshop", "Illustrator", "Figma", "Sketch", "GIMP", "Blender", "AutoCAD", "Premiere", "After Effects"],
    "视频":      ["抖音", "Douyin", "快手", "Kuaishou", "剪映", "CapCut", "OBS", "哔哩哔哩", "Bilibili", "小红书"],
    "电商":      ["淘宝", "京东", "拼多多", "阿里巴巴", "1688", "闲鱼", "美团"],
    "远程":      ["向日葵", "TeamViewer", "AnyDesk", "ToDesk", "RustDesk", "mstsc", "VNC", "Parsec"],
    "数据库":    ["Navicat", "DBeaver", "MySQL", "PostgreSQL", "MongoDB", "Redis", "HeidiSQL", "DataGrip"],
    "工具":      ["7-Zip", "WinRAR", "Everything", "Snipaste", "PowerToys", "Rufus", "Ventoy", "Bandicam", "ScreenToGif", "Ditto"],
    "安全":      ["火绒", "360", "腾讯电脑管家", "Defender", "Kaspersky", "ESET"],
    "其他":      [],
}

# ═══════════════════════════════════════════════════════
# 已知软件的特殊信息
# ═══════════════════════════════════════════════════════

KNOWN_APPS = {
    "Weixin.exe": {
        "name": "微信",
        "category": "IM",
        "description": "微信桌面客户端 (Weixin)",
        "launch_args": "",
        "process_name": "Weixin.exe",
        "sub_processes": ["WeChatAppEx.exe"],
    },
    "QQ.exe": {
        "name": "QQ",
        "category": "IM",
        "description": "腾讯 QQ 桌面客户端",
        "launch_args": "",
        "process_name": "QQ.exe",
    },
    "dingtalk.exe": {
        "name": "钉钉",
        "category": "IM",
        "description": "钉钉桌面客户端 (DingTalk)",
        "launch_args": "",
        "process_name": "dingtalk.exe",
    },
}

# ═══════════════════════════════════════════════════════
# 扫描引擎
# ═══════════════════════════════════════════════════════

def scan_registry_uninstall() -> list[dict]:
    """从注册表 Uninstall 键扫描已安装软件"""
    apps = []
    seen = set()

    registry_roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for root, subkey in registry_roots:
        try:
            with winreg.OpenKey(root, subkey) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, name) as app_key:
                            display = _reg_str(app_key, "DisplayName")
                            if not display or display in seen:
                                continue
                            seen.add(display)

                            install_path = _reg_str(app_key, "InstallLocation") or ""
                            exe = _find_main_exe(install_path)

                            apps.append({
                                "name": display,
                                "publisher": _reg_str(app_key, "Publisher") or "",
                                "version": _reg_str(app_key, "DisplayVersion") or "",
                                "install_path": install_path,
                                "exe_path": exe or _find_exe_from_uninstall(_reg_str(app_key, "UninstallString")),
                                "category": _categorize(display),
                                "description": "",
                                "launch_args": "",
                                "process_name": os.path.basename(exe) if exe else "",
                            })
                    except Exception:
                        pass
        except Exception:
            pass

    return apps


def scan_start_menu() -> list[dict]:
    """从 Start Menu 扫描快捷方式"""
    apps = []
    seen = set()
    start_dirs = [
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
    ]

    for start_dir in start_dirs:
        if not os.path.isdir(start_dir):
            continue
        for root, _, files in os.walk(start_dir):
            for f in files:
                if not f.endswith(".lnk"):
                    continue
                lnk_path = os.path.join(root, f)
                target = _resolve_shortcut(lnk_path)
                if not target or not os.path.exists(target):
                    continue
                name = f.replace(".lnk", "")
                if name in seen:
                    continue
                seen.add(name)

                # 去掉 "微信.lnk" 这类后缀
                apps.append({
                    "name": name,
                    "publisher": "",
                    "version": _get_file_version(target) or "",
                    "install_path": os.path.dirname(target),
                    "exe_path": target,
                    "category": _categorize(name),
                    "description": "",
                    "launch_args": "",
                    "process_name": os.path.basename(target),
                })

    return apps


def scan_running_processes() -> list[dict]:
    """从运行中的进程补充信息"""
    import subprocess
    result = []
    try:
        output = subprocess.check_output(
            'wmic process get Name,ProcessId,ExecutablePath /format:csv',
            shell=True, timeout=10
        ).decode('utf-8', errors='ignore')
        for line in output.strip().split('\n')[1:]:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3 and parts[2]:
                pname = parts[1]
                ppath = parts[2]
                if pname.endswith('.exe') and os.path.exists(ppath):
                    ver = _get_file_version(ppath)
                    result.append({
                        "process_name": pname,
                        "exe_path": ppath,
                        "version": ver or "",
                    })
    except Exception:
        pass
    return result


# ═══════════════════════════════════════════════════════
# 合并 + 增强
# ═══════════════════════════════════════════════════════

def merge_and_enhance(registry_apps: list[dict], start_apps: list[dict],
                      running: list[dict]) -> list[dict]:
    """合并多个来源，去重，补全已知信息"""
    merged = {}
    running_map = {r["process_name"]: r for r in running if r["process_name"]}

    for app in registry_apps + start_apps:
        key = app["name"].lower()
        if key in merged:
            # 合并: 取版本更高的
            existing = merged[key]
            if _version_newer(app["version"], existing["version"]):
                existing["version"] = app["version"]
            if app["exe_path"] and not existing["exe_path"]:
                existing["exe_path"] = app["exe_path"]
            if app["install_path"] and not existing["install_path"]:
                existing["install_path"] = app["install_path"]
            continue

        # 补全已知软件信息
        pname = app.get("process_name", "")
        if pname in KNOWN_APPS:
            known = KNOWN_APPS[pname]
            app["name"] = known.get("name", app["name"])
            app["category"] = known.get("category", app["category"])
            app["description"] = known.get("description", "")
            app["launch_args"] = known.get("launch_args", "")

        # 补全版本（从运行进程）
        if pname in running_map and not app["version"]:
            app["version"] = running_map[pname].get("version", "")

        merged[key] = app

    # 排序
    result = sorted(merged.values(), key=lambda a: (a["category"], a["name"]))
    return result


# ═══════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════

def _reg_str(key, name) -> Optional[str]:
    try:
        val = winreg.QueryValueEx(key, name)[0]
        return str(val).strip() if val else ""
    except Exception:
        return ""


def _find_main_exe(path: str) -> str:
    """在安装目录找主 exe"""
    if not path or not os.path.isdir(path):
        return ""
    exes = list(Path(path).glob("*.exe"))
    if not exes:
        return ""
    # 优先选最大的（通常是主程序）
    exes.sort(key=lambda x: x.stat().st_size, reverse=True)
    return str(exes[0])


def _find_exe_from_uninstall(uninst: str) -> str:
    """从卸载命令中提取 exe 路径"""
    if not uninst:
        return ""
    for part in uninst.strip('"').split('"'):
        if part.endswith('.exe') and os.path.exists(part):
            return part
    return ""


def _categorize(name: str) -> str:
    """根据名称自动分类"""
    for cat, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw.lower() in name.lower():
                return cat
    return "其他"


def _resolve_shortcut(lnk_path: str) -> Optional[str]:
    """解析 .lnk 文件得到目标路径"""
    try:
        import pythoncom
        from win32com.client import Dispatch
        pythoncom.CoInitialize()
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        target = shortcut.TargetPath
        pythoncom.CoUninitialize()
        return target if target else None
    except Exception:
        return None


def _get_file_version(path: str) -> Optional[str]:
    """获取 exe 文件版本"""
    try:
        import win32api
        info = win32api.GetFileVersionInfo(path, "\\")
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    except Exception:
        return None


def _version_newer(a: str, b: str) -> bool:
    """简单比较版本号"""
    try:
        pa = [int(x) for x in a.split('.')]
        pb = [int(x) for x in b.split('.')]
        return pa > pb
    except Exception:
        return bool(a)


# ═══════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════

def scan_all(output_path: str = None) -> dict:
    """全量扫描，输出结构化 JSON"""
    registry = scan_registry_uninstall()
    startmenu = scan_start_menu()
    running = scan_running_processes()

    merged = merge_and_enhance(registry, startmenu, running)

    result = {
        "scanned_at": datetime.now().isoformat(),
        "total": len(merged),
        "categories": {},
        "apps": merged,
    }

    # 按分类统计
    for app in merged:
        cat = app["category"]
        result["categories"][cat] = result["categories"].get(cat, 0) + 1

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Windows 软件资产扫描器")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径",
                        default=os.path.expanduser("~/.hermes/winpeek/assets/software_inventory.json"))
    parser.add_argument("--category", "-c", help="只输出指定分类")
    args = parser.parse_args()

    data = scan_all(args.output)

    if args.category:
        apps = [a for a in data["apps"] if a["category"] == args.category]
        print(json.dumps({"apps": apps, "total": len(apps)}, ensure_ascii=False, indent=2))
    else:
        print(f"✅ 扫描完成: {data['total']} 个软件")
        for cat, count in sorted(data["categories"].items()):
            print(f"   {cat}: {count} 个")
        print(f"已保存到: {args.output}")
