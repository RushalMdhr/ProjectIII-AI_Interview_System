"""Evaluate interview question retrieval using the evaluation CSV."""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "simple_questions_with_embeddings.csv"
RESULT_FILE = ROOT / "results" / "production_retrieval_detailed_results.csv"

TOP_K = 3


def normalize(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def evaluate():
    df = pd.read_csv(DATA_FILE)

    required = {"question", "role", "difficulty"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing CSV columns: {missing}")

    df = df.dropna(subset=["question"]).reset_index(drop=True)

    results = []

    for query_index, query_row in df.iterrows():

        target_role = normalize(query_row["role"])
        target_difficulty = normalize(query_row["difficulty"])

        # Match the production role condition:
        # selected role OR common.
        role_candidates = df[
            df["role"].apply(
                lambda value: normalize(value) in {target_role, "common"}
            )
        ].copy()

        # Exclude the current question, simulating an already-asked question.
        role_candidates = role_candidates[
            role_candidates.index != query_index
        ]

        # Apply difficulty filtering only when difficulty is provided.
        difficulty_filter_active = bool(target_difficulty)

        if difficulty_filter_active:
            difficulty_candidates = role_candidates[
                role_candidates["difficulty"].apply(
                    lambda value: normalize(value) == target_difficulty
                )
            ]
        else:
            difficulty_candidates = role_candidates.copy()

        fallback_used = False

        if not difficulty_candidates.empty:
            candidates = difficulty_candidates
        else:
            # Production fallback: retry without difficulty filtering.
            candidates = role_candidates
            fallback_used = difficulty_filter_active

        prefetched = candidates.head(TOP_K)

        # Check the returned candidates against the retrieval rules.
        role_compliant = all(
            normalize(row["role"]) in {target_role, "common"}
            for _, row in prefetched.iterrows()
        )

        asked_question_excluded = (
            query_index not in prefetched.index
        )

        if not difficulty_filter_active or fallback_used:
            difficulty_compliant = True
        else:
            difficulty_compliant = all(
                normalize(value) == target_difficulty
                for value in prefetched["difficulty"]
            )

        if prefetched.empty:
            status = "no_candidates"
        else:
            status = "success"

        results.append({
            "query": query_row["question"],
            "role": query_row["role"],
            "difficulty": query_row["difficulty"],
            "role_candidate_count": len(role_candidates),
            "difficulty_candidate_count": len(difficulty_candidates),
            "prefetched_candidate_count": len(prefetched),
            "candidate_questions": " || ".join(
                prefetched["question"].astype(str)
            ),
            "role_compliant": role_compliant,
            "difficulty_compliant": difficulty_compliant,
            "asked_question_excluded": asked_question_excluded,
            "fallback_used": fallback_used,
            "retrieval_status": status,
        })

    result_df = pd.DataFrame(results)

    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(RESULT_FILE, index=False)

    total = len(result_df)
    successful = (result_df["retrieval_status"] == "success").sum()

    print("\n========== DETAILED RETRIEVAL EVALUATION ==========")
    print(f"Total test questions: {total}")
    print(f"Successful retrievals: {successful}")
    print(f"Retrieval availability: {successful / total:.4f}")
    print(
        "Role compliance: "
        f"{result_df['role_compliant'].mean():.4f}"
    )
    print(
        "Difficulty compliance: "
        f"{result_df['difficulty_compliant'].mean():.4f}"
    )
    print(
        "Previously asked question exclusion: "
        f"{result_df['asked_question_excluded'].mean():.4f}"
    )
    print(
        "Difficulty fallback count: "
        f"{result_df['fallback_used'].sum()}"
    )
    print(
        "Average prefetched candidates: "
        f"{result_df['prefetched_candidate_count'].mean():.2f}"
    )
    print(
        "No-candidate cases: "
        f"{(result_df['retrieval_status'] == 'no_candidates').sum()}"
    )

    print(f"\nDetailed results saved to: {RESULT_FILE}")


if __name__ == "__main__":
    evaluate()
