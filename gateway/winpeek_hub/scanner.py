"""WinPeek local system scanner — software inventory + hardware info.

Scans Windows via registry, filesystem, and WMI.
Feeds into winpeek_software / winpeek_software_account tables.
"""

import json as _json
import logging
import os
import platform
import subprocess
import sys
import winreg
from datetime import datetime
from pathlib import Path

from .db import get_conn
from .software import ensure_tables, upsert_software

logger = logging.getLogger(__name__)

# ── Software category taxonomy ──

SOFTWARE_CATEGORIES = {
    # 社交 / IM
    "微信": "社交",
    "WeChat": "社交",
    "企业微信": "社交",
    "WorkWeChat": "社交",
    "QQ": "社交",
    "Telegram": "社交",
    "Discord": "社交",
    "钉钉": "社交",
    "DingTalk": "社交",
    "飞书": "社交",
    "Feishu": "社交",
    "Lark": "社交",
    "WhatsApp": "社交",
    "Signal": "社交",
    "Line": "社交",
    "Skype": "社交",
    "Slack": "社交",
    "Microsoft Teams": "社交",
    # 商城
    "淘宝": "商城",
    "天猫": "商城",
    "京东": "商城",
    "拼多多": "商城",
    "闲鱼": "商城",
    "1688": "商城",
    "小红书": "商城",
    "抖音": "商城",
    # 财务/银行
    "中国银行": "金融",
    "工商银行": "金融",
    "建设银行": "金融",
    "农业银行": "金融",
    "招商银行": "金融",
    "交通银行": "金融",
    "浦发银行": "金融",
    "支付宝": "金融",
    "微信支付": "金融",
    "用友": "金融",
    "金蝶": "金融",
    "SAP": "金融",
    # 政务
    "个人所得税": "政务",
    "政企通": "政务",
    "粤省事": "政务",
    "国家医保": "政务",
    "交管12123": "政务",
    # 编程
    "Visual Studio Code": "编程",
    "VS Code": "编程",
    "PyCharm": "编程",
    "IntelliJ": "编程",
    "WebStorm": "编程",
    "Vim": "编程",
    "Notepad++": "编程",
    "Sublime Text": "编程",
    "Cursor": "编程",
    "Git": "编程",
    "SourceTree": "编程",
    "Docker": "编程",
    "Postman": "编程",
    "Node.js": "编程",
    "Python": "编程",
    "Xshell": "编程",
    "Xftp": "编程",
    "MobaXterm": "编程",
    "PuTTY": "编程",
    "Terminal": "编程",
    "PowerShell": "编程",
    "Windows Terminal": "编程",
    # 办公
    "Microsoft Word": "办公",
    "Microsoft Excel": "办公",
    "Microsoft PowerPoint": "办公",
    "Microsoft Outlook": "办公",
    "Microsoft OneNote": "办公",
    "WPS Office": "办公",
    "WPS 文字": "办公",
    "WPS 表格": "办公",
    "WPS 演示": "办公",
    "Adobe Acrobat": "办公",
    "Foxit Reader": "办公",
    "Notion": "办公",
    "Obsidian": "办公",
    "Typora": "办公",
    "Microsoft Edge": "办公",
    "Google Chrome": "办公",
    "Firefox": "办公",
    "搜狗输入法": "办公",
    "百度输入法": "办公",
    # 图形
    "Adobe Photoshop": "图形",
    "Adobe Illustrator": "图形",
    "Adobe Premiere": "图形",
    "Adobe After Effects": "图形",
    "Figma": "图形",
    "Sketch": "图形",
    "GIMP": "图形",
    "Blender": "图形",
    "AutoCAD": "图形",
    "CorelDRAW": "图形",
    "DaVinci Resolve": "图形",
    "剪映": "图形",
    "CapCut": "图形",
    "OBS Studio": "图形",
    "Snipaste": "图形",
    "ScreenToGif": "图形",
    # 磁盘工具
    "DiskGenius": "磁盘",
    "CrystalDiskInfo": "磁盘",
    "CrystalDiskMark": "磁盘",
    "SpaceSniffer": "磁盘",
    "TreeSize": "磁盘",
    "WinDirStat": "磁盘",
    "Everything": "磁盘",
    "7-Zip": "磁盘",
    "WinRAR": "磁盘",
    "Bandizip": "磁盘",
    "HWiNFO": "磁盘",
    "CPU-Z": "磁盘",
    "GPU-Z": "磁盘",
    "鲁大师": "磁盘",
    "AIDA64": "磁盘",
    # 影音
    "PotPlayer": "影音",
    "VLC": "影音",
    "网易云音乐": "影音",
    "QQ音乐": "影音",
    "酷狗音乐": "影音",
    "Spotify": "影音",
    "哔哩哔哩": "影音",
    "暴风影音": "影音",
    "迅雷": "影音",
    # 安全
    "360安全卫士": "安全",
    "腾讯电脑管家": "安全",
    "火绒": "安全",
    "Windows Defender": "安全",
}


