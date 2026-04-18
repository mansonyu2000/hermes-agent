---
name: hermes-config-manager
description: >
  Manage Hermes Agent configuration including config.yaml settings, .env variables,
  and platform-specific configs. Use when modifying settings, adding environment
  variables, or troubleshooting configuration issues.
  Trigger keywords: config, configuration, settings, .env, api key.
---

# Hermes Config Manager

## Configuration Systems

### Two Separate Config Loaders

| Loader | Used By | Location |
|--------|---------|----------|
| `load_cli_config()` | CLI mode | `cli.py` |
| `load_config()` | Tools, setup | `hermes_cli/config.py` |
| Direct YAML load | Gateway | `gateway/run.py` |

### Config Files

- `~/.hermes/config.yaml` - User settings
- `~/.hermes/.env` - API keys and secrets

## Adding Configuration

### config.yaml Options

1. Add to `DEFAULT_CONFIG` in `hermes_cli/config.py`:
```python
DEFAULT_CONFIG = {
    # ... existing config
    "new_option": "default_value",
}
```

2. Bump `_config_version` (currently 5) to trigger migration:
```python
_config_version = 6  # Increment to migrate existing users
```

### .env Variables

Add to `OPTIONAL_ENV_VARS` in `hermes_cli/config.py`:
```python
OPTIONAL_ENV_VARS = {
    "NEW_API_KEY": {
        "description": "What it's for",
        "prompt": "Display name",
        "url": "https://example.com/get-key",
        "password": True,  # Mask in output
        "category": "tool",  # provider/tool/messaging/setting
    },
}
```

## Common Configuration Tasks

### Set API Keys

```bash
# Edit .env file
nano ~/.hermes/.env

# Or use setup wizard
hermes setup
```

### View Current Config

```bash
# CLI
hermes status

# Dashboard
hermes dashboard
```

### Profile-Specific Config

Each profile has isolated config:
```
~/.hermes/profiles/<name>/config.yaml
~/.hermes/profiles/<name>/.env
```

## Troubleshooting

### Config Not Loading

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('~/.hermes/config.yaml'))"

# Verify file location
ls -la ~/.hermes/config.yaml
```

### Migration Issues

If config version mismatch:
1. Backup config: `cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak`
2. Let migration run automatically
3. Verify settings preserved

### Environment Variables Not Picked Up

- Restart Hermes after .env changes
- Check HERMES_HOME points to correct profile
- Verify .env syntax (KEY=VALUE, no spaces around =)
