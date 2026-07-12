"""
conpty_inject.py — ConPTY 后台注入模块

原理:
  CC 进程通过 ConPTY (Windows 伪终端) 读取"键盘输入"。
  找到 CC 的 ConDrv 句柄 → 复制到本进程 → 写入输入。

架构:
  WindowsTerminal → OpenConsole(ConPTY host) → claude(Console client via ConDrv)

  ConDrv 是 ConPTY 的设备驱动，claude.exe 持有 8 个 ConDrv 句柄 (type=File)。
  这些句柄通过 NtQueryInformationProcess 枚举 + DuplicateHandle 复制可获得。

  注意: WriteFile/DeviceIoControl 到 ConDrv 句柄返回 ERROR_NOT_SUPPORTED。
  ConDrv 使用未公开的 IOCTL 码通信。真正的 ConPTY 输入管道在 OpenConsole.exe 中。

效果:
  - 不激活窗口 (不抢焦点)
  - 不模拟键鼠 (不占外设)

用法:
  from conpty_inject import inject_to_process
  inject_to_process("claude-code.exe", "hello world\\n")

依赖: Windows 10+ (ConPTY), Python 3.10+
"""

import ctypes
from ctypes import wintypes, byref, sizeof, POINTER, Structure, windll, c_ulong, c_size_t
import os
import sys
import time
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# Windows API bindings
# ═══════════════════════════════════════════════════════════════════════

kernel32 = windll.kernel32
ntdll = windll.ntdll
advapi32 = windll.advapi32

# ════════════════════════════════════════════════════════════════════
# 64-bit 兼容: restype/argtypes (否则 HANDLE 截断 → error=6)
# ════════════════════════════════════════════════════════════════════
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.DuplicateHandle.restype = wintypes.BOOL
kernel32.DuplicateHandle.argtypes = [wintypes.HANDLE, wintypes.HANDLE, wintypes.HANDLE,
                                     ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
                                     wintypes.BOOL, wintypes.DWORD]
kernel32.WriteFile.restype = wintypes.BOOL
kernel32.WriteFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                               ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.Process32First.restype = wintypes.BOOL
kernel32.Process32First.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
kernel32.Process32Next.restype = wintypes.BOOL
kernel32.Process32Next.argtypes = [wintypes.HANDLE, ctypes.c_void_p]

advapi32.OpenProcessToken.restype = wintypes.BOOL
advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                       ctypes.POINTER(wintypes.HANDLE)]
advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL
advapi32.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR,
                                            ctypes.c_void_p]  # PLUID
advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL
advapi32.AdjustTokenPrivileges.argtypes = [wintypes.HANDLE, wintypes.BOOL,
                                            ctypes.c_void_p, wintypes.DWORD,
                                            ctypes.c_void_p, ctypes.c_void_p]

# ════════════════════════════════════════════════════════════════════

# ── Constants ────────────────────────────────────────────
SystemHandleInformation = 0x10
ObjectNameInformation = 1
ObjectTypeInformation = 2
STATUS_SUCCESS = 0
STATUS_INFO_LENGTH_MISMATCH = 0xC0000004
STATUS_BUFFER_OVERFLOW = 0x80000005
STATUS_BUFFER_TOO_SMALL = 0xC0000023
STATUS_ACCESS_DENIED = 0xC0000022
PROCESS_DUP_HANDLE = 0x0040
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000  # Vista+ 低权限备选
PROCESS_VM_READ = 0x0010
DUPLICATE_SAME_ACCESS = 0x00000002
GENERIC_WRITE = 0x40000000
GENERIC_READ = 0x80000000
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008

# ── NT Structures ─────────────────────────────────────────
class UNICODE_STRING(Structure):
    _fields_ = [("Length", wintypes.USHORT),
                ("MaximumLength", wintypes.USHORT),
                ("Buffer", wintypes.LPWSTR)]

