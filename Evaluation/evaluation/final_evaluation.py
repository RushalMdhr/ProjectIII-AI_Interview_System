from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FINAL = RESULTS / "final"

FINAL.mkdir(parents=True, exist_ok=True)

# ---------------- RETRIEVAL ----------------

retrieval_file = RESULTS / "production_retrieval_detailed_results.csv"
retrieval = pd.read_csv(retrieval_file)

total = len(retrieval)
successful = (retrieval["retrieval_status"] == "success").sum()
no_candidates = (retrieval["retrieval_status"] == "no_candidates").sum()

retrieval_summary = pd.DataFrame([
    ["Total Test Questions", total],
    ["Successful Retrievals", successful],
    ["Retrieval Availability", f"{successful / total:.4f}" if total else "0"],
    ["Average Prefetched Candidates",
     f"{retrieval['prefetched_candidate_count'].mean():.2f}" if total else "0"],
    ["No-Candidate Cases", no_candidates],
], columns=["Metric", "Average Score"])

retrieval_summary.to_csv(
    FINAL / "retrieval_final_results.csv", index=False
)

# Retrieval chart: percentage-based measures only
availability = successful / total if total else 0
no_candidate_rate = no_candidates / total if total else 0
candidate_fill = (
    retrieval["prefetched_candidate_count"].mean() / 3 if total else 0
)

plt.figure(figsize=(8, 5))
plt.bar(
    ["Retrieval Availability", "Candidate Fill Rate", "No-Candidate Rate"],
    [availability, candidate_fill, no_candidate_rate]
)
plt.ylim(0, 1.1)
plt.ylabel("Score")
plt.title("Retrieval Evaluation Results")
plt.xticks(rotation=15, ha="right")
plt.tight_layout()
plt.savefig(FINAL / "retrieval_metrics.png", dpi=300)
plt.close()

# ---------------- GENERATION ----------------

generation_file = RESULTS / "generation_results.csv"
generation = pd.read_csv(generation_file)

metrics = [
    "exact_match",
    "token_f1",
    "bleu",
    "rouge1",
    "rouge2",
    "rougeL",
]

generation_summary = pd.DataFrame([
    [metric.replace("_", " ").upper(), generation[metric].mean()]
    for metric in metrics
], columns=["Metric", "Average Score"])

generation_summary["Average Score"] = (
    generation_summary["Average Score"].round(6)
)

generation_summary.to_csv(
    FINAL / "generation_final_results.csv", index=False
)

plt.figure(figsize=(9, 5))
plt.bar(
    generation_summary["Metric"],
    generation_summary["Average Score"]
)
plt.ylim(0, 1.0)
plt.ylabel("Average Score")
plt.title("Generation Evaluation Results")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig(FINAL / "generation_metrics.png", dpi=300)
plt.close()

# ---------------- FINAL OUTPUT ----------------

print("\n========== FINAL RETRIEVAL RESULTS ==========")
print(retrieval_summary.to_string(index=False))

print("\n========== FINAL GENERATION RESULTS ==========")
print(generation_summary.to_string(index=False))

print("\nFinal files saved in:", FINAL)
