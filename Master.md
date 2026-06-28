# Soccer Sports Analytics Multi-Agent System — Master Document

> **Disclaimer**: This is an internship project meant for upskilling in agentic AI. It uses sample data and simulated API connections. Not intended for production betting, gambling, or commercial sports analytics use.

---

## 1. Purpose & Context

This system provides **automated soccer match analytics** — it ingests raw match data, generates human-readable game summaries, and predicts win probabilities for upcoming fixtures. The three-agent pipeline mirrors how professional sports analytics desks operate: data collection → narrative generation → predictive modeling.

**Domain**: Sports Analytics — Soccer (Football)  
**Target Users**: Students learning agentic AI architecture  
**Scope**: League matches (Premier League, La Liga, Serie A, Bundesliga, Ligue 1)

### What Does This System Do?

1. **Post-match**: Takes raw match event data (goals, cards, possession, shots) and generates a natural-language summary suitable for publication
2. **Pre-match**: Takes two teams' historical records and current form to predict win/draw/loss probabilities for an upcoming fixture

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (main.py)                     │
│     Receives match data or fixture request → routes to agents│
└──────────┬──────────────────┬──────────────────┬─────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌──────────────────┐ ┌────────────────────┐ ┌────────────────────────┐
│  Agent 1:        │ │  Agent 2:          │ │  Agent 3:              │
│  Match Data      │ │  Game Summary      │ │  Win Probability       │
│  Ingestion       │ │  Generation        │ │  Prediction            │
│                  │ │                    │ │                        │
│  - Parses raw    │ │  - Builds match    │ │  - Loads team form     │
│    match feeds   │ │    narrative       │ │  - Computes head-to-   │
│  - Structures    │ │  - Highlights key  │ │    head stats          │
│    events        │ │    moments         │ │  - Calculates win/     │
│  - Validates     │ │  - Adds context    │ │    draw/loss probs     │
│    completeness  │ │    (standings,     │ │  - Outputs confidence  │
│  - Computes      │ │    form)           │ │    intervals           │
│    derived stats │ │                    │ │                        │
└──────────────────┘ └────────────────────┘ └────────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────┐
│                       SHARED MEMORY                          │
│  - Team profiles & rosters   - League standings              │
│  - Historical match results  - Head-to-head records          │
│  - Season form (last 5)      - Decision/output audit trail   │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

**Post-match pipeline** (Summary generation):
1. **Input**: Raw match event JSON (lineups, goals, cards, substitutions, stats)
2. **Agent 1** parses and validates → outputs `StructuredMatchData`
3. **Agent 2** takes `StructuredMatchData` + memory context → outputs `GameSummary`

**Pre-match pipeline** (Win probability):
1. **Input**: Fixture request JSON (home team, away team, league, date)
2. **Agent 1** retrieves historical data from memory → outputs `TeamFormProfile` for each team
3. **Agent 3** takes both `TeamFormProfile` objects → outputs `WinProbability`

---

## 3. Agent Definitions

### Agent 1: Match Data Ingestion Agent

| Field | Value |
|-------|-------|
| **Role** | Parse raw match feeds into structured, validated match data |
| **Input** | Raw match event JSON or fixture request JSON |
| **Output** | `StructuredMatchData` or `TeamFormProfile` |
| **Skills Used** | `match_data_parsing` |
| **Guardrails** | Must flag missing required fields; never fabricate match events; validate all player names against lineup data |

### Agent 2: Game Summary Generation Agent

| Field | Value |
|-------|-------|
| **Role** | Generate natural-language match summaries from structured data |
| **Input** | `StructuredMatchData` from Agent 1 |
| **Output** | `GameSummary` (headline + body + key stats) |
| **Skills Used** | `summary_generation` |
| **Guardrails** | Must reference only events present in the data; no speculation about injuries unless in source data; tone must be neutral and factual |

### Agent 3: Win Probability Prediction Agent

| Field | Value |
|-------|-------|
| **Role** | Calculate win/draw/loss probabilities for upcoming fixtures |
| **Input** | `TeamFormProfile` objects for home and away teams |
| **Output** | `WinProbability` with confidence intervals |
| **Skills Used** | `probability_calculation` |
| **Guardrails** | Probabilities must sum to 1.0; must disclose sample size; must include disclaimer that predictions are statistical estimates only |

---

## 4. Data Schemas

### 4.1 Input: Raw Match Event

```json
{
  "match_id": "PL-2025-GW12-ARS-CHE",
  "league": "Premier League",
  "season": "2025-26",
  "gameweek": 12,
  "date": "2025-11-08",
  "venue": "Emirates Stadium",
  "home_team": {
    "name": "Arsenal",
    "lineup": ["player_1", "player_2", "..."],
    "formation": "4-3-3"
  },
  "away_team": {
    "name": "Chelsea",
    "lineup": ["player_1", "player_2", "..."],
    "formation": "4-2-3-1"
  },
  "events": [
    {"minute": 23, "type": "goal", "team": "home", "player": "Saka", "assist": "Odegaard"},
    {"minute": 45, "type": "yellow_card", "team": "away", "player": "Caicedo"},
    {"minute": 67, "type": "substitution", "team": "home", "player_in": "Nketiah", "player_out": "Jesus"}
  ],
  "stats": {
    "home": {"possession": 58, "shots": 14, "shots_on_target": 6, "corners": 7, "fouls": 11},
    "away": {"possession": 42, "shots": 9, "shots_on_target": 3, "corners": 4, "fouls": 14}
  },
  "result": {"home_goals": 2, "away_goals": 1}
}
```

