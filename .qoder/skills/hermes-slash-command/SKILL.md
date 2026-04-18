---
name: hermes-slash-command
description: >
  Guide through adding new slash commands to Hermes Agent following the central
  registry pattern. Use when creating CLI commands, gateway commands, or extending
  the command system. Trigger keywords: slash command, add command, new command.
---

# Hermes Slash Command Creator

## Command Addition Process

### Step 1: Add CommandDef to hermes_cli/commands.py

Add entry to `COMMAND_REGISTRY` list:

```python
from hermes_cli.commands import CommandDef

COMMAND_REGISTRY = [
    # ... existing commands
    CommandDef(
        name="mycommand",              # Canonical name without slash
        description="What it does",    # Human-readable description
        category="Session",            # One of: Session, Configuration, Tools & Skills, Info, Exit
        aliases=("mc",),               # Optional: alternative names
        args_hint="[arg]",             # Optional: argument placeholder
        cli_only=False,                # Optional: CLI-only
        gateway_only=False,            # Optional: Gateway-only
        gateway_config_gate=None,      # Optional: config dotpath for gateway gating
    ),
]
```

### Step 2: Add handler in cli.py

In `HermesCLI.process_command()`:

```python
elif canonical == "mycommand":
    self._handle_mycommand(cmd_original)
```

Then implement the handler:

```python
def _handle_mycommand(self, original: str):
    """Handle /mycommand"""
    # Parse arguments
    # Execute logic
    # Display output
    pass
```

### Step 3: Gateway handler (if applicable)

In `gateway/run.py`:

```python
if canonical == "mycommand":
    return await self._handle_mycommand(event)
```

## CommandDef Fields

| Field | Required | Description |
|-------|----------|-------------|
| name | Yes | Canonical name (e.g., "background") |
| description | Yes | Human-readable description |
| category | Yes | Session/Configuration/Tools & Skills/Info/Exit |
| aliases | No | Tuple of alternative names |
| args_hint | No | Argument placeholder shown in help |
| cli_only | No | Only available in CLI |
| gateway_only | No | Only available in messaging platforms |
| gateway_config_gate | No | Config dotpath for conditional gateway availability |

## Adding Aliases

To add an alias, ONLY modify the `aliases` tuple on existing CommandDef:

```python
# Before
aliases=(),

# After
aliases=("bg", "b"),
```

All consumers update automatically:
- CLI dispatch
- Gateway dispatch
- Help text
- Telegram menu
- Slack mapping
- Autocomplete

## Category Guidelines

- **Session**: Session management (/clear, /resume, /export)
- **Configuration**: Settings (/model, /skin, /profile)
- **Tools & Skills**: Tool/skill management (/skills, /tools)
- **Info**: Information (/help, /status, /doctor)
- **Exit**: Exit commands (/quit, /exit)

## Testing Commands

```bash
# Test in CLI
hermes chat
/mycommand

# Test completion
# Type /my<TAB> in CLI
```
