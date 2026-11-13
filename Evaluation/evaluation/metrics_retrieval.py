"""Retrieval-oriented evaluation metrics."""
def precision_at_k(relevance, k):
    """
    Precision@K:
    Number of relevant retrieved items / K
    """

    if k == 0:
        return 0.0

    return sum(relevance[:k]) / k


def recall_at_k(relevance, total_relevant, k):
    """
    Recall@K:
    Relevant retrieved items / total relevant items
    """

    if total_relevant == 0:
        return 0.0

    return sum(relevance[:k]) / total_relevant


def reciprocal_rank(relevance):
    """
    Reciprocal rank of the first relevant result.
    """

    for position, value in enumerate(relevance, start=1):

        if value == 1:
            return 1.0 / position

    return 0.0


def f1_score(precision, recall):
    """
    F1 score from precision and recall.
    """

    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
        / (precision + recall)
    )


def average_similarity(scores):
    """
    Average similarity score of retrieved results.
    """

    if not scores:
        return 0.0

    return sum(scores) / len(scores)