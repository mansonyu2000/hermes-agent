# 软件开发多智能体流水线 · v3（Orchestrator + SubAgent 架构）

> 本文档是 `wokflow.md`（v2）的演进版本。**核心变更**：从单会话 7 步骤模型升级为 **Orchestrator 主控 + 7 个独立 SubAgent** 双层架构。v1/v2 仍保留，本版不覆盖。

---

## 〇、核心设计原则（继承 v2）

1. **需求驱动参考（锚与帆）**：用户先给「轮廓需求」定方向；萃取阶段围绕轮廓需求去参考物里**定向提取**，不盲解析全部资料。
2. **主干优先，旁支用行业基线**：先收敛跑通主干流程；旁支细节以行业通用基线为参照。
3. **任何材料有出处**：用户素材 / 联网参考物 / 行业基线 / 用户诉求，均须标注来源。
4. **文档契约门禁**：每个智能体严格以「上游定稿文档」为输入门禁，缺则拒绝开工。

### v3 新增核心原则

5. **SubAgent 纵深专业**：每个 SubAgent 独立会话，专注一个领域。做得越多越聪明——通过 session 历史积累领域经验，实现纵深专业能力。
6. **Orchestrator 只做调度，不做执行**：主控负责任务拆解、SubAgent 调用、产物校验、流转控制。不越俎代庖代替 SubAgent 做领域决策。
7. **产物即契约**：SubAgent 之间的通信不通过消息传递，而是通过标准化的文件产物（`docs/` 目录下的归档文档）。文件系统是唯一可信总线。

---

## 一、双层架构设计（v3 核心变化）

```
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator 主控会话                        │
│  职责：拆解任务 → 调用 SubAgent → 校验产物 → 流转下一阶段    │
│  当前 AI Session，读懂需求上下文，但不做领域执行              │
│                                                              │
│  ┌─ 方式B（主流程）：调用独立 SubAgent，传入产出路径         │
│  └─ 方式A（辅助）：直接在当前会话处理轻量任务                │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ SubAgent  │  │ SubAgent  │  │ SubAgent  │  │ SubAgent  │
│    #1     │  │    #2     │  │    #3     │  │   ...#7   │
│ 需求萃取  │→│ 需求确认  │→│ 任务拆解  │→│ 交付部署  │
│          │  │          │  │          │  │          │
│ 独立session│  │ 独立session│  │ 独立session│  │ 独立session│
│ 纵深经验积累│  │ 纵深经验积累│  │ 纵深经验积累│  │ 纵深经验积累│
└──────────┘  └──────────┘  └──────────┘  └──────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                          │
                    ┌─────▼──────┐
                    │  docs/ 目录  │ ← 产物即契约，文件系统是唯一总线
                    │  (统一存储)  │
                    └────────────┘
```

### 1.1 Orchestrator 主控层的职责

| 职责 | 说明 |
|------|------|
| **任务拆解** | 将用户"我要做 X"拆成有序的 SubAgent 调用序列 |
| **SubAgent 调度** | 按顺序调用 SubAgent，传入上游产物路径和输入参数 |
| **产物校验** | 每个 SubAgent 完成后，校验固化标识和产出物是否完整 |
| **异常处理** | 产物校验失败 → 重新调用 SubAgent 修复；需求歧义 → 回调需求确认 SubAgent |
| **进度通知** | 向用户报告当前进度、下一步计划、异常情况 |

Orchestrator 本身**不写代码、不做设计、不写需求**——它只做调度和校验。

### 1.2 SubAgent 执行层的职责

