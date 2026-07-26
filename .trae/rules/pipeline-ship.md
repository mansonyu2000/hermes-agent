---
description: "Run the pre-launch checklist via parallel fan-out to specialist personas, then synthesize go/no-go"
skills_invoked:
  - ".agents/skills/shipping-and-launch/SKILL.md"
---

# Pipeline: Ship

## Overview

运行发布前检查清单。通过并行派发到多个专家角色（代码审查、安全审计、测试工程师）收集评估结果，然后综合决策（GO/NO-GO）。目标是安全、可观察、可回滚地发布。

## Invoked Skill

读取 `.agents/skills/shipping-and-launch/SKILL.md` 获取完整发布工作流。

**不跳过任何步骤、Common Rationalizations、Red Flags 或 Verification checklists。**

## Workflow

### Phase A：并行派发（Parallel Fan-Out）

同时激活以下专家角色（来自 `.agents/personas/`）：

| 角色 | 评估内容 | 输出 |
|------|----------|------|
| **Code Reviewer** | 代码质量、正确性、可读性、架构 | 审查报告 |
| **Security Auditor** | 安全漏洞、密钥泄露、注入风险、认证 | 安全报告 |
| **Test Engineer** | 测试覆盖率、回归风险、关键流验证 | 测试报告 |

每个角色独立评估，输出结构化报告。所有报告收集完毕后进入 Phase B。

### Phase B：合并主上下文

汇总 Phase A 的所有报告，综合评估：

1. 合并各角色的发现和建议
2. 识别跨角色的共性问题
3. 评估整体发布风险等级
4. 准备决策依据

### Phase C：决策（GO / NO-GO）

基于综合评估做出决策：

#### GO 条件
- 所有 Critical 问题已解决
- 无未解决的安全漏洞
- 测试全部通过
- 回滚计划已就绪
- 监控和日志已配置

#### NO-GO 条件
- 存在未解决的 Critical 问题
- 安全审计发现高危漏洞
- 测试失败
- 关键用户流验证失败

### 回滚计划

每次发布前准备回滚计划：

```markdown
## Rollback Plan for [Feature/Release]

### Trigger Conditions
- 错误率 > 2x 基线
- P95 延迟 > [X]ms
- 用户报告 [特定问题]

### Rollback Steps
1. 禁用功能开关（如适用）
   或
1. 部署上一版本：`git revert <commit> && git push`
2. 验证回滚：健康检查、错误监控
3. 沟通：通知团队回滚

### Database Considerations
- 迁移 [X] 有回滚脚本
- 新功能插入的数据：[保留 / 清理]

### Time to Rollback
- 功能开关：< 1 分钟
- 重新部署：< 5 分钟
- 数据库回滚：< 15 分钟
```

## Hermes Integration

当在 hermes-agent 项目中运行时：

- **ZenTao**：如果 GO，通过 `zentao release create` 创建 Release
- **MIM**：通过 `winpeek_mim_send` 通知团队发布状态
- **通知内容**：发布版本、变更摘要、回滚计划、监控链接

参见 `website/docs/winpeek/mim-design/hermes-workflow-skill.md` 获取完整 Hermes 集成参考。
