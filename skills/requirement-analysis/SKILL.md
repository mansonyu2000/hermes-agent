---
name: requirement-analysis
description: 从本地 feature-inventory.md 素材池自动分析、去重、合并需求，同步到禅道 PM
metadata:
  type: skill
---

# /requirement-analysis — 需求分析与入库

## 触发条件

- 用户说"分析需求"/"同步需求"/"入库"/"requirement analysis"
- Agent 空闲时自动巡检（每 4 小时）
- 用户在 `feature-inventory.md` 新增功能后主动调用

## 工作流

```
1. 读取 website/docs/winpeek/mim-design/feature-inventory.md
2. 解析 70 个功能 → 按规则过滤
3. 输出候选清单 (dry-run)
4. 用户确认后 → 调 zentao_cli._api() 入库到产品 4
5. 报告入库结果
```

## 过滤规则

| 条件 | 动作 |
|------|------|
| status = ✅ | 跳过 |
| decision 含 V2 / ❌-skip | 跳过 |
| decision 含 V1.5 | 跳过 |
| decision 含 V1 / V1 P0 / V1 P1 | **入库** |

## 执行命令

```bash
# 只看候选
python tools/sync_features_to_pm.py --product 4 --project 6 --dry-run

# 正式入库
python tools/sync_features_to_pm.py --product 4 --project 6
```

## 输出格式

```
[sync] parsed 70 features
[sync] candidates: {N}  skipped: {M}
  SKIP F1.1 用户注册 → 已完成
  SKIP F2.6 好友温度 → V2
  ...

[sync] DRY RUN — 以下功能将入库:
  F1.4 P1 多身份支持
  F2.2 P1 真实在线状态
  ...

确认入库? (y/n)
```

## 日常巡检

Agent 空闲时跑 `python tools/sync_features_to_pm.py --product 4 --project 6 --dry-run`，如果候选数 > 0 且距上次同步 ≥ 4h，推送到禅道并通知用户。

## 依赖

- zentao_cli ≥ 0.2.0 (uv pip install)
- feature-inventory.md v2.0+
