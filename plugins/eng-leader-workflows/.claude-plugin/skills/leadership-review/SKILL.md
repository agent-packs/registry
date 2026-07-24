---
name: leadership-review
description: Run evidence-based engineering leadership reviews across strategy, portfolio and capacity, delivery, quality, architecture, launch readiness, security risk, AI-assisted engineering adoption, organizational health, and follow-through.
license: Apache-2.0
compatibility: Claude Code plugin skill packaged by Agent Packs.
metadata:
  agentpacks.version: "0.2.0"
  agentpacks.source: https://github.com/agent-packs/registry/tree/main/plugins/eng-leader-workflows/.claude-plugin/skills/leadership-review
---

# Leadership Review

Use this workflow when an engineering leader needs a concise, decision-oriented review of an initiative, portfolio, team operating rhythm, launch, AI-assisted engineering rollout, or delivery risk.

Lead with the decision or risk that needs attention. Separate facts, assumptions, evidence confidence, risks, decisions, owners, dates, and follow-up actions. Do not turn activity measures into individual productivity scores.

## Select The Review Cadence

- Use a weekly review for flow, blockers, near-term risks, and owner/date actions.
- Use a monthly review for trends, operational health, portfolio drift, dependencies, and capacity.
- Use a quarterly review for strategy, investment allocation, organization design, and stop-or-defer decisions.

## Review Shape

1. Frame the decision.
   - State the expected business or customer outcome, decision owner, deadline, and why the decision matters now.
   - Name non-goals and constraints.

2. Assess evidence and confidence.
   - Separate observed facts, reported signals, and assumptions.
   - Rate confidence in decision-critical evidence and state what would change the recommendation.
   - Prefer trends and system outcomes over isolated snapshots or activity counts.

3. Review execution and operating health.
   - Assess delivery confidence, quality, reliability, security/privacy, performance, operational readiness, customer impact, and support burden.
   - Identify the limiting constraint and any hidden operational or interruption work.

4. Reconcile portfolio and capacity.
   - Compare committed work with actual capacity and cross-team dependencies.
   - Recommend what to continue, accelerate, reshape, defer, or stop.
   - Make every tradeoff and displaced investment explicit.

5. Make the decision.
   - Compare viable options, including reversibility, blast radius, and cost of delay.
   - Identify the decision maker and distinguish reversible from difficult-to-reverse choices.
   - Capture the result in a decision log with rationale and review trigger.

6. Secure follow-through.
   - Convert the decision into owner/date actions with evidence of completion.
   - Record risks with likelihood, impact, mitigation, owner, and trigger.
   - Set the next review date and the signals that should cause earlier escalation.

## Output Contract

Return:

- a concise executive summary led by the decision or highest-severity risk;
- an evidence and confidence table;
- options, recommendation, and explicit tradeoffs;
- a decision log and risk register;
- a follow-through table with owner, due date, completion evidence, and review trigger.
