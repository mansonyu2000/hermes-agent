---
sidebar_position: 11
title: "WinPeek RPA 自愈型工作流引擎"
description: "人工+AI共建 → 自动纠错 → 零LLM自主执行：桌面UI自动化工作流的自学习、自愈架构"
---

> 📍 [返回文档索引](README)

---

## 一、核心理念

### 目标演进

```
Phase 1: 人工 + AI 共建 → 人工主导，AI 协助录制/编排
Phase 2: AI 执行 + 人工纠错 → 自动运行，出错时人工介入
Phase 3: AI 执行 + LLM 自愈 → 正常零 LLM，出错时 LLM+视觉诊断并修正
Phase 4: 完全自主 → 零人工、零 LLM，靠累积的经验库自主运行
```

### 关键原则

| 原则 | 说明 |
|------|------|
| **正常运行零 LLM** | LLM 推理成本高、速度慢，只作为安全网 |
| **错误即学习机会** | 每次出错都是 workflow 改进的契机 |
| **经验可累积** | 同一流程执行 N 次后，覆盖了 N 种边缘情况 |
| **视觉是最终兜底** | UIA 失效时，用截图+视觉模型判断状态 |
| **Oculix 为视觉执行核心** | OpenCV 模板匹配 + Tesseract OCR，通过 MCP 从 Python 调用 |

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      WinPeek RPA Self-Healing Engine                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │  ① Workflow       │    │  ② Execution     │    │  ③ Error     │  │
│  │  Designer         │───▶│  Engine           │───▶│  Detector    │  │
│  │  (可视化编排器)    │    │  (执行引擎)       │    │  (错误检测)   │  │
│  └───────────────────┘    └──────────────────┘    └──────┬───────┘  │
│         ▲                         │                      │         │
│         │                         ▼                      ▼         │
│         │                 ┌─────────────────────────────────────┐  │
│         │                 │  ④ Error Handler                    │  │
│         │                 │  ┌─────────┐  ┌──────────────────┐  │  │
│         │                 │  │已知错误库│  │ LLM+Vision 矫正器│  │  │
│         │                 │  │(匹配重试)│  │(未知错误分析修复) │  │  │
│         │                 │  └─────────┘  └──────────────────┘  │  │
│         │                 └─────────────────────────────────────┘  │
│         │                              │                           │
│         │                              ▼                           │
│         │                 ┌─────────────────────────────────────┐  │
│         └─────────────────│  ⑤ Workflow Memory Bank             │  │
│                           │  执行轨迹 / 失败模式 / 替代方案      │  │
│                           │  累积经验，越用越稳                  │  │
│                           └─────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、核心组件详解

### ① Workflow Designer（可视化编排器）

**人工+AI 共建**：先人工录制或 LLM 辅助生成操作步骤，形成初始 workflow。

**Workflow 节点类型**：

```
Workflow = DAG 图，节点类型：

Start ──▶ ActionNode ──▶ DecisionNode ──▶ ActionNode ──▶ End
              │                │
              ▼                ▼
         CheckNode        WaitNode
```

| 节点类型 | 功能 | 示例 |
|---------|------|------|
| **Start** | 启动目标应用 | `OpenApp("wechat.exe")` |
| **Action** | 执行 UI 操作 | `Click(btn_login)`, `Type(input_search, "张三")` |
| **Check** | 验证状态 | `CheckElement(chat_window)`, `CheckText("登录成功")` |
| **Decision** | 条件分支 | `If(登录成功) → 下一步 Else → 重试` |
| **Wait** | 等待/延迟 | `WaitElement(2000ms)`, `Wait(5s)` |
| **Loop** | 循环 | `ForEach(联系人列表) → 发送消息` |
| **SubWorkflow** | 子流程 | 复用已稳定的子流程 |
| **End** | 结束 | 返回执行结果 |

**每个 ActionNode 的元数据**：

```json
{
  "step_id": "step-003",
  "type": "click",
  "target": {
    "primary_method": "uia_aid",      // 首选：UIA AutomationId
    "selector": "btn_login",
    "backup_methods": [                // 后备定位器（越用越多）
      {"method": "position", "rect": [120, 340, 80, 36]},
      {"method": "visual", "image": "login_button.png"}
    ]
  },
  "validation": {                      // 执行后的验证
    "check": "element_appears",
    "selector": "chat_main_window",
    "timeout_ms": 5000
  }
}
```

---

### ② Execution Engine（执行引擎）

**运行时零 LLM**，纯粹按 workflow 描述执行。

```
Function execute_workflow(wf):
    for each step in wf.steps:
        try:
            result = step.execute()
            validate(step.validation, result)
            save_screenshot_before_and_after(step.step_id)
            push_to_memory(step.step_id, "success", result)
        catch Error:
            handle_error(step, error, wf)
```

