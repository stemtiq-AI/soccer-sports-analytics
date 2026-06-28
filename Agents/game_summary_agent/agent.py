"""
Agent 2: Game Summary Generation Agent
Generates natural-language match summaries from structured match data.

Disclaimer: This is an internship project meant for upskilling in agentic AI.
"""

import json
import os
from datetime import datetime

# Add your LLM API key here
# API_KEY = "your-api-key-here"

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Memory")


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
        "agent": "GameSummaryAgent",
        "action": action,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "warnings": warnings
    })
    save_memory("audit_log.json", audit)


def generate_headline(match_data: dict) -> str:
    """Generate a concise match headline."""
    home = match_data["home_team"]
    away = match_data["away_team"]
    h_goals = match_data["score"]["home"]
    a_goals = match_data["score"]["away"]

    if h_goals > a_goals:
        verb = "edge past" if h_goals - a_goals == 1 else "defeat"
        return f"{home} {verb} {away} {h_goals}-{a_goals} at home"
    elif a_goals > h_goals:
        verb = "edge past" if a_goals - h_goals == 1 else "defeat"
        return f"{away} {verb} {home} {a_goals}-{h_goals} away"
    else:
        return f"{home} and {away} share the spoils in {h_goals}-{a_goals} draw"


def calculate_match_rating(match_data: dict) -> float:
    """Rate match excitement 1-10 based on goals, drama, and closeness."""
    total_goals = match_data["score"]["home"] + match_data["score"]["away"]
    goal_diff = abs(match_data["score"]["home"] - match_data["score"]["away"])
    red_cards = len(match_data.get("cards", {}).get("red", []))

    # Base rating from goals
    rating = min(total_goals * 1.5, 6.0)

    # Bonus for close matches
    if goal_diff <= 1:
        rating += 1.5
    elif goal_diff == 0:
        rating += 2.0

    # Bonus for red cards (drama)
    rating += red_cards * 0.5

    # Bonus for late goals (after minute 80)
    late_goals = sum(1 for g in match_data.get("goals", []) if g["minute"] >= 80)
    rating += late_goals * 0.8

    return round(min(max(rating, 1.0), 10.0), 1)


def get_standings_context(team_name: str) -> dict | None:
    """Get team's current league position from memory."""
    try:
        standings = load_memory("league_standings.json")
        for entry in standings.get("standings", []):
            if entry["team"] == team_name:
                return entry
    except FileNotFoundError:
        pass
    return None


def build_summary_body(match_data: dict) -> str:
    """
    Build the narrative summary body.

    In a production system, this would call an LLM API to generate
    natural-language text. Here we use a template-based approach
    as a demonstration.
    """
    # --- In production, replace this block with an LLM API call ---
    # response = openai.ChatCompletion.create(
    #     model="gpt-4",
    #     messages=[
    #         {"role": "system", "content": SYSTEM_PROMPT},
    #         {"role": "user", "content": json.dumps(match_data)}
    #     ]
    # )
    # return response.choices[0].message.content
    # ---

    home = match_data["home_team"]
    away = match_data["away_team"]
    h_goals = match_data["score"]["home"]
    a_goals = match_data["score"]["away"]
    goals = match_data.get("goals", [])
    cards = match_data.get("cards", {})
    stats = match_data.get("stats", {})

    # Opening
    if h_goals > a_goals:
        result_text = f"{home} secured a {h_goals}-{a_goals} victory over {away}"
    elif a_goals > h_goals:
        result_text = f"{away} claimed a {a_goals}-{h_goals} win against {home}"
    else:
        result_text = f"{home} and {away} played out a {h_goals}-{a_goals} draw"

    league = match_data.get("league", "the league")
    date = match_data.get("date", "")
    opening = f"{result_text} in {league} action on {date}."

    # Standings context
    home_standing = get_standings_context(home)
    away_standing = get_standings_context(away)
    context = ""
    if home_standing and away_standing:
        context = (
            f" {home} sit {_ordinal(home_standing['position'])} in the table with "
            f"{home_standing['points']} points, while {away} are "
            f"{_ordinal(away_standing['position'])} on {away_standing['points']} points."
        )

    # Goal descriptions
    first_half_goals = [g for g in goals if g["minute"] <= 45]
    second_half_goals = [g for g in goals if g["minute"] > 45]

    first_half = ""
    if first_half_goals:
        descs = [_describe_goal(g) for g in first_half_goals]
        first_half = "The first half saw " + " ".join(descs)
    else:
        first_half = "The first half was a cagey affair with neither side finding the net."

    second_half = ""
    if second_half_goals:
        descs = [_describe_goal(g) for g in second_half_goals]
        second_half = "The second half brought more action. " + " ".join(descs)

    # Cards
    card_text = ""
    yellows = cards.get("yellow", [])
    reds = cards.get("red", [])
    if reds:
        red_descs = [f"{c['player']} ({c['team']}, {c['minute']}')" for c in reds]
        card_text += f" Red cards were shown to {', '.join(red_descs)}."
    if yellows:
        yellow_descs = [f"{c['player']} ({c['team']}, {c['minute']}')" for c in yellows]
        card_text += f" Yellow cards went to {', '.join(yellow_descs)}."

    # Stats
    poss = stats.get("possession", {})
    shots = stats.get("shots", {})
    stat_text = ""
    if poss.get("home") is not None:
        dominant = home if poss["home"] > poss["away"] else away
        stat_text = (
            f" {dominant} controlled possession with "
            f"{max(poss['home'], poss['away'])}% of the ball."
        )
    if shots.get("home") is not None:
        stat_text += (
            f" The shot count finished {shots['home']}-{shots['away']}"
            f" in {home if shots['home'] > shots['away'] else away}'s favor."
        )

    body = f"{opening}{context} {first_half} {second_half}{card_text}{stat_text}"
    return body.strip()


