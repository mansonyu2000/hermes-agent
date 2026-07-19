# sync_features_to_pm.py — 本地素材池 → 禅道 PM 入库工具

> 维护人: CC · 版本: 1.0 · 依赖: zentao_cli (0.2.0+) + feature-inventory.md v2.0+

---

## 一句话

从 `feature-inventory.md` 读 70 个功能素材 → 自动跳过已完成/V2 → 把 V1 候选推入禅道产品 `product=4`。

## 为什么需要它

`feature-inventory.md` 是灵感池——agent 随时往里加想法，不需要考虑格式、评审、指派。但它不是项目管理系统——不能指派、不能跟踪状态、不能在团队间共享。

禅道 `pm.test.com` 是正式需求库——有状态流转、评审、工时、指派。但它不是灵感池——不能随便灌模糊的需求。

**这个工具把两条线串起来**：

```
.md 素材池 (70)  →  [synctool]  →  禅道需求库 (4条合并)
    ↑                                   ↑
  随便写/模糊                          严谨/评审/指派
```

## 用法

```bash
# 1. 只看不写 — 看看哪些会入库
python tools/sync_features_to_pm.py --product 4 --project 6 --dry-run

# 2. 正式入库
python tools/sync_features_to_pm.py --product 4 --project 6

# 3. 指定其他产品/项目
python tools/sync_features_to_pm.py --product 1 --project 2 --dry-run
```

## 入库规则

| 条件 | 行为 |
|------|------|
| 状态 = `✅` | 跳过 — 已完成 |
| 决策 = `V2` / `❌-skip` | 跳过 — 远期或废弃 |
| 决策 = `V1.5` | 跳过 — 下个版本 |
| 决策含 `V1` / `V1 P0` / `V1 P1` | **入库** |
| 功能名 < 3 字符 | 跳过 — 太短 |

## 输出示例

```
[sync] parsed 70 features from feature-inventory.md

[sync] candidates: 23  skipped: 47
  SKIP F1.1 用户注册 → 已完成无需入库
  SKIP F2.6 好友温度 → V2, skip
  SKIP F2.5 实时状态推送 → V1.5, skip

[sync] DRY RUN - would create:
  F1.4 P1 多身份支持
  F2.2 P1 真实在线状态
  ...

[sync] Run without --dry-run to push
```

## 完整工作流

```
1. Agent 在 feature-inventory.md 新增功能 → add + commit + push
2. Agent 跑 sync --dry-run → 确认候选清单
3. Agent 跑 sync → 入库到禅道
4. 人在禅道 Web 做评审 → draft → reviewing → active
5. 指派 → 转任务 → 开发
6. 做完后回填 .md 状态 → status: ✅
```

## 常见问题

**Q: 禅道里已经有同名需求怎么办？**

A: 工具调用 `_api("POST /stories")`，禅道不拦截重名需求（允许多条同名）。如果需要去重，先在禅道 Web 里手动清理。

**Q: 能反过来——禅道 → .md 吗？**

A: 当前不支持。方向是单向的：`.md(源) → 禅道(目标)`。反向同步需要禅道状态回写 .md，V1.5 做。

**Q: 为什么用 Python API 而不是 CLI 子进程？**

A: 安全审查发现 `subprocess.run(shell=True)` 有命令注入风险。改为直接 `import zentao_cli._api` 调用。如果 `zentao_cli` 不可用（pip 没装），工具会报 ImportError 并跳过对应的 story。

## 依赖

- `zentao_cli` ≥ 0.2.0: `uv pip install git+http://gitlab.test.com/hotime/cp/CLI-Anything.git@dev#subdirectory=zentao/agent-harness --system`
- `feature-inventory.md` v2.0+: 位于 `website/docs/winpeek/mim-design/feature-inventory.md`
