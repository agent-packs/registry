---
name: crafting-engineering-strategy
description: Create, critique, and operationalize engineering strategy documents using diagnosis, tradeoff exploration, guiding policy, coherent actions, and operating cadence. Use when an engineering leader needs strategy for a team, platform, architecture, migration, reliability program, or multi-quarter technical investment.
license: Apache-2.0
compatibility: Works with coding agents that support Agent Skills.
metadata:
  agentpacks.version: "0.1.0"
  agentpacks.reference: https://craftingengstrategy.com/
  agentpacks.referenceTitle: Crafting Engineering Strategy
---

# Crafting Engineering Strategy

Use this skill when asked to create, review, or refine engineering strategy. Treat strategy as a clear set of choices that helps an organization decide what to do, what not to do, and how to sequence work under real constraints.

This skill is original Agent Packs content informed by the public Crafting Engineering Strategy site. Do not copy or quote the source text unless the user explicitly asks for a short attributed quote.

## Workflow

1. Frame the mandate.
   - Name the business or user outcome, decision owner, time horizon, and teams affected.
   - Separate strategy from roadmap: strategy explains choices and tradeoffs; roadmap schedules work.
   - Identify non-goals early so the strategy has edges.

2. Diagnose the situation.
   - Summarize the current system, constraints, bottlenecks, risks, and relevant history.
   - Distinguish facts from assumptions.
   - Look for the limiting factor: delivery throughput, reliability, architecture, developer experience, staffing, product ambiguity, operational load, or dependency drag.

3. Explore strategic options.
   - Generate 3-5 plausible approaches, including a conservative option and a more ambitious option.
   - For each option, evaluate customer impact, business value, engineering cost, reversibility, risk, sequencing, and organizational fit.
   - State the option you reject and why; strategy gets stronger when tradeoffs are explicit.

4. Choose the guiding policy.
   - Convert the diagnosis into a small number of principles or rules that guide decisions.
   - Keep policies concrete enough to resolve future disagreements.
   - Prefer policies that can be tested by asking, "What would this make us stop doing?"

5. Define coherent actions.
   - List the initiatives, owners, dependencies, milestones, and first irreversible decisions.
   - Include what changes in architecture, process, staffing, tooling, quality gates, and operating cadence.
   - Tie every action back to the diagnosis and policy.

6. Operationalize the strategy.
   - Define review cadence, decision forums, metrics, and refresh triggers.
   - Name risks that require escalation and signals that mean the strategy is no longer working.
   - Translate the strategy into the next 30, 60, and 90 days of action.

## Strategy Memo Shape

Use this structure unless the user provides another format:

```markdown
# Engineering Strategy: <area>

## Decision Needed

## Context And Mandate

## Diagnosis

## Strategic Options

## Recommended Strategy

## Guiding Policy

## Coherent Actions

## Tradeoffs And Non-Goals

## Risks And Mitigations

## Operating Cadence

## 30 / 60 / 90 Day Plan

## Open Questions
```

## Review Checklist

- Is there a clear diagnosis, or only a list of projects?
- Does the strategy make meaningful tradeoffs?
- Are non-goals explicit?
- Does the guiding policy help teams make future decisions?
- Are the actions coherent, sequenced, and owned?
- Are risks, assumptions, and refresh triggers visible?
- Can an executive understand the strategy without reading implementation details?
- Can an engineer understand how their daily work should change?

## Output Guidance

When creating a strategy, produce:

- one concise executive summary;
- the full strategy memo;
- a decision table comparing options;
- owner/date actions for the next 30 days;
- explicit assumptions and missing evidence.

When reviewing a strategy, lead with the strongest finding first, then list gaps by severity. Avoid generic leadership advice; ground feedback in the diagnosis, choices, sequencing, and operating model.