def _describe_goal(goal: dict) -> str:
    """Create a sentence describing a goal."""
    assist_text = f", set up by {goal['assist']}" if goal.get("assist") else ""
    return f"{goal['scorer']} found the net for {goal['team']} on {goal['minute']} minutes{assist_text}."


def _ordinal(n: int) -> str:
    """Convert integer to ordinal string."""
    if 11 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def extract_key_stats(match_data: dict) -> dict:
    """Extract top statistical highlights."""
    stats = match_data.get("stats", {})
    goals = match_data.get("goals", [])
    key = {}

    # Possession
    poss = stats.get("possession", {})
    if poss.get("home") is not None:
        dominant = match_data["home_team"] if poss["home"] > poss["away"] else match_data["away_team"]
        key["possession_dominant"] = f"{dominant} ({max(poss['home'], poss['away'])}%)"

    # Top scorer
    scorer_counts = {}
    for g in goals:
        name = g["scorer"]
        scorer_counts[name] = scorer_counts.get(name, 0) + 1
    if scorer_counts:
        top = max(scorer_counts, key=scorer_counts.get)
        assists = sum(1 for g in goals if g.get("assist") == top)
        parts = [f"{scorer_counts[top]} goal{'s' if scorer_counts[top] > 1 else ''}"]
        if assists:
            parts.append(f"{assists} assist{'s' if assists > 1 else ''}")
        key["top_performer"] = f"{top} ({', '.join(parts)})"

    # Shots
    shots = stats.get("shots", {})
    if shots.get("home") is not None:
        key["shots_ratio"] = f"{shots['home']}-{shots['away']} ({match_data['home_team']} vs {match_data['away_team']})"

    return key


def generate_summary(structured_match_data: dict) -> dict:
    """
    Main function: generate a complete game summary from structured match data.
    """
    warnings = []

    # Check data quality
    quality = structured_match_data.get("data_quality", {})
    if quality.get("completeness_score", 1.0) < 0.80:
        warnings.append("Data completeness below 80% — summary may be incomplete")

    headline = generate_headline(structured_match_data)
    body = build_summary_body(structured_match_data)
    key_stats = extract_key_stats(structured_match_data)
    rating = calculate_match_rating(structured_match_data)
    word_count = len(body.split())

    # Validate word count
    if word_count < 200:
        warnings.append(f"Summary below minimum length: {word_count} words")
    if word_count > 350:
        warnings.append(f"Summary exceeds maximum length: {word_count} words")

    summary = {
        "match_id": structured_match_data.get("match_id"),
        "headline": headline,
        "summary": body,
        "key_stats": key_stats,
        "match_rating": rating,
        "word_count": word_count
    }

    log_to_audit(
        action="generate_summary",
        input_summary=f"Match {structured_match_data.get('match_id')}",
        output_summary=f"Headline: {headline}, Rating: {rating}, Words: {word_count}",
        warnings=warnings
    )

    return summary


# --- Sample usage ---

SAMPLE_STRUCTURED_DATA = {
    "match_id": "PL-2025-GW04-LIV-ARS",
    "league": "Premier League",
    "date": "2025-09-13",
    "home_team": "Liverpool",
    "away_team": "Arsenal",
    "score": {"home": 2, "away": 1},
    "goals": [
        {"minute": 12, "scorer": "Salah", "assist": "Alexander-Arnold", "team": "Liverpool"},
        {"minute": 55, "scorer": "Saka", "assist": "Odegaard", "team": "Arsenal"},
        {"minute": 72, "scorer": "Nunez", "assist": "Salah", "team": "Liverpool"}
    ],
    "cards": {
        "yellow": [{"player": "Rice", "team": "Arsenal", "minute": 34}],
        "red": []
    },
    "stats": {
        "possession": {"home": 54, "away": 46},
        "shots": {"home": 15, "away": 11},
        "shots_on_target": {"home": 7, "away": 5},
        "corners": {"home": 6, "away": 5}
    },
    "key_moments": [
        {"minute": 12, "description": "Goal by Salah (Liverpool), assisted by Alexander-Arnold"},
        {"minute": 55, "description": "Goal by Saka (Arsenal), assisted by Odegaard"},
        {"minute": 72, "description": "Goal by Nunez (Liverpool), assisted by Salah"}
    ],
    "data_quality": {"completeness_score": 0.93, "missing_fields": ["fouls"]}
}


if __name__ == "__main__":
    print("=" * 60)
    print("Game Summary Agent — Sample Run")
    print("=" * 60)

    result = generate_summary(SAMPLE_STRUCTURED_DATA)
    print(json.dumps(result, indent=2))
