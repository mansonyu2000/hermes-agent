---
description: "Conduct a five-axis code review — correctness, readability, architecture, security, performance"
skills_invoked:
  - ".agents/skills/code-review-and-quality/SKILL.md"
---

# Pipeline: Review

## Overview

对代码变更执行五轴代码审查——正确性、可读性、架构、安全性、性能。每次变更在合并前都必须经过审查，没有例外。

## Invoked Skill

读取 `.agents/skills/code-review-and-quality/SKILL.md` 获取完整代码审查工作流。

**不跳过任何步骤、Common Rationalizations、Red Flags 或 Verification checklists。**

## Workflow

### Step 1：理解上下文

在查看代码之前，先理解变更意图：

- 这次变更试图完成什么？
- 它实现的是哪个规范或任务？
- 预期的行为变化是什么？

### Step 2：五轴审查

沿以下五个维度评估代码：

#### 1. 正确性（Correctness）
- 代码是否匹配规范/任务要求？
- 是否处理了边界情况（null、空值、边界值）？
- 是否处理了错误路径（不只是快乐路径）？
- 测试是否通过？测试是否在测试正确的东西？

#### 2. 可读性与简洁性（Readability & Simplicity）
- 命名是否描述性且与项目约定一致？
- 控制流是否直接明了？
- 能否用更少的行数完成？
- 抽象是否值得其复杂性？

#### 3. 架构（Architecture）
- 是否遵循现有模式或引入了新模式？
- 是否保持了清晰的模块边界？
- 是否有代码重复应当共享？
- 依赖方向是否正确（无循环依赖）？

#### 4. 安全性（Security）
- 用户输入是否经过验证和清理？
- 密钥是否远离代码、日志和版本控制？
- 需要的地方是否检查了认证/授权？
- SQL 查询是否参数化？
- 外部数据源是否被视为不可信？

#### 5. 性能（Performance）
- 是否存在 N+1 查询模式？
- 是否存在无界循环或不受限制的数据获取？
- 列表端点是否缺少分页？
- 是否存在同步操作应当异步？

### Step 3：分类发现

为每条发现标注严重级别：

| 前缀 | 含义 | 作者操作 |
|------|------|----------|
| *(无前缀)* | 必须修改 | 合并前必须处理 |
| **Critical：** | 阻塞合并 | 安全漏洞、数据丢失、功能破坏 |
| **Nit：** | 可选，微小 | 作者可忽略 |
| **Optional：** / **Consider：** | 建议 | 值得考虑但不强制 |
| **FYI** | 仅供参考 | 无需操作 |

按杠杆率排序：正确性和安全性优先，然后是架构问题和遗漏的简化，最后是其他。

### Step 4：验证验证过程

检查作者的验证证据：

- 运行了什么测试？
- 构建是否通过？
- 是否进行了手动测试？
- UI 变更是否有截图？
- 是否有前后对比？

### Step 5：给出裁决

- **Approve** — 准备合并
- **Request changes** — 问题必须解决

## Hermes Integration

当在 hermes-agent 项目中运行时：

- **ZenTao**：将审查结果提交到 ZenTao
- **MIM**：通过 `winpeek_mim_send` 通知作者审查结果
- **关联**：审查链接到对应的 Story/Task ID

参见 `website/docs/winpeek/mim-design/hermes-workflow-skill.md` 获取完整 Hermes 集成参考。
