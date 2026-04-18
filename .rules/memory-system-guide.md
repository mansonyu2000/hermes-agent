# Hermes Agent 记忆系统快速参考

> 本文档总结 Hermes Agent 记忆系统的核心机制和使用方法。
> 适用于开发人员和 AI 助手快速查阅。
> **本文档已索引到项目知识库。**
> 最后更新: 2026-04-18

---

## 📚 文档导航

### 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **项目知识库** | [../HERMES_AGENT_KNOWLEDGE_BASE.md](../HERMES_AGENT_KNOWLEDGE_BASE.md) | 知识库主入口（第十二章：记忆系统详解） |
| **开发指南** | [../AGENTS.md](../AGENTS.md) | AI助手开发指南 |
| **完整开发规矩** | [./development-rules.md](./development-rules.md) | 第十三章：记忆系统规则 |
| **测试模板** | [./test-templates.md](./test-templates.md) | 测试模板和案例 |
| **Skills/Commands** | [../.qoder/README.md](../.qoder/README.md) | Skills和Commands索引 |

---

## 🧠 记忆系统概览

Hermes Agent 的记忆系统是其**核心优势**，实现了：
- ✅ **自动整理** - AI 自动提取和归纳知识
- ✅ **持久化存储** - SQLite + 文件双重保障
- ✅ **跨会话记忆** - 新会话自动加载历史记忆
- ✅ **多策略检索** - 语义搜索 + 实体图谱 + 关键词匹配
- ✅ **推理综合** - 不仅检索，还能推理和总结

---

## 📊 三层记忆架构

### 1. 会话级记忆（SQLite）

**作用：** 保存当前会话的所有消息和状态

**实现：** `hermes_state.py` 的 `SessionDB` 类

**特性：**
- WAL 模式支持并发
- FTS5 全文搜索
- 随机退避策略

**存储位置：**
```
~/.hermes/sessions.db                    # 默认 Profile
~/.hermes/profiles/<name>/sessions.db    # 自定义 Profile
```

**使用示例：**
```python
from hermes_state import SessionDB

db = SessionDB()

# 保存消息
db.save_message(session_id, "user", "你好")
db.save_message(session_id, "assistant", "你好！有什么可以帮助你的？")

# 搜索消息
results = db.search_messages("搜索关键词")

# 获取会话历史
history = db.get_session_history(session_id)
```

---

### 2. 用户级记忆（文件）

**作用：** 保存跨会话的用户偏好和重要信息

**文件位置：**
```
~/.hermes/MEMORY.md          # 用户级记忆（所有会话共享）
~/.hermes/USER.md            # 用户偏好和配置
```

**内容示例：**
```markdown
# 用户记忆

## 偏好
- 喜欢使用深色主题
- 偏好 Python 开发
- 使用 VS Code 编辑器

## 项目决策
- 2026-04-15: 决定使用 SQLite 作为会话存储
- 2026-04-16: 选择 Hindsight 作为记忆插件

## 重要知识点
- Profile 隔离必须使用 get_hermes_home()
- 工具 Handler 必须返回 JSON 字符串
```

---

### 3. 插件级记忆（Hindsight）

**作用：** 真正的跨会话学习和知识积累

**实现：** `plugins/memory/hindsight/__init__.py`

**核心机制：** 三阶段学习循环

```
retain(存储) → recall(检索) → reflect(推理综合)
```

---

## 🔄 Hindsight 三阶段学习

### 阶段 1: Retain（存储）

**工具：** `hindsight_retain`

**触发方式：**
- **自动**：每 N 轮对话自动存储（默认每 1 轮）
- **手动**：AI 调用工具存储重要信息

**使用示例：**
```python
# 自动触发（配置）
auto_retain = true
retain_every_n_turns = 1

# 手动调用
hindsight_retain(
    content="用户偏好使用深色主题，不喜欢亮色界面",
    context="user preference"
)

# 带标签存储
hindsight_retain(
    content="项目决定使用 SQLite 作为会话存储",
    context="project decision",
    tags=["architecture", "database"]
)
```

**后台处理：**
```python
# 整个会话内容作为 JSON 数组存储
content = '[{"role": "user", "content": "..."}, ...]'

# 自动提取结构化事实
# 解析实体（用户、项目、技术等）
# 建立知识图谱索引
```

---

### 阶段 2: Recall（检索）

**工具：** `hindsight_recall`

**触发方式：**
- **自动**：每次对话前自动检索相关记忆（Prefetch）
- **手动**：AI 调用工具搜索特定信息

