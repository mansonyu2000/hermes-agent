"""
mcp_server.py — WinPeek RPA MCP Server

将自学习生成的 MCP 模板暴露为 Hermes Agent 可调用的工具。
基于 stdio JSON-RPC 协议（MCP 标准）。

启动后 Hermes Agent 可通过 MCP 协议调用:
  - wechat_send_message(contact_name, message)
  - list_templates()
  - learn_new_skill(app, task_description)
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from typing import Any

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

TEMPLATES_DIR = Path(os.path.expanduser("~/.hermes/winpeek/templates"))

# ── 模板加载 ──────────────────────────────────────────────

def load_template(name: str) -> dict | None:
    """加载一个 MCP 模板 JSON"""
    path = TEMPLATES_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def list_available_templates() -> list[dict]:
    """列出所有可用模板"""
    if not TEMPLATES_DIR.exists():
        return []
    templates = []
    for f in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            meta = data.get("meta", {})
            templates.append({
                "name": meta.get("name", f.stem),
                "version": meta.get("version", "?"),
                "description": meta.get("description", ""),
                "tested": meta.get("tested", False),
            })
        except Exception:
            pass
    return templates

# ── 模板执行（占位，实际调用 computer_use 或 wechat_api）────

def execute_template(name: str, inputs: dict) -> dict:
    """执行一个模板"""
    template = load_template(name)
    if not template:
        return {"error": f"模板 '{name}' 未找到", "available": [t["name"] for t in list_available_templates()]}

    steps = template.get("steps", [])
    results = []
    context = {"inputs": inputs}

    for step in steps:
        # 解析 $变量 引用
        args = {}
        for k, v in step.get("args", {}).items():
            if isinstance(v, str) and v.startswith("$"):
                # 变量替换
                var_name = v[1:]
                args[k] = context.get("inputs", {}).get(var_name, v)
            else:
                args[k] = v

        # 这里应该调用实际的 computer_use 或 wechat_api
        # 当前为占位实现
        results.append({
            "step": step.get("id"),
            "name": step.get("name", ""),
            "tool": step.get("tool", ""),
            "args": args,
            "status": "pending",
            "note": "实际执行需集成 computer_use 或 wechat_uia.py"
        })

    return {
        "template": name,
        "version": template.get("meta", {}).get("version", "?"),
        "steps_executed": len(results),
        "results": results,
    }

# ── MCP Server ────────────────────────────────────────────

def create_server() -> Server:
    server = Server("winpeek-rpa")

    @server.tool()
    async def list_templates() -> str:
        """列出所有已学习的 MCP 模板"""
        templates = list_available_templates()
        return json.dumps({"count": len(templates), "templates": templates}, ensure_ascii=False)

    @server.tool()
    async def wechat_send_message(contact_name: str, message: str) -> str:
        """给微信好友发送消息（基于自学习模板 v2.1）"""
        result = execute_template("wechat_send_message", {
            "contact_name": contact_name,
            "message": message,
        })
        return json.dumps(result, ensure_ascii=False)

    @server.tool()
    async def learn_new_skill(app: str, task_description: str) -> str:
        """启动自学习流程，为指定软件学习新操作"""
        return json.dumps({
            "status": "learning_started",
            "app": app,
            "task": task_description,
            "steps": [
                "1. cua-driver 录制操作轨迹",
                "2. AI 分析轨迹 → 提取 UIA 控件",
                "3. 生成 MCP 模板 JSON",
                "4. 迭代测试 3-5 轮",
                "5. 置信度达标 → 入库"
            ],
            "instruction": "在 Hermes 中加载 trace-to-template 技能，按提示操作。",
        }, ensure_ascii=False)

    @server.tool()
    async def get_uia_map(app: str = "wechat") -> str:
        """获取已知的 UIA 控件映射表"""
        map_path = Path(os.path.expanduser(f"~/.hermes/winpeek/maps/{app}_uia_map.json"))
        if map_path.exists():
            return map_path.read_text(encoding="utf-8")
        return json.dumps({"error": f"控件映射 '{app}' 未找到"}, ensure_ascii=False)

    return server

# ── 入口 ──────────────────────────────────────────────────

async def main():
    if not HAS_MCP:
        print("MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
        sys.exit(1)

    server = create_server()
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
