# Shared Memory — Soccer Sports Analytics

> **Disclaimer**: This is an internship project meant for upskilling. Sample data only.

This directory serves as the **persistent shared memory** for all agents in the pipeline. Each agent reads from and writes to this memory to maintain context across runs.

---

## Memory Structure

```
Memory/
├── Memory.md                  ← This file (index)
├── team_profiles.json         ← Team metadata, rosters, league info
├── historical_results.json    ← Past match results for form & H2H lookups
├── league_standings.json      ← Current league table
└── audit_log.json             ← Record of all agent outputs
```

---

## 1. Team Profiles (`team_profiles.json`)

Stores metadata for each team: full name, short code, league, home venue, and current season roster. Updated at the start of each season or when transfers occur.

**Written by**: Manual setup / Agent 1 (roster updates)  
**Read by**: Agent 1, Agent 2, Agent 3

---

## 2. Historical Results (`historical_results.json`)

Stores completed match results with scores, goal scorers, and basic stats. Used by Agent 3 for form calculation and head-to-head lookups.

**Written by**: Agent 1 (after processing a completed match)  
**Read by**: Agent 2 (for context), Agent 3 (for predictions)

---

## 3. League Standings (`league_standings.json`)

Current league table with points, goal difference, and position for each team. Rebuilt after each gameweek.

**Written by**: Agent 1 (derived from historical results)  
**Read by**: Agent 2 (standings context in summaries), Agent 3 (league position factor)

---

## 4. Audit Log (`audit_log.json`)

Append-only log of every agent invocation: timestamp, agent name, input hash, output summary, and any warnings or errors. Used for debugging and traceability.

**Written by**: All agents  
**Read by**: Orchestrator (for error tracking)
