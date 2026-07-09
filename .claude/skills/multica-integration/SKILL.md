---
name: multica-integration
description: Interact with Multica (AI-native task management) — pull assigned tasks, update progress, post results. Use when the user mentions Multica, asks about task tracking, or needs to sync work status between Hermes and Multica.
---

# Multica Integration

## Overview

Multica is an AI-native task management platform where agents are first-class assignees. Hermes agents can pull their assigned work from Multica, execute tasks, and report results back.

**Start by announcing:** "Contacting Multica to check assigned work..."

## Architecture

```
Hermes (Claude Code)
    │
    ├─→ Multica API (HTTP REST + PAT auth)
    │     └─ Issues, tasks, comments, agents
    │
    └─→ Local tools (code, wechat, etc.)
          └─ Execute work, report results
```

## Connection Config

Default Multica instance for the WinPeek project:

```
Base URL:       http://multica.test.com
PAT:            mul_fcd7c9fc9771ce73f8a3f1dc0588a94bcc4457ae
Workspace UUID: cca8e6e7-b718-4c44-ac40-b1bf58fb1599
Workspace Slug: winpeek
Agent UUID:     11064c9b-e38e-430d-8eb3-b28193bf490d
Agent Name:     tech2CC-YU2 (WinPeek 主力开发者 — Claude Code · yu2机器)
```

All API requests use:
- Header: `Authorization: Bearer <PAT>`
- Header: `X-Workspace-Id: cca8e6e7-b718-4c44-ac40-b1bf58fb1599`

## Core Concepts

| Concept | Multica Term | How Hermes Uses It |
|---------|-------------|-------------------|
| Issue | A unit of work with title, description, status, assignee | Source of truth for what needs doing |
| Agent | An AI that can be assigned issues | Hermes (this agent) is assignee=11064c9b... |
| Task | One execution of an issue by an agent | Each time Hermes works an issue, a task is created |
| Comment | Threaded discussion on an issue | Hermes posts progress/analysis as comments |
| Status | Issue workflow state | backlog → todo → in_progress → done |

## API Reference

### Read Assignments

```bash
WS_UUID="cca8e6e7-b718-4c44-ac40-b1bf58fb1599"
AGENT_UUID="11064c9b-e38e-430d-8eb3-b28193bf490d"

# List issues assigned to this agent (todo + in_progress)
curl -s -H "Authorization: Bearer $MULTICA_PAT" \
  -H "X-Workspace-Id: $WS_UUID" \
  "http://multica.test.com/api/issues?assignee_id=$AGENT_UUID&status=todo,in_progress"

# Get agent detail
curl -s -H "Authorization: Bearer $MULTICA_PAT" \
  "http://multica.test.com/api/agents/$AGENT_UUID"

# Get single issue detail
curl -s -H "Authorization: Bearer $MULTICA_PAT" \
  -H "X-Workspace-Id: $WS_UUID" \
  "http://multica.test.com/api/issues/<issue-uuid>"

# Search issues
curl -s -H "Authorization: Bearer $MULTICA_PAT" \
  -H "X-Workspace-Id: $WS_UUID" \
  "http://multica.test.com/api/issues/search?q=<keyword>"
```

### Post Progress

```bash
WS_UUID="cca8e6e7-b718-4c44-ac40-b1bf58fb1599"

# Add a comment to an issue (reports findings / progress)
curl -s -X POST -H "Authorization: Bearer $MULTICA_PAT" \
  -H "X-Workspace-Id: $WS_UUID" \
  -H "Content-Type: application/json" \
  -d '{"content": "## Phase 1 Progress\n\n- ✅ Database schema created\n- ✅ Friend list component built\n- ⚠️ Waiting on API endpoint for portrait data"}' \
  "http://multica.test.com/api/issues/<issue-uuid>/comments"

# Update issue status (statuses: backlog, todo, in_progress, in_review, done, blocked, cancelled)
curl -s -X PATCH -H "Authorization: Bearer $MULTICA_PAT" \
  -H "X-Workspace-Id: $WS_UUID" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}' \
  "http://multica.test.com/api/issues/<issue-uuid>"
```

### Create Issues

```bash
WS_UUID="cca8e6e7-b718-4c44-ac40-b1bf58fb1599"
AGENT_UUID="11064c9b-e38e-430d-8eb3-b28193bf490d"

# Create a new issue (assignee_type MUST be provided with assignee_id)
curl -s -X POST -H "Authorization: Bearer $MULTICA_PAT" \
  -H "X-Workspace-Id: $WS_UUID" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement friend portrait radar chart",
    "description": "## 目标\n- 8-dimension radar chart\n- Real-time data from wechat_friend\n...",
    "assignee_type": "agent",
    "assignee_id": "'$AGENT_UUID'",
    "priority": "high",
    "status": "todo"
  }' \
  "http://multica.test.com/api/issues"
```

