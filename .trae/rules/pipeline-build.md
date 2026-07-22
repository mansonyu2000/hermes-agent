---
description: "Implement tasks incrementally — build, test, verify, commit. Support 'auto' mode for full plan execution"
skills_invoked:
  - ".agents/skills/incremental-implementation/SKILL.md"
  - ".agents/skills/test-driven-development/SKILL.md"
---

# Pipeline: Build

## Overview

以增量方式实现任务——完成一个切片、测试、验证、提交，然后继续下一个。支持两种模式：**默认模式**（逐个任务执行 TDD 循环）和 **Auto 模式**（一次性批准后自动执行整个计划）。

## Invoked Skills

- 读取 `.agents/skills/incremental-implementation/SKILL.md` 获取增量实现工作流
- 读取 `.agents/skills/test-driven-development/SKILL.md` 获取 TDD 循环

**不跳过任何步骤、Common Rationalizations、Red Flags 或 Verification checklists。**

## Workflow

### 默认模式：逐个任务执行

1. **选择下一个待办任务** — 从 `tasks/todo.md` 中选择优先级最高的待办任务
2. **TDD 循环**（RED → GREEN → REFACTOR）：
   - **RED**：为任务编写失败的测试
   - **GREEN**：编写最少代码使测试通过
   - **REFACTOR**：在保持测试通过的情况下清理代码
3. **回归检查** — 运行完整测试套件确保无回归
4. **构建验证** — 确认构建成功
5. **提交** — 使用描述性信息提交，引用 Story/Task ID
6. **重复** — 进入下一个待办任务

### Auto 模式：全自动执行

1. **前置条件检查**：
   - 需要已批准的规范（`SPEC.md`）
   - 需要干净的基线（无未提交更改）
   - 需要计划（`tasks/plan.md` 和 `tasks/todo.md`），如缺少则自动生成
2. **一次性批准** — 向用户展示完整执行计划并请求一次批准
3. **执行所有任务** — 按顺序自动执行每个任务，遵循默认模式的 TDD 循环
4. **进度报告** — 每个任务完成后报告状态

### 切片策略

优先使用**垂直切片**——每次构建一条完整的端到端路径：

```
切片 1：创建任务（DB + API + 基本 UI）
    → 测试通过，用户可通过 UI 创建任务

切片 2：列出任务（查询 + API + UI）
    → 测试通过，用户可查看任务列表
```

高风险切片先做，快速验证可行性。

## 实现规则

- **Rule 0：简单优先** — 先问"最简单能工作的方法是什么？"
- **Rule 0.5：范围纪律** — 只接触任务要求的内容，不做无关"清理"
- **Rule 1：一次一事** — 每个增量只改动一个逻辑单元
- **Rule 2：保持可编译** — 每次增量后项目必须可构建
- **Rule 5：可回滚** — 每个增量可独立回滚

## Hermes Integration

当在 hermes-agent 项目中运行时：

- **MIM 通知**：任务完成时通过 `winpeek_mim_send` 通知协作者
- **ZenTao 更新**：更新 ZenTao 任务状态
- **提交信息**：提交信息引用 ZenTao Story/Task ID

参见 `website/docs/winpeek/mim-design/hermes-workflow-skill.md` 获取完整 Hermes 集成参考。
