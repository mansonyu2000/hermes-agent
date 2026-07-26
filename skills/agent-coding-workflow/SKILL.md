---
name: agent-coding-workflow
description: 当 Agent 收到开发任务时自动激活。桥接 agent-skills(24技能) + superpowers-zh(流程) → 本项目的3个独特层(文档治理+双系统同步+集群规则)。触发词：开发、做功能、启动流水线、新功能、发消息。
---

# Agent Coding Workflow — 三层桥接

## 定位

此技能不重造轮子。它桥接三个成熟层 + 本项目的三层独特能力：

```
Layer 0: agent-skills (Addy Osmani, 24 skills)
  Define → Plan → Build → Verify → Review → Ship
  覆盖: interview-me, spec-driven-development, planning-and-task-breakdown,
        incremental-implementation, test-driven-development, code-review-and-quality,
        shipping-and-launch, +17 more

Layer 1: superpowers-zh (流程技能)
  brainstorming, writing-plans, subagent-driven-development,
  systematic-debugging, verification-before-completion, +10 more

─────── 本项目独特层 ───────

Layer 2: 文档治理 + 双系统同步
  document-manager-agent → docs/索引+frontmatter+禅道/Multica双向同步

Layer 3: 功能集群治理
  docs/governance/standards/cluster-rules.md → 集群判定+灵活归并+文档必留

Layer 4: 24/7 Supervisor
  hermes-peeka(uid=3000) → 禅道巡检+进度驱动+MIM say指挥
```

## 触发规则

| 用户说 | 加载的技能链 |
|--------|------------|
| "做发消息功能" | `interview-me` → `spec-driven-development` → `planning-and-task-breakdown` → `incremental-implementation` + `test-driven-development` |
| "这个需求不清" | `interview-me` → `idea-refine` → `spec-driven-development` |
| "代码审查" | `code-review-and-quality` + `code-simplification` |
| "部署上线" | `shipping-and-launch` + `ci-cd-and-automation` |
| "修 bug" | `systematic-debugging`(superpowers-zh) → `test-driven-development` |
| "提交/合并" | `git-workflow-and-versioning` + `finishing-a-development-branch`(superpowers-zh) |

## 不可跳过的门禁

<HARD-GATE>
1. **新功能 = interview-me + spec-driven-development 必须跑** — 没 spec 不写代码
2. **多文件改动 = incremental-implementation** — 垂直切片，每片测试+提交
3. **逻辑改动 = test-driven-development** — 红→绿→重构
4. **合并前 = code-review-and-quality** — 五维审查
5. **每次改动 = git-workflow-and-versioning** — 原子提交
</HARD-GATE>

## 本项目独特规则（写在 agent-skills 之上）

1. **文档沉淀** — 每个阶段产出必须写入 `docs/{cluster}/`，由 document-manager-agent 治理
2. **功能集群** — 按 `cluster-rules.md` 判定粒度（2-8周），灵活归并
3. **禅道同步** — Spec 定稿后同步到 pm.test.com (story)，交付后同步 (release)
4. **Multica 任务** — 拆解后的任务推送 Multica Issue，Agent 自主领取
5. **MIM 通讯** — 阻塞/疑问通过 `say <uid>` 通知相关 Agent

## 可用自定义 Agent

| Agent | 用途 |
|-------|------|
| `document-manager-agent` | 文档索引+frontmatter+双系统同步 |
| `orchestrator-agent` | 复杂多阶段任务调度（仅大项目用） |

## 设计参考

- agent-skills 24 技能: `.agents/skills/` 或 `skills/`
- v3 架构文档: `docs/agent-coding-workflow/wokflow-v3.md`
- 集群治理: `docs/governance/standards/cluster-rules.md`
- Supervisor 设计: [[supervisor-agent-design]]