class SYSTEM_HANDLE_TABLE_ENTRY_INFO(Structure):
    _fields_ = [("UniqueProcessId", ctypes.c_ushort),
                ("CreatorBackTraceIndex", ctypes.c_ushort),
                ("ObjectTypeIndex", ctypes.c_byte),
                ("HandleAttributes", ctypes.c_byte),
                ("HandleValue", ctypes.c_ushort),
                ("Object", wintypes.LPVOID),
                ("GrantedAccess", ctypes.c_ulong)]

class SYSTEM_HANDLE_INFORMATION(Structure):
    _fields_ = [("NumberOfHandles", ctypes.c_ulong),
                ("Handles", SYSTEM_HANDLE_TABLE_ENTRY_INFO * 1)]

class LUID(Structure):
    _fields_ = [("LowPart", wintypes.DWORD),
                ("HighPart", wintypes.LONG)]

class LUID_AND_ATTRIBUTES(Structure):
    _fields_ = [("Luid", LUID),
                ("Attributes", wintypes.DWORD)]

class TOKEN_PRIVILEGES(Structure):
    _fields_ = [("PrivilegeCount", wintypes.DWORD),
                ("Privileges", LUID_AND_ATTRIBUTES * 1)]

# ── NtQuerySystemInformation prototype ────────────────────
ntdll.NtQuerySystemInformation.restype = ctypes.c_long
ntdll.NtQuerySystemInformation.argtypes = [
    ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong, POINTER(ctypes.c_ulong)
]

# NtQueryObject
ntdll.NtQueryObject.restype = ctypes.c_long
ntdll.NtQueryObject.argtypes = [
    wintypes.HANDLE, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong, POINTER(ctypes.c_ulong)
]


def _enable_debug_privilege() -> bool:
    """启用 SeDebugPrivilege，返回 (是否成功, 错误信息)。"""
    try:
        token = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(
            kernel32.GetCurrentProcess(),
            TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
            byref(token)
        ):
            print(f"  [dbg] OpenProcessToken failed: {kernel32.GetLastError()}")
            return False

        luid = LUID()
        if not advapi32.LookupPrivilegeValueW(None, "SeDebugPrivilege", byref(luid)):
            err = kernel32.GetLastError()
            print(f"  [dbg] LookupPrivilegeValue failed: {err}")
            kernel32.CloseHandle(token)
            return False

        tp = TOKEN_PRIVILEGES()
        tp.PrivilegeCount = 1
        tp.Privileges[0].Luid = luid
        tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

        ok = advapi32.AdjustTokenPrivileges(token, False, byref(tp),
                                             sizeof(TOKEN_PRIVILEGES), None, None)
        err = kernel32.GetLastError()
        kernel32.CloseHandle(token)

        if not ok:
            print(f"  [dbg] AdjustTokenPrivileges failed: {err}")
            return False
        if err == 0x514:  # ERROR_NOT_ALL_ASSIGNED — privilege not in token
            print("  [dbg] SeDebugPrivilege 不在 token 中 (可能被策略移除)")
            return False
        return True
    except Exception as e:
        print(f"  [dbg] _enable_debug_privilege exception: {e}")
        return False


def _get_parent_pid(pid: int) -> int | None:
    """通过 CreateToolhelp32Snapshot 获取父进程 PID。不需要特殊权限。"""
    TH32CS_SNAPPROCESS = 0x00000002

    class PROCESSENTRY32(Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.CHAR * 260),
        ]

    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    # INVALID_HANDLE_VALUE on 64-bit
    if snap is None or snap == 0 or snap == -1 or snap == 0xFFFFFFFFFFFFFFFF:
        return None

    try:
        entry = PROCESSENTRY32()
        entry.dwSize = sizeof(PROCESSENTRY32)
        if kernel32.Process32First(snap, byref(entry)):
            while True:
                if entry.th32ProcessID == pid:
                    return entry.th32ParentProcessID
                if not kernel32.Process32Next(snap, byref(entry)):
                    break
    finally:
        kernel32.CloseHandle(snap)

    return None