| # | SubAgent | 输入 | 产出 | 纵深经验 |
|---|----------|------|------|---------|
| 1 | 需求与参考萃取 | 轮廓需求 + 参考资料 | 萃取素材库 + 需求草案 | 积累行业参考库、竞品分析经验 |
| 2 | 需求与参考对齐确认 | 萃取素材库 | 需求规格书 + 参考对照表 + 验收要点 | 积累领域需求模式、常见歧义处理 |
| 3 | **任务拆解与计划**（v3 新增） | 需求规格书 | 开发计划 + 任务清单（关联禅道） | 积累工作量估算、任务拆解模式 |
| 4 | UI 界面设计 | 需求定稿 | UI 原型规范 | 积累组件库、交互模式 |
| 5 | 架构设计 | 需求 + UI 双定稿 | 架构方案 | 积累技术选型、架构模式 |
| 6 | 代码开发 | 需求 + UI + 架构 三文档 | 完整可运行代码 | 积累项目模板、代码模式 |
| 7 | 测试校验 | 上游文档 + 代码 | 测试报告 | 积累测试用例库、缺陷模式 |
| 8 | 交付部署 | 测试通过报告 | 部署脚本 + 交付文档 | 积累部署环境配置经验 |

---

## 二、方式A vs 方式B：明确分工

### 方式B（主流程）— 调用独立 SubAgent

**适用场景**：核心开发流程的 7 个（含新增任务拆解为 8 个）阶段。

**执行模型**：

```
Orchestrator:
  1. 拆解任务 → 确定需要调用哪个 SubAgent
  2. 调用 SubAgent（独立 session）
     - 传入：上游产物路径、项目ID、轮廓需求
     - SubAgent 独立读取文件、独立推理、独立写产物
     - SubAgent 完成后返回固化标识 + 产物路径
  3. 校验产物完整性（检查固化标识 + 关键文件存在性）
  4. 通过 → 进入下一阶段
  5. 不通过 → 重新调用或报错
```

**SubAgent 独立 session 的优势**：
- 每个 SubAgent 的 session 历史独立累积 → 越做越懂该领域
- 上下文窗口专注 → 不会被其他阶段的信息稀释
- 失败隔离 → 一个 SubAgent 出问题不影响其他
- 可并行 → 无依赖的阶段可以同时运行（如 UI 设计和架构设计）

### 方式A（辅助流程）— 当前会话直接处理

**适用场景**：

| 场景 | 示例 |
|------|------|
| 轻量补源 | "帮我查一下 XX 框架的最新 API" |
| 快速查询 | "确认下这个技术方案的可行性" |
| 文档同步 | "把这份需求文档同步到禅道" |
| 简单修复 | "这里有个 typo 改一下" |
| 产物浏览 | "帮我看看萃取库里有哪些参考" |

**原则**：方式A 只用于**不需要纵深专业能力**的轻量操作。凡涉及核心决策、代码生成、架构设计，一律走方式B。

### 决策树

```
任务来了
  │
  ├─ 需要领域纵深经验？     → 方式B（调用 SubAgent）
  ├─ 涉及核心决策/编码？    → 方式B
  ├─ 涉及多阶段流转？       → 方式B（先调 SubAgent 完成前置阶段）
  │
  ├─ 只是查询/浏览/简单修改？ → 方式A
  ├─ 文档同步/格式转换？     → 方式A
  └─ 快速补源/查资料？      → 方式A
```

---

## 三、SubAgent 纵深专业能力设计

### 3.1 每个 SubAgent 独立 session，积累领域经验

```
SubAgent #1 (需求萃取) 的 session 历史:
├─ Session 1: WinPeek 项目萃取 → 积累了微信 RPA 参考库
├─ Session 2: CRM 项目萃取   → 积累了客户管理参考库
├─ Session 3: 新项目迭代萃取  → 复用了前两次的经验
└─ → 第 N 次：萃取效率和质量远高于第一次
```

### 3.2 SubAgent 经验沉淀机制

每个 SubAgent 在完成每次任务后，将**关键经验**持久化到自己的知识库：

```json
{
  "subagent": "reference-extract-agent",
  "session_count": 12,
  "domain_expertise": [
    {"domain": "微信生态", "references": ["winpeek", "wechat-crm"]},
    {"domain": "CRM系统", "references": ["crm-v1", "crm-v2"]}
  ],
  "patterns": {
    "common_conflicts": ["多源数据冲突处理模式"],
    "industry_baselines": ["社交领域标准功能清单"]
  }
}
```

