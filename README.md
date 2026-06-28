# Soccer Sports Analytics — Multi-Agent System

> **Disclaimer**: This is an internship project meant for upskilling in agentic AI. It uses sample data and simulated API connections. Not intended for production, betting, or gambling use.

## Overview

An autonomous multi-agent system that generates soccer match summaries and predicts win probabilities for upcoming fixtures. Three specialized agents work in a pipeline architecture to process raw match data, produce natural-language reports, and compute outcome predictions.

## Project Structure

```
Soccer_Sports_Analytics/
├── Master.md                          # System design, schemas, guardrails
├── main.py                            # Orchestrator — routes requests through agents
├── requirements.txt                   # Python dependencies
├── README.md                          # This file
│
├── Agents/
│   ├── match_data_ingestion_agent/    # Agent 1: Parse & validate match feeds
│   │   ├── agent.md                   #   Specification
│   │   └── agent.py                   #   Implementation
│   ├── game_summary_agent/            # Agent 2: Generate match reports
│   │   ├── agent.md
│   │   └── agent.py
│   └── win_probability_agent/         # Agent 3: Predict match outcomes
│       ├── agent.md
│       └── agent.py
│
├── Skills/
│   ├── match_data_parsing/            # Validation & structuring rules
│   │   └── match_data_parsing.md
│   ├── summary_generation/            # Narrative template & tone guide
│   │   └── summary_generation.md
│   └── probability_calculation/       # Weighted factor model spec
│       └── probability_calculation.md
│
├── Memory/
│   ├── Memory.md                      # Memory index & description
│   ├── team_profiles.json             # Team metadata & rosters
│   ├── historical_results.json        # Past match results
│   ├── league_standings.json          # Current league table
│   └── audit_log.json                 # Agent output trail
│
└── Data/
    ├── sample_match_input.json        # Sample raw match for post-match pipeline
    └── sample_fixture_request.json    # Sample fixture for prediction pipeline
```

## Pipelines

**Post-match** (summary generation): Raw match JSON → Agent 1 → Agent 2 → Game Summary

**Pre-match** (win probability): Fixture request → Agent 1 → Agent 3 → Win Probability

## Running

```bash
python main.py
```

No external dependencies required for the sample run — uses only Python standard library.

## Extending

- Add a live data source API in Agent 1 (e.g., football-data.org)
- Replace the template-based summary in Agent 2 with an LLM API call
- Add more factors to the probability model in Agent 3 (injuries, weather, etc.)
- Expand memory with more teams/leagues
