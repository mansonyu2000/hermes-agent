# AgentMemory 完整接入指南

中央记忆服务器: `192.168.3.9` | v0.9.27 | RTX 4090 | 纯本地部署

- REST API: `http://192.168.3.9:3111`
- Viewer: `http://192.168.3.9:3113`
- Auth Token: `agentmemory-wuhai-2026`
- LLM: `qwen2.5:latest` (7B, 4.4GB) — 记忆压缩/总结/反思
- Embedding: `bge-m3:latest` (1024-dim, 1.1GB) — 中英双语语义搜索
- Ollama API: `http://192.168.3.9:11434/v1` — 局域网直接可用

---

## 一、客户端接入

### 1.1 一键接入（推荐）

```bash
AGENTMEMORY_URL=http://192.168.3.9:3111 \
AGENTMEMORY_SECRET=agentmemory-wuhai-2026 \
agentmemory connect claude-code --with-hooks
```

重启 Claude Code 或运行 `/mcp` 即生效。这会自动写入 `~/.claude.json`（MCP）和 `~/.claude/settings.json`（Hooks）。

### 1.2 全局手动配置

编辑 `~/.claude.json`，在 `mcpServers` 中添加:

```json
{
  "mcpServers": {
    "agentmemory": {
      "command": "npx",
      "args": ["-y", "@agentmemory/mcp"],
      "env": {
        "AGENTMEMORY_URL": "http://192.168.3.9:3111",
        "AGENTMEMORY_SECRET": "agentmemory-wuhai-2026",
        "AGENTMEMORY_TOOLS": "all"
      }
    }
  }
}
```

### 1.3 项目级配置（团队自动加载）

在项目根目录创建 `.claude/mcp.json`，内容同上。`git commit` 后，团队成员 `git pull` 自动加载，无需每人手动配置。

### 1.4 验证

```bash
curl -s -H "Authorization: Bearer agentmemory-wuhai-2026" \
  http://192.168.3.9:3111/agentmemory/health
# 返回 healthy 即正常
```

---

## 二、多项目使用模式

### 模式 A: 全局记忆（默认，无额外配置）

所有项目共享同一份记忆空间。项目 A 学到的经验，切换项目 B 依然可召回。适合个人开发者。

### 模式 B: Slot 隔离

为每个项目设置不同的 `AGENTMEMORY_SLOTS`（逻辑分区），同一 slot 内共享，不同 slot 完全隔离:

```json
// 项目 A — .claude/mcp.json
{
  "mcpServers": {
    "agentmemory": {
      "command": "npx",
      "args": ["-y", "@agentmemory/mcp"],
      "env": {
        "AGENTMEMORY_URL": "http://192.168.3.9:3111",
        "AGENTMEMORY_SECRET": "agentmemory-wuhai-2026",
        "AGENTMEMORY_SLOTS": "ecommerce-admin",
        "AGENTMEMORY_TOOLS": "all"
      }
    }
  }
}

// 项目 B — .claude/mcp.json
// env.AGENTMEMORY_SLOTS = "mobile-api"
```

### 模式 C: 混合模式

全局记忆存通用经验（调试技巧、Linux 命令、Git 操作），项目 slot 存专属知识（架构决策、API 约定、业务逻辑）。两组记忆互不干扰，Agent 可以同时搜索两者。

---

## 三、跨项目记忆策略

### 3.1 显式记住通用知识

在任何项目中遇到可复用经验，主动保存:

```
remember "Python asyncio: 高并发场景用 Semaphore 限制并发数，默认连接池 100"
remember "生产环境 nginx 配置路径: /etc/nginx/sites-available/prod"
remember "MySQL 死锁排查: SHOW ENGINE INNODB STATUS; 看 LATEST DETECTED DEADLOCK"
```

这些记忆进入当前 slot，跨项目可通过 `recall` 检索。

### 3.2 标签分类（Facet）

```
facet-tag mem_abc123 "python,async,performance,troubleshooting"
facet-query tags:python,async
facet-stats                    # 查看所有标签分布
```