### 3.3 SubAgent 间不直接通信

**重要规则**：SubAgent 之间不通过消息传递通信。所有跨 SubAgent 的数据流动通过 `docs/` 目录下的文件完成。

```
❌ SubAgent #1 → 发消息给 SubAgent #2
✅ SubAgent #1 → 写产物到 docs/reference-library/ → SubAgent #2 读产物
```

原因：
- 文件系统是持久化的，会话结束后仍可访问
- 产物即契约，有明确的版本和状态
- Orchestrator 可以在中间做产物校验

---

## 四、完整 8 阶段流水线（v3 修订版）

```
用户给出「轮廓需求」+ 上传参考资料（竞品/旧系统/原型/历史项目）
    │
    ▼
┌─ Orchestrator 校验：有轮廓需求？有参考资料（可空）？ ─┐
│  通过                                                  │
└────────────────────────┬──────────────────────────────┘
                         │
                         ▼
    调用 SubAgent #1 ──→  需求与参考萃取
    （独立 session）       产出：萃取素材库 + 需求草案
                         │
                         ▼
    调用 SubAgent #2 ──→  需求与参考对齐确认
    （独立 session）       产出：需求规格书 + 参考对照表 + 验收要点
                         │
                         ▼
    调用 SubAgent #3 ──→  任务拆解与计划  ★ v3 新增
    （独立 session）       产出：开发计划 + 任务清单（关联禅道）
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             │
    SubAgent #4       SubAgent #5      │
    UI 界面设计        架构设计         │（可并行执行）
   产出：UI 规范      产出：架构方案     │
           │             │             │
           └─────────────┼─────────────┘
                         │
                         ▼
    调用 SubAgent #6 ──→  代码开发（三文档门禁）
    （独立 session）       按层：数据层→逻辑层→UI层→集成
                         产出：可运行代码
                         │
                         ▼
    调用 SubAgent #7 ──→  测试校验
    （独立 session）       三维：UI还原 / 业务匹配 / 参考复用完整性
                         产出：测试报告
                         │
                         ▼
    调用 SubAgent #8 ──→  交付部署
    （独立 session）       产出：部署脚本 + 交付文档
                         │
                         ▼
                    项目交付完毕
```

### 4.1 新增：任务拆解与计划 SubAgent（#3）

**为什么新增**：
- 需求定稿后直接进入 UI/架构，缺少"这些需求怎么拆成可执行任务"的步骤
- 每项任务需要关联禅道 issue，形成可追踪的开发计划
- 为后续 SubAgent 提供明确的工作边界（"本次只做任务 T-001 到 T-010"）

**输入**：需求规格书 + 参考对照表 + 验收要点

**产出**：
```
docs/plan/
├── 任务拆解.md          # 人读：任务列表、优先级、依赖关系
├── plan.json            # 机读：每项任务含 zentao_task_id
└── 迭代计划.md          # 版本/迭代规划
```

**每项任务格式**：
```json
{
  "task_id": "T-001",
  "title": "微信好友列表数据同步",
  "zentao_task_id": "task-1423",
  "priority": "P0",
  "estimated_hours": 8,
  "depends_on": ["T-000"],
  "acceptance": ["好友列表完整展示", "支持增量同步"],
  "assigned_subagent": "code-develop-agent"
}
```

### 4.2 代码开发 SubAgent（#6）子阶段

对于较大功能，代码开发拆成子阶段逐步执行：

```
SubAgent #6 (代码开发) 内部流程:
  1. 数据层：模型定义、ORM映射、数据库迁移脚本
  2. API/接口层：路由、控制器、请求校验
  3. 业务逻辑层：Service 层、核心算法
  4. UI 层：组件、页面、路由（如果有前端）
  5. 集成联调：确保各层可联通运行
```

