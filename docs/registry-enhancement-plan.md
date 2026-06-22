# Registry Enhancement Plan

This plan captures the next phase of Agent Packs Registry improvements from
three review lenses: product management, engineering, and quality. The goal is
to make the registry trustworthy, easy to choose from, and easy to contribute to
before expanding the catalog aggressively.

## Current Baseline

- Registry data is split from the CLI and lives in this repository.
- The registry has 44 packs, reusable skills, plugins, policies, examples, and a
  generated `index.json`.
- Core pack metadata coverage is strong: packs include license, maintainers,
  stability, review status, last verified date, categories, tags, tools, and
  scope.
- Most quality signals are still early-stage: packs are still experimental,
  direct skill/plugin refs often lack provenance metadata, and compatibility is
  broader in product messaging than in verified registry evidence.
- Registry CI validates schemas and index drift, but CLI-backed contract checks
  are not yet mandatory in this repo.

## Priorities

### P0: Trust And Catalog Quality

Define a graduation path from `experimental` to `stable`.

- Require clear maintainer ownership, current `lastVerified`, passing registry
  checks, successful dry-run install, compatibility evidence, source provenance,
  license review, and policy review.
- Promote a small flagship set before expanding aggressively: starter, frontend,
  backend, AI engineer, PR review, reliability/debugging, security, QA, platform,
  open-source maintainer, full lifecycle, and eng leader.
- Keep stable packs fresh by requiring re-verification at least every 90 days.

Make provenance visible.

- Prefer object refs over bare skill/plugin strings for popular, starter, role,
  and integration packs.
- Include `trust`, `source`, `repository` or `homepage`, and license metadata
  where available.
- Normalize trust vocabulary across registry schema, CLI policy, catalog UI, and
  docs before adding more trust-dependent behavior.

Introduce registry quality scoring.

- Add a quality report to `publish --check` or registry CI covering metadata
  completeness, trust metadata, moving source risk, license/provenance,
  compatibility, freshness, and index drift.
- Block new packs below the minimum quality bar once the scoring model is
  stable.

### P1: Discovery And Adoption

Make the catalog answer "what should I install?" quickly.

- Add guided adoption paths for starter, frontend, backend, AI engineer, PR
  review, and reliability/debugging workflows.
- Surface stability, review status, last verified date, categories, tools,
  scope, and trust summary in CLI discovery output and catalog views.
- Add filters for category, tool, stability, review status, trust, scope, and
  user persona.

Keep compatibility honest.

- Distinguish "target directory supported" from "pack verified on this agent."
- Add per-tool compatibility badges and warnings for Claude Code, Codex, Cursor,
  Gemini CLI, OpenCode, Copilot, and Goose.
- Soften or qualify public claims when a tool has target support but no verified
  pack coverage.

Track adoption signals.

- Use opt-in CLI telemetry or aggregate public signals to understand searches,
  installs, failed installs, copied install commands, popular packs, stale packs,
  and contributor throughput.
- Publish a lightweight monthly registry health snapshot once metrics exist.

### P1: Contributor Workflow

Make high-quality contributions predictable.

- Add issue and PR templates for requesting a pack, contributing a pack, and
  updating provenance metadata.
- Extend contribution guidance with a curation rubric for target user, source
  provenance, trust, compatibility, verification commands, index regeneration,
  and review expectations.
- Update `agent-packs new pack` so generated manifests include production-grade
  recommended fields such as categories, requirements, review status,
  `lastVerified`, and examples of trust-bearing object refs.

Reduce review churn.

- Require `index.json` freshness for pack changes.
- Add docs/catalog drift checks for pack counts, starter-path copy, and public
  compatibility claims.
- Keep registry README as the contributor-facing source for category and trust
  definitions.

### P2: Ecosystem Coverage

Grow the catalog from evidence, not breadth alone.

- Maintain a coverage map by category, tool, stack, and persona.
- Prioritize gaps where users already search or ask for help.
- Add stack and vendor packs only after trust and compatibility indicators are
  visible. Good candidates include Rails, Django/FastAPI, Node/Express,
  Kubernetes, AWS, Azure, GitHub Actions, Terraform, and Playwright.
- Prefer composable packs over duplicated skills; retire or merge low-use
  overlap when quality signals show confusion.

## Engineering Guardrails

Treat the registry metadata contract as a public API.

- Define which fields are authoritative in pack manifests, which are indexed in
  `index.json`, and which are CLI runtime state only.
- Version the schema and avoid breaking validation rules until a released CLI can
  validate and generate the new shape.
- For any discoverability field, update the registry schema, examples, CLI model,
  index generator, drift tests, and catalog rendering together.

Sequence cross-repo changes carefully.

1. Add additive CLI model, validation, and index support.
2. Update registry schema, examples, manifests, and generated index.
3. Update catalog and docs after the index contract is stable.
4. Introduce stricter validation only after the supported CLI release is
   available.

Close known contract gaps.

- Align top-level schema fields with CLI model fields such as `trust`, `requires`,
  and `conflictsWith`.
- Reconcile trust vocabularies across registry refs, inline capabilities,
  pack-level trust, and CLI policy/min-trust behavior.
- Treat `index.json` as a consumer contract, not an implementation cache.
- Document split-repo behavior consistently across CLI and registry docs.

## Quality Gates

Expand registry tests.

- Add valid and invalid fixture directories with expected error names.
- Cover missing trust, bad category, bad composed-pack reference, duplicate pack
  IDs, missing local skill/plugin refs, bad plugin manifest paths, stale
  `lastVerified`, invalid requirements, deprecated packs without replacement,
  and plugin commands without execution metadata.
- Add graph/content tests: every `packs[]`, `skills[]`, and `plugins[]`
  reference resolves; composed packs are acyclic; local skill names match their
  directories; expanded capability collisions are intentional.

Make CLI-backed registry checks mandatory.

- Build or install the CLI in registry CI and run it against this checkout with
  `AGENT_PACKS_REGISTRY=$PWD/packs`.
- Gate `agent-packs validate packs`, `validate skills`, `validate plugins`,
  `lint --all`, `verify --all`, `publish --check --policy policy/ci.json`, and
  index freshness.
- Smoke-test consumer commands such as `search --json`, `show --json`,
  `tree`, `audit --json`, `licenses`, `attribution`, `compat --agent codex`, and
  dry-run install in reference mode.

Keep CI safe and deterministic.

- Do not require network execution or native plugin execution for registry CI.
- Use dry-run or reference mode for install checks unless a command is isolated
  and explicitly safe.
- Run a scheduled compatibility job with the latest released CLI against the
  registry `main` branch to catch split-repo regressions.

## Success Criteria

- Ten flagship packs graduate to `stable` with fresh verification dates.
- One hundred percent of starter and popular packs use provenance-bearing object
  refs where provenance matters.
- Every pack declares actionable requirements metadata.
- Catalog and CLI discovery expose trust, stability, review status, freshness,
  compatibility, and install commands.
- Registry PRs fail fast on schema, index, graph, policy, and CLI contract drift.
- Contributors can request or add a pack using one documented checklist.
