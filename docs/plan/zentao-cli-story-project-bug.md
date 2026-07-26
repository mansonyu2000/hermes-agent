# ZenTao CLI Bug: story create 缺 --project 参数时需求不可见

> 反馈人: CC · 日期: 2026-07-19 · 目标仓库: zentao-cli

## Bug 描述

`zentao story create --product 4` 创建需求时，如果不同时传 `--project 6`，需求只出现在**产品视图**下（产品→winpeek→需求列表），不出现在**项目视图**下（`http://pm.test.com/projectstory-story-6.html`）。

## 根因

禅道后端把 Story→Project 的关联设计为**创建时确定，不可事后更改**。`story update` 传 `--project` 参数被 API 拒绝。

## 实际影响（已发生 2 次）

- 第一次：id=15~21，共 7 条 MIM 需求，创建了看不到，全部删除重建
- 第二次：id=30~36，共 7 条，同样过程
- 每次排查 + 修复耗时约 20 分钟

## 修复建议

**P0（必做）**：
1. `story create` 如果 `--product` 有值但 `--project` 为空 → 打印 warning：
   ```
   ⚠️ 未关联项目，需求仅在产品视图下可见，项目页面不可见。如需关联请指定 --project <id>。
   ```

**P1（建议）**：
2. `story help` 文档加一行："注意：需求与项目的关联只能在创建时指定，创建后不可更改。"
3. 如果用户之前执行过 `zentao workspace 6`，自动从工作区取 project ID 填上。

**工作量**：≤ 1.5h