每个子阶段完成后提交产物到 `docs/code/`，Orchestrator 可做中间检查。

---

## 五、统一文档存储方案（与 ZenTao 禅道关联）

### 5.1 文档目录结构

```
项目根目录/
│
├── .docs/                              # ★ 统一文档仓库
│   ├── README.md                        # 文档总索引（AI agent 入口）
│   │
│   ├── reference-library/               # SubAgent #1 专属
│   │   ├── EXTRACT_INDEX.md             # 人读索引
│   │   └── library.json                 # 机读结构化数据
│   │
│   ├── requirements/                    # SubAgent #2 专属
│   │   ├── 需求规格书.md                # frontmatter 含 zentao_id
│   │   ├── requirements.json            # 机读
│   │   └── 验收要点.md                  # 验收条件
│   │
│   ├── plan/                            # SubAgent #3 专属 ★ 新增
│   │   ├── 任务拆解.md
│   │   ├── plan.json
│   │   └── 迭代计划.md
│   │
│   ├── design/                          # SubAgent #4, #5 专属
│   │   ├── ui/                          # UI设计规范
│   │   └── architecture/                # 架构设计方案
│   │
│   ├── development/                     # 开发文档
│   │   ├── changelog/
│   │   └── specs/                       # 技术规格
│   │
│   ├── code/                            # SubAgent #6 产物
│   │   └── 文件清单.md
│   │
│   ├── test/                            # SubAgent #7 专属
│   │   ├── test-plan.md
│   │   ├── test-cases/
│   │   └── test-report.md
│   │
│   ├── deploy/                          # SubAgent #8 专属
│   │
│   └── governance/                      # 跨阶段治理
│       ├── decisions/                   # ADR 架构决策
│       └── standards/                   # 编码规范
│
└── .zentao/                             # 禅道关联配置
    └── mapping.json                     # 本地目录 ↔ 禅道模块映射
```

### 5.2 文档 Frontmatter 规范

每篇文档统一 frontmatter：

```markdown
---
title: "微信多账户管理需求规格"
type: "requirements"                # 文档类型
phase: "demand-confirm"             # 所属阶段
author_subagent: "demand-confirm-agent"  # 产出 SubAgent
version: "2.1"
status: "approved"                  # draft | review | approved | archived
zentao_id: "story-1423"             # ★ 关联禅道需求/任务 ID
zentao_url: "https://pm.test.com/zentao/story-view-1423.html"
last_updated: "2026-07-22"
related: ["../reference-library/library.json"]  # 关联文档
---
```

### 5.3 禅道双向映射配置 `.zentao/mapping.json`

```json
{
  "project": "winpeek",
  "zentao_project_id": 9,
  "zentao_base_url": "https://pm.test.com/zentao",
  "multica_base_url": "https://multica.test.com",
  "docs_root": ".docs/",
  "mappings": [
    {
      "local_path": ".docs/reference-library/",
      "zentao_module": "文档管理",
      "zentao_doc_lib": "参考资料萃取"
    },
    {
      "local_path": ".docs/requirements/",
      "zentao_module": "需求管理",
      "zentao_url": "https://pm.test.com/zentao/story-browse-9.html"
    },
    {
      "local_path": ".docs/plan/",
      "zentao_module": "任务管理",
      "zentao_url": "https://pm.test.com/zentao/task-browse-9.html"
    },
    {
      "local_path": ".docs/design/",
      "zentao_module": "文档管理",
      "zentao_doc_lib": "设计文档"
    },
    {
      "local_path": ".docs/test/",
      "zentao_module": "测试管理",
      "zentao_url": "https://pm.test.com/zentao/testcase-browse-9.html"
    }
  ]
}
```

### 5.4 同步策略