**定位策略链**（四层由快到慢）：

```
Tier 1 UIA-AID:    0.1s  → 通过 → 执行操作     ← rpa_tools.py uia_find()
    ↓ 失败
Tier 2 位置记忆:    0.2s  → 通过 → 执行操作     ← 自建执行轨迹积累
    ↓ 失败
Tier 3 图像匹配:    0.3s  → 通过 → 执行操作     ← Oculix OpenCV 模板匹配
    ↓ 失败
Tier 4 OCR 定位:    0.5s  → 通过 → 执行操作     ← Oculix Tesseract OCR
    ↓ 全部失败
触发 Error Handler
```

---

### ③ Error Detector（错误检测）

**不需要 LLM**，通过规则检测异常。

| 检测规则 | 触发条件 | 错误码 |
|---------|---------|--------|
| `TimeoutError` | 等待超时 | `E001` |
| `ElementNotFound` | 三层次定位全部失败 | `E002` |
| `ElementDisappeared` | 点击前元素已消失 | `E003` |
| `UnexpectedDialog` | 检测到意外弹窗 | `E004` |
| `StateMismatch` | 执行后验证不通过 | `E005` |
| `AppCrash` | 目标窗口关闭 | `E006` |

---

### ④ Error Handler（错误处理器）

**这是自愈的核心**，分两级：

#### 4a 已知错误库（Known Error Bank）— 零 LLM

```
已知错误匹配:
  错误码 + 当前截图哈希 + 步骤ID → 命中已知解决方案

示例:
  错误: E002 (元素未找到) @ step-003 (click btn_login)
  匹配: 已知解决方案 "login_btn_moved_v2"
  动作: 更新 step-003.target.selector = "btn_login_v2"
        ↓
  Workflow 被自动修正，下次执行正确
```

#### 4b LLM+Vision 矫正器（仅未知错误调用）

只在已知错误库未命中时调用：

```
触发条件: 已知错误库未命中
流程:
  1. 截图当前状态
  2. 截图期望状态（从历史成功执行中取）
  3. 调用 LLM + 视觉模型（Qwen2.5VL）
  4. LLM 分析:
     - "当前处于什么状态？"
     - "期望处于什么状态？"
     - "差异是什么？"
     - "如何修正 workflow？"
  5. 生成修正方案
  6. 人工确认（Phase 1-2）/ 自动应用（Phase 3-4）
  7. 将修正方案存入已知错误库
```

**LLM 矫正器的 Prompt 模板**：

```
你是一个RPA工作流诊断专家。以下是执行失败的上下文：

[Workflow步骤]
{step_description}

[当前截图]
{screenshot_base64}

[预期状态]
{expected_state_description}

[错误信息]
{error_message}

请分析：
1. 当前界面处于什么状态？
2. 期望的状态应该是什么？
3. 两者差异在哪里？
4. 导致失败的根本原因是什么？
5. 如何修改workflow的这一步来修复？
输出修正方案（JSON格式）。
```

---

### ⑤ Workflow Memory Bank（经验库）

**这是从 Phase 1 走到 Phase 4 的关键**。每执行一次，积累一份经验。

```json
{
  "workflow_id": "wechat-send-message-v3",
  "total_runs": 127,
  "success_runs": 121,
  "failure_runs": 6,
  "last_success": "2026-07-25T10:30:00",

  "step_memories": {
    "step-001": {
      "step_desc": "打开微信",
      "success_count": 127,
      "failure_count": 0,
      "avg_duration_ms": 3200,
      "known_issues": []
    },
    "step-003": {
      "step_desc": "点击登录按钮",
      "success_count": 123,
      "failure_count": 4,
      "avg_duration_ms": 450,
      "known_issues": [
        {
          "issue_id": "ISS-001",
          "first_seen": "2026-07-20",
          "times_occurred": 3,
          "last_seen": "2026-07-23",
          "symptom": "UIA AutomationId 'btn_login' 找不到",
          "root_cause": "微信版本更新后登录按钮 ID 变为 'btn_login_v2'",
          "fix_action": "更新 target.selector 为 'btn_login_v2'",
          "fixed": true,
          "fixed_at": "2026-07-20",
          "verification_runs": 50
        },
        {
          "issue_id": "ISS-002",
          "first_seen": "2026-07-24",
          "times_occurred": 1,
          "last_seen": "2026-07-24",
          "symptom": "UIA 定位失败，位置记忆也失败",
          "root_cause": "登录窗口位置偏移（屏幕分辨率变更）",
          "fix_action": [
            "方案A: 添加像素锚点定位作为第三后备",
            "方案B: 先用 UIA 查找父窗口，再相对定位"
          ],
          "fixed": false,
          "pending_review": true
        }
      ]
    }
  }
}
```