def _guess_category(name: str) -> str:
    """Guess software category from name."""
    name_lower = name.lower()
    for keyword, cat in SOFTWARE_CATEGORIES.items():
        if keyword.lower() in name_lower:
            return cat
    # heuristic fallbacks
    if any(kw in name_lower for kw in ("银行", "bank", "金融", "税务", "税")):
        return "金融"
    if any(kw in name_lower for kw in ("微信", "wechat", "qq", "telegram", "钉钉", "飞书", "whatsapp", "signal")):
        return "社交"
    if any(kw in name_lower for kw in ("淘宝", "京东", "拼多", "shop", "mall", "商城")):
        return "商城"
    if any(kw in name_lower for kw in ("政务", "政府", "税务", "公安", "交管", "医保", "社保")):
        return "政务"
    if any(kw in name_lower for kw in ("财务", "会计", "金蝶", "用友", "sap", "erp", "发票")):
        return "金融"
    if any(kw in name_lower for kw in ("vscode", "pycharm", "intellij", "vim", "git", "docker",
                                         "python", "node", "npm", "cursor", "powershell", "terminal",
                                         "编程", "开发", "ide", "debug")):
        return "编程"
    if any(kw in name_lower for kw in ("word", "excel", "ppt", "powerpoint", "outlook", "wps",
                                         "笔记", "notion", "obsidian", "pdf", "chrome", "edge",
                                         "浏览器", "输入法", "office")):
        return "办公"
    if any(kw in name_lower for kw in ("photoshop", "illustrator", "premiere", "figma", "gimp",
                                         "blender", "cad", "剪映", "capcut", "obs", "screen",
                                         "照片", "图片", "视频", "剪辑", "设计", "画图")):
        return "图形"
    if any(kw in name_lower for kw in ("disk", "partition", "crystal", "空间", "解压", "zip",
                                         "rar", "7z", "备份", "还原", "鲁大师", "aida", "cpu",
                                         "gpu", "硬件", "驱动", "磁盘")):
        return "磁盘"
    if any(kw in name_lower for kw in ("播放", "音乐", "视频", "影音", "b站", "bili", "spotify",
                                         "酷狗", "网易云", "暴风", "迅雷")):
        return "影音"
    if any(kw in name_lower for kw in ("安全", "杀毒", "管家", "防火墙", "defender", "火绒")):
        return "安全"
    # if launcher paths match known program dirs
    for path_kw, cat in [
        ("adobe", "图形"), ("autodesk", "图形"), ("figma", "图形"),
        ("microsoft office", "办公"), ("wps", "办公"),
        ("visual studio", "编程"), ("jetbrains", "编程"),
        ("tencent", "社交"), ("weixin", "社交"),
    ]:
        if path_kw in name_lower:
            return cat
    return "其它"


# ═══════════════════════════════════════════════════════
#  SOFTWARE SCANNER (Windows)
# ═══════════════════════════════════════════════════════

def _scan_registry_uninstall() -> list[dict]:
    """Read installed software from Windows registry (HKLM + HKCU)."""
    results: list[dict] = []
    for hive, key_path, access in [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
         winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
         winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
         winreg.KEY_READ),
    ]:
        try:
            with winreg.OpenKey(hive, key_path, 0, access) as root:
                for i in range(winreg.QueryInfoKey(root)[0]):
                    try:
                        subkey_name = winreg.EnumKey(root, i)
                        with winreg.OpenKey(root, subkey_name) as sk:
                            name = _read_reg(sk, "DisplayName")
                            if not name:
                                continue
                            if "update" in name.lower() or "hotfix" in name.lower():
                                continue  # skip patches
                            results.append({
                                "name": name,
                                "display_version": _read_reg(sk, "DisplayVersion"),
                                "publisher": _read_reg(sk, "Publisher"),
                                "install_path": _read_reg(sk, "InstallLocation"),
                                "install_source": _read_reg(sk, "InstallSource"),
                                "uninstall_string": _read_reg(sk, "UninstallString"),
                                "display_icon": _read_reg(sk, "DisplayIcon"),
                            })
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            continue
    return results