### 3.3 交接模式（Handoff）

阶段工作完成后生成交接摘要:

```
handoff
```

下次在任何项目中启动 Claude Code 时，AgentMemory 自动注入上次交接的上下文。

### 3.4 跨项目语义搜索

```
# 自然语言搜索（bge-m3 向量）
smart-search "上次那个 MySQL 死锁是怎么解决的"

# 关键词搜索（BM25）
search "deadlock mysql innodb"

# 时间线查询
timeline --project ecommerce-admin --since 7d

# Cypher 图查询（记忆关系网络）
graph-query "MATCH (n) WHERE n.type='memory' RETURN n.content LIMIT 10"
```

---

## 四、Hook 机制

### 4.1 什么是 Hook

安装 `--with-hooks` 后，AgentMemory 注册以下 Hook 到 Claude Code:

| Hook | 触发时机 | 记录内容 |
|------|----------|----------|
| PreToolUse | Edit/Write/Read 文件 | 文件路径、操作类型、diff |
| SessionStart | 会话开始 | 项目路径、时间戳 |
| Stop | 会话结束 | 会话统计、压缩上下文 |

### 4.2 开销

| 指标 | 值 |
|------|-----|
| 每次 Hook 延迟 | < 1ms（局域网 HTTP POST） |
| Hook 超时 | 5 秒（超时自动跳过，不阻塞 Agent） |
| 典型日请求量 | 100-500 次 |
| 客户端资源 | 零（MCP shim 仅 11KB，纯协议转换） |
| 服务端处理 | 异步队列，不阻塞 |

### 4.3 不想要 Hook

```bash
# 只加 MCP 不加 Hook（手动模式）
AGENTMEMORY_URL=http://192.168.3.9:3111 \
AGENTMEMORY_SECRET=agentmemory-wuhai-2026 \
agentmemory connect claude-code
# 不加 --with-hooks，文件操作不会自动记录，仅 remember/recall 等手动命令可用
```

### 4.4 追加 Hook

如果之前只装了 MCP，后续想加 Hook:

```bash
agentmemory connect claude-code --with-hooks
# 只追加 Hook 配置，不覆盖已有的 MCP 配置
```

---

## 五、全部命令

### 5.1 常用（自然语言调用）

| 命令 | 示例 | 说明 |
|------|------|------|
| `remember <内容>` | `remember "nginx 配置在 /etc/nginx/sites-available/prod"` | 保存记忆 |
| `recall <关键词>` | `recall nginx 配置` | 搜索记忆（语义+关键词混合） |
| `recap` | `recap` | 查看当前会话做了什么 |
| `forget <id>` | `forget mem_abc123` | 删除指定记忆 |
| `handoff` | `handoff` | 生成交接摘要 |
| `summarize` | `summarize` | LLM 压缩当前会话 |
| `search <关键词>` | `search "TypeScript generic"` | BM25 关键词搜索 |
| `smart-search <自然语言>` | `smart-search "跨域问题怎么解决的"` | 语义向量搜索 |
| `status` | `status` | 查看记忆服务状态 |
| `facet-tag <id> <tags>` | `facet-tag mem_123 "python,deploy"` | 打标签 |
| `facet-query <条件>` | `facet-query tags:python` | 按标签检索 |
| `patterns` | `patterns` | 查找重复行为模式 |
| `graph-query <cypher>` | `graph-query "MATCH (n) RETURN n LIMIT 10"` | Cypher 图查询 |
| `timeline` | `timeline --since 7d` | 时间线 |

### 5.2 高级工具分类（共 53 个 MCP 工具）

**内存**: `remember` `forget` `search` `smart-search` `context` `summarize` `consolidate` `compress` `evolve` `heal`
**会话**: `recap` `handoff` `commit-context` `sessions` `observations` `timeline`
**图谱**: `graph-query` `graph-stats` `graph-extract` `graph-reset`
**标签**: `facet-tag` `facet-untag` `facet-query` `facet-stats` `facet-get`
**自动化**: `routines` `routine-create` `routine-run` `sentinels` `sentinel-create`
**导入导出**: `export` `import` `mesh-register` `mesh-sync`

