
"""Evaluate retrieval using common_questions.xlsx and LangSmith."""

from pathlib import Path
import os

import pandas as pd
from langsmith import Client, evaluate

try:
    from .adapter import retrieve
    from .metrics_retrieval import (
        precision_at_k,
        recall_at_k,
        reciprocal_rank,
        f1_score,
        average_similarity,
    )
except ImportError:
    from adapter import retrieve
    from metrics_retrieval import (
        precision_at_k,
        recall_at_k,
        reciprocal_rank,
        f1_score,
        average_similarity,
    )


K = 5

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "common_questions.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "results" / "retrieval_results.csv"

DATASET_NAME = "Interview-Common-Questions-40"
PROJECT_NAME = "Interview-System-Evaluation"


def is_relevant(retrieved_question, relevant_questions):

    retrieved_question = retrieved_question.lower().strip()

    for expected in relevant_questions:
        if retrieved_question == expected.lower().strip():
            return 1

    return 0


def main():

    # Check LangSmith configuration
    if not os.getenv("LANGSMITH_API_KEY"):
        raise ValueError("LANGSMITH_API_KEY is not configured.")

    # Load the 40 common questions
    data = pd.read_excel(DATA_FILE)

    data = data.dropna(subset=["question"])

    print("Total questions:", len(data))

    # Create or reuse LangSmith dataset
    client = Client()

    existing_datasets = list(
        client.list_datasets(dataset_name=DATASET_NAME)
    )

    if existing_datasets:
        dataset = existing_datasets[0]
        print("Using existing LangSmith dataset:", DATASET_NAME)

    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="40 common interview questions with ideal answers."
        )

        print("Created LangSmith dataset:", DATASET_NAME)

    # Add examples only when the dataset is empty
    existing_examples = list(
        client.list_examples(dataset_id=dataset.id)
    )

    if not existing_examples:

        inputs = []
        outputs = []

        for _, row in data.iterrows():

            question = str(row["question"]).strip()

            inputs.append({
                "query": question
            })

            outputs.append({
                "relevant_questions": [question],
                "ideal_answer": str(row["ideal_answer"]),
                "roles": str(row["roles"]),
                "keywords": str(row["keywords"])
            })

        client.create_examples(
            inputs=inputs,
            outputs=outputs,
            dataset_id=dataset.id
        )

        print("Added", len(inputs), "examples to LangSmith.")

    else:
        print("Dataset already contains examples. Skipping upload.")

    # Target function: retrieves questions from your system
    def target(inputs):

        query = inputs["query"]

        print("\nQuery:", query)

        response = retrieve(query, top_k=K)

        return {
            "results": response["results"]
        }

    # LangSmith evaluator
    def retrieval_evaluator(run, example):

        retrieved_results = run.outputs["results"]

        relevant_questions = example.outputs["relevant_questions"]

        relevance = []
        similarity_scores = []

        for result in retrieved_results:

            question = result["question"]

            score = result.get("score", 0)

            relevant = is_relevant(
                question,
                relevant_questions
            )

            relevance.append(relevant)
            similarity_scores.append(score)

            print(
                question,
                "Score:", score,
                "Relevant:", relevant
            )

        precision = precision_at_k(relevance, K)

        recall = recall_at_k(
            relevance,
            len(relevant_questions),
            K
        )

        mrr = reciprocal_rank(relevance)

        f1 = f1_score(precision, recall)

        similarity = average_similarity(similarity_scores)

        # Store results for the local CSV
        local_results.append({

            "query": example.inputs["query"],

            "precision@5": precision,

            "recall@5": recall,

            "mrr": mrr,

            "f1": f1,

            "average_similarity": similarity

        })

        return [
            {"key": "precision@5", "score": precision},
            {"key": "recall@5", "score": recall},
            {"key": "mrr", "score": mrr},
            {"key": "f1", "score": f1},
            {"key": "average_similarity", "score": similarity}
        ]

    local_results = []

    print("\nStarting LangSmith retrieval evaluation...")

    # Run evaluation and record experiment in LangSmith
    evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[retrieval_evaluator],
        experiment_prefix="common-questions-retrieval",
        metadata={
            "top_k": K,
            "dataset_size": len(data),
            "evaluation_type": "retrieval"
        }
    )

    # Save local results
    results_df = pd.DataFrame(local_results)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n========== FINAL RESULTS ==========")

    print(
        results_df[
            [
                "precision@5",
                "recall@5",
                "mrr",
                "f1",
                "average_similarity"
            ]
        ].mean()
    )

    print("\nTotal evaluated questions:", len(results_df))

    print("\nSaved to:", OUTPUT_FILE)

    print("\nLangSmith dataset:", DATASET_NAME)

    print("LangSmith project:", PROJECT_NAME)


if __name__ == "__main__":
    main()
