# 模板库

> 📍 [返回参考资料库](../README.md)
> ⚠️ **只读参考，禁止直接修改**——用的时候复制出去改

## 目录

| 文件 | 用途 | 使用场景 |
|------|------|---------|
| `doc-template.md` | 标准文档元数据模板 | 新建任何 `.md` 文档时 |
| `dev-plan-template.md` | 开发计划模板 | 写修复/功能/重构计划（含问题/方案/验收/图） |
| `acceptance-template.md` | 验收标准空白模板 | 为新功能/新模块编写验收标准时套用 |
| `acceptance-phase1.md` | 第一阶段验收（1-3月） | 写短期里程碑验收标准时参考 |
| `acceptance-phase2.md` | 第二阶段验收（3-6月） | 写中期里程碑验收标准时参考 |
| `acceptance-phase3.md` | 第三阶段验收（6-12月） | 写长期里程碑验收标准时参考 |

## 如何使用

```bash
# 1. 复制模板到目标位置
cp reference/templates/dev-plan-template.md development/plans/2026-07-18-mim-v1-plan.md

# 2. 编辑内容，保留 frontmatter 和章节结构
# 3. 填写实际的问题、方案、验收标准、图
```

## 开发计划模板结构

`dev-plan-template.md` 包含 10 个章节：

| # | 章节 | 说明 |
|---|------|------|
| 1 | Summary | 一句话问题描述 |
| 2 | Problem Frame | 上下文、触发条件、影响范围 |
| 3 | Requirements | 可验证的编号需求（R1/R2/R3） |
| 4 | Key Technical Decisions | 设计决策和理由 |
| 5 | High-Level Technical Design | 流程图/时序图（必填 Mermaid） |
| 6 | Implementation Units | 分单元：Goal/Deps/Files/Approach/Tests/Verification |
| 7 | Scope Boundaries | In/Out/Deferred |
| 8 | Risks & Mitigations | 风险识别和防范 |
| 9 | Sources & Research | 引用的截图、日志、代码、文档 |
| 10 | Verification Strategy | 要跑的测试和验证步骤 |

## 验收标准模板结构

每个阶段模板包含 6 个验收维度：

| 维度 | 内容 |
|------|------|
| 技术架构 | 各层实现、环境搭建、API 网关、认证 |
| 核心功能 | 工作流引擎、知识库、AI 能力、IDE 插件 |
| 性能 | 响应时间、稳定性、并发、资源 |
| 质量 | 代码覆盖、安全、文档、测试 |
| 用户体验 | 易用性、满意度 |
| 业务价值 | 技术可行性、团队能力、ROI |