def _get_ancestor_pids(pid: int, max_depth: int = 10) -> list[int]:
    """沿进程树向上追溯，返回 [父pid, 祖父pid, ...]，最近的在前。"""
    ancestors = []
    seen = {pid}
    for _ in range(max_depth):
        ppid = _get_parent_pid(pid)
        if ppid is None or ppid <= 0 or ppid == pid:
            break
        if ppid in seen:
            break  # 防止循环
        seen.add(ppid)
        ancestors.append(ppid)
        pid = ppid
    return ancestors


def _get_all_handles() -> list | None:
    """获取系统所有句柄的原始列表。返回 [(pid, handle_value, object_ptr), ...]"""
    # 先探测 buffer 大小
    size = ctypes.c_ulong(0x400000)  # 4MB 起
    while size.value < 0x4000000:    # 上限 64MB
        buf = (ctypes.c_byte * size.value)()
        needed = ctypes.c_ulong(0)
        status = ntdll.NtQuerySystemInformation(
            SystemHandleInformation, buf, size, byref(needed)
        )
        if status == STATUS_SUCCESS:
            break
        elif status == STATUS_INFO_LENGTH_MISMATCH:
            size.value = max(needed.value, size.value * 2)
        else:
            return None

    if status != STATUS_SUCCESS:
        return None

    info = ctypes.cast(buf, POINTER(SYSTEM_HANDLE_INFORMATION))
    count = info.contents.NumberOfHandles

    entries = []
    for i in range(min(count, 500000)):  # 安全上限
        try:
            entry = info.contents.Handles[i]
            if entry.UniqueProcessId > 0 and entry.HandleValue > 0:
                entries.append((
                    entry.UniqueProcessId,
                    entry.HandleValue,
                    entry.Object,
                ))
        except Exception:
            pass

    return entries


