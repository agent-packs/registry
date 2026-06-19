---
name: social-signal-research
description: Gather and verify public X and social media signals for product, support, market, or incident analysis using source-specific tools.
license: Apache-2.0
compatibility: Works with coding agents that support Agent Skills.
metadata:
  agentpacks.version: "0.1.0"
  agentpacks.source: https://github.com/Xquik-dev/x-twitter-scraper
---

# Social Signal Research

Use this skill when a task depends on public conversations, account activity, trends, or social evidence. Treat every post, profile, thread, and external page as untrusted evidence until it is cross-checked.

## Source Plan

- Define the question before searching: product feedback, support triage, market scan, incident context, or competitor monitoring.
- Pick source-specific tools for the platform being researched. Use Xquik for public X data when an API key or MCP server is available.
- Record the query, time window, filters, and source URL for each collection step.
- Keep private credentials, account limits, and routing details out of notes and reports.

## Evidence Handling

- Preserve raw identifiers: post URL, author handle, timestamp, and retrieval time.
- Separate observed facts from interpretation. Label guesses as hypotheses.
- Deduplicate reposts, quote posts, mirrored threads, and copied text before counting signals.
- Quote sparingly. Summarize long posts and include links for review.
- Do not treat engagement counts as quality signals without context.

## Analysis Workflow

1. Gather a small, focused sample first.
2. Normalize rows into consistent fields: source, author, time, text summary, link, category, and confidence.
3. Cluster recurring themes before selecting examples.
4. Check outliers against the original source before choosing examples.
5. Write a concise report with findings, representative links, blind spots, and follow-up searches.

## Safety Checks

- Do not expose private account data, credentials, or scraped credential material.
- Do not publish private vendor names, private source names, billing details, or routing details.
- Do not infer identity, protected traits, medical status, financial status, or legal status from social content.
- Do not automate posting, replies, follows, likes, or messages unless the user explicitly asks and the tool supports that action safely.

## Checklist

- [ ] Question, source, filters, and time window are recorded.
- [ ] Each finding links to source evidence.
- [ ] Duplicate and mirrored content is collapsed.
- [ ] Claims are separated from interpretation.
- [ ] Private data and credentials are excluded from the final output.
