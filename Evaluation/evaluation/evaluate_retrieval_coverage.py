"""Analyze role and difficulty coverage in the evaluation CSV."""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "simple_questions_with_embeddings.csv"
OUTPUT_FILE = ROOT / "results" / "retrieval_coverage.csv"


def main():
    df = pd.read_csv(DATA_FILE)

    for column in ["role", "difficulty"]:
        if column not in df.columns:
            raise ValueError(f"Missing column: {column}")

        df[column] = df[column].fillna("Unknown").astype(str).str.strip()

    coverage = (
        df.groupby(["role", "difficulty"], dropna=False)
        .size()
        .reset_index(name="question_count")
        .sort_values(["role", "difficulty"])
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(OUTPUT_FILE, index=False)

    print("\n========== DATASET COVERAGE ==========")
    print(f"Total questions: {len(df)}")
    print(f"Unique roles: {df['role'].nunique()}")
    print(f"Unique difficulty levels: {df['difficulty'].nunique()}")

    print("\nQuestions per role and difficulty:")
    print(coverage.to_string(index=False))

    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
