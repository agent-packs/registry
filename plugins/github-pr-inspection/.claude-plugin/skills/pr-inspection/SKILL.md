---
name: pr-inspection
description: Inspect GitHub pull requests for leadership-relevant release risk, quality gates, ownership, and follow-up actions.
license: Apache-2.0
compatibility: Claude Code plugin skill packaged by Agent Packs.
metadata:
  agentpacks.version: "0.1.0"
  agentpacks.source: https://github.com/agent-packs/registry/tree/main/plugins/github-pr-inspection/.claude-plugin/skills/pr-inspection
---

# PR Inspection

Use this workflow when reviewing a pull request from an engineering leadership perspective.

Focus on release risk, customer impact, missing tests, operational readiness, security/privacy exposure, ownership clarity, and whether the change needs broader stakeholder review.

## Output

- Findings ordered by severity.
- Merge readiness: ready, blocked, or needs owner decision.
- Required follow-ups with owners and dates.
