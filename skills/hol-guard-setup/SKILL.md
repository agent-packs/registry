---
name: hol-guard-setup
description: Install or initialize HOL Guard local runtime protection for supported coding-agent workflows. Use when the user explicitly asks to install, enable, set up, verify, or repair HOL Guard.
compatibility: Works with coding agents that support Agent Skills. The referenced HOL Guard setup skill uses the maintained hol-guard CLI and asks before installation.
metadata:
  agentpacks.version: "0.1.0"
  agentpacks.source: https://github.com/hashgraph-online/hol-guard/tree/45a24462f9e5c2987edccf87d6524ec4ff111a56/integrations/claude-code-plugin/skills/setup
  agentpacks.upstreamSource: https://github.com/hashgraph-online/hol-guard/tree/main/integrations/claude-code-plugin/skills/setup
  agentpacks.upstream: hashgraph-online/hol-guard/integrations/claude-code-plugin/skills/setup
---

# hol-guard-setup

This registry entry references HOL Guard's maintained setup skill. The upstream flow checks whether `hol-guard` is installed, asks before installing it with `pipx install hol-guard`, initializes local protection with `hol-guard init`, and verifies the resulting state with `hol-guard status`.

Installers should use `agentpacks.source` and avoid copying upstream content into this registry. HOL Guard remains the runtime security boundary; this skill only provides the official setup and verification workflow.