def _get_handle_name(pid: int, handle_value: int) -> str:
    """查询指定进程中的句柄名称 (NtQueryObject → ObjectNameInformation)"""
    try:
        # 打开目标进程
        hproc = kernel32.OpenProcess(
            PROCESS_DUP_HANDLE | PROCESS_QUERY_INFORMATION,
            False, pid
        )
        if not hproc:
            hproc = kernel32.OpenProcess(
                PROCESS_DUP_HANDLE | PROCESS_QUERY_LIMITED_INFORMATION,
                False, pid
            )
        if not hproc:
            return ""

        # 复制句柄到本进程
        duped = wintypes.HANDLE()
        ok = kernel32.DuplicateHandle(
            hproc, wintypes.HANDLE(handle_value),
            kernel32.GetCurrentProcess(), byref(duped),
            0, False, DUPLICATE_SAME_ACCESS
        )
        kernel32.CloseHandle(hproc)
        if not ok:
            return ""

        # 查询名称（先探测 size）
        buf_size = ctypes.c_ulong(1024)
        name_info = (ctypes.c_byte * buf_size.value)()
        status = ntdll.NtQueryObject(
            duped, ObjectNameInformation,
            name_info, buf_size, byref(buf_size)
        )

        if status == STATUS_INFO_LENGTH_MISMATCH or status == STATUS_BUFFER_OVERFLOW:
            # 缓冲区不够，重试
            name_info = (ctypes.c_byte * buf_size.value)()
            status = ntdll.NtQueryObject(
                duped, ObjectNameInformation,
                name_info, buf_size, byref(buf_size)
            )

        name = ""
        if status == STATUS_SUCCESS:
            us = ctypes.cast(name_info, POINTER(UNICODE_STRING))
            if us.contents.Buffer and us.contents.Length > 0:
                try:
                    name = us.contents.Buffer[:us.contents.Length // 2]
                except Exception:
                    pass

        kernel32.CloseHandle(duped)
        return name

    except Exception:
        return ""


# ── NtQueryInformationProcess (ProcessHandleInformation) ──────────────
ProcessHandleInformation = 51  # 0x33

class PROCESS_HANDLE_TABLE_ENTRY_INFO(Structure):
    _fields_ = [("HandleValue", wintypes.HANDLE),
                ("HandleCount", ctypes.c_ulonglong),
                ("PointerCount", ctypes.c_ulonglong),
                ("GrantedAccess", ctypes.c_ulong),
                ("ObjectTypeIndex", ctypes.c_ulong),
                ("HandleAttributes", ctypes.c_ulong),
                ("Reserved", ctypes.c_ulong)]

class PROCESS_HANDLE_SNAPSHOT_INFORMATION(Structure):
    _fields_ = [("NumberOfHandles", ctypes.c_ulonglong),
                ("Reserved", ctypes.c_ulonglong),
                ("Handles", PROCESS_HANDLE_TABLE_ENTRY_INFO * 1)]


def _get_process_handles_via_query(pid: int) -> list:
    """通过 NtQueryInformationProcess 枚举指定进程的句柄。不需要 SeDebugPrivilege。"""
    hproc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_DUP_HANDLE, False, pid)
    if not hproc:
        # 备选: PROCESS_QUERY_LIMITED_INFORMATION (Vista+), 权限要求更低
        hproc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_DUP_HANDLE, False, pid)
    if not hproc:
        return []

    # 探测 buffer 大小
    buf_size = ctypes.c_ulong(0x10000)  # 64KB
    while buf_size.value < 0x400000:     # 上限 4MB
        buf = (ctypes.c_byte * buf_size.value)()
        ret_len = ctypes.c_ulong(0)
        status = ntdll.NtQueryInformationProcess(
            hproc, ProcessHandleInformation, buf, buf_size, byref(ret_len)
        )
        if status == STATUS_SUCCESS:
            break
        elif status in (STATUS_INFO_LENGTH_MISMATCH, STATUS_BUFFER_OVERFLOW):
            buf_size.value = max(ret_len.value, buf_size.value * 2)
        else:
            kernel32.CloseHandle(hproc)
            return []

    if status != STATUS_SUCCESS:
        kernel32.CloseHandle(hproc)
        return []

    info = ctypes.cast(buf, POINTER(PROCESS_HANDLE_SNAPSHOT_INFORMATION))
    count = min(info.contents.NumberOfHandles, 50000)
    entries = []
    # ctypes flexible array 只能访问 [0]，超过用指针偏移
    base = ctypes.addressof(info.contents.Handles)
    entry_size = ctypes.sizeof(PROCESS_HANDLE_TABLE_ENTRY_INFO)
    for i in range(count):
        entry_ptr = ctypes.cast(base + i * entry_size, POINTER(PROCESS_HANDLE_TABLE_ENTRY_INFO))
        try:
            hv = entry_ptr.contents.HandleValue
            if hv:
                entries.append(hv)
        except Exception:
            pass

    kernel32.CloseHandle(hproc)
    return entries