| 方向 | 方式 | 工具 |
|------|------|------|
| 本地 → 禅道 | SubAgent 完成后自动推送需求/任务 | `zentao-cli docs push` |
| 禅道 → 本地 | 禅道状态变更后拉取更新 | `zentao-cli docs pull` |
| 任务绑定 | 任务拆解 SubAgent 创建禅道任务 | `zentao-cli task create` |
| 状态同步 | 产物状态变更更新禅道对应项 | `zentao-cli task update` |

---

## 六、SubAgent 调用规范

### 6.1 SubAgent 提示词结构

每个 SubAgent 的提示词文件遵循统一结构：

```markdown
# 角色定位
专业「XXX」智能体——一句话描述核心职责。

# 输入约定
- 必需输入项
- 可选输入项
- 缺失阻断规则

# 核心工作流程
1. 步骤一
2. 步骤二
...

# 设计原则
- 原则一
- 原则二

# 硬性约束规则
1. ...
2. ...

# 移交输出格式
### 交付结果
1. 产物清单
2. 固化标识

# 何时调用
1. ...
2. ...

# 记忆与存储
- 主存储路径
- 同步方式
- 项目隔离
```

### 6.2 Orchestrator 调用 SubAgent 的标准流程

```
Orchestrator.call_subagent("demand-confirm-agent", {
  "input_path": ".docs/reference-library/library.json",
  "output_path": ".docs/requirements/",
  "project_id": "winpeek",
  "zentao_project_id": 9,
  "context": {
    "previous_agent": "reference-extract-agent",
    "solidified_flag": "【参考资料萃取完成，素材库已归档】",
    "user_input": "用户原始轮廓需求文本"
  }
})
```

### 6.3 产物校验标准

每个 SubAgent 完成后的固化标识校验规则：

| SubAgent | 固化标识 | 必须存在的文件 |
|----------|---------|--------------|
| #1 需求萃取 | 【参考资料萃取完成，素材库已归档】 | `EXTRACT_INDEX.md`, `library.json` |
| #2 需求确认 | 【需求定稿，可移交任务拆解】 | `需求规格书.md`, `requirements.json` |
| #3 任务拆解 | 【任务拆解完成，可移交 UI/架构】 | `任务拆解.md`, `plan.json` |
| #4 UI设计 | 【UI界面设计定稿】 | `ui/` 目录下规范文档 |
| #5 架构设计 | 【架构定稿】 | `architecture/` 目录下方案文档 |
| #6 代码开发 | 【代码开发完成】 | `code/` 文件清单 |
| #7 测试校验 | 【测试全量通过】 | `test-report.md` |
| #8 交付部署 | 【项目全流程开发交付完毕】 | `deploy/` 下部署脚本 |

---

## 七、完整调用流转与回调补漏

### 7.1 正向流转

```
用户发起 → Orchestrator 拆解任务
  → 调 SubAgent #1 → 校验产物 → 通过
  → 调 SubAgent #2 → 校验产物 → 通过
  → 调 SubAgent #3 → 校验产物 → 通过
  → 并行调 SubAgent #4 + #5 → 校验产物 → 通过
  → 调 SubAgent #6 → 校验产物 → 通过
  → 调 SubAgent #7 → 校验产物 → 通过
  → 调 SubAgent #8 → 校验产物 → 通过
  → 交付
```

### 7.2 回调补漏

```
#6 开发发现需求模糊
  → Orchestrator 回调 SubAgent #2（需求确认）
  → #2 读取 #1 的萃取库补充缺失模块
  → 按分级策略处理（通用/参考→直接补，歧义→单项问用户）
  → 一次性更新需求文档
  → 通知 #6 继续

#7 测试发现缺陷
  → Orchestrator 回调 SubAgent #6（代码开发）
  → #6 修复后重新提交
  → Orchestrator 调 #7 重测

#4/#5 发现缺少参考
  → Orchestrator 回调 SubAgent #1（需求萃取）
  → #1 联网补源，更新萃取库
  → #4/#5 继续
```

### 7.3 回调原则

