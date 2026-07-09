# WinPeek RPA Plugin

Desktop automation engine for WeChat, Douyin, and other platforms.
Provides UIA-based automation tools via Hermes tool system + MCP protocol.

## Architecture

```
__init__.py        → Hermes Plugin 入口
plugin.yaml        → 插件元数据
mcp_server.py      → MCP stdio server（模板执行 + 自学习）
shared/            → 共享工具函数
platforms/
  wechat/          → 微信自动化（~15 文件）
    uia.py         → WeChatUIA 基础控件封装
    api.py         → Eyes/Hands/Engine 三层架构
    db.py          → SQLite 数据库操作
    contacts.py    → 通讯录采集
    collect.py     → 消息采集
  douyin/          → 抖音自动化（预留）
skills/            → AI 技能模板
```

## WeChat 三层架构

- **Eyes（感知）** — 纯读不写：`get_sessions()`, `get_messages()`, `is_right_place()`
- **Hands（执行）** — 全写不读：`click_session()`, `scrollbar_sink()`, `send_message()`
- **Engine（调度）** — 组合 eyes+hands+db 执行采集策略

## 注册的工具

| 工具 | 说明 | 触发平台 |
|------|------|----------|
| `winpeek_wechat_send` | 发消息 | 微信 |
| `winpeek_wechat_collect_msgs` | 采集聊天记录 | 微信 |
| `winpeek_wechat_collect_contacts` | 采集通讯录 | 微信 |
| `winpeek_list_templates` | 列出 MCP 模板 | 通用 |

## 配置

- `DB_BACKEND`: `sqlite`（默认）或 `mysql`
- 模板目录: `~/.hermes/winpeek/templates/`
- 控件映射: `~/.hermes/winpeek/maps/`

## 降级策略

微信 UIA 直连（毫秒级）→ 失败 → MCP 模板（秒级）→ 失败 → 提示用户手动操作

## 扩展平台

新建 `plugins/winpeek_rpa/platforms/<name>/` 目录，参考 wechat/ 结构实现：
- `<name>_api.py` — Eyes/Hands/Engine 三层
- `<name>_uia.py` — UIA 基础控件封装
- `<name>_db.py` — 数据库操作
- 在 `mcp_server.py` 中注册新工具
