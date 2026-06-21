# Agent Packs Registry

The curated registry of **Agent Packs** — packs, skills, and plugins for AI coding
agents (Claude Code, Codex, Cursor, Gemini CLI, Copilot, Goose, OpenCode).

This repository holds the registry **data**. The CLI that installs from it lives at
[agent-packs/cli](https://github.com/agent-packs/cli) and fetches this registry at
runtime (override with `AGENT_PACKS_REGISTRY`, `AGENT_PACKS_REGISTRY_REPO`, or
`AGENT_PACKS_REGISTRY_REF`).

## Layout

- `packs/` — one JSON manifest per pack (e.g. `backend-engineer.json`).
- `skills/<id>/SKILL.md` — reusable Agent Skills with required frontmatter.
- `plugins/<id>/.claude-plugin/plugin.json` — reusable Claude Code plugins.
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

## Contributing a pack

1. `agent-packs new pack my-pack --dir packs`
2. Fill in skills/plugins/capabilities.
3. `agent-packs validate packs` and `agent-packs lint my-pack`.
4. Regenerate `index.json` and open a PR.

## License

Apache-2.0
