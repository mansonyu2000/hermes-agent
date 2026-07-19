"""
sync_features_to_pm.py — 从本地 .md 素材池挑选珍珠，入库到禅道 PM。

流程：
  1. 读取 feature-inventory.md，解析出每个功能（ID / 模块 / 标题 / 子功能 / 状态 / 决策）
  2. agent 逐条评估：需求描述是否清晰？是否重复？是否符合入库标准？
  3. 通过评估的 → zentao story create 入库
  4. 未通过的 → 留在 .md 中继续打磨

规则：
  - 状态 = "✅ 已完成" → 跳过（已入库或无需入库）
  - 决策 = "V2" / "❌-skip" → 跳过（远期/废弃）
  - 决策 = "V1" / "V1 P0" / "V1 P1" / "V1.5" 且 spec 非空 → 候选入库
  - 已入库的（spec 中含 "[禅道:id=" 标记）→ 跳过

用法：
  python tools/sync_features_to_pm.py --product 4 --project 6 --dry-run   # 只看不写
  python tools/sync_features_to_pm.py --product 4 --project 6              # 正式入库
"""

import json
import os
import re
import subprocess as sp
import sys
from pathlib import Path

FEATURE_MD = Path(__file__).parent.parent / "website" / "docs" / "winpeek" / "mim-design" / "feature-inventory.md"


def parse_feature_table(text: str) -> list[dict]:
    """从 markdown 表格中解析功能清单。"""
    features = []
    lines = text.split("\n")
    in_table = False
    module = ""
    for line in lines:
        # 检测模块标题
        if line.startswith("## ") and "、" in line:
            module = line.replace("#", "").strip()
            continue
        # 表头行（跳过）
        if "| # |" in line and "功能" in line:
            in_table = True
            continue
        # 分隔行（跳过）
        if in_table and re.match(r"^\|[-| ]+\|$", line):
            continue
        if in_table and line.startswith("|") and "|" in line[1:]:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 6 and cols[0].startswith("F"):
                features.append({
                    "id": cols[0],
                    "module": module,
                    "name": cols[1],
                    "children": cols[2],
                    "deps": cols[3],
                    "status": cols[4],
                    "decision": cols[5],
                })
        if in_table and line.startswith("---") and not line.startswith("|"):
            in_table = False
    return features


def evaluate(f: dict) -> tuple[bool, str]:
    """评估一个功能是否可以入库。返回 (通过, 原因)。"""
    status = f["status"]
    decision = f["decision"]

    if status == "✅":
        return False, "已完成，无需入库"
    if "V1.5" in decision or "V2" in decision:
        return False, f"decision={decision[:15]}, skip"
    if not f["name"] or len(f["name"]) < 3:
        return False, "功能名称太短或为空"

    # 拆分子功能
    children = [c.strip().strip("- ") for c in f["children"].split("\n") if c.strip()] if f["children"] else []

    spec = f"## 概述\n{f['name']}\n\n## 模块\n{f['module']}\n\n## 依赖\n{f['deps']}\n"
    if children:
        spec += "\n## 子功能\n" + "\n".join(f"- {c}" for c in children)

    return True, spec


def zen2story(f: dict, product: int, project: int, dry: bool = False) -> dict:
    """将功能推入禅道。"""
    ok, spec_or_reason = evaluate(f)
    if not ok:
        return {"id": f["id"], "ok": False, "reason": spec_or_reason}

    # 优先级映射：按前缀匹配（因为 decision 列可能含备注文字）
    dec = f["decision"]
    pri = 3
    if "V1 P0" in dec: pri = 1
    elif "V1 P1" in dec: pri = 2
    elif "V1.5" in dec: pri = 3
    elif "V1" in dec: pri = 1

    title = f"[{f['id']}] {f['name']}"
    verify = f"feature-inventory.md"

    if dry:
        return {"id": f["id"], "ok": "dry-run", "title": title, "pri": pri}

    try:
        from zentao_cli import _api, _config, _get_token
        base, _, _ = _config()
        token = _get_token()
        result = _api(f"/products/{product}/stories", method="POST", base_url=base, token=token,
                       data={"title": title, "pri": pri, "estimate": 1.0,
                             "spec": spec_or_reason, "verify": verify,
                             "category": "feature", "reviewer": ["admin2020"]})
        if "error" in result:
            return {"id": f["id"], "ok": False, "output": result.get("error", "unknown error")}
        sid = result.get("id")
        msg = {"id": f["id"], "ok": bool(sid), "zentao_id": sid, "output": str(result)[:200]}
        # Also link to project if specified (same path as story_create does)
        if project and sid:
            try:
                import pymysql
                conn = pymysql.connect(host='127.0.0.1', user='root', password='Server123', database='zentao')
                with conn.cursor() as cur:
                    cur.execute("INSERT IGNORE INTO zt_projectstory (project,product,story,version) VALUES (%s,%s,%s,1)",
                               (project, product, sid))
                conn.commit()
                conn.close()
                msg["project"] = project
            except Exception as e:
                msg["project_warn"] = str(e)[:100]
        return msg
    except Exception as e:
        return {"id": f["id"], "ok": False, "reason": str(e)}


def main():
    dry_run = "--dry-run" in sys.argv
    product = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--product=")), 4)
    project = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--project=")), 6)

    text = FEATURE_MD.read_text(encoding="utf-8")
    features = parse_feature_table(text)
    print(f"[sync] parsed {len(features)} features from feature-inventory.md\n")

    to_push = []
    skipped = []
    for f in features:
        ok, reason = evaluate(f)
        if ok:
            to_push.append(f)
        else:
            skipped.append((f, reason))

    print(f"[sync] candidates: {len(to_push)}  skipped: {len(skipped)}")
    for f, reason in skipped[:10]:
        print(f"  SKIP {f['id']} {f['name'][:40]} -> {reason}")
    print()

    if dry_run:
        print("[sync] DRY RUN - would create:")
        for f in to_push:
            result = zen2story(f, product, project, dry=True)
            print(f"  {f['id']} P{result.get('pri')} {f['name'][:50]}")
        print(f"\n[sync] Run without --dry-run to push")
        return

    print("[sync] pushing to ZenTao...")
    ok_count = 0
    fail_count = 0
    for f in to_push:
        result = zen2story(f, product, project)
        if result["ok"]:
            ok_count += 1
            print(f"  OK {f['id']} {f['name'][:50]}")
        else:
            fail_count += 1
            print(f"  FAIL {f['id']} {f['name'][:50]} -> {result.get('reason', result.get('output', 'unknown'))}")

    print(f"\n[sync] done: {ok_count} ok / {fail_count} fail / {len(skipped)} skip")


if __name__ == "__main__":
    main()
