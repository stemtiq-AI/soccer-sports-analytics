# Skill: Probability Calculation

> **Disclaimer**: This is an internship project meant for upskilling in agentic AI. Predictions are statistical estimates and must not be used for betting or gambling.

## Purpose

Computes win/draw/loss probabilities for upcoming soccer fixtures using a weighted factor model. Used by the Win Probability Agent (Agent 3).

## When to Use

- When a fixture prediction is requested
- After Agent 1 has built `TeamFormProfile` objects for both teams

## Capabilities

1. **Base rate initialization**: Starts from historical league-average outcome rates
2. **Home advantage calculation**: Adjusts based on the home team's home record
3. **Form differential**: Compares last-5 results between the two teams
4. **Head-to-head bias**: Adjusts based on recent meetings between the teams
5. **League position gap**: Adjusts based on table positions
6. **Normalization**: Ensures all probabilities sum to exactly 1.0

## Input Format

Two `TeamFormProfile` objects — see Master.md §4.4

## Output Format

`WinProbability` — see Master.md §4.6

## Model Specification

### Base Rates (Historical League Averages)

| Outcome | Base Rate |
|---------|-----------|
| Home Win | 0.46 |
| Draw | 0.27 |
| Away Win | 0.27 |

### Factor Adjustments

| Factor | Range | Calculation |
|--------|-------|-------------|
| Home advantage | 0.00 to 0.10 | `home_win_rate_at_home × 0.10` |
| Form differential | -0.08 to +0.08 | `(home_form_score - away_form_score) × 0.08` |
| Head-to-head bias | -0.05 to +0.05 | `(h2h_win_rate - h2h_loss_rate) × 0.05` |
| League position gap | -0.05 to +0.05 | `(away_position - home_position) / 19 × 0.05` |

Form score: W=1.0, D=0.5, L=0.0, averaged over last 5 matches.

### Normalization

After adjustments, all probabilities are floored at 0.05 (no outcome can be <5%) and then normalized to sum to 1.0.

### Confidence Levels

| Sample Size | Confidence |
|-------------|------------|
| < 5 matches | Low |
| 5–15 matches | Medium |
| > 15 matches | High |

## Validation Rules

- All three probabilities must sum to 1.0 (tolerance: 0.001)
- Minimum 2 historical matches per team required
- Sample size must be disclosed in output
- Gambling disclaimer must be present in every output
- No single probability can be below 0.05 or above 0.90

## Limitations

- Does not account for individual player availability (injuries, suspensions)
- Does not factor in weather, referee assignments, or travel distance
- Small sample sizes produce low-confidence predictions
- Model assumes league-average base rates; may not reflect specific league dynamics