---

## 六、语义搜索

### 6.1 架构

```
Agent 发出查询: smart-search("MySQL 死锁怎么排查")
        │
        ├──▶ bge-m3 向量化 → 1024-dim
        │         │
        │         ▼ 余弦相似度
        │    [向量索引] → top-K 相似记忆
        │
        ├──▶ BM25 关键词 → 匹配记忆
        │
        ▼
    混合排序: vector_score × 0.6 + BM25_score × 0.4
        │
        ▼
    返回最相关记忆 → 注入 Agent 上下文
```

### 6.2 模型

| 角色 | 模型 | 尺寸 | 场景 |
|------|------|------|------|
| LLM | `qwen2.5:latest` | 7B / 4.4GB | 日常压缩/总结 |
| LLM 高级 | `qwen2.5:32b` | 32B / 18.5GB | 深度反思/巩固 |
| Embedding | `bge-m3:latest` | 1.1GB / 1024-dim | 中英双语语义搜索 |
| Embedding 备选 | `nomic-embed-text` | 274MB / 768-dim | 纯英文场景 |

切换模型: 修改服务器 `/root/.agentmemory/.env` 中的 `OPENAI_MODEL` 或 `OPENAI_EMBEDDING_MODEL`，重启 agentmemory 服务。

### 6.3 安装更多模型

```bash
ollama pull nomic-embed-text     # 英文代码嵌入, 274MB
ollama pull qwen2.5:32b          # 更强 LLM, 18.5GB
ollama pull deepseek-coder-v2:16b  # 代码专用, 8.3GB
```

### 6.4 远程主机直接调用 Ollama

agentmemory 的 LLM/Embedding 调用走服务端。其他用途可直接调:

```bash
# 文本生成
curl http://192.168.3.9:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:latest","messages":[{"role":"user","content":"hello"}]}'

# 向量嵌入
curl http://192.168.3.9:11434/api/embed \
  -d '{"model":"bge-m3:latest","input":"需要检索的文本"}'
```

---

## 七、Viewer（实时回放）

浏览器打开 `http://192.168.3.9:3113`:
- 实时查看所有 Agent 的 Session 流
- 按时间线回放文件操作
- 图谱可视化
- 搜索/过滤/导出记忆

---

## 八、Team 模式（多用户）

服务器 `.env` 中启用:

```
TEAM_MODE=shared
TEAM_ID=myteam
USER_ID=alice    # 每个用户不同
```

记忆按 `TEAM_ID + USER_ID` 隔离。团队共享知识图谱，各自操作历史分开。

---

## 九、故障排查

### MCP 连接失败

```bash
# 检查服务
curl http://192.168.3.9:3111/agentmemory/health -H "Authorization: Bearer agentmemory-wuhai-2026"
# 检查端口
ss -tlnp | grep 3111
# 检查进程
ps aux | grep agentmemory
```

### LLM 不工作（noop 模式）

```bash
# 检查 Ollama
curl http://192.168.3.9:11434/api/tags
# 检查模型
curl http://192.168.3.9:11434/api/tags | grep qwen2.5
# 检查 agentmemory 配置
ssh root@192.168.3.9 'grep OPENAI /root/.agentmemory/.env'
```

### 语义搜索返回空

```bash
# 确认 bge-m3 可用
curl http://192.168.3.9:11434/api/embed -d '{"model":"bge-m3:latest","input":"test"}'
# 检查 provider
agentmemory status | grep -i embed
```

---

## 十、最佳实践

1. **开局 remember**: 新项目把关键架构决策存入记忆
2. **定期 recap**: 长会话中回顾，避免遗忘早期上下文
3. **善用 handoff**: 结束工作前交接，下次新会话无缝衔接
4. **标签分类**: 给记忆打标签，便于按主题检索
5. **项目隔离**: 多项目用不同 slot，避免记忆污染
6. **Tag 分维度**: 业务逻辑 `#business`、技术实现 `#tech`、Bug 修复 `#bugfix`
