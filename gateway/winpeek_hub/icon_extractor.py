"""Extract .ico/.png from .exe files via Windows GDI + PIL.

Caches to: %HERMES_HOME%/winpeek/soft-icons/{name}.png
"""

import ctypes
import logging
import os
import struct
from ctypes import wintypes
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Cache dir
HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
ICON_CACHE = HERMES_HOME / "winpeek" / "soft-icons"


def ensure_cache_dir() -> Path:
    ICON_CACHE.mkdir(parents=True, exist_ok=True)
    return ICON_CACHE


class SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]


def _extract_icon_from_exe(exe_path: str) -> Optional[bytes]:
    """Use Windows GDI to render the 32x32 app icon as PNG bytes."""
    import win32gui, win32ui, win32con, win32api

    try:
        shfi = SHFILEINFO()
        ctypes.windll.shell32.SHGetFileInfoW(
            exe_path, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), 0x100)
        if not shfi.hIcon:
            return None

        size = 32
        hdc = win32gui.GetDC(0)
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(win32ui.CreateDCFromHandle(hdc), size, size)
        dc_mem = win32ui.CreateDCFromHandle(hdc)
        mem_dc = dc_mem.CreateCompatibleDC()
        mem_dc.SelectObject(hbmp)

        win32gui.DrawIconEx(
            mem_dc.GetHandleOutput(), 0, 0, shfi.hIcon,
            size, size, 0, None, win32con.DI_NORMAL,
        )

        # Save to BMP in-memory then convert
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".bmp", delete=False)
        tmp.close()
        try:
            hbmp.SaveBitmapFile(mem_dc, tmp.name)
            from PIL import Image
            img = Image.open(tmp.name)
            import io
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"Icon extract failed for {exe_path}: {e}")
        return None


def _safe_filename(name: str) -> str:
    """Strip all path separators and unsafe chars. Keeps alphanumeric + underscore."""
    import re
    safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', name.lower())[:64]
    return safe.strip('_.') or 'unnamed'


def cache_icon(software_name: str, exe_path: str = "") -> Optional[str]:
    """Extract icon from exe and save to cache. Returns web-relative path."""
    if not exe_path or not os.path.isfile(exe_path):
        return None

    png_path = ICON_CACHE / f"{_safe_filename(software_name)}.png"

    # Skip if already cached
    if png_path.exists():
        return f"soft-icons/{safe_name}.png"

    try:
        data = _extract_icon_from_exe(exe_path)
        if data:
            ensure_cache_dir()
            png_path.write_bytes(data)
            return f"soft-icons/{safe_name}.png"
    except Exception as e:
        logger.debug(f"cache_icon failed for {software_name}: {e}")

    return None


def get_icon_url(software_name: str) -> str:
    """Get the URL path for a cached icon, or empty string."""
    p = ICON_CACHE / f"{_safe_filename(software_name)}.png"
    return f"soft-icons/{_safe_filename(software_name)}.png" if p.exists() else ""
