#!/usr/bin/env python3
"""
sync-to-zentao.py — 同步本地 tasks/*-todo.md 的 checkbox 状态到 Zentao 任务。

用法:
    python bin/sync-to-zentao.py [--dry-run] [--module=mim]

映射:
    [x] → done (finished)
    [ ] → wait (no change)

每个 todo 项需要 `[zentao:#NN]` 标记来关联 Zentao 任务 ID。
"""
import os
import re
import subprocess
import sys
from pathlib import Path


TASKS_DIR = Path(__file__).parent.parent / "tasks"
ZENTAO_DB_HOST = os.environ.get("ZENTAO_DB_HOST", "192.168.3.23")


def parse_todo(filepath: Path) -> list[dict]:
    """解析 todo.md 文件，提取任务列表"""
    tasks = []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配: - [ ] / - [x] 任务名 `[zentao:#NN]`
    pattern = r"^- \[(.)\] (.+?) `\[zentao:#(\d+)\]`"
    for match in re.finditer(pattern, content, re.MULTILINE):
        checked = match.group(1) != " "
        name = match.group(2).strip()
        zentao_id = int(match.group(3))
        tasks.append({
            "name": name,
            "done": checked,
            "zentao_id": zentao_id,
        })
    return tasks


def sync_task(zentao_id: int, done: bool, dry_run: bool = False) -> bool:
    """同步单个任务状态到 Zentao"""
    env = {**os.environ, "ZENTAO_DB_HOST": ZENTAO_DB_HOST}

    if done:
        cmd = ["zentao", "task", "finish", str(zentao_id), "--consumed=0"]
    else:
        # 不更新 — zentao 没有 "unfinish" 命令
        return True

    if dry_run:
        print(f"  [DRY RUN] {'✅' if done else '⏳'} zentao:#{zentao_id}: {' '.join(cmd)}")
        return True

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"  ✅ zentao:#{zentao_id} synced")
            return True
        else:
            print(f"  ❌ zentao:#{zentao_id} failed: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ zentao:#{zentao_id} error: {e}")
        return False


def main():
    dry_run = "--dry-run" in sys.argv
    module_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--module="):
            module_filter = arg.split("=", 1)[1]

    print(f"🔍 Scanning {TASKS_DIR}...")
    if dry_run:
        print("🏃 DRY RUN mode — no changes will be made")

    todo_files = list(TASKS_DIR.glob("*-todo.md"))
    if module_filter:
        todo_files = [f for f in todo_files if module_filter in f.name]

    total = 0
    synced = 0
    for tf in sorted(todo_files):
        print(f"\n📄 {tf.name}")
        tasks = parse_todo(tf)
        for task in tasks:
            total += 1
            status = "✅" if task["done"] else "⏳"
            print(f"  {status} [{task['zentao_id']}] {task['name']}")
            if task["done"]:
                if sync_task(task["zentao_id"], task["done"], dry_run):
                    synced += 1

    print(f"\n📊 Total: {total} tasks | Done: {synced} synced")
    if total == 0:
        print("⚠️  No tasks found. Make sure todo files use `[zentao:#NN]` format.")


if __name__ == "__main__":
    main()
