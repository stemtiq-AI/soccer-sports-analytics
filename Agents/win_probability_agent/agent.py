"""
Agent 3: Win Probability Prediction Agent
Calculates win/draw/loss probabilities for upcoming fixtures.

Disclaimer: This is an internship project meant for upskilling in agentic AI.
Predictions are statistical estimates and should NOT be used for betting or gambling.
"""

import json
import os
from datetime import datetime

# Add your LLM API key here
# API_KEY = "your-api-key-here"

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Memory")

# Historical league-average base rates
BASE_RATES = {
    "home_win": 0.46,
    "draw": 0.27,
    "away_win": 0.27
}

DISCLAIMER = (
    "These probabilities are statistical estimates based on historical data "
    "and do not guarantee outcomes. This is an educational project and should "
    "not be used for betting or gambling decisions."
)


def load_memory(filename: str) -> dict:
    filepath = os.path.join(MEMORY_DIR, filename)
    with open(filepath, "r") as f:
        return json.load(f)


def save_memory(filename: str, data: dict) -> None:
    filepath = os.path.join(MEMORY_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def log_to_audit(action: str, input_summary: str, output_summary: str, warnings: list) -> None:
    audit = load_memory("audit_log.json")
    audit["log"].append({
        "timestamp": datetime.now().isoformat(),
        "agent": "WinProbabilityAgent",
        "action": action,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "warnings": warnings
    })
    save_memory("audit_log.json", audit)


def compute_form_score(last_5: list) -> float:
    """Convert last-5 results to a 0-1 score. W=1, D=0.5, L=0."""
    if not last_5:
        return 0.5
    values = {"W": 1.0, "D": 0.5, "L": 0.0}
    total = sum(values.get(r, 0.5) for r in last_5)
    return total / len(last_5)


def calculate_home_advantage(home_profile: dict) -> float:
    """Calculate home advantage adjustment (0.0 to 0.10)."""
    home_record = home_profile.get("home_record", {})
    played = home_record.get("played", 0)
    if played == 0:
        return 0.05  # Default moderate advantage

    win_rate = home_record.get("won", 0) / played
    # Scale: 0% home wins → 0.0 adjustment, 100% → 0.10
    return round(min(win_rate * 0.10, 0.10), 4)


def calculate_form_differential(home_profile: dict, away_profile: dict) -> float:
    """
    Calculate form differential adjustment.
    Positive = favors home, negative = favors away.
    Range: -0.08 to +0.08.
    """
    home_form = compute_form_score(home_profile.get("last_5", []))
    away_form = compute_form_score(away_profile.get("last_5", []))
    diff = home_form - away_form  # range: -1.0 to 1.0
    return round(diff * 0.08, 4)


def calculate_h2h_bias(home_profile: dict) -> float:
    """
    Calculate head-to-head bias.
    Positive = favors home, negative = favors away.
    Range: -0.05 to +0.05.
    """
    h2h = home_profile.get("head_to_head_vs_opponent", {})
    wins = h2h.get("wins", 0)
    losses = h2h.get("losses", 0)
    total = wins + losses + h2h.get("draws", 0)

    if total == 0:
        return 0.0

    win_rate = wins / total
    loss_rate = losses / total
    bias = (win_rate - loss_rate)  # range: -1.0 to 1.0
    return round(bias * 0.05, 4)


def calculate_position_gap(home_profile: dict, away_profile: dict) -> float:
    """
    Calculate league position gap adjustment.
    Positive = home is higher in table, negative = away is higher.
    Range: -0.05 to +0.05.
    """
    home_pos = home_profile.get("league_position")
    away_pos = away_profile.get("league_position")

    if home_pos is None or away_pos is None:
        return 0.0

    # Lower position number = higher in table
    gap = away_pos - home_pos  # positive if home is higher
    max_gap = 19  # max possible gap in a 20-team league
    normalized = gap / max_gap  # range: ~ -1.0 to 1.0
    return round(normalized * 0.05, 4)


def normalize_probabilities(probs: dict) -> dict:
    """Normalize probabilities to sum to exactly 1.0."""
    total = sum(probs.values())
    if total == 0:
        return {"home_win": 0.33, "draw": 0.34, "away_win": 0.33}
    return {k: round(v / total, 2) for k, v in probs.items()}


def determine_confidence(home_profile: dict, away_profile: dict) -> tuple[str, int]:
    """Determine confidence level based on sample size."""
    home_played = home_profile.get("overall_record", {}).get("played", 0)
    away_played = away_profile.get("overall_record", {}).get("played", 0)
    sample = min(home_played, away_played)

    if sample < 5:
        return "low", sample
    elif sample <= 15:
        return "medium", sample
    else:
        return "high", sample


def predict_outcome(home_profile: dict, away_profile: dict, fixture_date: str = "") -> dict:
    """
    Main function: predict win/draw/loss probabilities for a fixture.
    """
    warnings = []

    # Validate minimum data
    home_played = home_profile.get("overall_record", {}).get("played", 0)
    away_played = away_profile.get("overall_record", {}).get("played", 0)

    if home_played < 2 or away_played < 2:
        return {
            "error": "Insufficient historical data. Need at least 2 matches per team.",
            "home_matches": home_played,
            "away_matches": away_played
        }

    # Calculate factors
    home_adv = calculate_home_advantage(home_profile)
    form_diff = calculate_form_differential(home_profile, away_profile)
    h2h_bias = calculate_h2h_bias(home_profile)
    pos_gap = calculate_position_gap(home_profile, away_profile)

    # Apply adjustments to base rates
    raw_probs = {
        "home_win": BASE_RATES["home_win"] + home_adv + max(form_diff, 0) + max(h2h_bias, 0) + max(pos_gap, 0),
        "draw": BASE_RATES["draw"] - abs(form_diff) * 0.3 - abs(h2h_bias) * 0.2,
        "away_win": BASE_RATES["away_win"] - home_adv + max(-form_diff, 0) + max(-h2h_bias, 0) + max(-pos_gap, 0)
    }

    # Ensure no negative probabilities
    for key in raw_probs:
        raw_probs[key] = max(raw_probs[key], 0.05)

    # Normalize
    probs = normalize_probabilities(raw_probs)

    # Fix rounding to ensure exact sum of 1.0
    total = sum(probs.values())
    if total != 1.0:
        diff = round(1.0 - total, 2)
        probs["draw"] = round(probs["draw"] + diff, 2)

    # Validate sum
    prob_sum = sum(probs.values())
    if abs(prob_sum - 1.0) > 0.001:
        warnings.append(f"Probability sum {prob_sum} deviates from 1.0")

    confidence, sample_size = determine_confidence(home_profile, away_profile)

    home_team = home_profile.get("team", "Home")
    away_team = away_profile.get("team", "Away")

    result = {
        "fixture": f"{home_team} vs {away_team}",
        "date": fixture_date,
        "probabilities": probs,
        "confidence": confidence,
        "sample_size": sample_size,
        "factors": {
            "home_advantage": home_adv,
            "form_differential": form_diff,
            "head_to_head_bias": h2h_bias,
            "league_position_gap": pos_gap
        },
        "disclaimer": DISCLAIMER
    }

    log_to_audit(
        action="predict_outcome",
        input_summary=f"{home_team} vs {away_team} on {fixture_date}",
        output_summary=f"H:{probs['home_win']} D:{probs['draw']} A:{probs['away_win']} ({confidence})",
        warnings=warnings
    )

    return result


# --- Sample usage ---

SAMPLE_HOME_PROFILE = {
    "team": "Arsenal",
    "league": "Premier League",
    "season": "2025-26",
    "overall_record": {"played": 3, "won": 1, "drawn": 2, "lost": 0, "gf": 5, "ga": 4},
    "home_record": {"played": 2, "won": 1, "drawn": 1, "lost": 0, "gf": 4, "ga": 3},
    "last_5": ["W", "D", "D"],
    "last_5_goals_scored": 5,
    "last_5_goals_conceded": 4,
    "league_position": 3,
    "points": 5,
    "head_to_head_vs_opponent": {
        "last_5_meetings": [
            {"date": "2025-08-30", "home": "Arsenal", "away": "Chelsea", "score": "2-1", "result": "W"}
        ],
        "wins": 1, "draws": 0, "losses": 0
    }
}

SAMPLE_AWAY_PROFILE = {
    "team": "Chelsea",
    "league": "Premier League",
    "season": "2025-26",
    "overall_record": {"played": 3, "won": 0, "drawn": 0, "lost": 3, "gf": 2, "ga": 7},
    "home_record": {"played": 1, "won": 0, "drawn": 0, "lost": 1, "gf": 0, "ga": 2},
    "last_5": ["L", "L", "L"],
    "last_5_goals_scored": 2,
    "last_5_goals_conceded": 7,
    "league_position": 4,
    "points": 0,
    "head_to_head_vs_opponent": {
        "last_5_meetings": [
            {"date": "2025-08-30", "home": "Arsenal", "away": "Chelsea", "score": "2-1", "result": "L"}
        ],
        "wins": 0, "draws": 0, "losses": 1
    }
}


if __name__ == "__main__":
    print("=" * 60)
    print("Win Probability Agent — Sample Run")
    print("=" * 60)

    prediction = predict_outcome(SAMPLE_HOME_PROFILE, SAMPLE_AWAY_PROFILE, "2025-12-15")
    print(json.dumps(prediction, indent=2))
