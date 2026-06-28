"""
Agent 1: Match Data Ingestion Agent
Parses raw match feeds into structured data for downstream agents.

Disclaimer: This is an internship project meant for upskilling in agentic AI.
"""

import json
import os
from datetime import datetime
from typing import Optional

# Add your LLM API key here
# API_KEY = "your-api-key-here"

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Memory")


def load_memory(filename: str) -> dict:
    """Load a JSON file from shared memory."""
    filepath = os.path.join(MEMORY_DIR, filename)
    with open(filepath, "r") as f:
        return json.load(f)


def save_memory(filename: str, data: dict) -> None:
    """Save a JSON file to shared memory."""
    filepath = os.path.join(MEMORY_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def log_to_audit(agent_name: str, action: str, input_summary: str, output_summary: str, warnings: list) -> None:
    """Append an entry to the audit log."""
    audit = load_memory("audit_log.json")
    audit["log"].append({
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "action": action,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "warnings": warnings
    })
    save_memory("audit_log.json", audit)


def validate_player(player_name: str, lineup: list, roster: list) -> bool:
    """Check if a player exists in lineup or roster."""
    return player_name in lineup or player_name in roster


def compute_completeness(match_data: dict) -> tuple[float, list]:
    """Compute data completeness score and list missing fields."""
    required_fields = [
        "match_id", "league", "date", "home_team", "away_team",
        "events", "stats", "result"
    ]
    stat_fields = ["possession", "shots", "shots_on_target", "corners", "fouls"]

    missing = []
    for field in required_fields:
        if field not in match_data or match_data[field] is None:
            missing.append(field)

    if "stats" in match_data and match_data["stats"]:
        for side in ["home", "away"]:
            if side in match_data["stats"]:
                for stat in stat_fields:
                    if stat not in match_data["stats"][side]:
                        missing.append(f"stats.{side}.{stat}")

    total_checks = len(required_fields) + len(stat_fields) * 2
    score = (total_checks - len(missing)) / total_checks
    return round(score, 2), missing


def extract_goals(events: list, home_team: str, away_team: str) -> list:
    """Extract and structure goal events."""
    goals = []
    for event in events:
        if event.get("type") == "goal":
            team_name = home_team if event.get("team") == "home" else away_team
            goals.append({
                "minute": event.get("minute"),
                "scorer": event.get("player"),
                "assist": event.get("assist"),
                "team": team_name
            })
    return sorted(goals, key=lambda g: g["minute"])


def extract_cards(events: list, home_team: str, away_team: str) -> dict:
    """Extract yellow and red card events."""
    yellow = []
    red = []
    for event in events:
        if event.get("type") == "yellow_card":
            team_name = home_team if event.get("team") == "home" else away_team
            yellow.append({
                "player": event.get("player"),
                "team": team_name,
                "minute": event.get("minute")
            })
        elif event.get("type") == "red_card":
            team_name = home_team if event.get("team") == "home" else away_team
            red.append({
                "player": event.get("player"),
                "team": team_name,
                "minute": event.get("minute")
            })
    return {"yellow": yellow, "red": red}


def identify_key_moments(goals: list, cards: dict) -> list:
    """Identify key match moments from goals and cards."""
    moments = []
    for goal in goals:
        desc = f"Goal by {goal['scorer']} ({goal['team']})"
        if goal.get("assist"):
            desc += f", assisted by {goal['assist']}"
        moments.append({"minute": goal["minute"], "description": desc})

    for card in cards.get("red", []):
        moments.append({
            "minute": card["minute"],
            "description": f"Red card for {card['player']} ({card['team']})"
        })

    return sorted(moments, key=lambda m: m["minute"])


def process_match(raw_match: dict) -> dict:
    """
    Main function: process a raw match event feed into StructuredMatchData.
    """
    warnings = []

    home_team = raw_match["home_team"]["name"]
    away_team = raw_match["away_team"]["name"]

    # Validate players against lineups
    home_lineup = raw_match["home_team"].get("lineup", [])
    away_lineup = raw_match["away_team"].get("lineup", [])

    # Load roster from memory for additional validation
    try:
        profiles = load_memory("team_profiles.json")
        team_map = {t["name"]: t.get("roster", []) for t in profiles.get("teams", [])}
        home_roster = team_map.get(home_team, [])
        away_roster = team_map.get(away_team, [])
    except FileNotFoundError:
        home_roster, away_roster = [], []
        warnings.append("team_profiles.json not found — skipping roster validation")

    for event in raw_match.get("events", []):
        player = event.get("player")
        team_side = event.get("team")
        if player:
            lineup = home_lineup if team_side == "home" else away_lineup
            roster = home_roster if team_side == "home" else away_roster
            if not validate_player(player, lineup, roster):
                warnings.append(f"Player '{player}' not found in lineup or roster")

    # Extract structured data
    goals = extract_goals(raw_match.get("events", []), home_team, away_team)
    cards = extract_cards(raw_match.get("events", []), home_team, away_team)
    key_moments = identify_key_moments(goals, cards)

    # Compute completeness
    completeness_score, missing_fields = compute_completeness(raw_match)
    if completeness_score < 0.80:
        warnings.append(f"Low data completeness: {completeness_score}")

    # Build stats
    raw_stats = raw_match.get("stats", {})
    stats = {}
    for stat_name in ["possession", "shots", "shots_on_target", "corners", "fouls"]:
        home_val = raw_stats.get("home", {}).get(stat_name)
        away_val = raw_stats.get("away", {}).get(stat_name)
        stats[stat_name] = {"home": home_val, "away": away_val}

    # Build output
    result = raw_match.get("result", {})
    structured = {
        "match_id": raw_match.get("match_id"),
        "league": raw_match.get("league"),
        "date": raw_match.get("date"),
        "home_team": home_team,
        "away_team": away_team,
        "score": {"home": result.get("home_goals"), "away": result.get("away_goals")},
        "goals": goals,
        "cards": cards,
        "stats": stats,
        "key_moments": key_moments,
        "data_quality": {
            "completeness_score": completeness_score,
            "missing_fields": missing_fields
        }
    }

    # Log to audit
    log_to_audit(
        agent_name="MatchDataIngestionAgent",
        action="process_match",
        input_summary=f"Match {raw_match.get('match_id')}",
        output_summary=f"Score: {result.get('home_goals')}-{result.get('away_goals')}, {len(goals)} goals, completeness: {completeness_score}",
        warnings=warnings
    )

    # Append to historical results
    try:
        history = load_memory("historical_results.json")
        existing_ids = {r["match_id"] for r in history.get("results", [])}
        if structured["match_id"] not in existing_ids:
            history["results"].append({
                "match_id": structured["match_id"],
                "date": structured["date"],
                "home_team": structured["home_team"],
                "away_team": structured["away_team"],
                "score": structured["score"],
                "scorers": {
                    "home": [g["scorer"] for g in goals if g["team"] == home_team],
                    "away": [g["scorer"] for g in goals if g["team"] == away_team]
                },
                "stats": {
                    "possession": stats.get("possession", {}),
                    "shots": stats.get("shots", {})
                }
            })
            save_memory("historical_results.json", history)
    except FileNotFoundError:
        warnings.append("historical_results.json not found — skipping history update")

    return structured


def build_team_form(team_name: str, opponent_name: str, league: str) -> Optional[dict]:
    """
    Build a TeamFormProfile for prediction requests.
    Reads historical results and standings from memory.
    """
    warnings = []

    try:
        history = load_memory("historical_results.json")
        standings = load_memory("league_standings.json")
    except FileNotFoundError as e:
        return {"error": f"Memory file not found: {e}"}

    # Filter results for this team
    team_results = []
    for match in history.get("results", []):
        if match["home_team"] == team_name or match["away_team"] == team_name:
            team_results.append(match)

    # Sort by date descending
    team_results.sort(key=lambda m: m["date"], reverse=True)

    if not team_results:
        return {"error": f"No historical data found for {team_name}"}

    # Compute overall record
    record = {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0}
    home_record = {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0}
    last_5_results = []
    last_5_gf = 0
    last_5_ga = 0

    for i, match in enumerate(team_results):
        is_home = match["home_team"] == team_name
        gf = match["score"]["home"] if is_home else match["score"]["away"]
        ga = match["score"]["away"] if is_home else match["score"]["home"]

        record["played"] += 1
        record["gf"] += gf
        record["ga"] += ga

        if gf > ga:
            record["won"] += 1
            result_char = "W"
        elif gf == ga:
            record["drawn"] += 1
            result_char = "D"
        else:
            record["lost"] += 1
            result_char = "L"

        if is_home:
            home_record["played"] += 1
            home_record["gf"] += gf
            home_record["ga"] += ga
            if gf > ga:
                home_record["won"] += 1
            elif gf == ga:
                home_record["drawn"] += 1
            else:
                home_record["lost"] += 1

        if i < 5:
            last_5_results.append(result_char)
            last_5_gf += gf
            last_5_ga += ga

    # Head-to-head
    h2h_matches = [m for m in team_results if m["home_team"] == opponent_name or m["away_team"] == opponent_name]
    h2h_last5 = h2h_matches[:5]
    h2h_wins, h2h_draws, h2h_losses = 0, 0, 0
    h2h_details = []

    for match in h2h_last5:
        is_home = match["home_team"] == team_name
        gf = match["score"]["home"] if is_home else match["score"]["away"]
        ga = match["score"]["away"] if is_home else match["score"]["home"]
        score_str = f"{match['score']['home']}-{match['score']['away']}"

        if gf > ga:
            h2h_wins += 1
            res = "W"
        elif gf == ga:
            h2h_draws += 1
            res = "D"
        else:
            h2h_losses += 1
            res = "L"

        h2h_details.append({
            "date": match["date"],
            "home": match["home_team"],
            "away": match["away_team"],
            "score": score_str,
            "result": res
        })

    # League position
    team_standing = None
    for entry in standings.get("standings", []):
        if entry["team"] == team_name:
            team_standing = entry
            break

    profile = {
        "team": team_name,
        "league": league,
        "season": standings.get("season", "unknown"),
        "overall_record": record,
        "home_record": home_record,
        "last_5": last_5_results,
        "last_5_goals_scored": last_5_gf,
        "last_5_goals_conceded": last_5_ga,
        "league_position": team_standing["position"] if team_standing else None,
        "points": team_standing["points"] if team_standing else None,
        "head_to_head_vs_opponent": {
            "last_5_meetings": h2h_details,
            "wins": h2h_wins,
            "draws": h2h_draws,
            "losses": h2h_losses
        }
    }

    log_to_audit(
        agent_name="MatchDataIngestionAgent",
        action="build_team_form",
        input_summary=f"{team_name} vs {opponent_name}",
        output_summary=f"Record: {record['won']}W-{record['drawn']}D-{record['lost']}L, Position: {profile['league_position']}",
        warnings=warnings
    )

    return profile


# --- Sample usage ---

SAMPLE_RAW_MATCH = {
    "match_id": "PL-2025-GW04-LIV-ARS",
    "league": "Premier League",
    "season": "2025-26",
    "gameweek": 4,
    "date": "2025-09-13",
    "venue": "Anfield",
    "home_team": {
        "name": "Liverpool",
        "lineup": ["Alisson", "Alexander-Arnold", "Van Dijk", "Konate", "Robertson",
                    "Mac Allister", "Szoboszlai", "Gravenberch", "Salah", "Gakpo", "Nunez"],
        "formation": "4-3-3"
    },
    "away_team": {
        "name": "Arsenal",
        "lineup": ["Raya", "White", "Saliba", "Gabriel", "Timber",
                    "Rice", "Odegaard", "Havertz", "Saka", "Martinelli", "Jesus"],
        "formation": "4-3-3"
    },
    "events": [
        {"minute": 12, "type": "goal", "team": "home", "player": "Salah", "assist": "Alexander-Arnold"},
        {"minute": 34, "type": "yellow_card", "team": "away", "player": "Rice"},
        {"minute": 55, "type": "goal", "team": "away", "player": "Saka", "assist": "Odegaard"},
        {"minute": 72, "type": "goal", "team": "home", "player": "Nunez", "assist": "Salah"},
        {"minute": 80, "type": "substitution", "team": "away", "player_in": "Nketiah", "player_out": "Jesus"}
    ],
    "stats": {
        "home": {"possession": 54, "shots": 15, "shots_on_target": 7, "corners": 6, "fouls": 10},
        "away": {"possession": 46, "shots": 11, "shots_on_target": 5, "corners": 5, "fouls": 13}
    },
    "result": {"home_goals": 2, "away_goals": 1}
}


if __name__ == "__main__":
    print("=" * 60)
    print("Match Data Ingestion Agent — Sample Run")
    print("=" * 60)

    # Post-match processing
    print("\n--- Post-match processing ---")
    structured = process_match(SAMPLE_RAW_MATCH)
    print(json.dumps(structured, indent=2))

    # Pre-match form profile
    print("\n--- Pre-match team form ---")
    form = build_team_form("Arsenal", "Chelsea", "Premier League")
    print(json.dumps(form, indent=2))
