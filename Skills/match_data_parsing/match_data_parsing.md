# Skill: Match Data Parsing

> **Disclaimer**: This is an internship project meant for upskilling in agentic AI.

## Purpose

Validates and restructures raw match event feeds into clean, typed data objects. This skill is used by the Match Data Ingestion Agent (Agent 1).

## When to Use

- When a raw match event JSON is received from a data source (API, file, etc.)
- When building team form profiles from historical data

## Capabilities

1. **Field extraction**: Pulls match metadata (ID, league, date, venue), lineups, events, and stats from raw JSON
2. **Event classification**: Categorizes events into goals, cards, substitutions, and other
3. **Player validation**: Cross-checks player names against lineup and roster data
4. **Completeness scoring**: Counts present vs. required fields and returns a 0-1 score
5. **Key moment identification**: Flags high-impact events (goals, red cards, late drama)

## Input Format

Raw match event JSON with fields:
- `match_id`, `league`, `season`, `gameweek`, `date`, `venue`
- `home_team` / `away_team` (each with `name`, `lineup`, `formation`)
- `events[]` (each with `minute`, `type`, `team`, `player`, optional `assist`/`player_in`/`player_out`)
- `stats.home` / `stats.away` (possession, shots, shots_on_target, corners, fouls)
- `result` (home_goals, away_goals)

## Output Format

`StructuredMatchData` — see Master.md §4.3

## Validation Rules

| Rule | Action on Failure |
|------|-------------------|
| `match_id` must be present | Reject input |
| At least one team must have lineup data | Warn, proceed |
| Event player must be in lineup or roster | Flag event as unvalidated |
| Stats must have at least possession and shots | Reduce completeness score |
| Score in `result` must match goal count in `events` | Warn, trust `result` field |

## Error Codes

| Code | Meaning |
|------|---------|
| `MISSING_MATCH_ID` | No match_id in input |
| `INCOMPLETE_LINEUP` | Lineup has fewer than 11 players |
| `UNKNOWN_PLAYER` | Event references player not in lineup/roster |
| `STAT_MISMATCH` | Computed stats differ from provided stats |
| `LOW_COMPLETENESS` | Data completeness below 80% threshold |
