# 电脑资产管理 — 产品需求规格说明书 (PRD)

> **版本**: v1.0 · **日期**: 2026-07-12 · **负责人**: 待分配
> **分支**: 待定
> **适用范围**: WinPeek Assets 模块 (`apps/desktop/.../winpeek/assets/` + `plugins/winpeek_rpa/shared/software_scanner.py`)

---

## 一、产品概述

### 1.1 产品定位

电脑资产管理是 WinPeek 的系统运维模块。自动发现本机安装软件、磁盘使用、文件结构、硬件配置和运行进程，为 Agent 提供"了解这台机器"的基础能力。

### 1.2 目标用户

| 角色 | 场景 |
|------|------|
| 开发者 | 查看本机安装的开发工具、磁盘剩余空间 |
| 运维 | 监控磁盘使用率、进程健康 |
| Agent | 知道机器上有什么软件可用、文件在哪 |

### 1.3 遗产来源

PeekabooWin 原有功能，需迁移到 Hermes Desktop 架构。

---

## 二、现有代码状态

### 2.1 前端 (`apps/desktop/src/app/winpeek/assets/index.tsx`)

| 功能 | 行数 | 状态 | 问题 |
|------|------|------|------|
| 软件列表 | 150行 | ✅ 按分类 Tab 展示 | ❌ 11 个硬编码 mock，未接 scanner |
| 磁盘信息 | 10行 | ✅ 展示 2 块盘 | ❌ 假数据 C:200G/D:500G |
| 重新扫描按钮 | 1行 | ✅ 有 UI | ❌ onClick 是空函数 |
| 文件管理 | 0行 | ❌ 无 | 未规划 |
| 硬件信息 | 0行 | ❌ 无 | 未规划 |
| 进程管理 | 0行 | ❌ 无 | 未规划 |

### 2.2 后端 (`plugins/winpeek_rpa/shared/software_scanner.py`)

| 功能 | 行数 | 状态 | 问题 |
|------|------|------|------|
| 注册表扫描 (HKLM+HKCU) | 381行 | ✅ 已有 | Windows only |
| Start Menu 快捷方式扫描 | ✅ | ✅ 已有 | |
| 便携软件目录扫描 | ✅ | ✅ 已有 | |
| 60+ 品类分类规则 | ✅ | ✅ CATEGORY_RULES | |
| JSON 输出 | ✅ | ✅ | ❌ 未注册为 Hermes 工具 |

---

## 三、功能需求

### 模块 A：软件资产

| # | 需求 | 优先级 | 数据来源 | 验收标准 |
|---|------|--------|---------|---------|
| A1 | 扫描本机已安装软件 | P0 | 注册表 + Start Menu + 便携目录 | 扫描完成返回软件列表 |
| A2 | 软件分类展示（Tab 切换） | P0 | `CATEGORY_RULES` 自动归类 | IM/视频/开发/办公/工具等 Tab 正确分组 |
| A3 | 软件详情（版本/发布商/安装路径/进程名） | P0 | 扫描 JSON | 点击软件展开详情 |
| A4 | 注册 winpeek_scan_software 工具 | P0 | software_scanner.py | Hermes Agent 可直接调用 |
| A5 | 软件对比（两台机器差异） | P2 | 两台机器的扫描 JSON 对比 | 显示 A有B无 / B有A无 / 版本差异 |
| A6 | 软件搜索 | P1 | 前端过滤 | 输入关键词实时过滤 |
| A7 | "重新扫描"按钮对接后端 | P0 | 按钮→调工具→更新列表 | 点击后刷新软件列表 |

### 模块 B：磁盘管理

| # | 需求 | 优先级 | 数据来源 | 验收标准 |
|---|------|--------|---------|---------|
| B1 | 磁盘分区列表（盘符/卷标/总容量/已用/剩余/占比） | P0 | `psutil.disk_partitions()` + `shutil.disk_usage()` | 进度条 + 数字 |
| B2 | 磁盘空间不足告警（<10%） | P1 | 同上 | 红色告警 |
| B3 | 注册 winpeek_get_disk_info 工具 | P0 | Python psutil | Hermes Agent 可调用 |
| B4 | 大文件扫描（>100MB 的文件列表） | P2 | `os.walk` + 文件大小 | 按大小排序 |
| B5 | 临时文件/缓存清理建议 | P2 | 扫描 Temp/AppData 目录 | 显示可释放空间 |

### 模块 C：文件管理

| # | 需求 | 优先级 | 数据来源 | 验收标准 |
|---|------|--------|---------|---------|
| C1 | 目录浏览（树形结构） | P1 | `os.listdir` | 点击展开/折叠 |
| C2 | 文件搜索（按名称/后缀/大小） | P1 | 递归搜索 | 搜索框输入 → 结果列表 |
| C3 | 文件大小排序（Top N 大文件） | P1 | 同上 | 降序排列 |
| C4 | 注册 winpeek_list_files 工具 | P1 | Python os/pathlib | Agent 可查文件结构 |
| C5 | 文件操作（复制路径/打开所在文件夹） | P1 | 系统调用 | 右键菜单可用 |

### 模块 D：硬件信息

| # | 需求 | 优先级 | 数据来源 | 验收标准 |
|---|------|--------|---------|---------|
| D1 | CPU 型号/核心数/使用率 | P1 | `psutil.cpu_info()` + `psutil.cpu_percent()` | 显示 CPU 名称 + 实时使用率 |
| D2 | 内存总量/已用/可用 | P1 | `psutil.virtual_memory()` | 进度条 + GB 数字 |
| D3 | 显卡信息 | P2 | `GPUtil` 或 `dxdiag` | GPU 型号 + 显存 |
| D4 | 网卡/IP/MAC | P2 | `psutil.net_if_addrs()` | 列表展示 |
| D5 | 注册 winpeek_get_hardware_info 工具 | P1 | Python psutil | Agent 可查询 |

