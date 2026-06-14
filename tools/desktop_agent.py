"""
Hermes Desktop Agent Tool - 通过 HTTP 调用 OpenClaw Desktop Agent

这个工具让 Hermes 能够控制桌面：
- 鼠标点击、移动、滚动
- 键盘输入
- 截图
- 视觉识别（5 层级联）
- 窗口管理
- 启动程序

Desktop Agent 作为独立进程运行在 :18791 端口。
"""

import json
import requests
from typing import Optional
from tools.registry import registry

# Desktop Agent HTTP 服务地址
DESKTOP_AGENT_URL = "http://localhost:18791"


# ─── 健康检查 ─────────────────────────────────────────────────────────────

def check_desktop_agent() -> bool:
    """检查 Desktop Agent 是否运行"""
    try:
        resp = requests.get(f"{DESKTOP_AGENT_URL}/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


# ─── 鼠标操作 ─────────────────────────────────────────────────────────────

def desktop_click(x: int, y: int, button: str = "left", task_id: str = None) -> str:
    """鼠标点击指定坐标
    
    Args:
        x: X 坐标（像素）
        y: Y 坐标（像素）
        button: 按键 (left/right/middle)
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/click",
            json={"x": x, "y": y, "button": button},
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_double_click(x: int, y: int, task_id: str = None) -> str:
    """鼠标双击"""
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/double-click",
            json={"x": x, "y": y},
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_right_click(x: int, y: int, task_id: str = None) -> str:
    """鼠标右键点击"""
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/right-click",
            json={"x": x, "y": y},
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_mouse_move(x: int, y: int, smooth: bool = True, 
                       duration: float = 0.3, task_id: str = None) -> str:
    """移动鼠标到指定坐标
    
    Args:
        x: 目标 X 坐标
        y: 目标 Y 坐标
        smooth: 是否平滑移动（模拟人类）
        duration: 移动时长（秒）
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/mouse-move",
            json={
                "x": x, 
                "y": y, 
                "smooth": smooth,
                "duration": duration
            },
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_scroll(x: int, y: int, clicks: int, task_id: str = None) -> str:
    """鼠标滚动
    
    Args:
        x: X 坐标
        y: Y 坐标
        clicks: 滚动量（正数向上，负数向下）
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/scroll",
            json={"x": x, "y": y, "clicks": clicks},
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── 键盘操作 ─────────────────────────────────────────────────────────────

def desktop_type(text: str, task_id: str = None) -> str:
    """键盘输入文字
    
    Args:
        text: 要输入的文字
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/type",
            json={"text": text},
            timeout=10
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_keypress(keys: str, task_id: str = None) -> str:
    """按键操作
    
    Args:
        keys: 按键组合，如 "ctrl+c", "win+e", "alt+tab"
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/keypress",
            json={"keys": keys},
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── 截图操作 ─────────────────────────────────────────────────────────────

def desktop_screenshot(region: dict = None, task_id: str = None) -> str:
    """截取屏幕
    
    Args:
        region: 可选，截取区域 {"x": 0, "y": 0, "width": 1920, "height": 1080}
    
    Returns:
        {"success": true, "screenshot": "base64...", "width": 1920, "height": 1080}
    """
    try:
        params = {}
        if region:
            params["region"] = region
        
        resp = requests.get(
            f"{DESKTOP_AGENT_URL}/screenshot",
            params=params,
            timeout=10
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── 视觉识别 ─────────────────────────────────────────────────────────────

def desktop_vision_find(target: str, mode: str = "desktop", 
                       task_id: str = None) -> str:
    """视觉查找目标对象
    
    使用 5 层级联视觉识别：
    L0:   Win32 API (桌面图标)
    L0.5: OpenCV 模板匹配
    L2:   PaddleOCR (文字识别)
    L1:   OmniParser (UI 元素)
    L3:   Qwen2.5-VL (语义理解)
    
    Args:
        target: 查找目标，如 "QQ图标", "发送按钮", "微信窗口"
        mode: 查找模式 (desktop/general)
    
    Returns:
        {"found": true, "x": 1234, "y": 567, "confidence": 0.95, ...}
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/vision/find",
            json={"target": target, "mode": mode},
            timeout=30
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_vision_ocr(task_id: str = None) -> str:
    """OCR 文字识别（截图 + 识别）
    
    Returns:
        {"text": "识别到的文字", "blocks": [...]}
    """
    try:
        resp = requests.get(f"{DESKTOP_AGENT_URL}/vision/ocr", timeout=15)
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_vision_analyze(prompt: str, task_id: str = None) -> str:
    """视觉语义分析（截图 + VLM 理解）
    
    Args:
        prompt: 分析提示，如 "描述屏幕上的内容", "找到输入框的位置"
    
    Returns:
        {"analysis": "分析结果", "elements": [...]}
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/vision/analyze",
            json={"prompt": prompt},
            timeout=30
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_vision_health(task_id: str = None) -> str:
    """检查视觉识别服务状态
    
    Returns:
        {"paddleocr": true, "omniparser": true, "qwen_vl": true, ...}
    """
    try:
        resp = requests.get(f"{DESKTOP_AGENT_URL}/vision/health", timeout=5)
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── 窗口管理 ─────────────────────────────────────────────────────────────

def desktop_list_windows(task_id: str = None) -> str:
    """列出所有打开的窗口
    
    Returns:
        {"windows": [{"pid": 1234, "title": "...", "visible": true}, ...]}
    """
    try:
        resp = requests.get(f"{DESKTOP_AGENT_URL}/windows", timeout=5)
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_activate_window(title: str = None, pid: int = None, 
                           task_id: str = None) -> str:
    """激活指定窗口
    
    Args:
        title: 窗口标题（模糊匹配）
        pid: 进程 ID
    """
    try:
        params = {}
        if title:
            params["title"] = title
        if pid:
            params["pid"] = pid
        
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/window/activate",
            json=params,
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_minimize_window(title: str = None, pid: int = None, 
                           task_id: str = None) -> str:
    """最小化窗口"""
    try:
        params = {}
        if title:
            params["title"] = title
        if pid:
            params["pid"] = pid
        
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/window/minimize",
            json=params,
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_maximize_window(title: str = None, pid: int = None, 
                           task_id: str = None) -> str:
    """最大化窗口"""
    try:
        params = {}
        if title:
            params["title"] = title
        if pid:
            params["pid"] = pid
        
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/window/maximize",
            json=params,
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── 程序启动 ─────────────────────────────────────────────────────────────

def desktop_launch(exe: str, args: str = None, task_id: str = None) -> str:
    """启动程序
    
    Args:
        exe: 可执行文件路径，如 "C:\\Program Files\\Tencent\\QQ\\Bin\\QQ.exe"
        args: 可选参数
    
    Returns:
        {"success": true, "pid": 1234}
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/launch",
            json={"exe": exe, "args": args},
            timeout=10
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_open_explorer(path: str, task_id: str = None) -> str:
    """打开资源管理器
    
    Args:
        path: 文件夹路径，如 "D:\\Projects"
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/open-explorer",
            json={"path": path},
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── 高级操作 ─────────────────────────────────────────────────────────────

def desktop_human_click(target: str, action: str = "click", 
                       task_id: str = None) -> str:
    """模拟人类操作全流程
    
    视觉查找 + 鼠标移动 + 点击，一步到位。
    
    Args:
        target: 目标描述，如 "发送按钮", "QQ图标"
        action: 动作类型 (click/double_click/right_click)
    
    Returns:
        {"success": true, "position": {"x": 1234, "y": 567}}
    """
    try:
        resp = requests.post(
            f"{DESKTOP_AGENT_URL}/human-click",
            json={"target": target, "action": action},
            timeout=30
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_reset(task_id: str = None) -> str:
    """回到桌面原点（最小化所有窗口）"""
    try:
        resp = requests.post(f"{DESKTOP_AGENT_URL}/desktop/reset", timeout=5)
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def desktop_list_files(path: str = "D:\\", task_id: str = None) -> str:
    """列出目录内容
    
    Args:
        path: 目录路径
    """
    try:
        resp = requests.get(
            f"{DESKTOP_AGENT_URL}/files",
            params={"path": path},
            timeout=5
        )
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── 工具注册 ─────────────────────────────────────────────────────────────

# 鼠标操作
registry.register(
    name="desktop_click",
    toolset="desktop",
    schema={
        "name": "desktop_click",
        "description": "鼠标点击指定坐标。用于点击按钮、图标、链接等。",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X 坐标（像素）"},
                "y": {"type": "integer", "description": "Y 坐标（像素）"},
                "button": {
                    "type": "string", 
                    "enum": ["left", "right", "middle"], 
                    "default": "left",
                    "description": "鼠标按键"
                }
            },
            "required": ["x", "y"]
        }
    },
    handler=lambda args, **kw: desktop_click(
        args["x"], args["y"], args.get("button", "left"), kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

registry.register(
    name="desktop_double_click",
    toolset="desktop",
    schema={
        "name": "desktop_double_click",
        "description": "鼠标双击指定坐标。用于打开文件、启动程序等。",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X 坐标（像素）"},
                "y": {"type": "integer", "description": "Y 坐标（像素）"}
            },
            "required": ["x", "y"]
        }
    },
    handler=lambda args, **kw: desktop_double_click(
        args["x"], args["y"], kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

registry.register(
    name="desktop_mouse_move",
    toolset="desktop",
    schema={
        "name": "desktop_mouse_move",
        "description": "移动鼠标到指定坐标。可以平滑移动，模拟人类操作。",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "目标 X 坐标"},
                "y": {"type": "integer", "description": "目标 Y 坐标"},
                "smooth": {
                    "type": "boolean", 
                    "default": True,
                    "description": "是否平滑移动"
                },
                "duration": {
                    "type": "number", 
                    "default": 0.3,
                    "description": "移动时长（秒）"
                }
            },
            "required": ["x", "y"]
        }
    },
    handler=lambda args, **kw: desktop_mouse_move(
        args["x"], args["y"], 
        args.get("smooth", True),
        args.get("duration", 0.3),
        kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

# 键盘操作
registry.register(
    name="desktop_type",
    toolset="desktop",
    schema={
        "name": "desktop_type",
        "description": "键盘输入文字。用于在输入框、编辑器中输入内容。",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "要输入的文字"}
            },
            "required": ["text"]
        }
    },
    handler=lambda args, **kw: desktop_type(
        args["text"], kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

registry.register(
    name="desktop_keypress",
    toolset="desktop",
    schema={
        "name": "desktop_keypress",
        "description": "按键操作。支持组合键，如 'ctrl+c', 'win+e', 'alt+tab'。",
        "parameters": {
            "type": "object",
            "properties": {
                "keys": {
                    "type": "string", 
                    "description": "按键组合，如 'ctrl+c', 'win+e'"
                }
            },
            "required": ["keys"]
        }
    },
    handler=lambda args, **kw: desktop_keypress(
        args["keys"], kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

# 截图操作
registry.register(
    name="desktop_screenshot",
    toolset="desktop",
    schema={
        "name": "desktop_screenshot",
        "description": "截取屏幕图像。可选指定区域。返回 base64 编码的 PNG。",
        "parameters": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "width": {"type": "integer"},
                        "height": {"type": "integer"}
                    },
                    "description": "截取区域（可选）"
                }
            }
        }
    },
    handler=lambda args, **kw: desktop_screenshot(
        args.get("region"), kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

# 视觉识别
registry.register(
    name="desktop_vision_find",
    toolset="desktop",
    schema={
        "name": "desktop_vision_find",
        "description": "视觉查找目标对象。使用 5 层级联识别（Win32/OpenCV/OCR/OmniParser/VLM）。返回目标坐标。",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string", 
                    "description": "查找目标，如 'QQ图标', '发送按钮', '微信窗口'"
                },
                "mode": {
                    "type": "string", 
                    "enum": ["desktop", "general"],
                    "default": "desktop",
                    "description": "查找模式：desktop=桌面图标，general=通用UI"
                }
            },
            "required": ["target"]
        }
    },
    handler=lambda args, **kw: desktop_vision_find(
        args["target"], args.get("mode", "desktop"), kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

registry.register(
    name="desktop_vision_analyze",
    toolset="desktop",
    schema={
        "name": "desktop_vision_analyze",
        "description": "视觉语义分析。截图后用 VLM 理解屏幕内容。用于复杂场景理解。",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string", 
                    "description": "分析提示，如 '描述屏幕上的内容', '找到输入框的位置'"
                }
            },
            "required": ["prompt"]
        }
    },
    handler=lambda args, **kw: desktop_vision_analyze(
        args["prompt"], kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

# 窗口管理
registry.register(
    name="desktop_list_windows",
    toolset="desktop",
    schema={
        "name": "desktop_list_windows",
        "description": "列出所有打开的窗口。返回窗口列表（标题、PID、可见性）。",
        "parameters": {"type": "object", "properties": {}}
    },
    handler=lambda args, **kw: desktop_list_windows(kw.get("task_id")),
    check_fn=check_desktop_agent,
)

registry.register(
    name="desktop_activate_window",
    toolset="desktop",
    schema={
        "name": "desktop_activate_window",
        "description": "激活指定窗口（Bring to front）。通过标题或 PID 查找。",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "窗口标题（模糊匹配）"},
                "pid": {"type": "integer", "description": "进程 ID"}
            }
        }
    },
    handler=lambda args, **kw: desktop_activate_window(
        args.get("title"), args.get("pid"), kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

# 程序启动
registry.register(
    name="desktop_launch",
    toolset="desktop",
    schema={
        "name": "desktop_launch",
        "description": "启动程序。返回进程 PID。",
        "parameters": {
            "type": "object",
            "properties": {
                "exe": {
                    "type": "string", 
                    "description": "可执行文件路径，如 'C:\\Program Files\\Tencent\\QQ\\Bin\\QQ.exe'"
                },
                "args": {"type": "string", "description": "可选参数"}
            },
            "required": ["exe"]
        }
    },
    handler=lambda args, **kw: desktop_launch(
        args["exe"], args.get("args"), kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

# 高级操作
registry.register(
    name="desktop_human_click",
    toolset="desktop",
    schema={
        "name": "desktop_human_click",
        "description": "模拟人类操作全流程：视觉查找 + 鼠标移动 + 点击。一步到位，推荐使用。",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string", 
                    "description": "目标描述，如 '发送按钮', 'QQ图标'"
                },
                "action": {
                    "type": "string", 
                    "enum": ["click", "double_click", "right_click"],
                    "default": "click",
                    "description": "动作类型"
                }
            },
            "required": ["target"]
        }
    },
    handler=lambda args, **kw: desktop_human_click(
        args["target"], args.get("action", "click"), kw.get("task_id")
    ),
    check_fn=check_desktop_agent,
)

registry.register(
    name="desktop_reset",
    toolset="desktop",
    schema={
        "name": "desktop_reset",
        "description": "回到桌面原点（最小化所有窗口）。用于清理工作环境。",
        "parameters": {"type": "object", "properties": {}}
    },
    handler=lambda args, **kw: desktop_reset(kw.get("task_id")),
    check_fn=check_desktop_agent,
)
