# 禅道 AI 智能体使用指南

> 禅道已内置完整的 AI 需求管理套件。本文档说明如何使用，而非如何开发。
> 📍 [返回总索引](../../README.md)

---

## 禅道已提供的智能体清单

> http://pm.test.com

| 序号 | 智能体 | 用途 | 创建者 |
|:--:|------|------|:--:|
| 1 | 需求润色 | 优化需求标题、描述和验收标准的表述 | system |
| 2 | **需求评审** | 结构完整性、逻辑一致性、INVEST 标准评审 | system |
| 3 | **绘制需求原型图** | 从需求字段生成 HTML 原型 | system |
| 4 | 编写开发设计文档 | 根据需求生成技术设计文档 | system |
| 5 | 需求转任务 | 将需求拆分为可执行的开发任务 | system |
| 6 | 一键拆用例 | 为需求生成测试用例 | system |
| 7 | Bug 转需求 | Bug → 研发需求 | system |
| 8 | Bug 润色 | 优化 Bug 描述 | system |
| 9 | 任务润色 | 优化任务描述 | system |
| 10 | 拆分子计划 | 将计划拆分为子任务 | system |
| 11 | 文档润色 | 优化文档表述 | system |

## MIM 项目使用方式

### 1. 录入需求

在禅道中创建 Story，填写需求标题、描述、验收标准。

### 2. 需求评审（写代码前先过这一关）

```
点击 Story → AI 操作 → 需求评审
  ↓
输出：
  · 结构完整性分析
  · 逻辑一致性检查
  · 核心优先改进项
  · 次要优化建议
```

### 3. 需求润色

```
需求评审通过后 → 需求润色 → 自动优化表述
```

### 4. 生成原型图

```
润色完成后 → 绘制需求原型图 → 生成 HTML 原型
```

### 5. 拆分任务

```
原型确认后 → 需求转任务 → 生成开发任务列表
```

### 6. 生成测试用例

```
任务拆分后 → 一键拆用例 → 生成验收测试
```

## 完整流程

```
禅道 Story
  │
  ├─→ [需求润色] → 优化表述
  ├─→ [需求评审] → 检查完整性/一致性
  ├─→ [绘制原型图] → HTML 预览
  ├─→ [需求转任务] → 开发任务
  └─→ [一键拆用例] → 测试用例
```

## 与开发流程的对接

```
禅道（需求管理）          GitLab（代码管理）
─────────────────        ─────────────────
Story 创建               →
需求评审通过             →
原型图确认               →
任务拆分                 → Branch 创建
                         → 编码实现
                         → MR + Code Review
                         → 合并到 DEV
测试用例                 → 测试执行
                         → 发布上线
```

## Agent 接入方式

### 方式一：官方 CLI（推荐——功能最全）

```bash
npm install -g zentao-cli
npx zentao-cli login -s http://pm.test.com -u admin2020 -p Server3314
npx zentao-cli --format markdown story list --product 4
```

### 方式二：轻量 CLI（无需 npm，纯 Python）

```bash
.venv\Scripts\python.exe website/docs/reference/zentao_cli.py product list
.venv\Scripts\python.exe website/docs/reference/zentao_cli.py story list --product 4
.venv\Scripts\python.exe website/docs/reference/zentao_cli.py story create -p 4 -t "标题" --pri 2 --spec "描述"
```

Agent 一句话就能操作禅道：
```bash
# 查所有产品
python zentao_cli.py product list

# 查 DA 电脑数字人产品的需求
python zentao_cli.py story list --product 4

# 创建新需求
python zentao_cli.py story create -p 4 -t "新功能" --pri 2 --spec "功能描述"

# 查项目
python zentao_cli.py project list

# 查 Bug
python zentao_cli.py bug list --product 4
```

## 结论

**不需要自建需求管理系统。** 禅道已覆盖需求全生命周期。我们只需：
1. 把 MIM 功能录入禅道 Story
2. 用智能体完成评审/原型/拆分
3. Agent 通过禅道 API 查询任务状态
