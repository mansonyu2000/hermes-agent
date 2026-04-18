# Hermes Agent 文档体系总览

> 本文档展示项目所有文档的关系和导航路径。
> 最后更新: 2026-04-18

---

## 📊 文档架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    项目根目录                                │
│                                                             │
│  ┌─────────────────────┐      ┌──────────────────────┐     │
│  │   AGENTS.md         │◄────►│  HERMES_AGENT_       │     │
│  │   (开发指南-英文)   │      │  KNOWLEDGE_BASE.md   │     │
│  │                     │      │  (知识库-中文)       │     │
│  │  ★ AI助手首要阅读   │      │  ★ 人类首要阅读      │     │
│  └─────────┬───────────┘      └──────────┬───────────┘     │
│            │                              │                 │
│            │ 双向链接                     │ 双向链接         │
│            ▼                              ▼                 │
│  ┌─────────────────────────────────────────────────┐       │
│  │          文档导航索引（两个文件都有）            │       │
│  │                                                 │       │
│  │  核心文档  │  开发规矩  │  Skills/Commands      │       │
│  └─────────────────────────┬───────────────────────┘       │
│                            │                               │
│            ┌───────────────┼───────────────┐               │
│            │               │               │               │
│            ▼               ▼               ▼               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │  .rules/     │ │  .rules/     │ │  .rules/     │      │
│  │development-  │ │memory-system-│ │test-         │      │
│  │rules.md      │ │guide.md      │ │templates.md  │      │
│  │              │ │              │ │              │      │
│  │13章完整规矩  │ │记忆系统指南  │ │测试模板案例  │      │
│  │1800+行       │ │500+行        │ │580+行        │      │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘      │
│         │                │                │               │
│         └────────────────┼────────────────┘               │
│                          │                                │
│                          ▼                                │
│              ┌───────────────────────┐                   │
│              │    .qoder/README.md   │                   │
│              │                       │                   │
│              │  Skills/Commands索引  │                   │
│              │  8 Skills + 6 Cmds    │                   │
│              └──────────┬────────────┘                   │
│                         │                                 │
│            ┌────────────┼────────────┐                   │
│            ▼            ▼            ▼                   │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│     │ skills/  │ │ skills/  │ │commands/ │             │
│     │ 8个SKILL │ │ 8个SKILL │ │ 6个CMD   │             │
│     │ .md文件  │ │ .md文件  │ │ .md文件  │             │
│     └──────────┘ └──────────┘ └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 文档清单

### 核心文档（2个）

| 文件 | 路径 | 语言 | 用途 | 目标读者 |
|------|------|------|------|---------|
| **开发指南** | `AGENTS.md` | 英文 | AI助手和开发者的开发指南 | AI助手、开发者 |
| **知识库** | `HERMES_AGENT_KNOWLEDGE_BASE.md` | 中文 | 项目知识库主入口 | 人类、AI助手 |

**关系：** 两个文件都有文档导航索引，互相链接。

---

### 开发规矩（3个）

| 文件 | 路径 | 行数 | 说明 |
|------|------|------|------|
| **完整开发规矩** | `.rules/development-rules.md` | 1800+ | 13章完整规范 |
| **记忆系统指南** | `.rules/memory-system-guide.md` | 500+ | Hindsight完整指南 |
| **测试模板** | `.rules/test-templates.md` | 580+ | 测试模板和案例 |

**关系：** 
- 都链接回知识库主入口
- 互相链接（规矩↔记忆↔测试）
- 链接到 Skills/Commands

---

### Qoder Skills & Commands（1个索引 + 14个实现）

| 类型 | 数量 | 位置 | 说明 |
|------|------|------|------|
| **索引文档** | 1 | `.qoder/README.md` | Skills/Commands使用说明 |
| **Skills** | 8 | `.qoder/skills/*/SKILL.md` | 自动触发的专业技能 |
| **Commands** | 6 | `.qoder/commands/*.md` | 手动触发的命令 |

**关系：**
- 索引文档链接回所有相关文档
- 每个 Skill/Command 都链接到相关规矩文档

---

## 🔄 导航流程

### 从知识库出发

```
HERMES_AGENT_KNOWLEDGE_BASE.md (主入口)
  ├── 核心文档
  │   ├── AGENTS.md (开发指南)
  │   └── README.md (项目介绍)
  │
  ├── 开发规矩和指南
  │   ├── .rules/development-rules.md (完整规矩)
  │   ├── .rules/memory-system-guide.md (记忆系统)
  │   └── .rules/test-templates.md (测试模板)
  │
  └── Qoder Skills 和 Commands
      ├── .qoder/README.md (索引)
      ├── .qoder/skills/ (8个Skills)
      └── .qoder/commands/ (6个Commands)
```

### 从 AGENTS.md 出发

```
AGENTS.md (开发指南)
  ├── Documentation Index
  │   ├── HERMES_AGENT_KNOWLEDGE_BASE.md (知识库)
  │   ├── .rules/development-rules.md (规矩)
  │   ├── .rules/memory-system-guide.md (记忆)
  │   ├── .rules/test-templates.md (测试)
  │   └── .qoder/README.md (Skills/Commands)
  │
  └── 具体开发指南内容...
```

### 从任意规矩文档出发

```
.rules/*.md (任意规矩文档)
  ├── 文档导航
  │   ├── 返回知识库主入口
  │   ├── 链接到其他规矩文档
  │   └── 链接到相关 Skills
  │
  └── 文档具体内容...
```

---

## 🎯 使用场景

