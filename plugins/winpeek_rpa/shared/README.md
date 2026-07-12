# Assets — Computer Management

Computer management dashboard. Five independent sub-modules, each with its own backend scanner and frontend tab.

## Sub-Modules

| Module | Features | Status |
|--------|----------|--------|
| **Software** | Scan registry + Start Menu + portable dirs, 60+ category rules | scanner ready, tool pending |
| **Disk** | All drives with label, total/used/free, usage % progress bars | pending |
| **Files** | Directory tree navigation, search by name/suffix/size, top N largest | pending |
| **Hardware** | CPU model/cores/usage, total/used/available memory | pending |
| **Processes** | Running process list (name/PID/memory/CPU), search/filter | pending |

## Code Layout

```
Assets
├── plugins/winpeek_rpa/shared/
│   ├── README.md              ← This file
│   ├── software_scanner.py    (381 lines) Registry + Start Menu
│   ├── disk_scanner.py         pending
│   ├── hardware_info.py        pending
│   ├── file_browser.py         pending
│   └── process_manager.py      pending
│
├── tools/winpeek_tools.py
│   ├── winpeek_scan_software   pending
│   ├── winpeek_get_disk_info   pending
│   ├── winpeek_get_hardware    pending
│   ├── winpeek_list_files      pending
│   └── winpeek_list_processes  pending
│
├── apps/desktop/.../winpeek/assets/index.tsx  (150 lines, mock data)
└── website/docs/user-guide/features/assets.md  User guide
```

## How to Start

1. Implement backend scanners in `plugins/winpeek_rpa/shared/`
2. Register 5 tools in `tools/winpeek_tools.py`
3. Replace mock tabs in `apps/desktop/.../winpeek/assets/index.tsx`
4. Run: `python scripts/winpeek-quality-check.py`
