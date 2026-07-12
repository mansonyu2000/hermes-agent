---
sidebar_position: 3
title: "Computer Assets"
description: "Computer management — software scanner, disk usage, file browser, hardware info, process manager"
---

# Computer Assets

Windows computer management dashboard. Five independent sub-modules, each with its own backend scanner and frontend tab.

## Sub-Modules

| Module | Backend | Tool | Description |
|--------|---------|------|-------------|
| **Software** | `software_scanner.py` (381 lines ✅) | `winpeek_scan_software` 🆕 | Scan registry + Start Menu + portable dirs, 60+ category rules |
| **Disk** | `disk_scanner.py` 🆕 | `winpeek_get_disk_info` 🆕 | All drives with label, total/used/free, usage % as progress bars |
| **Files** | `file_browser.py` 🆕 | `winpeek_list_files` 🆕 | Directory tree navigation, file search by name/suffix/size, top N largest |
| **Hardware** | `hardware_info.py` 🆕 | `winpeek_get_hardware` 🆕 | CPU model/cores/usage, total/used/available memory |
| **Processes** | `process_manager.py` 🆕 | `winpeek_list_processes` 🆕 | Running process list (name/PID/memory/CPU), search/filter, terminate |

## Quick Start

```bash
# Scan installed software
python plugins/winpeek_rpa/shared/software_scanner.py

# Or through Hermes Agent
> Scan my installed software
> Show disk usage
> What's my CPU model?
> List running processes
```

## Frontend

`apps/desktop/src/app/winpeek/assets/index.tsx` — one panel with 5+ sub-tabs. Each tab connects to its backend tool via `useGatewayRequest()`.

## Related

- [Architecture](../developer-guide/architecture.md)
- [Source: plugins/winpeek_rpa/shared/](../../../plugins/winpeek_rpa/shared/)
