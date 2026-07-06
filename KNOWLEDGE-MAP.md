# feat/winpeek 知识库地图

> **基座**: Hermes upstream (`main`) — 不改  
> **我们的代码**: `feat/winpeek` — 全在这 46 个文件里  
> **验证命令**: `git diff main..feat/winpeek --name-only`

---

## 一、前端 View（5 文件 + 2 处修改）

```
apps/desktop/src/app/
├── winpeek/                          ← 🆕 我们的一级目录
│   ├── index.tsx                     # 统一导出 (AutomationView + MimView + AssetsView)
│   ├── automation/index.tsx          # 桌面自动化面板 → 6 平台子页签
│   ├── mim/index.tsx                 # MIM 多平台即时通讯 → 5 平台状态卡片
│   ├── assets/index.tsx              # 电脑资产 → 软件分类 + 磁盘信息
│   └── wechat/index.tsx              # 微信控制面板 → 步进器 + 日志 + 快捷操作
│
├── routes.ts                         # ⚡ 修改: +14 行 (AUTOMATION_ROUTE, WECHAT_ROUTE)
└── desktop-controller.tsx            # ⚡ 修改: +11 行 (lazy import + overlay 渲染)
```

---

## 二、Hub 后端（5 文件）

```
gateway/winpeek_hub/
├── __init__.py       # 模块导出
├── tenant.py         # 多租户管理 (平台UID → tenant → 成员列表)
├── routing.py        # 跨平台路由 (微信张三 → 钉钉李四)
├── archive.py        # 消息归档 (MySQL/JSONL/off 三引擎)
└── hub_bridge.py     # 零侵入集成桥 (WINPEEK_HUB_ENABLED=1 启用)
```

---

## 三、Python 自动化引擎（18 文件）

```
plugins/winpeek_rpa/
├── plugin.yaml                       # Hermes 插件声明
├── __init__.py
├── mcp_server.py                     # MCP 工具接口 (4 个工具)
│
├── platforms/
│   ├── wechat/                       # 微信 (← PeekabooWin 迁移)
│   │   ├── uia.py          731 行    # UIA 底层操作
│   │   ├── db.py           663 行    # 数据库 (SQLite/MySQL)
│   │   ├── api.py          637 行    # 三层架构 (Eyes/Hands/Engine/Brain)
│   │   ├── collect.py      319 行    # 全量采集入口
│   │   ├── contacts.py     311 行    # 通讯录采集
│   │   ├── collect_contacts.py 296行 # 联系人采集逻辑
│   │   ├── msg_traverse.py 220 行    # 会话遍历 (活塞式)
│   │   ├── profile.py      219 行    # 资料采集
│   │   ├── analyze.py      190 行    # AI 分析引擎
│   │   ├── msg_collect.py  134 行    # 单会话消息采集
│   │   └── find.py         137 行    # 查找功能
│   └── douyin/                       # 🚧 预留
│
├── shared/                           # 跨平台共享
│   ├── rpa_tools.py                  # RPA 工具函数
│   ├── bg_input.py                   # 后台输入 (BGInput)
│   ├── config.py                     # 配置管理
│   ├── position_memory.py            # 位置记忆
│   ├── pixel_anchors.json            # 像素锚点 (97 个)
│   ├── nav_map.json                  # 导航映射 (268 行)
│   ├── software_scanner.py           # Windows 软件资产扫描器
│   └── hub_schema.sql                # Hub 数据库建表 SQL
│
└── skills/                           # 🚧 预留 SKILL.md 目录
```

---

## 四、Skills 知识库（4 文件）

```
skills/
├── trace-to-template/SKILL.md         # 操作历史 → MCP 模板 (含迭代测试+自愈)
├── wechat-automation-rules/SKILL.md   # 微信操作守则 (ESC陷阱/功能区/搜索分类)
├── software-self-learning/SKILL.md    # 全流程自学习 (5 阶段)
└── software-assets/wechat.md          # 微信软件资产卡 (进程/路径/窗口/UIA控件)
```

---

## 五、工具注册（1 文件）

```
tools/winpeek_tools.py    # 注册 4 个工具到 Hermes 工具系统
                          # winpeek_wechat_send / collect_msgs / collect_contacts / list_templates
```

---

## 六、层级关系图

```
┌── apps/desktop/winpeek/  ← 用户看到的面板
│       │ WebSocket JSON-RPC
├── tools/winpeek_tools.py ← 注册到 Hermes 工具系统
│       │ Python import
├── plugins/winpeek_rpa/   ← 自动化引擎 (UIA + DB)
│       │
├── gateway/winpeek_hub/   ← SaaS 后端 (租户 + 路由 + 归档)
│       │
└── skills/                 ← AI 知识库 (SKILL.md × 4)
```