### 场景 1: 人类开发者首次接触项目

```
1. 阅读 README.md (项目介绍)
   ↓
2. 阅读 HERMES_AGENT_KNOWLEDGE_BASE.md (知识库主入口)
   ↓
3. 根据需要选择:
   ├── 学习开发规矩 → .rules/development-rules.md
   ├── 学习记忆系统 → .rules/memory-system-guide.md
   ├── 学习测试编写 → .rules/test-templates.md
   └── 使用 Qoder AI → .qoder/README.md
```

### 场景 2: AI 助手（Qoder）开始工作

```
1. 阅读 AGENTS.md (开发指南 - 首要)
   ↓
2. 从 Documentation Index 发现所有文档
   ↓
3. 根据任务需要:
   ├── 开发新功能 → development-rules.md
   ├── 编写测试 → test-templates.md + hermes-python-test-expert Skill
   ├── 调试问题 → memory-system-guide.md + hermes-debug-helper Skill
   └── 提交代码 → hermes-git-commit Skill
```

### 场景 3: 查找特定主题

```
主题: 如何编写测试？

路径 1: 从知识库
  HERMES_AGENT_KNOWLEDGE_BASE.md
    → 第十二章：记忆系统详解
    → 相关文档链接
      → .rules/test-templates.md
      → .qoder/skills/hermes-python-test-expert/SKILL.md

路径 2: 从规矩文档
  .rules/development-rules.md
    → 第五章：测试规则
    → 相关文档链接
      → .rules/test-templates.md
      → Skills/Commands

路径 3: 直接使用 Skill
  在 Qoder 中说："编写测试"
    → 自动触发 hermes-python-test-expert
```

---

## 📊 文档统计

| 类别 | 数量 | 总行数 | 语言 |
|------|------|--------|------|
| **核心文档** | 2 | ~500 | 中/英 |
| **规矩指南** | 3 | ~2900 | 中文 |
| **Skills** | 8 | ~4000 | 英文 |
| **Commands** | 6 | ~400 | 英文 |
| **索引文档** | 2 | ~200 | 中/英 |
| **总计** | 21 | ~8000 | 中/英 |

---

## 🔗 链接关系图

```
                    ┌──────────────┐
                    │  README.md   │
                    │  (项目介绍)  │
                    └──────┬───────┘
                           │
                           ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  AGENTS.md   │◄──►│  KNOWLEDGE_  │◄──►│ .qoder/      │
│  (开发指南)  │    │  BASE.md     │    │ README.md    │
│              │    │  (知识库)    │    │ (S/C索引)    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   │                   ├── skills/
       │                   │                   │   ├── hermes-test-runner
       │                   │                   │   ├── hermes-git-commit
       │                   │                   │   ├── hermes-tool-creator
       │                   │                   │   ├── hermes-slash-command
       │                   │                   │   ├── hermes-debug-helper
       │                   │                   │   ├── hermes-config-manager
       │                   │                   │   ├── hermes-python-test-expert
       │                   │                   │   └── hermes-frontend-test-expert
       │                   │                   │
       │                   │                   └── commands/
       │                   │                       ├── hermes-full-test
       │                   │                       ├── hermes-quick-review
       │                   │                       ├── hermes-prepare-release
       │                   │                       ├── hermes-env-setup
       │                   │                       ├── hermes-run-all-tests
       │                   │                       └── hermes-write-test
       │                   │
       ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ .rules/      │◄──►│ .rules/      │◄──►│ .rules/      │
│ development- │    │ memory-system│    │ test-        │
│ rules.md     │    │ guide.md     │    │ templates.md │
└──────────────┘    └──────────────┘    └──────────────┘
     │                    │                    │
     └────────────────────┼────────────────────┘
                          │
                          ▼
                   所有文档互相链接
                   形成完整导航网络
```

---

## ✅ 文档完整性检查清单

- [x] 所有文档都有清晰的标题和说明
- [x] 所有文档都有"文档导航"部分
- [x] 核心文档（AGENTS.md + KNOWLEDGE_BASE.md）互相链接
- [x] 规矩文档链接回知识库主入口
- [x] 规矩文档互相链接
- [x] Skills/Commands 索引链接回知识库
- [x] 每个 Skill 链接到相关规矩文档
- [x] 没有孤立文档（所有文档都可从入口到达）
- [x] 双向链接（A→B 且 B→A）

---

## 🚀 快速访问命令

```bash
# 从知识库开始
cat HERMES_AGENT_KNOWLEDGE_BASE.md

# 查看开发规矩
cat .rules/development-rules.md

# 查看记忆系统
cat .rules/memory-system-guide.md

# 查看测试模板
cat .rules/test-templates.md

# 查看 Skills/Commands
cat .qoder/README.md

# 查看特定 Skill
cat .qoder/skills/hermes-python-test-expert/SKILL.md

# 查看特定 Command
cat .qoder/commands/hermes-run-all-tests.md
```

---

## 📝 维护规则

1. **新增文档时：**
   - 在知识库的"文档导航"中添加链接
   - 在 AGENTS.md 的"Documentation Index"中添加链接
   - 在新文档中添加"文档导航"部分
   - 在相关文档中添加反向链接

2. **修改文档时：**
   - 检查链接是否仍然有效
   - 更新"最后更新"日期
   - 如有重大变更，更新相关文档的导航

3. **删除文档时：**
   - 从所有索引中移除链接
   - 检查是否有其他文档链接到它
   - 更新相关导航

---

**维护者**: Hermes Agent 开发团队  
**最后更新**: 2026-04-18