def _search_conpty_in_pid(pid: int) -> wintypes.HANDLE | None:
    """在单个进程中搜索 ConPTY 句柄 (方法1+方法2)。内部函数，被 find_conpty_handle 调用。"""
    # ── 方法 1: NtQueryInformationProcess ──
    print(f"  [conpty] pid={pid}, 方法1: NtQueryInformationProcess...")
    handles = _get_process_handles_via_query(pid)
    if handles:
        print(f"  [conpty] 找到 {len(handles)} 个句柄")
        for hv in handles:
            name = _get_handle_name(pid, hv.value if isinstance(hv, wintypes.HANDLE) else hv)
            if not name:
                continue
            if "\\Device\\ConDrv" in name:
                hproc = kernel32.OpenProcess(PROCESS_DUP_HANDLE, False, pid)
                if not hproc:
                    hproc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_DUP_HANDLE, False, pid)
                if hproc:
                    duped = wintypes.HANDLE()
                    ok = kernel32.DuplicateHandle(
                        hproc, wintypes.HANDLE(int(hv) if not isinstance(hv, wintypes.HANDLE) else hv),
                        kernel32.GetCurrentProcess(), byref(duped),
                        GENERIC_WRITE | GENERIC_READ, False, 0
                    )
                    kernel32.CloseHandle(hproc)
                    if ok and duped.value:
                        print(f"  [OK] 找到 ConPTY (方法1): {name} -> h={duped.value}")
                        return duped
                    # fallback: try same_access
                    hproc2 = kernel32.OpenProcess(PROCESS_DUP_HANDLE, False, pid)
                    if not hproc2:
                        hproc2 = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_DUP_HANDLE, False, pid)
                    if hproc2:
                        duped2 = wintypes.HANDLE()
                        ok2 = kernel32.DuplicateHandle(
                            hproc2, wintypes.HANDLE(int(hv) if not isinstance(hv, wintypes.HANDLE) else hv),
                            kernel32.GetCurrentProcess(), byref(duped2),
                            0, False, DUPLICATE_SAME_ACCESS
                        )
                        kernel32.CloseHandle(hproc2)
                        if ok2 and duped2.value:
                            print(f"  [OK] 找到 ConPTY (方法1, limited): {name} -> h={duped2.value}")
                            return duped2
    else:
        print(f"  [conpty] pid={pid}, 方法1 失败，尝试方法2 (全系统枚举)...")

    # ── 方法 2: 全系统句柄枚举 (需要 SeDebugPrivilege) ──
    _enable_debug_privilege()
    entries = _get_all_handles()
    if not entries:
        print(f"  [conpty] pid={pid}, 方法2 无法枚举系统句柄")
        return None

    candidates = []
    for e_pid, e_handle, e_obj in entries:
        if e_pid == pid:
            candidates.append((e_handle, e_obj))

    print(f"  [conpty] 方法2: pid={pid}, 共 {len(candidates)} 个句柄，扫描中...")

    for handle_value, obj_ptr in candidates:
        name = _get_handle_name(pid, handle_value)
        if not name or "\\Device\\ConDrv" not in name:
            continue

        hproc = kernel32.OpenProcess(PROCESS_DUP_HANDLE, False, pid)
        if not hproc:
            hproc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_DUP_HANDLE, False, pid)
        if not hproc:
            continue
        duped = wintypes.HANDLE()
        ok = kernel32.DuplicateHandle(
            hproc, wintypes.HANDLE(handle_value),
            kernel32.GetCurrentProcess(), byref(duped),
            GENERIC_WRITE | GENERIC_READ, False, 0
        )
        kernel32.CloseHandle(hproc)
        if ok and duped.value:
            print(f"  [OK] 找到 ConPTY (方法2): {name} -> h={duped.value}")
            return duped

    return None


def find_conpty_handle(pid: int) -> wintypes.HANDLE | None:
    """
    在指定进程及其父进程中查找 ConPTY 输入句柄。

    通常 claude.exe 是子进程，ConPTY 句柄在其父进程（WindowsTerminal / conhost）中。
    所以先查目标进程，再查父进程。

    方法 1: NtQueryInformationProcess (不需要 SeDebugPrivilege, 同用户即可)
    方法 2: NtQuerySystemInformation 全系统枚举 (需要 SeDebugPrivilege)

    返回: ConPTY 的 HANDLE (已在本地进程打开, 可 WriteFile)，或 None
    """
    # 先查目标进程自身
    result = _search_conpty_in_pid(pid)
    if result:
        return result

    # 再沿祖先链向上查 (终端进程如 WindowsTerminal 持有 ConPTY 句柄)
    ancestors = _get_ancestor_pids(pid)
    if ancestors:
        print(f"  [conpty] pid={pid} 无 ConPTY, 查祖先链: {ancestors}")
    for anc_pid in ancestors:
        result = _search_conpty_in_pid(anc_pid)
        if result:
            return result

    return None


def conpty_write(handle: wintypes.HANDLE, text: str) -> bool:
    """
    向 ConPTY 句柄写入文本。

    text: 要写入的文本，末尾应换行 (如 "hello\\n" 代表一条命令+回车)
    返回: 是否成功
    """
    if not handle or not handle.value:
        return False

    data = text.encode("utf-8")
    written = wintypes.DWORD(0)

    # 需要设置正确的句柄属性
    ok = kernel32.WriteFile(
        handle,
        data,
        len(data),
        byref(written),
        None  # 非 OVERLAPPED
    )

    if not ok:
        err = kernel32.GetLastError()
        print(f"  [ERR] WriteFile 失败: err={err}, handle={handle.value}")
        return False

    print(f"  [OK] ConPTY 写入 {written.value}/{len(data)} 字节")
    return written.value == len(data)


