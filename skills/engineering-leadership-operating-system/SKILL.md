---
name: engineering-leadership-operating-system
description: Route ambiguous engineering leadership work into decision-ready reviews and operating artifacts. Use for engineering strategy, portfolio and capacity choices, delivery or reliability reviews, architecture and modernization decisions, launches and incidents, organization and talent planning, cost and vendor choices, AI adoption, or leadership communication.
---

# Engineering Leadership Operating System

Turn leadership questions into the smallest useful decision process. Optimize for outcomes, evidence, explicit tradeoffs, accountable follow-through, and sustainable engineering systems.

## Route The Request

Classify the primary leadership job before producing an artifact:

- **Strategy:** diagnosis, options, guiding policy, coherent actions, and non-goals.
- **Portfolio:** capacity, dependencies, opportunity cost, sequencing, and stop/defer decisions.
- **Delivery or reliability:** outcome confidence, system constraints, risks, recovery, and owner/date actions.
- **Architecture or modernization:** lifecycle risk, options, reversibility, migration increments, and value realization.
- **Launch or incident:** customer impact, readiness or containment, decision gates, communication, and follow-up.
- **Organization or talent:** ownership, capability, manager load, succession, retention risk, and fair development actions.
- **Cost or vendor:** total cost, lock-in, security, operating burden, alternatives, and exit conditions.
- **AI adoption:** bounded experiments using delivery, quality, security, cost, and developer-experience evidence.
- **Change communication:** audiences, decisions, impacts, objections, channels, feedback, and reinforcement.

If several jobs are present, name the primary decision and treat the others as supporting reviews.

## Build The Decision Frame

1. State the outcome, customer or business impact, decision owner, time horizon, and decision needed.
2. Separate observed facts, interpretations, assumptions, and unknowns. Rate confidence only where it changes the decision.
3. Identify constraints: capacity after operational load, dependencies, security or compliance, architecture, skills, cost, and timing.
4. Distinguish reversible from difficult-to-reverse choices. Use a smaller experiment for uncertain reversible choices; require broader evidence and review for consequential ones.
5. Compare realistic options, including continuing the current path. Show benefits, costs, risks, reversibility, and opportunity cost.
6. Recommend one path and explain why now. Name non-goals and rejected options so the choice has clear edges.
7. Define owners, dates, decision gates, tripwires, counter-metrics, and a review cadence.

Ask only for missing context that could materially change the recommendation. Otherwise proceed with labeled assumptions.

## Apply Leadership Guardrails

- Measure systems and outcomes, not individual activity. Never use commits, lines of code, tickets, tool usage, prompts, or AI tokens as individual productivity scores.
- Use DORA and SPACE as complementary signals, not targets or league tables.
- Keep people reviews evidence-based, role-relevant, bias-aware, and separate from diagnosis of system constraints.
- Protect psychological safety in incidents and retrospectives while preserving clear accountability for decisions and follow-through.
- Treat security, privacy, accessibility, reliability, and operational readiness as product constraints, not final-stage checks.
- Label source provenance and confidence. Do not manufacture precision when evidence is weak.
- Escalate when risk exceeds the decision owner's authority or when legal, HR, security, or compliance expertise is required.

## Produce A Decision-Ready Brief

Use this shape unless the user provides another format:

```markdown
# Leadership Decision Brief: <topic>

## Decision Needed
## Outcome And Context
## Evidence, Assumptions, And Confidence
## Options And Tradeoffs
## Recommendation And Non-Goals
## Risks, Mitigations, And Tripwires
## Decisions And Owner/Date Actions
## Communication And Stakeholders
## Measures And Counter-Metrics
## Review Date And Open Questions
```

Lead with the decision, not background. Keep the executive summary concise, make disagreement visible, and end with no ownerless action.

## Review Existing Work

When critiquing a strategy, plan, review, or update:

1. Lead with the highest-risk gap.
2. Separate factual errors, unsupported assumptions, missing decisions, and execution risks.
3. Check whether the artifact makes a real choice and fits actual capacity.
4. Check customer impact, security, reliability, operability, cost, talent, and stakeholder consequences where relevant.
5. Recommend concrete revisions and the smallest evidence-gathering step for unresolved uncertainty.
6. End with a clear readiness judgment: ready, ready with conditions, or not ready.