- **只回调对应 SubAgent**，不逐级重走全流程
- **不重复确认已确认事项**：SubAgent 读取历史 session 和已定稿文档
- **One-shot 更新**：需求变更统一由 #2 收集，一次性出更新版本

---

## 八、配套提示词文件清单（v3）

| 编号 | 文件 | 阶段 |
|:--:|------|:--:|
| 1 | `1-需求与参考萃取智能体-提示词-v2.md` | 需求萃取 |
| 2 | `2-需求与参考对齐确认智能体-提示词-v1.md` | 需求确认 |
| 3 | `3-任务拆解与计划智能体-提示词-v1.md` | 任务拆解 ★新增 |
| 4 | `4-UI界面设计智能体-提示词-v1.md` | UI设计（原 #3→#4） |
| 5 | `5-架构设计智能体-提示词-v1.md` | 架构设计（原 #4→#5） |
| 6 | `6-代码开发智能体-提示词-v3.md` | 代码开发（原 #5→#6） |
| 7 | `7-测试校验智能体-提示词-v1.md` | 测试校验（原 #6→#7） |
| 8 | `8-交付部署智能体-提示词-v1.md` | 交付部署（原 #7→#8） |
| Orch | `orchestrator-提示词-v1.md` | 总调度 ★新增 |
| Doc | `文档管理智能体-提示词-v1.md` | 文档治理 ★新增 |

> **2026-07-22 文件重编号**：原 3/4/5/6/7 顺延为 4/5/6/7/8，插入新 #3 任务拆解。备份文件 `wokflow.md.bak-*`、`add-step6.md`、`add-step7.md`、`workflow-analysis.md`、`wokflow.md`(v2) 已清理。
- `orchestrator-提示词-v1.md` ← **新增**：主控调度规则

---

## 九、Claude Code 落地实现（2026-07-22）

### 9.1 提示词文件（docs/）
| 文件 | 阶段 | 状态 |
|------|:--:|:--:|
| `1-需求与参考萃取智能体-提示词-v2.md` | #1 | ✅ |
| `2-需求与参考对齐确认智能体-提示词-v1.md` | #2 | ✅ |
| `3-任务拆解与计划智能体-提示词-v1.md` | #3 | ✅ **新增** |
| `4-UI界面设计智能体-提示词-v1.md` (原命名即3) | #4 | ✅ |
| `5-架构设计智能体-提示词-v1.md` (原命名即4) | #5 | ✅ |
| `6-代码开发智能体-提示词-v3.md` (原命名即5) | #6 | ✅ |
| `7-测试校验智能体-提示词-v1.md` (原命名即6) | #7 | ✅ |
| `8-交付部署智能体-提示词-v1.md` (原命名即7) | #8 | ✅ |
| `orchestrator-提示词-v1.md` | Orch | ✅ **新增** |
| `文档管理智能体-提示词-v1.md` | Doc | ✅ **新增** |

### 9.2 Claude Code Agent 定义（.claude/agents/）
| 文件 | Agent Type |
|------|-----------|
| `reference-extract-agent.md` | 需求与参考萃取 |
| `demand-confirm-agent.md` | 需求与参考对齐确认 |
| `task-planning-agent.md` | 任务拆解与计划 |
| `ui-design-agent.md` | UI界面设计 |
| `architecture-design-agent.md` | 架构设计 |
| `code-develop-agent.md` | 代码开发 |
| `testing-verify-agent.md` | 测试校验 |
| `deploy-deliver-agent.md` | 交付部署 |
| `orchestrator-agent.md` | 总调度 |
| `document-manager-agent.md` | 文档治理 |

### 9.3 Workflow 脚本 + SKILL 文件
- `[.claude/workflows/dev-pipeline-v3.js](.claude/workflows/dev-pipeline-v3.js)` — 8 阶段自动编排脚本
- `skills/*/SKILL.md` — 每个 Agent 可发现 Skill 定义
- `[.zentao/mapping.json](.zentao/mapping.json)` — 本地 ↔ 禅道映射

