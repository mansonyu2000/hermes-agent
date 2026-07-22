---
name: hermes-workflow
description: Hermes Agent enterprise workflow — MIM messaging, ZenTao PM sync, Document Manager. Use when working with Hermes-specific infrastructure.
---

# Hermes Workflow

## Overview
Hermes-specific workflow extensions that integrate agent-skills pipeline with Hermes enterprise infrastructure: MIM Agent messaging, ZenTao PM task management, Document Manager dual-system sync, and Supervisor Agent monitoring.

## When to Use
- Working in hermes-agent project
- Tasks involve ZenTao (pm.test.com) updates
- Collaborating via MIM Agent-to-Agent messaging
- Dual-system sync between ZenTao and Multica
- 24/7 Supervisor Agent monitoring is active

## Hermes Infrastructure

### 1. ZenTao CLI
```bash
# Available commands:
zentao login                          # Login to pm.test.com
zentao story create                   # Create requirement
zentao task create                    # Create task (needs ZENTAO_DB_* env vars)
zentao task list --execution <id>     # List tasks
zentao bug list                       # List bugs
zentao product list                   # List products
zentao project list                   # List projects
zentao execution list                 # List executions/sprints

# DB env vars for task operations:
# ZENTAO_DB_HOST=192.168.3.23
# ZENTAO_DB_PORT=3306
# ZENTAO_DB_USER=root
# ZENTAO_DB_PASS=Server123
# ZENTAO_DB_NAME=zentao
```

### 2. MIM Agent Messaging
```
Available MIM tools:
- winpeek_mim_send       → Send message to another agent (to_uid, body)
- winpeek_mim_poll       → Check for new messages
- winpeek_mim_contacts   → List registered agents
- winpeek_mim_history    → Get conversation history
- winpeek_mim_user_info  → Look up agent profile
- winpeek_mim_local_agents → List local daemon-discovered agents
```

MIM is the communication layer between agents. Use it to:
- Notify collaborators when pipeline stages complete
- Request input from other agents
- Share review results and artifacts

### 3. Peeka Router (Message Classification)
```
Incoming messages are automatically classified:
- greeting → daemon auto-replies (0 Token)
- request → forwarded to target agent
- advertisement → filtered out
```

The PeekaName system provides relation-aware addressing:
- Same machine → share file paths directly
- Same org → use project jargon without explanation

## Pipeline Integration

When running the agent-skills pipeline (`pipeline:spec → plan → build → review → ship`),
integrate Hermes infrastructure at each stage:

### pipeline:spec → ZenTao
- Create/update ZenTao story (requirement) with spec content
- Link to zenTao project 6 (winpeek)

### pipeline:plan → ZenTao
- Create ZenTao tasks under execution 9 (开发)
- Link tasks to the story

### pipeline:build → MIM
- Notify collaborators on task completion
- Use `winpeek_mim_send` to share progress

### pipeline:review → MIM + ZenTao
- Send review report via MIM to relevant agents
- Update ZenTao task status

### pipeline:ship → ZenTao
- Update ZenTao release status
- Document release notes

## Pipeline Commands (summary)

| Command | agent-skills skill | Hermes integration |
|---------|-------------------|-------------------|
| `pipeline:spec` | spec-driven-development | Update ZenTao story |
| `pipeline:plan` | planning-and-task-breakdown | Create ZenTao tasks |
| `pipeline:build` | incremental-implementation + TDD | MIM progress notify |
| `pipeline:test` | test-driven-development | — |
| `pipeline:review` | code-review-and-quality | MIM + ZenTao update |
| `pipeline:code-simplify` | code-simplification | — |
| `pipeline:ship` | shipping-and-launch | ZenTao release |

## Files & Locations

| Resource | Path |
|----------|------|
| Pipeline rules | `.trae/rules/pipeline-*.md` |
| Session start | `.trae/rules/session-start.md` |
| Agent skills | `.agents/skills/` (24 skills) |
| Peeka router | `gateway/winpeek_hub/peeka_router.py` |
| MIM chat | `gateway/winpeek_hub/chat.py` |
| daemon | `apps/winpeek_injector/daemon.py` |
| Identity | `gateway/winpeek_hub/identity.py` (includes peeka_name) |
| Feature inventory | `website/docs/winpeek/mim-design/feature-inventory.md` |
| Peeka design | `website/docs/winpeek/mim-design/peeka-design.md` |

## Verification

After any pipeline stage:
- [ ] ZenTao updated if applicable
- [ ] MIM notified collaborators if applicable
- [ ] Artifacts committed to version control
- [ ] Tests pass
- [ ] Build succeeds
