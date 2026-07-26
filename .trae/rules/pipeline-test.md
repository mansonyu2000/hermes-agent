---
description: "Run TDD workflow — write failing tests, implement, verify. For bugs, use Prove-It pattern"
skills_invoked:
  - ".agents/skills/test-driven-development/SKILL.md"
---

# Pipeline: Test

## Overview

执行测试驱动开发工作流。先编写失败的测试，再编写使其通过的代码。对于 Bug 修复，使用 Prove-It 模式：先编写重现 Bug 的测试，再修复。测试是证据——"看起来是对的"不算完成。

## Invoked Skill

读取 `.agents/skills/test-driven-development/SKILL.md` 获取完整 TDD 工作流。

**不跳过任何步骤、Common Rationalizations、Red Flags 或 Verification checklists。**

## Workflow

### Step 1：发现项目测试栈

在编写第一个测试之前，先了解当前仓库的测试方式：

- **构建系统** — `package.json`、`pyproject.toml`、`go.mod`、`Cargo.toml` 等
- **测试框架和配置** — 如何运行单个测试 vs 完整套件
- **现有约定** — 测试位置、文件命名、周边测试的模式
- **文档化命令** — README、CONTRIBUTING、CI 工作流中的命令

### Step 2：选择模式

#### 新功能模式

```
RED          →  GREEN          →  REFACTOR
写失败测试      编写最少代码        清理实现
测试 FAILS      测试 PASSES        测试仍 PASS
```

1. **RED**：编写描述期望行为的测试，确认它失败
2. **GREEN**：编写最少代码使测试通过，不要过度工程化
3. **REFACTOR**：在测试保持绿色的情况下改进代码
4. **回归检查** — 运行完整测试套件

#### Bug 修复模式（Prove-It）

```
Bug 报告到达
    │
    ▼
编写重现 Bug 的测试
    │
    ▼
测试 FAILS（确认 Bug 存在）
    │
    ▼
实现修复
    │
    ▼
测试 PASSES（证明修复有效）
    │
    ▼
运行完整测试套件（无回归）
```

**关键规则**：不要先尝试修复 Bug。先写一个重现它的测试。

### Step 3：测试金字塔指导

根据测试金字塔分配测试精力：

```
          ╱╲
         ╱  ╲         E2E 测试（~5%）
        ╱    ╲
       ╱──────╲
      ╱        ╲      集成测试（~15%）
     ╱          ╲
    ╱────────────╲
   ╱              ╲   单元测试（~80%）
  ╱──────────────────╲
```

### Step 4：测试质量检查

- 测试行为而非实现细节
- DAMP 优于 DRY（每个测试自包含可读）
- 优先使用真实实现 > Fake > Stub > Mock
- 使用 Arrange-Act-Assert 模式
- 每个概念一个断言
- 测试名称描述性（读起来像规范）

## Hermes Integration

当在 hermes-agent 项目中运行时：

- **ZenTao 链接**：将测试结果链接到 ZenTao Story/Task
- **MIM 通知**：通过 `winpeek_mim_send` 通知团队回归测试结果
- **Bug 追溯**：Bug 修复测试关联到 ZenTao Bug ID

参见 `website/docs/winpeek/mim-design/hermes-workflow-skill.md` 获取完整 Hermes 集成参考。