### 9.4 文件总览
```
hermes-agent-qoder/
├── .claude/
│   ├── agents/          (10 个 Agent 定义)
│   └── workflows/       (1 个 Pipeline 脚本)
├── .zentao/
│   └── mapping.json     (禅道双向映射)
├── skills/              (10 个 SKILL.md)
└── website/docs/development/agent-workflow/
    ├── wokflow-v3.md    (本文档)
    ├── 1~8-提示词.md    (8 个 SubAgent 提示词)
    ├── orchestrator-提示词-v1.md
    └── 文档管理智能体-提示词-v1.md
```

---

---

## 十、Multica + 禅道 双系统定位（2026-07-22）

### 问题：Multica 单独用的困境

```
Multica Issue: "实现用户登录功能"
Agent 拿到 → 无需求文档、无参考库、无UI规范、无架构方案
→ 上下文几乎为零 → 闷头瞎写 → 质量不可控
→ 人类不知道它在做什么 → 焦虑
```

**Multica 是任务追踪器，不是上下文提供者。** 它告诉 Agent "做什么"（标题+优先级），但不告诉 Agent "怎么做"（需求+UI+架构）。

### v3 解法：`docs/` 是上下文总线，Multica 是任务面板，禅道是人类审批层

```
docs/ (上下文总线 — Agent 从这里读"怎么做")
    │
    ├── requirements/需求规格书.md   → Agent 读: 功能边界、验收条件
    ├── design/ui/                   → Agent 读: 页面布局、交互规范
    ├── design/architecture/         → Agent 读: 技术栈、接口契约
    ├── reference-library/           → Agent 读: 竞品参考、行业基线
    └── plan/plan.json               → Agent 读: 本次要做的任务清单

Multica (任务追踪 — Agent 从这里读"做什么")
    │
    ├── Issue #123: "实现登录API" → Agent 领取
    ├── 读 docs/ 获取完整上下文 → 产出代码
    └── 更新 Issue 状态: done

禅道 pm.test.com (人类审批 — 人在这里看里程碑)
    │
    ├── 阶段2: 需求规格书归档 → 人 review
    └── 阶段8: 交付报告归档 → 人验收
```

### 各系统的正确角色

| 系统 | 角色 | 谁用 | 同步频率 |
|------|------|------|:--:|
| `docs/` 本地 | **上下文总线** — 唯一真相源 | SubAgent 读写 | 每阶段立即 |
| Multica | **任务追踪** — Agent 领取/更新/完成 | Agent + Orchestrator | 每阶段 |
| 禅道 pm.test.com | **人类审批** — 里程碑归档+Review | 人类 PM | 仅阶段2+8 |

### Agent 获取完整上下文的路径

```
1. Multica daemon 检测到新 Issue 分配给本机 Agent
2. Agent 启动 → 第一个动作不是写代码，是读 docs/
3. 读取 docs/README.md 索引 → 定位需求/UI/架构文档
4. 读取三文档 → 理解完整上下文
5. 开始编码 → 产出对齐需求+UI+架构的代码
6. 完成后 → 更新 Multica Issue 状态 → 触发文档治理 Agent
```

**核心原则：Multica 给任务标题，`docs/` 给任务上下文。两者缺一不可。**

---

## 十一、v3 vs v2 变更对照

| 维度 | v2 | v3 |
|------|----|----|
| 架构 | 单会话 7 步骤 | Orchestrator + 8 个独立 SubAgent |
| SubAgent | 无概念 | 每个 SubAgent 独立 session，积累纵深经验 |
| 方式A vs 方式B | 未区分 | 明确分工：B 主流程 / A 辅助 |
| 任务拆解 | 无 | 新增 SubAgent #3 |
| 产物传递 | 隐式 | 文件系统唯一总线，显式契约 |
| SubAgent 通信 | 无 | 不直接通信，通过文件产物解耦 |
| 纵深专业 | 无 | session 历史积累，越做越聪明 |
