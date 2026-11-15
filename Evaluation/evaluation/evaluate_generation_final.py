from pathlib import Path
import time

import pandas as pd
import requests

try:
    from .metrics_generation import (
        exact_match,
        token_f1,
        bleu_score,
        rouge_scores,
    )
except ImportError:
    from metrics_generation import (
        exact_match,
        token_f1,
        bleu_score,
        rouge_scores,
    )

ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = ROOT / "data" / "simple_questions_with_embeddings.csv"
DETAIL_FILE = ROOT / "results" / "generation_final_details.csv"
SUMMARY_FILE = ROOT / "results" / "generation_final_results.csv"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:latest"


def generate_answer(question):
    prompt = f"""
You are a candidate answering an interview question.

Answer the following interview question naturally and professionally.
Keep the answer concise, around 3 to 5 sentences.
Give a direct, relevant answer without unnecessary introduction.
Do not use placeholders.

Interview question:
{question}

Your answer:
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 180
            },
            "keep_alive": "2m"
        },
        timeout=300
    )

    response.raise_for_status()

    answer = response.json().get("response", "").strip()

    if not answer:
        raise ValueError("Ollama returned an empty answer.")

    return answer


def main():
    data = pd.read_csv(DATA_FILE)
    data = data.dropna(subset=["question", "ideal_answer"])

    print("Dataset:", DATA_FILE.name)
    print("Questions to evaluate:", len(data))
    print("Model:", MODEL)

    results = []

    for index, row in data.iterrows():
        question = str(row["question"]).strip()
        reference = str(row["ideal_answer"]).strip()

        print(f"\nQuestion {len(results) + 1}/{len(data)}")
        print(question)

        generated = generate_answer(question)

        print("Generated answer:")
        print(generated)

        em = exact_match(reference, generated)
        f1 = token_f1(reference, generated)
        bleu = bleu_score(reference, generated)
        rouge = rouge_scores(reference, generated)

        results.append({
            "question": question,
            "ideal_answer": reference,
            "generated_answer": generated,
            "exact_match": em,
            "token_f1": f1,
            "bleu": bleu,
            "rouge1": rouge["rouge1"],
            "rouge2": rouge["rouge2"],
            "rougeL": rouge["rougeL"]
        })

        pd.DataFrame(results).to_csv(DETAIL_FILE, index=False)
        time.sleep(0.5)

    result_df = pd.DataFrame(results)

    metrics = [
        "exact_match",
        "token_f1",
        "bleu",
        "rouge1",
        "rouge2",
        "rougeL"
    ]

    summary = pd.DataFrame({
        "Metric": metrics,
        "Average Score": [
            result_df[metric].mean()
            for metric in metrics
        ]
    })

    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)

    result_df.to_csv(DETAIL_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    print("\n========== FINAL GENERATION EVALUATION ==========")
    print("Total evaluated questions:", len(result_df))
    print(summary.to_string(index=False))
    print("\nDetailed results:", DETAIL_FILE)
    print("Summary results:", SUMMARY_FILE)


if __name__ == "__main__":
    main()
