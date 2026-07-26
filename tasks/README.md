# Peeka 开发任务索引

> 按模块分层。新任务启动时，从这里找到对应模块的任务文件。

## 已完成的会话

| 模块 | 版本 | 日期 | Plan | Todo | Spec | 验收 |
|------|------|------|------|------|------|------|
| 系统设置 (settings) | v1 | 2026-07-26 | [plan](settings-v1-2026-07-26-plan.md) | [todo](settings-v1-2026-07-26-todo.md) | — | [验收](../docs/peeka/settings-v1-acceptance.md) |

## 进行中 / 规划中

| 模块 | 版本 | 状态 | Plan | Spec |
|------|------|:--:|------|------|
| MIM 聊天 (mim) | v1 | 🟢 进行中 | [plan](mim-chat-v1-plan.md) / [todo](mim-chat-v1-todo.md) | [spec](../docs/peeka/mim-chat-v1-spec.md) |
| 开发流程 (workflow) | v1 | 🟢 进行中 | — | — |

## 功能模块树

参见 [功能模块树](../docs/governance/standards/dev-doc-standards.md#1-功能模块树2层)

## Zentao 任务追踪

| 产品 | Sprint | 需求 | 任务 | 链接 |
|------|:--:|:--:|:--:|------|
| peeka数字机器人 (#11) | #30 | 4 (#117-120) | 13 (#45-57) | [需求](https://pm.test.com/zentao/story-browse-117.html) · [任务](https://pm.test.com/zentao/task-browse-30.html) |

## 新会话启动指南 🚀

**快速上手（2 步）：**

1. **看任务**: `cat tasks/README.md` → 找到目标模块 → 读 plan + todo
2. **查 Zentao**: `ZENTAO_DB_HOST=192.168.3.23 zentao task list --execution=30` → 看 Sprint 任务

**深度上手（接手模块时）：**
1. 从本文件找到目标模块的任务文件路径
2. 按 [上下文加载流程](../docs/governance/standards/dev-doc-standards.md#3-任务启动时的上下文加载流程) 依次加载
3. 阅读对应模块的禁止事项列表
4. 运行 `zentao task list --execution=<id>` 查看对应 Zentao 任务状态