---

## 四、从 Phase 1 到 Phase 4 的演进

### Phase 1：人工 + AI 共建

```
人工操作流程:
  打开微信 → 截图 → 告诉 AI "这里要点登录"
    ↓
AI 生成 ActionNode
    ↓
人工审核 workflow
    ↓
首次执行（人工监控）
```

### Phase 2：AI 执行 + 人工纠错

```
Workflow 自动执行
    ↓
出错了 → Error Detector 捕获 → 截图
    ↓
人工查看截图 → 告诉 AI "登录按钮变位置了，在右上角"
    ↓
LLM+Vision 修正 workflow
    ↓
修正后的方案存入 Known Error Bank
    ↓
下次执行直接按修正后的方案走（不再需要人工）
```

### Phase 3：AI 执行 + LLM 自愈

```
Workflow 自动执行
    ↓
出错了 → Error Detector 捕获 → 截图
    ↓
已知错误库匹配 → 命中 → 自动修正 → 继续执行
    ↓
未命中 → LLM+Vision 分析 → 生成修正方案
    ↓
方案存入已知错误库
    ↓
人工确认（可选）→ 自动应用
```

### Phase 4：完全自主

```
Workflow 自动执行
    ↓
遇到任何错误 → 错误库都已覆盖 → 零 LLM 自动修正
    ↓
执行 1000 次 → 遇到 200 种边缘情况 → 全部入库
    ↓
新版本微信更新 → 少量新错误 → LLM 介入 → 入库 → 又稳了
```

---

## 五、与现有 WinPeek 基础设施的集成

```
现有组件                  自愈引擎集成点
─────────────────────────────────────────────────
rpa_tools.py               Execution Engine 调用
  ├── uia_find()           → Tier 1 定位器
  ├── mouse_click()        → Action 执行器
  └── ocr_region_mcp()     → Check 验证器

wechat-rpa-navigation.md    → 四层定位策略 + 窗口布局信息
  四层定位策略               → 内置于 Execution Engine
  虚拟列表三戒               → CheckNode 的验证规则

Oculix（SikuliX 分支）       → 视觉执行引擎（Java 进程，Python 通过 MCP 调用）
  ├── oculix_find_image     → Tier 3 图像匹配定位
  ├── oculix_click_image    → Action 执行器（图像级）
  ├── oculix_click_text     → Tier 4 OCR 定位 + 点击
  ├── oculix_find_text      → Check 验证器（OCR）
  ├── oculix_type_text      → Action 执行器
  ├── oculix_wait_for_image → WaitNode 等待器
  ├── oculix_wait_for_stable→ WaitNode 等待屏幕静止
  ├── oculix_screenshot     → Error Handler 截图输入
  └── oculix_read_text_in_region → Check 验证器

WinPeek MCP 工具            → 截图 + 视觉分析
  窗口截图                   → Error Handler 的输入
  VL 分析                   → LLM+Vision 矫正器

── Oculix 集成说明 ──
Oculix 本质是 Java 进程，但通过 stdio JSON-RPC（MCP 协议）暴露 13 个工具，
Python 代码以 subprocess 或 MCP 客户端方式调用，不写一行 Java。
安装：java -jar oculix-mcp.jar（需 Java 11+），连接方式见 Oculix MCP 文档。
```

---

## 六、落地路线图

```
Week 1-2: 构建 Workflow Designer
          - 定义 workflow JSON schema
          - 可视化节点编辑器
          - 初始 ActionNode 类型

Week 3-4: 构建 Execution Engine
          - 三层定位执行器
          - 验证器
          - 错误检测

Week 5-6: 构建 Error Handler
          - Known Error Bank
          - LLM+Vision 矫正器
          - Prompt 模板

Week 7-8: 构建 Memory Bank
          - 执行轨迹存储
          - 失败模式索引
          - 自愈效果统计

Week 9-10: Phase 1 人工+AI 共建
          - 录制 WeChat 发送消息流程
          - 人工审核修正
          - 首次全流程执行

Week 11-12: Phase 2-3 演进
          - 积累边缘情况
          - 验证自愈效果
          - 逐步减少人工介入
```

---

## 七、关键成功指标

| 指标 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|
| 人工介入率 | 100% | 50% | 10% | <1% |
| LLM 调用率 | 0% | 30% | 15% | <2% |
| 自愈成功率 | 0% | 40% | 85% | >98% |
| 已知错误库 | 0 | ~50 | ~500 | ~2000+ |
| 单次执行耗时 | N/A | ~30s | ~15s | ~8s |
