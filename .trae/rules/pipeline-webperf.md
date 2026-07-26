---
description: "Run a web performance audit — quick static analysis or deep Lighthouse/PSI audit"
skills_invoked:
  - ".agents/personas/web-performance-auditor.md"
---

# Pipeline: Web Performance Audit

## Overview

执行 Web 性能审计。支持两种模式：**快速模式**（静态分析）和**深度模式**（Lighthouse/PageSpeed Insights 等运行时工具）。返回结构化审计报告，包含发现、影响评估和修复建议。

## Invoked Persona

读取 `.agents/personas/web-performance-auditor.md` 获取完整审计工作流。

> **注意**：该 Persona 文件需要在 `.agents/personas/` 目录中存在。如果不存在，将使用本规则中定义的轻量级审计流程。

## Workflow

### Step 1：选择审计模式

#### 快速模式（Quick Mode）— 静态分析

无需运行浏览器或外部工具，基于代码分析进行评估：

1. **构建产物分析**
   - 检查 bundle 大小和分割情况
   - 识别未优化的资源（未压缩图片、未精简的 JS/CSS）
   - 检查是否启用了 tree-shaking 和代码分割

2. **前端性能检查**
   - 是否使用了懒加载（图片、组件、路由）
   - 是否存在渲染阻塞资源
   - 是否配置了缓存策略（Service Worker、CDN 缓存头）
   - 是否存在不必要的重渲染（React key 属性、memo 使用）

3. **运行时性能信号**
   - 是否存在 N+1 API 调用
   - 是否存在大对象在热路径中创建
   - 是否存在同步操作阻塞主线程

4. **Core Web Vitals 预估**
   - LCP（最大内容绘制）—— 是否有大图片或慢字体
   - INP（交互到下一次绘制）—— 是否有长任务（>50ms）
   - CLS（累积布局偏移）—— 是否有未设置尺寸的图片/嵌入内容

#### 深度模式（Deep Mode）— 运行时审计

使用 Lighthouse / PageSpeed Insights / Chrome DevTools MCP 进行运行时评估：

1. **运行 Lighthouse 审计**（如可用）
   - 获取 Performance、Accessibility、Best Practices、SEO 评分
   - 获取 Core Web Vitals 实测数据
   - 获取优化建议列表

2. **Chrome DevTools 分析**（如可用）
   - 检查网络请求瀑布图
   - 检查 Console 错误和警告
   - 检查 Performance 面板的长任务和帧率

3. **PSI（PageSpeed Insights）**（如可用）
   - 获取实验室数据和字段数据
   - 对比移动端和桌面端评分

### Step 2：生成审计报告

输出结构化审计报告：

```markdown
# Performance Audit Report

## Summary
- **Mode：** [Quick / Deep]
- **URL：** [URL]
- **Overall Assessment：** [Good / Needs Improvement / Poor]

## Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| LCP | [value] | < 2.5s | ✅ / ⚠️ / ❌ |
| INP | [value] | < 200ms | ✅ / ⚠️ / ❌ |
| CLS | [value] | < 0.1 | ✅ / ⚠️ / ❌ |
| [其他指标] | | | |

## Findings
### Critical
1. [发现描述] — [影响] — [建议修复]

### Recommended
1. [发现描述] — [影响] — [建议修复]

### Optional
1. [发现描述] — [影响] — [建议修复]

## Recommendations by Priority
1. [高优先级修复项]
2. [中优先级修复项]
3. [低优先级修复项]
```

### Step 3：呈现并建议操作

- 展示报告给用户
- 根据审计结果建议后续操作
- 如有性能回归，建议创建性能优化任务

## Hermes Integration

当在 hermes-agent 项目中运行时：

- **ZenTao**：如果发现性能回归，通过 `zentao task create` 创建性能优化任务
- **MIM**：通过 `winpeek_mim_send` 通知团队审计结果

参见 `website/docs/winpeek/mim-design/hermes-workflow-skill.md` 获取完整 Hermes 集成参考。
