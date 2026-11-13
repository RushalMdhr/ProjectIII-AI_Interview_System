"""Generation-oriented evaluation metrics."""
import re

from nltk.translate.bleu_score import (
    sentence_bleu,
    SmoothingFunction
)

from rouge_score import rouge_scorer


def normalize_text(text):
    """
    Normalize text before comparison.
    """

    text = str(text).lower().strip()

    text = re.sub(r"\s+", " ", text)

    return text


def exact_match(reference, generated):
    """
    Exact Match after basic normalization.
    """

    reference = normalize_text(reference)
    generated = normalize_text(generated)

    return 1 if reference == generated else 0


def token_f1(reference, generated):
    """
    Token-level F1 between reference and generated answer.
    """

    reference_tokens = normalize_text(reference).split()
    generated_tokens = normalize_text(generated).split()

    if not reference_tokens or not generated_tokens:
        return 0.0

    reference_counts = {}

    for token in reference_tokens:
        reference_counts[token] = (
            reference_counts.get(token, 0) + 1
        )

    generated_counts = {}

    for token in generated_tokens:
        generated_counts[token] = (
            generated_counts.get(token, 0) + 1
        )

    common = 0

    for token in generated_counts:

        if token in reference_counts:

            common += min(
                generated_counts[token],
                reference_counts[token]
            )

    if common == 0:
        return 0.0

    precision = common / len(generated_tokens)

    recall = common / len(reference_tokens)

    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
        / (precision + recall)
    )


def bleu_score(reference, generated):
    """
    BLEU score.
    """

    reference_tokens = normalize_text(reference).split()
    generated_tokens = normalize_text(generated).split()

    if not reference_tokens or not generated_tokens:
        return 0.0

    smoothie = SmoothingFunction().method1

    return sentence_bleu(
        [reference_tokens],
        generated_tokens,
        smoothing_function=smoothie
    )


def rouge_scores(reference, generated):
    """
    ROUGE-1, ROUGE-2 and ROUGE-L.
    """

    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL"],
        use_stemmer=True
    )

    scores = scorer.score(
        normalize_text(reference),
        normalize_text(generated)
    )

    return {
        "rouge1": scores["rouge1"].fmeasure,
        "rouge2": scores["rouge2"].fmeasure,
        "rougeL": scores["rougeL"].fmeasure
    }