def _read_reg(key, name: str) -> str:
    try:
        val, _ = winreg.QueryValueEx(key, name)  # type: ignore[reportImportError]
        return str(val) if val else ""
    except OSError:
        return ""


def _find_exe_in_dir(path: str, name_hint: str = "") -> str:
    """Find main .exe in a directory."""
    if not path or not os.path.isdir(path):
        return ""
    candidates = []
    for f in os.listdir(path):
        if f.lower().endswith(".exe"):
            fp = os.path.join(path, f)
            candidates.append(fp)
            if name_hint and name_hint.lower() in f.lower():
                return fp
    # prefer non-uninstall executables
    exes = [c for c in candidates if "unins" not in c.lower()]
    return exes[0] if exes else (candidates[0] if candidates else "")


def scan_software() -> dict:
    """Scan and upsert all detected software. Returns summary counts."""
    ensure_tables()
    reg_entries = _scan_registry_uninstall()
    created = updated = icons_extracted = 0
    seen = set()
    for e in reg_entries:
        name = e["name"].strip()
        if not name or name in seen:
            continue
        seen.add(name)
        install_path = e.get("install_path") or ""
        exe_path = e.get("display_icon") or ""  # DisplayIcon often IS the exe
        if (not exe_path or exe_path.endswith(".ico")) and install_path:
            exe_path = _find_exe_in_dir(install_path, name_hint=name)
        cat = _guess_category(name)

        # Extract and cache icon
        icon_path = ""
        if exe_path:
            try:
                from .icon_extractor import cache_icon
                ip = cache_icon(name, exe_path)
                if ip:
                    icon_path = ip
                    icons_extracted += 1
            except Exception:
                pass

        result = upsert_software(
            name,
            install_path=install_path or "",
            exe_path=exe_path or "",
            icon_path=icon_path,
            company=e.get("publisher") or "",
            version=e.get("display_version") or "",
            category=cat,
        )
        if result.get("ok"):
            if result.get("id") and result.get("id") != (e.get("_prev_id")):
                created += 1
            else:
                updated += 1
    return {"ok": True, "scanned": len(reg_entries), "synced": len(seen),
            "created": created, "updated": updated,
            "icons_extracted": icons_extracted}


# ═══════════════════════════════════════════════════════
#  HARDWARE INFO (cross-platform)
# ═══════════════════════════════════════════════════════

def get_hardware_info() -> dict:
    """Return hardware summary: CPU, RAM, GPU, disks, OS."""
    info: dict = {}

    # OS
    info["os"] = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "hostname": platform.node(),
        "processor": platform.processor(),
    }

    # CPU
    cpu = {"name": platform.processor(), "cores": os.cpu_count()}
    info["cpu"] = cpu

    # RAM (via psutil if installed)
    try:
        import psutil
        vmem = psutil.virtual_memory()
        info["memory"] = {
            "total_gb": round(vmem.total / (1024**3), 1),
            "available_gb": round(vmem.available / (1024**3), 1),
        }
    except ImportError:
        info["memory"] = {"total_gb": "unknown"}

    # Disks
    disks = []
    if sys.platform == "win32":
        import win32api
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split("\000")[:-1]
        for d in drives:
            try:
                free_bytes = win32api.GetDiskFreeSpaceEx(d)
                total_bytes = win32api.GetDiskFreeSpaceEx(d)
            except Exception:
                continue
            try:
                import ctypes
                total = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wintypes.LPCWSTR(d), None,
                    ctypes.pointer(total), None)
                total_gb = round(total.value / (1024**3), 1)
            except Exception:
                total_gb = 0
            disks.append({"drive": d, "total_gb": total_gb})
    else:
        for p in Path("/").iterdir():
            if p.is_dir():
                try:
                    usage = os.statvfs(p)
                    total_gb = round(usage.f_frsize * usage.f_blocks / (1024**3), 1)
                    if total_gb > 1:
                        disks.append({"mount": str(p), "total_gb": total_gb})
                except Exception:
                    pass
    info["disks"] = disks[:10]

    # GPU — try nvidia-smi
    gpus = []
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5)
        for line in r.stdout.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                gpus.append({"name": parts[0], "memory_mb": parts[1]})
    except Exception:
        pass
    info["gpus"] = gpus

    # Network
    info["network"] = {"hostname": platform.node()}

    return info


def scan_and_sync() -> dict:
    """Full scan: hardware + software → DB sync. Returns combined report."""
    hw = get_hardware_info()
    sw = scan_software()
    return {"ok": True, "hardware": hw, "software": sw}