**使用示例：**
```python
# 自动 Prefetch（后台线程）
hindsight.queue_prefetch("用户喜欢什么主题？")
# 返回记忆自动注入到上下文

# 手动调用
result = hindsight_recall(
    query="用户的历史偏好和项目决策"
)

# 返回格式
{
  "result": "1. 用户偏好使用深色主题\n2. 项目决定使用 SQLite..."
}
```

**检索策略（多策略融合）：**
1. **语义搜索** - 向量相似度匹配
2. **关键词匹配** - 精确关键词搜索
3. **实体图谱遍历** - 通过实体关系查找
4. **重排序** - 按相关性排序结果

**过滤选项：**
```python
# 按标签过滤
recall_tags = ["architecture"]
recall_tags_match = "any"  # any/all/any_strict/all_strict

# 按类型过滤
recall_types = ["preference", "decision"]

# 结果限制
recall_max_tokens = 4096
```

---

### 阶段 3: Reflect（推理综合）

**工具：** `hindsight_reflect`

**触发方式：** 手动（需要深度推理时）

**与 Recall 的区别：**
- **Recall**：检索原始记忆
- **Reflect**：跨记忆推理，生成综合回答

**使用示例：**
```python
# 需要推理的问题
result = hindsight_reflect(
    query="根据历史对话，总结用户的开发偏好和技术栈"
)

# 返回综合后的回答
{
  "text": "根据多次对话记录，用户有以下偏好：\n"
          "1. 编程语言：偏好 Python\n"
          "2. 编辑器：使用 VS Code\n"
          "3. 主题：喜欢深色主题\n"
          "4. 数据库：倾向使用 SQLite..."
}
```

**推理过程：**
```python
# 1. 检索所有相关记忆
memories = recall_all_related(query)

# 2. 使用 LLM 进行推理综合
answer = llm.synthesize(
    query=query,
    memories=memories,
    instructions="基于这些记忆，给出综合性的回答"
)

# 3. 返回推理结果
return answer
```

---

## ⚙️ 配置指南

### Hindsight 配置文件

**位置：** `~/.hermes/hindsight/config.json`

**完整配置：**
```json
{
  "mode": "cloud",
  "apiKey": "your-hindsight-api-key",
  "api_url": "https://api.hindsight.ai",
  "bank_id": "hermes",
  "budget": "mid",
  
  "memory_mode": "hybrid",
  "prefetch_method": "recall",
  
  "auto_retain": true,
  "retain_async": true,
  "retain_every_n_turns": 1,
  "retain_context": "conversation between Hermes Agent and the User",
  "tags": ["hermes-agent"],
  
  "auto_recall": true,
  "recall_max_tokens": 4096,
  "recall_max_input_chars": 800,
  "recall_tags": [],
  "recall_tags_match": "any",
  "recall_prompt_preamble": "",
  
  "llm_provider": "openai",
  "llm_model": "gpt-4o-mini",
  "llm_base_url": ""
}
```

### 环境变量

```bash
# Hindsight API Key
HINDSIGHT_API_KEY=your-api-key

# 本地 LLM API Key（可选）
HINDSIGHT_LLM_API_KEY=your-llm-api-key
```

### 记忆模式选择

| 模式 | 适用场景 | 工具暴露 | 自动注入 |
|------|---------|---------|---------|
| **hybrid** | 默认推荐 | ✅ | ✅ |
| **context** | 仅需自动记忆 | ❌ | ✅ |
| **tools** | 完全手动控制 | ✅ | ❌ |

---

## 🎯 实际工作流示例

### 场景 1: 跨会话用户偏好记忆

**会话 1：**
```
用户: 我喜欢使用深色主题，亮色界面太刺眼了
AI:  [自动调用 hindsight_retain]
     → 存储: "用户偏好使用深色主题，不喜欢亮色界面"
     → 上下文: "user preference"
```

**会话 2（新会话）：**
```
用户: 推荐一个适合我的主题

AI:  [自动 Prefetch]
     → hindsight_recall("推荐主题")
     → 找到记忆: "用户偏好使用深色主题"
     → 自动注入到上下文

AI:  根据您的偏好，我推荐使用深色主题...
```

---

### 场景 2: 项目决策持久化

**会话 1：**
```
用户: 我们决定使用 SQLite 作为会话存储方案
AI:  [自动调用 hindsight_retain]
     → 存储: "项目决定使用 SQLite 作为会话存储方案"
     → 上下文: "project decision"
     → 标签: ["architecture", "database"]
```

