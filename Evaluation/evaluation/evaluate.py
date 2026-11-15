
"""Evaluate retrieval using the new 40-question CSV dataset and LangSmith."""

from pathlib import Path
import os
import math

import pandas as pd
from dotenv import load_dotenv
from langsmith import Client, evaluate

try:
    from .adapter import retrieve
except ImportError:
    from adapter import retrieve


K = 5

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

DATA_FILE = (
    PROJECT_ROOT / "data" / "simple_questions_with_embeddings.csv"
)

OUTPUT_FILE = PROJECT_ROOT / "results" / "retrieval_results.csv"

DATASET_NAME = "Interview-Retrieval-40-CSV-v2"
PROJECT_NAME = "Interview-System-Evaluation"


def is_relevant(retrieved_question, relevant_questions):

    retrieved_question = retrieved_question.lower().strip()

    for expected in relevant_questions:
        if retrieved_question == expected.lower().strip():
            return 1

    return 0


def hit_at_k(relevance, k):
    return 1.0 if sum(relevance[:k]) > 0 else 0.0


def reciprocal_rank(relevance):

    for position, value in enumerate(relevance, start=1):
        if value == 1:
            return 1.0 / position

    return 0.0


def ndcg_at_k(relevance, k):

    dcg = sum(
        value / math.log2(position + 1)
        for position, value in enumerate(relevance[:k], start=1)
    )

    ideal_dcg = 1.0

    return dcg / ideal_dcg


def average_similarity(scores):

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def main():

    if not os.getenv("LANGSMITH_API_KEY"):
        raise ValueError("LANGSMITH_API_KEY is not configured.")

    # Load the new CSV dataset
    data = pd.read_csv(DATA_FILE)

    data = data.dropna(subset=["question"])

    print("Dataset:", DATA_FILE.name)
    print("Total questions:", len(data))

    # Create or reuse a new LangSmith dataset
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
            description="40 interview questions from the new CSV dataset."
        )

        print("Created LangSmith dataset:", DATASET_NAME)

    # Upload examples only if the dataset is empty
    existing_examples = list(
        client.list_examples(dataset_id=dataset.id)
    )

    if not existing_examples:

        inputs = []
        outputs = []

        for _, row in data.iterrows():

            question = str(row["question"]).strip()
            role = str(row["role"]).strip()
            difficulty = str(row["difficulty"]).strip()
            keywords = str(row["keywords"]).strip()

            # Use metadata instead of the original question as the query
            query = (
                f"Role: {role}. "
                f"Difficulty: {difficulty}. "
                f"Keywords: {keywords}"
            )

            inputs.append({
                "query": query
            })

            outputs.append({
                "relevant_questions": [question],
                "ideal_answer": str(row["ideal_answer"]),
                "role": role,
                "difficulty": difficulty,
                "keywords": keywords,
                "categories": str(row["categories"]),
                "weights": str(row["weights"])
            })

        client.create_examples(
            inputs=inputs,
            outputs=outputs,
            dataset_id=dataset.id
        )

        print("Added", len(inputs), "examples to LangSmith.")

    else:
        print(
            "Dataset already contains examples. "
            "Skipping upload."
        )

    local_results = []

    # Retrieval target function
    def target(inputs):

        query = inputs["query"]

        print("\nQuery:", query)

        response = retrieve(query, top_k=K)

        return {
            "results": response["results"]
        }

    # Retrieval evaluator
    def retrieval_evaluator(run, example):

        retrieved_results = run.outputs["results"]

        relevant_questions = example.outputs["relevant_questions"]

        relevance = []
        similarity_scores = []
        retrieved_questions = []

        for result in retrieved_results:

            question = result["question"]
            score = result.get("score", 0)

            relevant = is_relevant(
                question,
                relevant_questions
            )

            relevance.append(relevant)
            similarity_scores.append(score)
            retrieved_questions.append(question)

            print(
                question,
                "Score:", score,
                "Relevant:", relevant
            )

        hit1 = hit_at_k(relevance, 1)
        hit3 = hit_at_k(relevance, 3)
        hit5 = hit_at_k(relevance, 5)

        mrr = reciprocal_rank(relevance)
        ndcg = ndcg_at_k(relevance, K)
        similarity = average_similarity(similarity_scores)

        local_results.append({

            "query": example.inputs["query"],

            "expected_question": relevant_questions[0],

            "retrieved_questions": " | ".join(retrieved_questions),

            "hit@1": hit1,

            "hit@3": hit3,

            "hit@5": hit5,

            "mrr": mrr,

            "ndcg@5": ndcg,

            "average_similarity": similarity

        })

        return [
            {"key": "hit@1", "score": hit1},
            {"key": "hit@3", "score": hit3},
            {"key": "hit@5", "score": hit5},
            {"key": "mrr", "score": mrr},
            {"key": "ndcg@5", "score": ndcg},
            {"key": "average_similarity", "score": similarity}
        ]

    print("\nStarting LangSmith retrieval evaluation...")

    evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[retrieval_evaluator],
        experiment_prefix="new-csv-retrieval",
        metadata={
            "top_k": K,
            "dataset_size": len(data),
            "evaluation_type": "metadata-based retrieval",
            "dataset_file": DATA_FILE.name
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

    metric_columns = [
        "hit@1",
        "hit@3",
        "hit@5",
        "mrr",
        "ndcg@5",
        "average_similarity"
    ]

    print(results_df[metric_columns].mean())

    print("\nTotal evaluated questions:", len(results_df))
    print("Saved to:", OUTPUT_FILE)
    print("LangSmith dataset:", DATASET_NAME)
    print("LangSmith project:", PROJECT_NAME)


if __name__ == "__main__":
    main()