## Workflow: Hermes ↔ Multica Task Loop

### Step 1: Check In (start of session or when asked)

```bash
curl -s -H "Authorization: Bearer $MULTICA_PAT" \
  "http://multica.test.com/api/workspaces/winpeek/issues?assignee_type=agent&assignee_id=11064c9b-e38e-430d-8eb3-b28193bf490d&status=in_progress,todo" \
  | python3 -c "import sys,json; [print(f'  [{i['status']}] {i['identifier']} {i['title']}') for i in json.load(sys.stdin).get('issues',[])]"
```

### Step 2: Claim & Begin Work

When starting on an issue:
1. Change status to `in_progress`
2. Post a comment: "🤖 Hermes starting work on this. Plan: [brief approach]"
3. Create TodoWrite items in the local session

### Step 3: Work & Report

During implementation:
- Post intermediate findings as comments (especially blockers or design decisions)
- Use comment threading for discussion with human reviewers
- Reference commits / branches in comments

### Step 4: Complete

When done:
1. Post a summary comment with:
   - What was done
   - Verification results (tests passed, screenshots)
   - Files changed
2. Change issue status to `done` (or `review` if PR needed)

### Step 5: Create Next Issues

After completing work, proactively create the next logical issues:
- If this was Phase N, create Phase N+1 issues
- Link them to the current issue
- Assign to yourself or mark for human review

## Critical Usage Rules

### DO
1. **Check Multica first** when asked "what should I work on?" — don't guess
2. **Post meaningful comments** — each comment should document a decision or result
3. **Keep issues atomic** — one issue = one verifiable outcome
4. **Use consistent issue structure** (see template below)
5. **Update status in real-time** — don't batch status changes

### DON'T
1. Don't silently complete work without updating Multica
2. Don't create issues without a clear completion criterion
3. Don't assign issues to humans without their explicit request
4. Don't spam the issue feed with noise — every comment should add value

## Issue Template

When creating new issues in Multica, use this structure:

```markdown
## 目标
[一句话说明要做什么]

## 背景
[为什么需要这个功能/修复]

## 需求描述
- [ ] 需求点 1
- [ ] 需求点 2

## 验收标准
- [ ] 标准 1：具体的、可验证的条件
- [ ] 标准 2

## 技术要点
- 涉及文件：[列出关键文件路径]
- 数据库变更：[如有]
- API 变更：[如有]

## 相关文档
- [链接到设计文档]
```

## Integration with Hermes Workflow

### When using superpowers:writing-plans
The plan should reference Multica issue IDs. After writing the plan:
1. Create corresponding issues in Multica
2. Link the plan file in each issue's description

### When using superpowers:executing-plans
Each task maps to a Multica issue:
1. Start → change issue to `in_progress` + comment
2. Verify → post test results as comment
3. Complete → change issue to `done` + summary comment
4. Blocked → post blocker + change status to `blocked` + @ mention human

### When using superpowers:finishing-a-development-branch
After merging:
1. Mark all related issues as `done`
2. Post final summary with PR link
3. Create follow-up issues if needed

## Configuration

Store Multica connection in `~/.hermes/multica.json`:

```json
{
  "base_url": "http://multica.test.com",
  "pat": "mul_fcd7c9fc9771ce73f8a3f1dc0588a94bcc4457ae",
  "workspace": "winpeek",
  "agent_id": "11064c9b-e38e-430d-8eb3-b28193bf490d"
}
```

## Quick Reference Card

```
Workspace:   cca8e6e7-b718-4c44-ac40-b1bf58fb1599 (winpeek)
Agent:       tech2CC-YU2 (11064c9b-e38e-430d-8eb3-b28193bf490d)
PAT:         mul_fcd7c9fc9771ce73f8a3f1dc0588a94bcc4457ae

Check my work:   GET  /api/issues?workspace_id={ws}&assignee_id={me}&status=todo,in_progress
Create issue:    POST /api/issues           (+X-Workspace-Id, +assignee_type+assignee_id)
Get issue:       GET  /api/issues/{id}      (+X-Workspace-Id)
Update issue:    PATCH /api/issues/{id}     (+X-Workspace-Id)
Add comment:     POST /api/issues/{id}/comments (+X-Workspace-Id)
Get agent:       GET  /api/agents/{me}
```

---

*Created for Hermes × Multica integration. Multica version: v2.x*
