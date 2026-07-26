# 参考资料萃取库

> 只读。仅 SubAgent #1 (reference-extract-agent) 可写入。

## 用途

保存从外部来源（文档、论文、网页、API 文档）萃取的参考资料。
原始内容经格式化、去重、标注来源后存入此目录。

## 目录结构

```
reference-library/
├── api-docs/       # API 参考文档
├── papers/         # 论文/技术报告
├── specs/          # 外部产品规格
└── benchmarks/     # 性能基准数据
```

## 写入规则

- 文件必须包含 frontmatter（`source_url`, `extracted_at`, `extractor`）
- 原始内容不修改，只做格式转换
- 每个文件 ≤ 10KB
