---
description: "Simplify code for clarity and maintainability — reduce complexity without changing behavior"
skills_invoked:
  - ".agents/skills/code-simplification/SKILL.md"
---

# Pipeline: Code Simplify

## Overview

简化代码以提高清晰度和可维护性——在不改变行为的前提下降低复杂度。目标不是减少行数，而是让代码更易读、易理解、易修改、易调试。

## Invoked Skill

读取 `.agents/skills/code-simplification/SKILL.md` 获取完整代码简化工作流。

**不跳过任何步骤、Common Rationalizations、Red Flags 或 Verification checklists。**

## Workflow

### Step 1：研究项目约定

在简化之前，先了解项目的代码风格和约定：

- 读取项目约定的规则文件
- 研究周边代码处理类似模式的方式
- 匹配项目的导入顺序、函数声明风格、命名约定、错误处理模式

### Step 2：识别目标代码

确定要简化的代码范围：

- 默认只简化最近修改的代码
- 避免无关联代码的"路过式"简化
- 除非被明确要求扩大范围，否则保持聚焦

### Step 3：理解代码（Chesterton's Fence）

在更改或删除任何内容之前，先理解它存在的原因：

```
BEFORE SIMPLIFYING, ANSWER：
- 这段代码的职责是什么？
- 谁调用它？它调用谁？
- 边界情况和错误路径是什么？
- 有哪些测试定义了期望行为？
- 为什么它可能被写成这样？
```

如果无法回答这些问题，说明你还没有准备好简化。先阅读更多上下文。

### Step 4：扫描简化机会

寻找以下模式：

**结构复杂度：**
- 深度嵌套（3+ 层）→ 提取为卫语句或辅助函数
- 长函数（50+ 行）→ 拆分为专注的命名函数
- 嵌套三元表达式 → 替换为 if/else 链、switch 或查找对象

**命名和可读性：**
- 通用命名（`data`、`result`、`temp`、`val`）→ 重命名为描述性名称
- 缩写名称 → 使用完整单词（除非是通用缩写如 `id`、`url`）

**冗余：**
- 重复逻辑 → 提取为共享函数
- 死代码 → 确认后移除
- 不必要的抽象 → 内联包装器

### Step 5：增量应用

一次做一个简化。每次修改后运行测试。

```
FOR EACH SIMPLIFICATION：
1. 做出修改
2. 运行测试套件
3. 测试通过 → 继续下一个简化
4. 测试失败 → 回滚并重新考虑
```

**500 行规则**：如果重构涉及超过 500 行，使用自动化工具（codemods、脚本）而不是手动修改。

### Step 6：验证结果

所有简化完成后，评估整体效果：

```
COMPARE BEFORE AND AFTER：
- 简化版本是否真正更易理解？
- 是否引入了与代码库不一致的新模式？
- diff 是否清晰可审查？
- 团队成员是否会批准这个变更？
```

如果"简化"后的版本更难理解或审查，则回滚。

## Hermes Integration

当在 hermes-agent 项目中运行时：

- **MIM**：如果进行了显著的简化，通过 `winpeek_mim_send` 通知协作者
- **通知内容**：简化的文件列表、简化的类型和程度

参见 `website/docs/winpeek/mim-design/hermes-workflow-skill.md` 获取完整 Hermes 集成参考。
