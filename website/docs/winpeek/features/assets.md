---
sidebar_position: 3
title: "Computer Assets"
description: "Computer asset management — installed software scanner, disk usage, hardware info, file browser"
---

# Computer Assets

Automatic discovery and monitoring of installed software, disk usage, hardware specs, and running processes. Replaces the legacy PeekabooWin asset panel.

## Quick Start

```bash
# Scan installed software
python plugins/winpeek_rpa/shared/software_scanner.py

# Or through Hermes Agent
> Scan my installed software
> Show disk usage
> What's my CPU model?
```

## Features

### Software Inventory (P0)

Scans Windows registry (HKLM + HKCU), Start Menu shortcuts, and portable app directories. Auto-categorizes into IM / Browser / Dev / Office / Media / Tools using 60+ category rules. Displays name, version, publisher, install path, and process name.

### Disk Management (P0)

Shows all drives with label, total/used/free capacity, and usage percentage as progress bars. V2.0 adds large file scanner and temp file cleanup suggestions.

### Hardware Info (P1)

CPU model, core count, real-time usage percentage. Total/used/available memory. V2.0 adds GPU info and network interfaces.

### File Browser (P1)

Directory tree navigation, file search by name/suffix/size, top N largest files.

### Process Manager (P2)

Running process list with name, PID, memory, CPU. Search/filter. Right-click to terminate.

## Architecture

```
software_scanner.py → Hermes Tools → Desktop UI
    ├── Registry scan (winreg)
    ├── Start Menu scan
    └── Portable dirs scan
         ↓
    JSON → winpeek_scan_software → AssetsView
```

## Hermes Tools

| Tool | Function | Phase |
|------|----------|-------|
| `winpeek_scan_software` | Scan installed software | V1.0 |
| `winpeek_get_disk_info` | Disk partitions + capacity | V1.0 |
| `winpeek_get_hardware_info` | CPU + memory info | V1.0 |
| `winpeek_list_files` | List directory contents | V2.0 |
| `winpeek_list_processes` | List running processes | V2.0 |

## Related

- [Quickstart](../quickstart.md)
- [Source: plugins/winpeek_rpa/shared/software_scanner.py](../../../plugins/winpeek_rpa/shared/software_scanner.py)
