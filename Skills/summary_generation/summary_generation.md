# Skill: Summary Generation

> **Disclaimer**: This is an internship project meant for upskilling in agentic AI.

## Purpose

Builds natural-language match reports from structured match data. Produces a headline, narrative body, and key statistics section. Used by the Game Summary Agent (Agent 2).

## When to Use

- After Agent 1 produces a `StructuredMatchData` object for a completed match
- When a post-match report is needed for publication or review

## Capabilities

1. **Headline generation**: Creates a concise one-line result summary (max 80 chars)
2. **Narrative construction**: Builds a 200-350 word match report following a chronological structure
3. **Context injection**: Adds league standings and form context from shared memory
4. **Key stats extraction**: Identifies the 3-5 most interesting statistical highlights
5. **Match rating**: Scores match excitement 1-10 based on goals, closeness, and drama

## Input Format

`StructuredMatchData` — see Master.md §4.3

## Output Format

`GameSummary` — see Master.md §4.5

## Narrative Template

```
1. OPENING — Result + venue + date + context
2. FIRST HALF — Chronological key events (goals, cards)
3. SECOND HALF — Chronological key events
4. CLOSING — Standings impact, form implications
5. KEY STATS — 3-5 bullet-point highlights
```

## Tone Guidelines

- **Neutral**: No fan bias, no team favoritism
- **Factual**: Every claim grounded in data
- **Engaging**: Use varied sentence structure, avoid repetition
- **Professional**: Sports journalism register, not casual/social media

## Match Rating Formula

| Factor | Weight |
|--------|--------|
| Total goals | 1.5 per goal (max 6.0) |
| Closeness (1-goal margin or draw) | +1.5 to +2.0 |
| Red cards | +0.5 per card |
| Late goals (80+ min) | +0.8 per goal |
| Final rating | Clamped to 1.0–10.0 |

## Quality Checks

- Word count in 200-350 range
- No player names mentioned that don't appear in `StructuredMatchData`
- No score referenced that differs from `StructuredMatchData.score`
- If `data_quality.completeness_score < 0.80`, add disclaimer to output
