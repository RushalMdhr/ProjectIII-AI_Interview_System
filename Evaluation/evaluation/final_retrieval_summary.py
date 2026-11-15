from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "results" / "production_retrieval_detailed_results.csv"
OUTPUT_FILE = ROOT / "results" / "retrieval_final_summary.csv"

df = pd.read_csv(INPUT_FILE)

total = len(df)
successful = (df["retrieval_status"] == "success").sum()
no_candidates = (df["retrieval_status"] == "no_candidates").sum()
availability = successful / total if total else 0
average_candidates = df["prefetched_candidate_count"].mean() if total else 0

summary = pd.DataFrame([
    ["Total Test Questions", total],
    ["Successful Retrievals", successful],
    ["Retrieval Availability", f"{availability:.4f}"],
    ["Average Prefetched Candidates", f"{average_candidates:.2f}"],
    ["No-Candidate Cases", no_candidates],
], columns=["Metric", "Value"])

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUTPUT_FILE, index=False)

print("\n========== FINAL RETRIEVAL EVALUATION ==========")
print(summary.to_string(index=False))
print(f"\nSaved to: {OUTPUT_FILE}")
