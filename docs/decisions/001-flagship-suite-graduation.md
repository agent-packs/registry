# ADR 001: Flagship Suite Graduation

- Status: accepted
- Date: 2026-07-25

## Context

The registry needs a small number of strong starting points rather than treating
every pack as equally mature. Stability and recommendation labels are not enough
without reproducible sources, compatibility evidence, and proof that the CLI can
resolve and plan the pack.

## Decision

`eng-leader` is the flagship role suite and `superpowers` is the flagship
engineering workflow suite.

A flagship suite must:

1. Pin every remote capability to an immutable source revision.
2. Preserve capability-level trust, license, repository, and upstream attribution.
3. Declare current compatibility evidence separately from advertised tools.
4. Pass schema validation, lint, source verification, policy, and index drift checks.
5. Produce a successful dry-run copy-mode install for at least one verified target.
6. Include realistic use cases and example prompts that describe the outcome, not internal feature names.
7. Hide deprecated dependencies from default discovery and declare replacements where applicable.

The Pages catalog bundles the exact committed registry index during deployment.
It does not fetch the mutable default branch at runtime.

## Consequences

- `stable` becomes an evidence-backed release state for flagship packs.
- Upstream upgrades require an immutable release pin and refreshed verification date.
- Registry CI depends on the public CLI contract and catches resolver drift.
- The catalog is reproducible for a deployment and may lag registry `main` until
  the next CLI Pages deployment, which is preferable to untested runtime drift.
