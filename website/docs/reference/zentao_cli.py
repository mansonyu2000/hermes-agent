"""cli-anything-zentao — CLI for ZenTao PM, following CLI-Anything harness pattern.

让 AI Agent 通过命令行操作禅道:
  登录、查产品、查需求、创建需求、调 AI 智能体。

默认连接 http://pm.test.com，通过 ZENTAO_URL/ZENTAO_ACCOUNT/ZENTAO_PASSWORD 环境变量配置。
"""

from __future__ import annotations

import json, os, sys
from typing import Any

import click
import requests

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
VERSION = "0.1.0"

def _config() -> tuple:
    return (os.environ.get("ZENTAO_URL", "http://pm.test.com"),
            os.environ.get("ZENTAO_ACCOUNT", "admin2020"),
            os.environ.get("ZENTAO_PASSWORD", "Server3314"))

def _auth(base: str, account: str, password: str) -> str:
    r = requests.post(f"{base}/api.php/v1/tokens",
                      json={"account": account, "password": password}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]

def _api(path: str, method: str = "GET", data: dict | None = None,
         base_url: str = "", token: str = "") -> dict:
    url = f"{base_url}/api.php/v1{path}"
    headers = {"Token": token, "Content-Type": "application/json"} if token else {}
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=15)
        elif method == "POST":
            r = requests.post(url, headers=headers, json=data or {}, timeout=15)
        else:
            return {"error": f"Unsupported method: {method}"}
        return r.json() if r.text.strip() else {"error": f"Empty response (status {r.status_code})"}
    except requests.ConnectionError:
        return {"error": f"Cannot connect to {base_url}"}
    except Exception as e:
        return {"error": str(e)}

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(VERSION, prog_name="zentao")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ZenTao CLI — AI Agent's command-line interface to ZenTao PM."""

# ═══════════════════════════════════════════════════════════
# login — 登录
# ═══════════════════════════════════════════════════════════
@cli.command()
@click.option("--server", "-s", envvar="ZENTAO_URL", default="http://pm.test.com")
@click.option("--user", "-u", envvar="ZENTAO_ACCOUNT", default="admin2020")
@click.option("--password", "-p", envvar="ZENTAO_PASSWORD", default="Server3314")
def login(server: str, user: str, password: str) -> None:
    """登录禅道，获取 token"""
    try:
        token = _auth(server, user, password)
        click.echo(json.dumps({"ok": True, "token": token[:20] + "...", "server": server, "user": user},
                              ensure_ascii=False))
    except Exception as e:
        click.echo(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)

def _get_token() -> str:
    base, user, pwd = _config()
    try:
        return _auth(base, user, pwd)
    except Exception as e:
        click.echo(json.dumps({"error": f"Auth failed: {e}"}, ensure_ascii=False), err=True)
        sys.exit(1)

# ═══════════════════════════════════════════════════════════
# product — 产品
# ═══════════════════════════════════════════════════════════
@cli.group()
def product() -> None:
    """产品管理"""

@product.command("list")
def product_list() -> None:
    """列出所有产品"""
    base, _, _ = _config()
    token = _get_token()
    result = _api("/products", base_url=base, token=token)
    products = result.get("products", [])
    click.echo(json.dumps([{"id": p["id"], "name": p["name"]} for p in products],
                          ensure_ascii=False, indent=2))

# ═══════════════════════════════════════════════════════════
# story — 需求
# ═══════════════════════════════════════════════════════════
@cli.group()
def story() -> None:
    """需求管理"""

@story.command("list")
@click.option("--product", "-p", type=int, required=True, help="产品 ID")
def story_list(product: int) -> None:
    """列出产品下的需求"""
    base, _, _ = _config()
    token = _get_token()
    result = _api(f"/products/{product}/stories", base_url=base, token=token)
    stories = result.get("stories", [])
    click.echo(json.dumps([{"id": s["id"], "title": s["title"], "status": s.get("status",""), "pri": s.get("pri","")}
                           for s in stories], ensure_ascii=False, indent=2))

@story.command("create")
@click.option("--product", "-p", type=int, required=True)
@click.option("--title", "-t", required=True)
@click.option("--pri", type=int, default=2)
@click.option("--estimate", type=float, default=0)
@click.option("--spec", default="")
@click.option("--reviewer", multiple=True, default=["admin2020"])
def story_create(product: int, title: str, pri: int, estimate: float, spec: str, reviewer: list) -> None:
    """创建需求"""
    base, _, _ = _config()
    token = _get_token()
    result = _api(f"/products/{product}/stories", method="POST", base_url=base, token=token,
                  data={"title": title, "pri": pri, "estimate": estimate, "category": "feature",
                        "spec": spec, "reviewer": list(reviewer)})
    if "id" in result:
        click.echo(json.dumps({"ok": True, "id": result["id"], "title": title}, ensure_ascii=False))
    else:
        click.echo(json.dumps({"ok": False, "error": str(result)}, ensure_ascii=False))
        sys.exit(1)

@story.command("update")
@click.option("--id", "-i", "story_id", type=int, required=True)
@click.option("--status", default="")
@click.option("--pri", type=int, default=None)
def story_update(story_id: int, status: str, pri: int | None) -> None:
    """更新需求状态"""
    base, _, _ = _config()
    token = _get_token()
    data = {}
    if status: data["status"] = status
    if pri is not None: data["pri"] = pri
    result = _api(f"/stories/{story_id}", method="PUT", base_url=base, token=token, data=data)
    click.echo(json.dumps({"ok": True, "id": story_id}, ensure_ascii=False))

# ═══════════════════════════════════════════════════════════
# project — 项目
# ═══════════════════════════════════════════════════════════
@cli.group()
def project() -> None:
    """项目管理"""

@project.command("list")
def project_list() -> None:
    """列出所有项目"""
    base, _, _ = _config()
    token = _get_token()
    result = _api("/projects", base_url=base, token=token)
    projects = result.get("projects", [])
    click.echo(json.dumps([{"id": p["id"], "name": p["name"], "status": p.get("status","")}
                           for p in projects], ensure_ascii=False, indent=2))

# ═══════════════════════════════════════════════════════════
# bug — Bug
# ═══════════════════════════════════════════════════════════
@cli.group()
def bug() -> None:
    """Bug 管理"""

@bug.command("list")
@click.option("--product", "-p", type=int, required=True)
def bug_list(product: int) -> None:
    """列出产品下的 Bug"""
    base, _, _ = _config()
    token = _get_token()
    result = _api(f"/products/{product}/bugs", base_url=base, token=token)
    bugs = result.get("bugs", [])
    click.echo(json.dumps([{"id": b["id"], "title": b["title"], "severity": b.get("severity",""), "status": b.get("status","")}
                           for b in bugs], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    cli()