def find_process_by_name(name: str) -> list[int]:
    """按进程名（不区分大小写）查找 PID 列表。如 'claude-code.exe'"""
    pids = []
    name_lower = name.lower()
    try:
        import subprocess
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().split("\n"):
            parts = line.replace('"', "").split(",")
            if len(parts) >= 2 and parts[0].strip().lower() == name_lower:
                try:
                    pids.append(int(parts[1].strip()))
                except ValueError:
                    pass
    except Exception:
        pass
    return pids


def find_pid_by_window(title_keyword: str) -> int | None:
    """通过窗口标题查找进程 PID。如 'agent2027' → 21656"""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        result = []
        def _enum(hwnd, _):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if title_keyword.lower() in buf.value.lower():
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, byref(pid))
                result.append(pid.value)
                return False  # 找到第一个就停
            return True
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(_enum), 0)
        return result[0] if result else None
    except Exception:
        return None


def inject_to_process(proc_name: str, text: str) -> bool:
    """
    一站式: 找到进程 → 找 ConPTY → 写入文本。

    proc_name: 进程名 (如 'claude.exe') 或窗口标题 (如 'agent2027')
    text: 要注入的文本 (末尾需换行)
    """
    # 先试窗口标题 → PID
    pid = find_pid_by_window(proc_name)
    if pid:
        print(f"  [conpty] 窗口 '{proc_name}' → PID={pid}")
        handle = find_conpty_handle(pid)
        if handle:
            ok = conpty_write(handle, text)
            kernel32.CloseHandle(handle)
            return ok

    # 再试进程名
    pids = find_process_by_name(proc_name)
    if not pids:
        if pid is None:
            print(f"  [ERR] 找不到进程: {proc_name}")
        return False

    print(f"  [conpty] 找到 {proc_name}: PIDs={pids}")

    for p in pids:
        handle = find_conpty_handle(p)
        if handle:
            ok = conpty_write(handle, text)
            kernel32.CloseHandle(handle)
            return ok

    print(f"  [ERR] 找不到 ConPTY 句柄 (进程可能不用 ConPTY)")
    return False


def inject_cc(text: str, window_title: str = None) -> bool:
    """
    注入到 Claude Code 进程。

    window_title: CC 窗口标题 (如 'agent2027')，用于区分多个 CC 实例。
    """
    # 如果有窗口标题，直接定位 PID
    if window_title:
        pid = find_pid_by_window(window_title)
        if pid:
            print(f"  [conpty] 窗口 '{window_title}' → PID={pid}")
            handle = find_conpty_handle(pid)
            if handle:
                ok = conpty_write(handle, text)
                kernel32.CloseHandle(handle)
                return ok

    # 回退：按进程名找
    for name in ["claude.exe", "claude-code.exe", "codex.exe"]:
        pids = find_process_by_name(name)
        if not pids:
            continue
        print(f"  [conpty] 进程 {name}: PIDs={pids}")
        for p in pids:
            handle = find_conpty_handle(p)
            if handle:
                ok = conpty_write(handle, text)
                kernel32.CloseHandle(handle)
                return ok

    return False


# ═══════════════════════════════════════════════════════════
# 自检
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("conpty_inject.py 自检")
    print("=" * 50)

    # 测试 1: 权限
    print(f"\n1. SeDebugPrivilege: {_enable_debug_privilege()}")

    # 测试 2: 找 CC 进程
    for name in ["claude-code.exe", "claude.exe", "cmd.exe"]:
        pids = find_process_by_name(name)
        if pids:
            print(f"2. {name}: PIDs={pids}")
            break
    else:
        print("2. 没找到 CC/cmd 进程")

    print("\n用法: python conpty_inject.py          # 自检")
    print("      from conpty_inject import inject_cc")
    print("      inject_cc('hello from ConPTY\\n')")