### 模块 E：进程管理

| # | 需求 | 优先级 | 数据来源 | 验收标准 |
|---|------|--------|---------|---------|
| E1 | 运行中进程列表（名称/PID/内存/CPU） | P2 | `psutil.process_iter()` | 表格展示，支持排序 |
| E2 | 进程搜索/过滤 | P2 | 前端过滤 | 输入进程名实时过滤 |
| E3 | 注册 winpeek_list_processes 工具 | P2 | Python psutil | Agent 可查询 |
| E4 | 结束进程（需确认） | P3 | `process.kill()` | 右键 → 确认 → 结束 |

---

## 四、Hermes 工具注册清单

| 工具名 | 功能 | 优先级 |
|-------|------|--------|
| `winpeek_scan_software` | 扫描本机已安装软件，返回 JSON | P0 |
| `winpeek_get_disk_info` | 获取磁盘分区 + 容量信息 | P0 |
| `winpeek_get_hardware_info` | 获取 CPU/内存/显卡/网卡信息 | P1 |
| `winpeek_list_files` | 列出指定目录的文件/子目录 | P1 |
| `winpeek_list_processes` | 列出运行中的进程 | P2 |

所有工具注册到 `tools/winpeek_tools.py`，与微信工具同级。

---

## 五、前端组件树

```
AssetsView
├── Header (标题 + 重新扫描 + 关闭)
├── MainTabBar
│   ├── 软件资产     → SoftwarePanel
│   ├── 磁盘管理     → DiskPanel
│   ├── 文件管理     → FilePanel
│   ├── 硬件信息     → HardwarePanel
│   └── 进程管理     → ProcessPanel
│
├── SoftwarePanel
│   ├── SearchBar (搜索)
│   ├── CategoryTabs (IM/视频/开发/办公/工具...)
│   └── SoftwareList
│       └── SoftwareCard[] (名称/版本/发布商/路径)
│
├── DiskPanel
│   ├── DiskBar[] (盘符/卷标/进度条/数字)
│   └── LargeFileList (大文件 Top N)
│
├── FilePanel
│   ├── PathBreadcrumb (路径导航)
│   ├── FileTree (树形目录)
│   └── FileList (表格: 名称/大小/修改时间)
│
├── HardwarePanel
│   ├── CPUCard (型号/核心数/使用率)
│   ├── MemoryCard (总量/已用/可用)
│   ├── GpuCard (型号/显存)          ← P2
│   └── NetworkCard[] (网卡/IP/MAC)  ← P2
│
└── ProcessPanel
    ├── SearchBar
    └── ProcessTable (名称/PID/内存/CPU) + 右键菜单
```

---

## 六、数据流

```
用户点击"重新扫描"
    │
    ▼
前端 → Hermes IPC → winpeek_scan_software 工具
    │
    ▼
software_scanner.py
    ├── 注册表扫描 (winreg)
    ├── Start Menu 扫描
    └── 便携目录扫描
    │
    ▼
返回 JSON → 前端更新 SoftwarePanel
```

---

## 七、版本计划

### V1.0 — 可用资产面板

| 模块 | 任务 |
|------|------|
| A 软件资产 | A1-A4, A7 (扫描+展示+工具注册) |
| B 磁盘管理 | B1, B3 (磁盘列表+工具注册) |
| D 硬件信息 | D1-D2, D5 (CPU+内存+工具注册) |

**交付物**：软件列表用真实扫描数据替换 mock，磁盘/硬件基本信息可查。

### V2.0 — 文件 + 进程

| 模块 | 任务 |
|------|------|
| A 软件资产 | A5-A6 (对比+搜索) |
| B 磁盘管理 | B2, B4-B5 (告警+大文件+清理) |
| C 文件管理 | C1-C5 (全部) |
| D 硬件信息 | D3-D4 (GPU+网络) |
| E 进程管理 | E1-E4 (全部) |

---

## 八、与 CC-yu2 / Hermes-htubs24 的边界

| 模块 | 归属 | 说明 |
|------|------|------|
| software_scanner.py 维护 | Assets Agent | 已有代码，接手即可 |
| 前端 AssetsView 改造 | Assets Agent | 替换 mock，接真实工具 |
| tools/winpeek_tools.py 新增工具 | Assets Agent | 5 个新工具注册 |
| 与微信 CRM 无关 | - | 独立模块，零依赖 |
| 与 MIM 无关 | - | 独立模块，零依赖 |

---

## 九、验收场景

| # | 操作 | 预期结果 |
|---|------|---------|
| 1 | 打开电脑资产页 | 显示软件列表（真实扫描数据，非 mock） |
| 2 | 切换软件分类 Tab | 过滤正确 |
| 3 | 点击"重新扫描" | 刷新软件列表 |
| 4 | 查看磁盘 Tab | 显示各盘容量+进度条 |
| 5 | 查看硬件 Tab | 显示 CPU 型号/内存总量 |
| 6 | Hermes 对话中说"扫描本机软件" | Agent 调用 winpeek_scan_software 返回结果 |

---

参见：[架构总览](../../website/docs/winpeek/ARCHITECTURE.md) · [后端扫描器](../../../plugins/winpeek_rpa/shared/software_scanner.py) · [开发总体规划](../plan/DEVELOPMENT-PLAN.md)
