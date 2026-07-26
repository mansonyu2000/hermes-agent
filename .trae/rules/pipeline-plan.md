---
description: "Break work into small verifiable tasks with acceptance criteria and dependency ordering"
skills_invoked:
  - ".agents/skills/planning-and-task-breakdown/SKILL.md"
---

# Pipeline: Plan

## Overview

将规范或需求分解为小的、可验证的任务，每项任务都有明确的验收条件和依赖顺序。良好的任务分解是可靠实现的基础——每项任务应足够小，可在一次专注的会话中完成实现、测试和验证。

## Invoked Skill

读取 `.agents/skills/planning-and-task-breakdown/SKILL.md` 获取完整计划工作流。

**不跳过任何步骤、Common Rationalizations、Red Flags 或 Verification checklists。**

## Workflow

### Step 1：阅读规范

- 读取 `SPEC.md`（如果存在）和相关代码库
- 识别现有模式和约定
- 标记风险和未知因素

**计划阶段不编写任何代码。** 输出是计划文档和任务列表，而非实现。

### Step 2：识别依赖图

绘制组件依赖关系：

```
数据库 Schema
    │
    ├── API 模型/类型
    │       │
    │       ├── API 端点
    │       │       │
    │       │       └── 前端 API 客户端
    │       │               │
    │       │               └── UI 组件
    │       │
    │       └── 验证逻辑
    │
    └── 种子数据 / 迁移
```

实现顺序遵循依赖图自底向上：先构建基础。

### Step 3：垂直切片

避免水平切片（先做所有数据库、再所有 API、再所有 UI）。改为每个任务完成一条完整的端到端路径：

**好的垂直切片示例：**
```
Task 1: 用户注册（注册 Schema + API + UI）
Task 2: 用户登录（认证 Schema + API + UI）
Task 3: 用户创建任务（任务 Schema + API + UI）
Task 4: 用户查看任务列表（查询 + API + UI）
```

### Step 4：编写任务

每项任务遵循以下结构：

```markdown
## Task [N]: [简短描述性标题]

**Description：** 一段说明该任务完成什么的描述。

**Acceptance criteria：**
- [ ] [具体、可测试的条件]
- [ ] [具体、可测试的条件]

**Verification：**
- [ ] 测试通过：`npm test -- --grep "feature-name"`
- [ ] 构建成功：`npm run build`
- [ ] 手动检查：[描述要验证的内容]

**Dependencies：** [依赖的任务编号，或 "None"]

**Files likely touched：**
- `src/path/to/file.ts`
- `tests/path/to/test.ts`

**Estimated scope：** [Small: 1-2 文件 | Medium: 3-5 文件 | Large: 5+ 文件]
```

### Step 5：排序并设置检查点

- 确保依赖关系满足（先构建基础）
- 每项任务后系统保持可工作状态
- 每 2-3 个任务设置验证检查点
- 高风险任务放在前面（快速失败）

添加显式检查点：

```markdown
## Checkpoint：完成 Tasks 1-3
- [ ] 所有测试通过
- [ ] 应用构建无错误
- [ ] 核心用户流端到端工作
- [ ] 与用户确认后继续
```

### Step 6：呈现给用户审查

将计划展示给用户，获取批准后再开始实现。

## Output Files

- **计划文档**：保存到 `tasks/plan.md`
- **任务列表**：保存到 `tasks/todo.md`

如果 `tasks/` 目录不存在则创建。这些路径是下游命令约定的路径。

## Hermes Integration

当在 hermes-agent 项目中运行时：

- **ZenTao**：通过 `zentao task create --execution 9 --name "..." --story <id>` 创建任务
- **同步**：将任务依赖顺序与执行计划同步
- **追溯**：将每个任务链接到 ZenTao Story ID

参见 `website/docs/winpeek/mim-design/hermes-workflow-skill.md` 获取完整 Hermes 集成参考。
