# WinPeek — 功能总览

WinPeek 是构建在 Hermes Agent 上的 Windows 桌面自动化与多 Agent 编排系统。由 3 个独立模块组成。

## 三模块

| 模块 | 做什么 | 后端代码 | Agent 入口 | 前端入口 |
|------|--------|---------|-----------|---------|
| **Automation** | 驱动桌面 App（微信/抖音/快手…） | `plugins/winpeek_rpa/platforms/` | `tools/winpeek_tools.py` → `winpeek_*` 工具 | `apps/desktop/.../winpeek/automation/` |
| **MIM** | 多 Agent 实时消息（MQTT） | `gateway/winpeek_hub/` | `tools/winpeek_tools.py` → `winpeek_mim_*` 工具 | `apps/desktop/.../winpeek/mim/` |
| **Assets** | 电脑资产管理（软件/磁盘/硬件/进程） | `plugins/winpeek_rpa/shared/` | `tools/winpeek_tools.py` → `winpeek_*` 工具 | `apps/desktop/.../winpeek/assets/` |

三模块平行独立，无互相依赖。

## Automation 现有平台

| 平台 | 状态 | 代码目录 |
|------|------|---------|
| 微信 WeChat | 生产中 | `plugins/winpeek_rpa/platforms/wechat/` |
| 抖音 Douyin | 预留 | `plugins/winpeek_rpa/platforms/douyin/` |
| 快手 Kuaishou | 预留 | `plugins/winpeek_rpa/platforms/kuaishou/` |
| 哔哩哔哩 | 预留 | `plugins/winpeek_rpa/platforms/bilibili/` |

每个平台提供相同的接口：UIA 驱动 + 数据采集 + 内容分析 + Hermes 工具注册。

## MIM 组件

| 组件 | 文件 | 类型 | 说明 |
|------|------|------|------|
| 身份管理 | `gateway/winpeek_hub/identity.py` | hub | 注册/登录/列表（JSONL 存储） |
| MQTT 适配 | `gateway/winpeek_hub/mqtt_adapter.py` | hub | 连接/发布/订阅（1883） |
| 消息引擎 | `gateway/winpeek_hub/chat.py` | hub | 消息 CRUD + 内存队列 |
| 消息归档 | `gateway/winpeek_hub/archive.py` | hub | MySQL/JSONL 归档 |
| MIM 发送工具 | `tools/winpeek_tools.py` → `winpeek_mim_send` | tool | Agent 调用发送消息 |
| MIM 轮询工具 | `tools/winpeek_tools.py` → `winpeek_mim_poll` | tool | Agent 调用收消息 |
| MIM 登录工具 | `tools/winpeek_tools.py` → `winpeek_mim_login` | tool | Agent 调用注册身份 |
| MIM 联系人工具 | `tools/winpeek_tools.py` → `winpeek_mim_contacts` | tool | Agent 调用查联系人 |
| MIM 前端 | `apps/desktop/.../winpeek/mim/index.tsx` | frontend | 聊天界面 |
| MIM Agent 知识 | `skills/mim-guidelines/` | skill | 操作规则 |

## Assets 子功能

| 子功能 | Python 后端 | Hermes 工具 | 前端 Tab |
|--------|-----------|------------|---------|
| 软件扫描 | `plugins/winpeek_rpa/shared/software_scanner.py` | `winpeek_scan_software` | Software |
| 磁盘分析 | `plugins/winpeek_rpa/shared/disk_scanner.py` | `winpeek_get_disk_info` | Disk |
| 文件浏览 | `plugins/winpeek_rpa/shared/file_browser.py` | `winpeek_list_files` | Files |
| 硬件信息 | `plugins/winpeek_rpa/shared/hardware_info.py` | `winpeek_get_hardware` | Hardware |
| 进程管理 | `plugins/winpeek_rpa/shared/process_manager.py` | `winpeek_list_processes` | Processes |

## 开发指南索引

| 文档 | 谁看 | 说啥 |
|------|------|------|
| `website/docs/guides/winpeek-development.md` | 想加功能的 Agent | **通用开发流程**——模块类型、代码位置、10步工作流 |
| `website/docs/developer-guide/winpeek.md` | 想了解模块关系的 Agent | **架构总览**——三模块怎么拼 |
| `website/docs/getting-started/winpeek-quickstart.md` | 刚来的 Agent | **5 分钟跑通**——发一条微信消息 |
| `plugins/winpeek_rpa/README.md` | 做 Automation 的 Agent | **微信 CRM 需求+设计** |
| `gateway/winpeek_hub/README.md` | 做 MIM 的 Agent | **MIM 需求+架构+迁移** |

## 质量门禁

每次 MR 自动跑 `scripts/winpeek-quality-check.py`——6 项检查（TypeScript / CSS token / Python ruff / frontmatter / 文件名 / 死链），不通过则无法合并。
