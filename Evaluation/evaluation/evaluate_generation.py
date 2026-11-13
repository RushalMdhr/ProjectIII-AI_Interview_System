
"""Evaluate answer generation using Ollama, common_questions.xlsx and LangSmith."""

from pathlib import Path

import pandas as pd
from langsmith import Client, evaluate

try:
    from .adapter import generate_answer
    from .metrics_generation import (
        exact_match,
        token_f1,
        bleu_score,
        rouge_scores,
    )
except ImportError:
    from adapter import generate_answer
    from metrics_generation import (
        exact_match,
        token_f1,
        bleu_score,
        rouge_scores,
    )


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "common_questions_improved.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "results" / "generation_results.csv"

DATASET_NAME = "Interview-Common-Questions-40-Improved"

# Evaluate only 5 questions initially
SAMPLE_SIZE = 40


def main():

    # Load Excel dataset
    data = pd.read_excel(DATA_FILE)
    data = data.dropna(subset=["question", "ideal_answer"])

    print("Total questions in Excel:", len(data))

    # Get only 5 examples from the existing LangSmith dataset
    client = Client()

    dataset = client.read_dataset(
        dataset_name=DATASET_NAME
    )

    examples = list(
        client.list_examples(
            dataset_id=dataset.id,
            limit=SAMPLE_SIZE
        )
    )

    print("Questions selected for evaluation:", len(examples))

    if not examples:
        print("No examples found in LangSmith dataset.")
        return

    local_results = []

    # Generate answers using Ollama
    def target(inputs):

        query = inputs["query"]

        print("\nQuestion:", query)

        response = generate_answer(query)

        answer = response["answer"]

        print("Generated answer:", answer)

        return {"answer": answer}

    # Compare generated answer with ideal answer
    def generation_evaluator(run, example):

        generated = run.outputs["answer"]
        reference = example.outputs["ideal_answer"]

        em = exact_match(reference, generated)
        f1 = token_f1(reference, generated)
        bleu = bleu_score(reference, generated)
        rouge = rouge_scores(reference, generated)

        local_results.append({
            "question": example.inputs["query"],
            "ideal_answer": reference,
            "generated_answer": generated,
            "exact_match": em,
            "token_f1": f1,
            "bleu": bleu,
            "rouge1": rouge["rouge1"],
            "rouge2": rouge["rouge2"],
            "rougeL": rouge["rougeL"]
        })

        return [
            {"key": "exact_match", "score": em},
            {"key": "token_f1", "score": f1},
            {"key": "bleu", "score": bleu},
            {"key": "rouge1", "score": rouge["rouge1"]},
            {"key": "rouge2", "score": rouge["rouge2"]},
            {"key": "rougeL", "score": rouge["rougeL"]}
        ]

    print("\nStarting generation evaluation...")

    # Sequential evaluation to reduce memory usage
    evaluate(
        target,
        data=examples,
        evaluators=[generation_evaluator],
        experiment_prefix="common-questions-generation",
        max_concurrency=1,
        metadata={
            "dataset_size": len(examples),
            "evaluation_type": "generation",
            "model": "llama3.2:latest"
        }
    )

    # Save results
    results_df = pd.DataFrame(local_results)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(OUTPUT_FILE, index=False)

    if results_df.empty:
        print("\nNo evaluation results were generated.")
        return

    print("\n========== GENERATION EVALUATION RESULTS ==========")

    print(
        results_df[
            [
                "exact_match",
                "token_f1",
                "bleu",
                "rouge1",
                "rouge2",
                "rougeL"
            ]
        ].mean()
    )

    print("\nEvaluated questions:", len(results_df))
    print("Saved to:", OUTPUT_FILE)
    print("LangSmith dataset:", DATASET_NAME)


if __name__ == "__main__":
    main()
