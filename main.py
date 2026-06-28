"""
Soccer Sports Analytics — Orchestrator
Routes incoming requests through the appropriate agent pipeline.

Disclaimer: This is an internship project meant for upskilling in agentic AI.
Not intended for production use or gambling.
"""

import json
import sys
import time
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from Agents.match_data_ingestion_agent.agent import process_match, build_team_form
from Agents.game_summary_agent.agent import generate_summary
from Agents.win_probability_agent.agent import predict_outcome


def run_post_match_pipeline(raw_match: dict) -> dict:
    """
    Post-match pipeline: raw match data → structured data → game summary.
    Agent 1 → Agent 2
    """
    print("\n" + "=" * 60)
    print("POST-MATCH PIPELINE")
    print("=" * 60)

    start = time.time()

    # Step 1: Match Data Ingestion (Agent 1)
    print("\n[Agent 1] Ingesting match data...")
    structured_data = process_match(raw_match)
    print(f"  ✓ Match {structured_data['match_id']} processed")
    print(f"  ✓ Score: {structured_data['score']['home']}-{structured_data['score']['away']}")
    print(f"  ✓ Goals: {len(structured_data['goals'])}")
    print(f"  ✓ Data quality: {structured_data['data_quality']['completeness_score']}")

    # Step 2: Game Summary Generation (Agent 2)
    print("\n[Agent 2] Generating game summary...")
    summary = generate_summary(structured_data)
    print(f"  ✓ Headline: {summary['headline']}")
    print(f"  ✓ Match rating: {summary['match_rating']}/10")
    print(f"  ✓ Word count: {summary['word_count']}")

    elapsed = round(time.time() - start, 2)
    print(f"\n[Pipeline] Completed in {elapsed}s")

    return {
        "pipeline": "post_match",
        "structured_data": structured_data,
        "summary": summary,
        "elapsed_seconds": elapsed
    }


def run_prediction_pipeline(fixture_request: dict) -> dict:
    """
    Pre-match pipeline: fixture request → team form profiles → win probability.
    Agent 1 → Agent 3
    """
    print("\n" + "=" * 60)
    print("PREDICTION PIPELINE")
    print("=" * 60)

    start = time.time()

    home_team = fixture_request["home_team"]
    away_team = fixture_request["away_team"]
    league = fixture_request["league"]
    date = fixture_request.get("date", "")

    # Step 1: Build team form profiles (Agent 1)
    print(f"\n[Agent 1] Building form profile for {home_team}...")
    home_profile = build_team_form(home_team, away_team, league)
    if "error" in home_profile:
        print(f"  ✗ Error: {home_profile['error']}")
        return {"error": home_profile["error"]}
    print(f"  ✓ Record: {home_profile['overall_record']['won']}W-{home_profile['overall_record']['drawn']}D-{home_profile['overall_record']['lost']}L")
    print(f"  ✓ Position: {home_profile['league_position']}")

    print(f"\n[Agent 1] Building form profile for {away_team}...")
    away_profile = build_team_form(away_team, home_team, league)
    if "error" in away_profile:
        print(f"  ✗ Error: {away_profile['error']}")
        return {"error": away_profile["error"]}
    print(f"  ✓ Record: {away_profile['overall_record']['won']}W-{away_profile['overall_record']['drawn']}D-{away_profile['overall_record']['lost']}L")
    print(f"  ✓ Position: {away_profile['league_position']}")

    # Step 2: Win Probability Prediction (Agent 3)
    print(f"\n[Agent 3] Predicting outcome for {home_team} vs {away_team}...")
    prediction = predict_outcome(home_profile, away_profile, date)
    if "error" in prediction:
        print(f"  ✗ Error: {prediction['error']}")
        return {"error": prediction["error"]}

    probs = prediction["probabilities"]
    print(f"  ✓ Home win: {probs['home_win']:.0%}")
    print(f"  ✓ Draw:     {probs['draw']:.0%}")
    print(f"  ✓ Away win: {probs['away_win']:.0%}")
    print(f"  ✓ Confidence: {prediction['confidence']}")

    elapsed = round(time.time() - start, 2)
    print(f"\n[Pipeline] Completed in {elapsed}s")

    return {
        "pipeline": "prediction",
        "home_profile": home_profile,
        "away_profile": away_profile,
        "prediction": prediction,
        "elapsed_seconds": elapsed
    }


def main():
    """Run both pipelines with sample data."""
    print("=" * 60)
    print("SOCCER SPORTS ANALYTICS — MULTI-AGENT SYSTEM")
    print("=" * 60)
    print("\nDisclaimer: This is an internship project meant for")
    print("upskilling. Not for production or gambling use.\n")

    # Load sample data
    data_dir = os.path.join(os.path.dirname(__file__), "Data")

    # --- Pipeline 1: Post-match summary ---
    match_file = os.path.join(data_dir, "sample_match_input.json")
    with open(match_file, "r") as f:
        raw_match = json.load(f)

    post_match_result = run_post_match_pipeline(raw_match)

    print("\n" + "-" * 60)
    print("GENERATED SUMMARY:")
    print("-" * 60)
    print(f"\n{post_match_result['summary']['headline']}\n")
    print(post_match_result['summary']['summary'])

    # --- Pipeline 2: Pre-match prediction ---
    fixture_file = os.path.join(data_dir, "sample_fixture_request.json")
    with open(fixture_file, "r") as f:
        fixture = json.load(f)

    prediction_result = run_prediction_pipeline(fixture)

    if "error" not in prediction_result:
        print("\n" + "-" * 60)
        print("PREDICTION RESULT:")
        print("-" * 60)
        pred = prediction_result["prediction"]
        print(f"\n{pred['fixture']} — {pred['date']}")
        print(f"Home Win: {pred['probabilities']['home_win']:.0%}")
        print(f"Draw:     {pred['probabilities']['draw']:.0%}")
        print(f"Away Win: {pred['probabilities']['away_win']:.0%}")
        print(f"Confidence: {pred['confidence']} (based on {pred['sample_size']} matches)")
        print(f"\n{pred['disclaimer']}")


if __name__ == "__main__":
    main()
