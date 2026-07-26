---
title: "参考资料库"
type: reference
role: ["architect", "developer"]
---

# 参考资料库

> 📍 [返回总索引](../README.md)

## 目录

```
reference/
├── zentao-prototype-agent.md ← 禅道 AI 智能体使用指南（需求评审/原型/拆分）
├── astrbot.md              ← AstrBot 架构参考（灵感来源）
├── AI-Driven-Dev-Platform/  ← ★ 完整 da 项目 [→入口](AI-Driven-Dev-Platform/index.md)
├── templates/              ← 文档/验收/测试模板 [→说明](templates/README.md)
│   ├── doc-template.md     ← 标准文档模板
│   ├── acceptance-template.md ← 验收标准空白模板
│   ├── acceptance-phase1.md   ← 第一阶段验收（1-3月）★ 来自 da 项目
│   ├── acceptance-phase2.md   ← 第二阶段验收（3-6月）★ 来自 da 项目
│   └── acceptance-phase3.md   ← 第三阶段验收（6-12月）★ 来自 da 项目
├── cases/                  ← 案例（成功的实践记录） [→说明](cases/README.md)
├── examples/               ← 样例（完整项目参考案例） [→说明](examples/README.md)
│   ├── example-requirements.md       ← 需求文档示范 ★ da 项目
│   ├── example-product-prototype.md  ← 产品原型示范 ★ da 项目
│   ├── example-architecture.md       ← 架构图示范 ★ da 项目
│   └── example-api-design.md         ← API 设计草案 ★ da 项目
```

## 使用方式

这里的文档是**素材和灵感来源**，不是必须遵循的规范。需要时从中选取对应模板，复制到目标位置，按其格式填写。

> 来源包括：Diátaxis 框架、CRMEB 文档体系、AstrBot 架构、AI-Driven-Dev-Platform 验收标准等。

## ⚠️ 使用规则（铁律）

1. **禁止直接修改原始文件**——本目录下所有文件一经入库即为不可变参考
2. **引用方式**——复制需要的文件到项目对应位置，在原文件基础上修改
3. **修正例外**——发现原始内容有事实性错误时，可修正并标注 `[已修正: 日期, 原因]`
4. **新增素材**——新发现的优秀参考素材放入对应子目录（templates/cases/examples）
5. **来源标注**——所有外部来源的素材在文件头部注明 `source:` 字段
