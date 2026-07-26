---
description: "Start spec-driven development — write a structured specification before writing code"
skills_invoked:
  - ".agents/skills/spec-driven-development/SKILL.md"
---

# Pipeline: Spec

## Overview

启动规范驱动开发流程。在编写任何代码之前，先编写结构化规范文档，确保需求、范围、技术方案和验收标准达成一致。规范是团队和 AI Agent 之间共享的单一事实来源。

## Invoked Skill

读取 `.agents/skills/spec-driven-development/SKILL.md` 获取完整规范工作流。

**不跳过任何步骤、Common Rationalizations、Red Flags 或 Verification checklists。**

## Workflow

### Step 1：澄清需求

在编写规范之前，先向用户提出澄清性问题，确保需求具体化：

1. **目标（Objective）** — 要构建什么？为什么？用户是谁？成功标准是什么？
2. **功能范围** — 核心功能列表，MVP 边界
3. **技术栈** — 框架、语言、关键依赖及版本
4. **边界约束** — Always do / Ask first / Never do 三层次

列出明确假设：

```markdown
ASSUMPTIONS I'M MAKING:
1. [关于需求的假设]
2. [关于技术方案的假设]
3. [关于范围的假设]
→ 如果不对请立即纠正，我将按此推进。
```

### Step 2：编写结构化规范

生成覆盖以下 6 个核心领域的规范文档：

1. **Objective（目标）** — 构建什么和为什么，用户故事或验收条件
2. **Commands（命令）** — 完整的可执行命令（build、test、lint、dev），包含所有 flags
3. **Project Structure（项目结构）** — 源码目录、测试目录、文档目录布局及说明
4. **Code Style（代码风格）** — 一个真实代码片段展示风格，包括命名约定、格式化规则
5. **Testing Strategy（测试策略）** — 框架、测试位置、覆盖率要求、测试层级
6. **Boundaries（边界）** — Always do / Ask first / Never do

### Step 3：保存并与用户确认

- 将规范保存为 `SPEC.md`（项目根目录）
- 展示给用户确认
- 根据反馈迭代修改直到用户批准

### Step 4：继续下游流程

规范批准后，通知用户可进入下一阶段：

- `pipeline:plan` — 分解为可验证的任务
- `pipeline:build` — 开始增量实现

## Hermes Integration

当在 hermes-agent 项目中运行时：

- **ZenTao**：通过 `zentao story create --product 8 --title "..." --project 6` 创建 Story
- **关联**：将 ZenTao Story ID 链接到规范文件头部
- **MIM**：如需跨 Agent 协调，通过 `winpeek_mim_send` 通知协作者

参见 `website/docs/winpeek/mim-design/hermes-workflow-skill.md` 获取完整 Hermes 集成参考。
