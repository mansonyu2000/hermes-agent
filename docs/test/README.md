# 测试产物

> SubAgent #7 (testing-verify-agent) 的输出目录。

## 目录结构

```
test/
├── test-plan.md       # 测试计划
├── test-cases/        # 测试用例
│   ├── e2e/           # 端到端测试
│   └── unit/          # 单元测试
└── test-report.md     # 测试报告
```

## 规则

- 测试用例命名: `{module}-{feature}-{scenario}.md`
- 测试报告含通过率 + 失败详情 + 截图