### 4.2 Input: Fixture Request

```json
{
  "request_type": "prediction",
  "home_team": "Arsenal",
  "away_team": "Chelsea",
  "league": "Premier League",
  "date": "2025-12-15",
  "gameweek": 16
}
```

### 4.3 Output: StructuredMatchData

```json
{
  "match_id": "PL-2025-GW12-ARS-CHE",
  "league": "Premier League",
  "date": "2025-11-08",
  "home_team": "Arsenal",
  "away_team": "Chelsea",
  "score": {"home": 2, "away": 1},
  "goals": [
    {"minute": 23, "scorer": "Saka", "assist": "Odegaard", "team": "Arsenal"},
    {"minute": 52, "scorer": "Havertz", "assist": "Saka", "team": "Arsenal"},
    {"minute": 78, "scorer": "Palmer", "assist": null, "team": "Chelsea"}
  ],
  "cards": {
    "yellow": [{"player": "Caicedo", "team": "Chelsea", "minute": 45}],
    "red": []
  },
  "stats": {
    "possession": {"home": 58, "away": 42},
    "shots": {"home": 14, "away": 9},
    "shots_on_target": {"home": 6, "away": 3},
    "pass_accuracy": {"home": 87, "away": 81},
    "corners": {"home": 7, "away": 4}
  },
  "key_moments": [
    {"minute": 23, "description": "Opening goal by Saka"},
    {"minute": 78, "description": "Palmer pulls one back for Chelsea late"}
  ],
  "data_quality": {"completeness_score": 0.95, "missing_fields": ["pass_accuracy"]}
}
```

### 4.4 Output: TeamFormProfile

```json
{
  "team": "Arsenal",
  "league": "Premier League",
  "season": "2025-26",
  "overall_record": {"played": 15, "won": 10, "drawn": 3, "lost": 2, "gf": 28, "ga": 12},
  "home_record": {"played": 8, "won": 7, "drawn": 1, "lost": 0, "gf": 18, "ga": 4},
  "last_5": ["W", "W", "D", "W", "L"],
  "last_5_goals_scored": 11,
  "last_5_goals_conceded": 5,
  "league_position": 2,
  "points": 33,
  "head_to_head_vs_opponent": {
    "last_5_meetings": [
      {"date": "2025-04-20", "home": "Chelsea", "away": "Arsenal", "score": "1-2", "result": "W"},
      {"date": "2024-11-10", "home": "Arsenal", "away": "Chelsea", "score": "3-1", "result": "W"}
    ],
    "wins": 3, "draws": 1, "losses": 1
  }
}
```

### 4.5 Output: GameSummary

```json
{
  "match_id": "PL-2025-GW12-ARS-CHE",
  "headline": "Arsenal edge past Chelsea 2-1 at the Emirates",
  "summary": "Arsenal secured a hard-fought 2-1 victory over Chelsea at the Emirates Stadium in Gameweek 12...",
  "key_stats": {
    "possession_dominant": "Arsenal (58%)",
    "top_scorer": "Saka (1 goal, 1 assist)",
    "shots_ratio": "14-9 in favor of Arsenal"
  },
  "match_rating": 7.2,
  "word_count": 250
}
```

### 4.6 Output: WinProbability

```json
{
  "fixture": "Arsenal vs Chelsea",
  "date": "2025-12-15",
  "probabilities": {
    "home_win": 0.52,
    "draw": 0.24,
    "away_win": 0.24
  },
  "confidence": "medium",
  "sample_size": 15,
  "factors": {
    "home_advantage": 0.08,
    "form_differential": 0.06,
    "head_to_head_bias": 0.04,
    "league_position_gap": 0.03
  },
  "disclaimer": "These probabilities are statistical estimates based on historical data and do not guarantee outcomes. This is an educational project and should not be used for betting or gambling decisions."
}
```

---

## 5. Guardrails

| Guardrail | Scope | Rule |
|-----------|-------|------|
| Data integrity | Agent 1 | Never fabricate match events or statistics not present in source data |
| Completeness check | Agent 1 | Flag matches with <80% data completeness and warn downstream agents |
| Neutral tone | Agent 2 | Summaries must be factually neutral — no fan bias, no sensationalism |
| Source grounding | Agent 2 | Every claim in the summary must trace to a specific data point in `StructuredMatchData` |
| Probability validity | Agent 3 | All three probabilities (home/draw/away) must sum to exactly 1.0 |
| Sample size disclosure | Agent 3 | Must state how many historical matches the prediction is based on |
| Gambling disclaimer | Agent 3 | Every prediction output must include the standard disclaimer |
| No injury speculation | All | Do not speculate about player injuries unless explicitly in the source data |
| Audit trail | All | Every agent output must be logged to shared memory for traceability |

---

## 6. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Data parsing accuracy | >95% of fields correctly extracted | Compare parsed output to raw input |
| Summary factual accuracy | 100% of claims grounded in data | Manual review: no hallucinated events |
| Summary readability | Flesch-Kincaid grade 8-12 | Automated readability scoring |
| Probability calibration | Predicted probabilities within ±10% of actual outcomes over 50+ matches | Brier score on historical validation set |
| Pipeline completion rate | 100% of valid inputs produce an output | No silent failures; all errors logged |
| End-to-end latency | <5 seconds per match (simulated) | Timer in orchestrator |

---

## 7. Technology Stack

- **Language**: Python 3.10+
- **LLM**: Any OpenAI-compatible API (GPT-4, Claude, etc.) — add API key where indicated
- **Data format**: JSON
- **Dependencies**: See `requirements.txt`
