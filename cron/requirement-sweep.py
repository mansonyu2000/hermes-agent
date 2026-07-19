"""定时需求巡检 — 每小时扫一次 feature-inventory.md, 有新候选就推禅道。

由 cron 调度, 不需要人工触发。
如果有新 V1 需求 ≥4h 未同步, 自动入库并 say 通知 PM。
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).parent.parent
FEATURE_MD = REPO / "website" / "docs" / "winpeek" / "mim-design" / "feature-inventory.md"
CACHE = Path(os.path.expanduser("~/.hermes/winpeek/sweep_cache.json"))
INTERVAL_H = float(os.getenv("MIM_SWEEP_INTERVAL_H", "1"))


def md_hash() -> str:
    if not FEATURE_MD.exists():
        return ""
    return hashlib.sha256(FEATURE_MD.read_bytes()).hexdigest()[:16]


def last_sweep() -> float:
    try:
        return json.loads(CACHE.read_text()).get("ts", 0)
    except Exception:
        return 0


def save_sweep(ts: float, candidates: int):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"ts": ts, "candidates": candidates}))


def run():
    h = md_hash()
    if not h:
        return

    prev = last_sweep()
    now = time.time()

    if now - prev < INTERVAL_H * 3600:
        return  # 还没到巡检时间

    # 跑 dry-run, 看有没有新候选
    sys.path.insert(0, str(REPO))
    from tools.sync_features_to_pm import parse_feature_table, evaluate, FEATURE_MD as FMD

    text = FMD.read_text(encoding="utf-8")
    features = parse_feature_table(text)

    candidates = []
    for f in features:
        ok, _ = evaluate(f)
        if ok:
            candidates.append(f)

    if not candidates:
        save_sweep(now, 0)
        return

    # 有候选 → 正式入库
    from zentao_cli import _api, _config, _get_token

    base, _, _ = _config()
    token = _get_token()

    ok_count = 0
    for f in candidates:
        spec = f"## {f['name']}\n\n模块: {f['module']}\n依赖: {f['deps']}\n子功能: {f['children']}"
        result = _api(
            f"/products/4/stories",
            method="POST",
            base_url=base,
            token=token,
            data={
                "title": f"[{f['id']}] {f['name']}",
                "pri": 1 if "P0" in f.get("decision", "") or "V1" in f.get("decision", "") else 2,
                "estimate": 1.0,
                "spec": spec,
                "verify": "feature-inventory.md",
                "category": "feature",
                "reviewer": ["admin2020"],
            },
        )
        if result.get("id"):
            ok_count += 1

    save_sweep(now, len(candidates))

    # say 通知 PM
    try:
        from bin.agent_role import say

        say(2022, f"[需求巡检] {ok_count}/{len(candidates)} 条新需求已入库 pm.test.com 产品4")
    except Exception:
        pass

    print(f"[sweep] {ok_count}/{len(candidates)} features synced at {time.strftime('%Y-%m-%dT%H:%M:%S')}")


if __name__ == "__main__":
    run()