**会话 2（一周后）：**
```
用户: 我们之前为什么选择 SQLite？

AI:  [调用 hindsight_reflect]
     → 检索所有相关决策记忆
     → 推理综合选择原因
     → 返回: "选择 SQLite 的原因包括..."
```

---

### 场景 3: 技术知识积累

**多次会话积累：**
```
会话 1: 学习了 Profile 隔离规则
        → retain: "Profile 隔离必须使用 get_hermes_home()"

会话 2: 学习了工具注册规范
        → retain: "工具 Handler 必须返回 JSON 字符串"

会话 3: 学习了 Prompt 缓存保护
        → retain: "对话中途不能修改上下文"

会话 N: 用户问"开发 Hermes 有什么注意事项？"
        → reflect: 综合所有技术知识
        → 返回完整的开发指南
```

---

## 🔧 调试和监控

### 查看记忆状态

```bash
# 查看 SQLite 会话数据库
sqlite3 ~/.hermes/sessions.db ".tables"
sqlite3 ~/.hermes/sessions.db "SELECT COUNT(*) FROM messages;"

# 查看用户级记忆文件
cat ~/.hermes/MEMORY.md
cat ~/.hermes/USER.md

# 查看 Hindsight 配置
cat ~/.hermes/hindsight/config.json
```

### 启用调试日志

```bash
# 启用 DEBUG 级别日志
export HERMES_LOG_LEVEL=DEBUG

# 启动 Hermes
hermes chat

# 查看日志
tail -f ~/.hermes/hermes.log | grep -i hindsight
```

### 监控记忆操作

```python
# 日志输出示例
# Hindsight initialized: mode=cloud, bank=hermes, memory_mode=hybrid
# Tool hindsight_retain: bank=hermes, content_len=245, context=user preference
# Tool hindsight_retain: success
# Tool hindsight_recall: bank=hermes, query_len=20, 5 results
# Prefetch: returning 1024 chars of context
```

---

## 📈 最佳实践

### 1. 自动记忆配置

```json
{
  "auto_retain": true,           // 开启自动存储
  "retain_every_n_turns": 1,     // 每轮都存储
  "retain_async": true,          // 异步处理（不阻塞对话）
  "auto_recall": true,           // 开启自动检索
  "recall_max_tokens": 4096      // 限制返回大小
}
```

### 2. 标签管理

```json
{
  "tags": ["hermes-agent", "production"],  // 存储时自动添加
  "recall_tags": ["architecture"],         // 检索时过滤
  "recall_tags_match": "any"               // 匹配模式
}
```

### 3. 本地 LLM（隐私优先）

```json
{
  "llm_provider": "ollama",
  "llm_model": "qwen/qwen3.5-9b",
  "llm_base_url": "http://localhost:11434/v1"
}
```

### 4. Profile 隔离

```bash
# 每个 Profile 独立的记忆系统
~/.hermes/profiles/coder/hindsight/config.json
~/.hermes/profiles/coder/MEMORY.md
~/.hermes/profiles/coder/sessions.db
```

---

## 🚨 常见问题

### Q: 记忆没有自动注入？

**检查：**
```bash
# 1. 确认 memory_mode 不是 "tools"
cat ~/.hermes/hindsight/config.json | grep memory_mode

# 2. 确认 auto_recall 开启
cat ~/.hermes/hindsight/config.json | grep auto_recall

# 3. 查看日志
tail -f ~/.hermes/hermes.log | grep -i prefetch
```

### Q: 跨会话记忆不生效？

**检查：**
```bash
# 1. 确认 Hindsight 配置正确
cat ~/.hermes/hindsight/config.json

# 2. 确认 API Key 有效
echo $HINDSIGHT_API_KEY

# 3. 测试 retain
hermes chat
# 说一些内容，然后检查日志
tail -f ~/.hermes/hermes.log | grep hindsight_retain
```

### Q: 记忆检索结果不相关？

**优化：**
```json
{
  "budget": "high",              // 提高检索预算
  "recall_max_tokens": 8192,     // 增加返回大小
  "recall_tags": ["relevant"]    // 使用标签过滤
}
```

---

## 📚 相关文档

- **完整知识库**: `HERMES_AGENT_KNOWLEDGE_BASE.md` (第十二章)
- **开发规矩**: `.rules/development-rules.md`
- **Hindsight README**: `plugins/memory/hindsight/README.md`
- **测试用例**: `tests/plugins/memory/test_hindsight_provider.py`

---

**维护者**: Hermes Agent 开发团队  
**最后更新**: 2026-04-18
