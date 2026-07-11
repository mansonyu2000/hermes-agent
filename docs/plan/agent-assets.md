# 电脑资产管理 — 开发计划

> **负责人**: 待分配
>
> 代码范围: `apps/desktop/.../winpeek/assets/` + `plugins/winpeek_rpa/shared/software_scanner.py`
>
> PRD: [docs/requirements/assets-prd.md](../requirements/assets-prd.md)

---

## 代码范围现状

| 层 | 文件 | 当前 | 目标 |
|----|------|------|------|
| 前端 | `assets/index.tsx` | 150行, 5 Tab, 11 mock软件 + 2假磁盘 | 5 Tab 全真实数据 |
| 后端 | `software_scanner.py` | 381行, 注册表+StartMenu+60品类规则 | 注册为 Hermes 工具 |
| 工具 | `tools/winpeek_tools.py` | 无资产工具 | +5 资产工具 |

---

## 版本计划

| 版本 | 内容 | 交付物 |
|------|------|--------|
| **V1.0** | 软件扫描+展示 + 磁盘信息 + CPU/内存 | 可用资产面板 (真实数据) |
| **V2.0** | 文件管理 + 进程管理 + GPU/网络 + 大文件扫描 | 完整运维面板 |

---

## V1.0 任务

### 后端工具

| # | 任务 | 依赖 |
|---|------|------|
| D1 | 注册 `winpeek_scan_software` 工具 | - |
| D2 | 注册 `winpeek_get_disk_info` 工具 | - |
| D3 | 注册 `winpeek_get_hardware_info` 工具 | - |

### 前端

| # | 任务 | 依赖 |
|---|------|------|
| D4 | 软件列表 Tab 对接真实扫描数据 (替换 mock) | D1 |
| D5 | 磁盘管理 Tab (真实 psutil 数据 + 进度条) | D2 |
| D6 | 硬件信息 Tab (CPU 型号/核心数/内存) | D3 |
| D7 | "重新扫描"按钮对接后端 | D1 |
| D8 | 文件管理/进程管理 Tab 占位 | - |

---

## V2.0 任务

| # | 任务 | 延期原因 |
|---|------|---------|
| D9 | 文件目录浏览 + 搜索 | V1.0 先做完软件/磁盘/硬件 |
| D10 | 进程列表 + 结束进程 | V1.0 先把基础展示做完 |
| D11 | GPU/网卡信息 | 需要额外 Python 包 (GPUtil) |
| D12 | 大文件扫描 + 清理建议 | 磁盘管理增强 |
| D13 | 两台机器软件对比 | 需要网络通信基础设施 |

---

## Hermes 工具清单

| 工具名 | 功能 | 版本 |
|-------|------|------|
| `winpeek_scan_software` | 扫描本机已安装软件 | V1.0 |
| `winpeek_get_disk_info` | 磁盘分区 + 容量 | V1.0 |
| `winpeek_get_hardware_info` | CPU/内存信息 | V1.0 |
| `winpeek_list_files` | 列出目录文件 | V2.0 |
| `winpeek_list_processes` | 列出运行进程 | V2.0 |

---

## 与其他 Agent 边界

- 与微信 CRM **无关** — 独立模块，零依赖
- 与 MIM **无关** — 独立模块，零依赖
- software_scanner.py 已有 381 行代码，接手即可用
