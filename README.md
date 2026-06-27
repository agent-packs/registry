# Agent Packs Registry

The curated registry of **Agent Packs** — packs, skills, plugins, managed tool
descriptors, MCP servers, commands, prompts, templates, memory, and settings for
AI coding agents (Claude Code, Codex, Cursor, Gemini CLI, Copilot, Goose,
OpenCode).

This repository holds the registry **data**. The CLI that installs from it lives at
[agent-packs/cli](https://github.com/agent-packs/cli) and fetches this registry at
runtime (override with `AGENT_PACKS_REGISTRY`, `AGENT_PACKS_REGISTRY_REPO`, or
`AGENT_PACKS_REGISTRY_REF`).

## Layout

- `packs/` — one JSON manifest per pack (e.g. `backend-engineer.json`).
- `skills/<id>/SKILL.md` — reusable Agent Skills with required frontmatter.
- `plugins/<id>/.claude-plugin/plugin.json` — reusable Claude Code plugins.
- `commands/<id>.json`, `hooks/<id>.json`, `subagents/<id>.json`, `prompts/<id>.json`, `templates/<id>.json`, `tools/<id>.json`, `memory/<id>.json`, `settings/<id>.json`, `mcp/<id>.json` — optional reusable JSON capability manifests for non-skill/plugin capability kinds.
- `schemas/agent-pack.schema.json` — authoritative JSON Schema for pack validation.
- `schemas/examples/` — canonical example manifests.
- `policy/` — built-in policy presets (`default`, `ci`, `strict`).
- `index.json` — pre-generated searchable index (kept in sync with `packs/`).

## Validate

```sh
python3 -m venv .venv && .venv/bin/pip install -r tests/requirements.txt
.venv/bin/python -m unittest discover -s tests
```

You can also validate with the CLI:

```sh
agent-packs validate packs
agent-packs validate skills
agent-packs validate plugins
```

## Regenerate the index

`index.json` must be regenerated whenever packs change:

```sh
AGENT_PACKS_REGISTRY=./packs agent-packs index --output index.json
```

## Categories

Each pack's `categories` array must use values from this canonical allowlist.
Keep categories meaningful and map new packs to the nearest existing term rather
than inventing one-off labels.

| Category | Use for |
| --- | --- |
| `engineering` | General software engineering craft and workflows |
| `frontend` | UI, web, mobile, and design-facing work |
| `backend` | Server-side, APIs, architecture, and systems |
| `infrastructure` | Cloud, provisioning, and operational infrastructure |
| `platform` | Internal platforms, plugins, integrations, and distribution |
| `data` | Data engineering, pipelines, and databases |
| `ml` | Machine learning and AI engineering |
| `security` | Security, hardening, and risk |
| `quality` | Code review and quality gates |
| `testing` | Test authoring and QA |
| `reliability` | SRE, performance, debugging, releases, and operations |
| `documentation` | Technical writing, ADRs, and content/authoring |
| `product` | Product discovery, planning, leadership, and community |
| `devex` | Developer experience and collaboration workflows |

## Trust levels

Every skill/plugin **object ref** in a pack (refs written as objects with an
`id`, not bare strings) must declare a `trust` value from this allowlist. Trust
records the provenance of the upstream source so installers and reviewers can
reason about how much vetting a capability has received.

| Trust | Use for |
| --- | --- |
| `official` | Maintained by the source tool's own vendor org, or first-party content shipped from the `agent-packs/registry` repo itself. Examples: `anthropics/skills`, `google/skills`, `vercel-labs/agent-skills`, Anthropic's first-party `claude-plugins-official` plugins, and registry-authored plugins such as `claude-code-review`. |
| `verified` | Third-party integrations packaged and curated by a trusted vendor (e.g. the external integrations under `anthropics/claude-plugins-official/external_plugins/*` like GitHub, GitLab, Terraform). Vendor-reviewed, but not authored by the vendor whose tool they integrate. |
| `community` | Independent third-party community sources that are referenced but not vendor-maintained (e.g. `addyosmani/agent-skills`, `obra/superpowers`). |

`trust` is **required** on object refs and validated against this enum by the
JSON schema and by `agent-packs validate` / `lint` / `publish --check`. Bare
string skill refs (which carry no provenance metadata) are unaffected.

## Capability type support

| Type | Reference | Copy | Native | Standalone lifecycle | Reusable refs | Drift/status | Uninstall | Native destinations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `skill` | yes | yes | reference-only | yes | `skills` | yes | yes | tool skill roots |
| `plugin` | yes | no | gated by `--execute-plugins` | yes | `plugins` | receipt only | gated cleanup | plugin installer |
| `command` | yes | yes | no | yes | `commands` | yes | yes | Claude commands; portable fallback |
| `hook` | yes | gated by `--allow-hooks` | no | yes | `hooks` | yes | yes | portable fallback |
| `subagent` | yes | yes | no | yes | `subagents` | yes | yes | Claude agents; portable fallback |
| `prompt` | yes | yes | no | yes | `prompts` | yes | yes | portable fallback |
| `template` | yes | yes | no | yes | `templates` | yes | yes | portable fallback |
| `tool` | yes | yes | no execution in v1 | yes | `toolRefs` | yes | yes | portable `.agent-packs/tools/*.json` |
| `memory` | yes | merge with `--mode copy` | no | yes | `memory` | yes | yes | verified agent instruction files |
| `settings` | yes | merge with `--mode copy` | no | yes | `settings` | yes | yes | verified agent settings files |
| `mcp` | yes | settings merge with `--mode copy` | gated by `--execute-mcps` | yes | `mcp` | yes | yes | settings-backed MCP config |

Pack-level `tools` means advertised target agents. Reusable tool descriptors use
`toolRefs` to avoid overloading that public field. `targets` is metadata only;
use `agentTargets` for explicit per-agent destination overrides.

## Contributing a pack

1. `agent-packs new pack my-pack --dir packs`
2. Fill in skills/plugins/capabilities.
3. `agent-packs validate packs` and `agent-packs lint my-pack`.
4. Regenerate `index.json` and open a PR.

## License

Apache-2.0
