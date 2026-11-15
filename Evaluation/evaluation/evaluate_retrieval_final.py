import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "simple_questions_with_embeddings.csv"
OUTPUT_FILE = ROOT / "results" / "retrieval_final_results.csv"
DETAIL_FILE = ROOT / "results" / "retrieval_final_details.csv"

TOP_K = 5


def parse_list(value):
    if isinstance(value, list):
        return value
    if pd.isna(value):
        return []
    try:
        return ast.literal_eval(str(value))
    except (ValueError, SyntaxError):
        return []


def cosine_similarity(a, b):
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0.0
    return float(np.dot(a, b) / denominator)


def main():
    df = pd.read_csv(DATA_FILE)

    df["embedding"] = df["embedding"].apply(
        lambda value: np.array(json.loads(value), dtype=float)
    )
    df["categories"] = df["categories"].apply(parse_list)
    df["keywords"] = df["keywords"].apply(parse_list)

    details = []

    for i, query in df.iterrows():
        query_categories = {
            str(x).lower() for x in query["categories"]
        }
        query_keywords = {
            str(x).lower() for x in query["keywords"]
        }

        candidates = []

        for j, candidate in df.iterrows():
            if i == j:
                continue

            similarity = cosine_similarity(
                query["embedding"],
                candidate["embedding"]
            )

            candidate_categories = {
                str(x).lower() for x in candidate["categories"]
            }
            candidate_keywords = {
                str(x).lower() for x in candidate["keywords"]
            }

            relevant = bool(
                query_categories & candidate_categories
                or query_keywords & candidate_keywords
            )

            candidates.append({
                "index": j,
                "similarity": similarity,
                "relevant": relevant,
            })

        candidates.sort(
            key=lambda x: x["similarity"],
            reverse=True
        )

        top_results = candidates[:TOP_K]

        relevant_total = sum(
            item["relevant"] for item in candidates
        )
        relevant_retrieved = sum(
            item["relevant"] for item in top_results
        )

        precision = relevant_retrieved / TOP_K
        recall = (
            relevant_retrieved / relevant_total
            if relevant_total else 0
        )

        reciprocal_rank = 0

        for rank, item in enumerate(top_results, start=1):
            if item["relevant"]:
                reciprocal_rank = 1 / rank
                break

        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall else 0
        )

        average_similarity = np.mean([
            item["similarity"] for item in top_results
        ])

        details.append({
            "question": query["question"],
            "similarity_score": average_similarity,
            "precision_at_5": precision,
            "recall_at_5": recall,
            "mrr": reciprocal_rank,
            "f1": f1,
            "relevant_total": relevant_total,
            "relevant_retrieved": relevant_retrieved,
        })

    result = pd.DataFrame(details)

    metrics = [
        ("Similarity Score", "similarity_score"),
        ("Precision@5", "precision_at_5"),
        ("Recall@5", "recall_at_5"),
        ("Mean Reciprocal Rank", "mrr"),
        ("F1 Score", "f1"),
    ]

    summary = pd.DataFrame([
        {
            "Metric": name,
            "Average Score": result[column].mean()
        }
        for name, column in metrics
    ])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(DETAIL_FILE, index=False)
    summary.to_csv(OUTPUT_FILE, index=False)

    print("\n========== FINAL RETRIEVAL EVALUATION ==========")
    print("Total test questions:", len(result))
    print(summary.to_string(index=False))
    print("\nDetailed results:", DETAIL_FILE)
    print("Final summary:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
