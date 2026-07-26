---
title: "模块名 — 功能需求规格说明书"
type: "requirements"
phase: "plan"
author_subagent: ""
version: "1.0"
status: "draft"
last_updated: ""
module: ""
parent_module: "Peeka"
related: []
---

# 模块名 功能需求规格

## 1. 模块定位

（一句话描述这个模块做什么，为什么存在）

### 与业界对比（可选）

| 特性 | 竞品A | 竞品B | **本模块** |
|------|------|------|-----------|
| 特性1 | ... | ... | ... |

## 2. 功能树（2层）

```
模块名
├── F1. 功能组1
│   ├── F1.1 子功能A
│   └── F1.2 子功能B
└── F2. 功能组2
    └── F2.1 子功能C
```

## 3. 当前状态 vs 目标状态

| 功能 | 当前 | 目标 |
|------|:--:|:--:|
| F1.1 | ❌ 无 | ✅ |
| F1.2 | ⚠️ 部分 | ✅ |

## 4. 数据模型

### 已有表
```sql
-- 描述已有表结构
```

### 新增表
```sql
-- 需要新建的表
CREATE TABLE xxx (...);
```

## 5. 修改清单（按功能）

| 文件 | 改动 |
|------|------|
| `gateway/xxx.py` | 新增 function() |
| `tools/xxx.py` | 新增 handler |

## 6. 数据流动线

```
用户操作 → RPC handler → 业务逻辑 → DB
```

## 7. 验证计划

### 后端
```bash
python -c "..."
```

### 前端
```bash
npx tsc --noEmit
```
