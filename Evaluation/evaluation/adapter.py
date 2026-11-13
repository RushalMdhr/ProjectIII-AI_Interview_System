"""Adapters for model and evaluation inputs."""
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import requests


# Change this later to your friend's real backend URL.
BASE_URL = "http://localhost:8000"
LOCAL_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "common_questions_improved.xlsx"



def _local_retrieve(query, top_k):
    """Retrieve similar questions locally, excluding the exact query."""

    questions = pd.read_excel(LOCAL_DATA_FILE)["question"].dropna().astype(str)
    query_words = set(query.lower().split())

    scored_questions = []

    for question in questions:

        # Exclude the exact query to prevent self-matching
        if question.lower().strip() == query.lower().strip():
            continue

        question_words = set(question.lower().split())

        overlap = len(query_words & question_words) / max(len(query_words), 1)

        similarity = SequenceMatcher(
            None,
            query.lower(),
            question.lower()
        ).ratio()

        score = (overlap + similarity) / 2

        scored_questions.append({
            "question": question,
            "score": score
        })

    scored_questions.sort(
        key=lambda result: result["score"],
        reverse=True
    )

    return {"results": scored_questions[:top_k]}



def retrieve(query, top_k=5):
    """
    Calls the project's retrieval API.

    The final project should provide an endpoint
    that returns retrieved documents/questions and
    their similarity scores.
    """

    response = requests.post(
        f"{BASE_URL}/api/evaluation/retrieve/",
        json={
            "query": query,
            "top_k": top_k
        },
        timeout=60
    )

    if response.status_code == 404:
        return _local_retrieve(query, top_k)

    response.raise_for_status()

    return response.json()


def generate_answer(query):
    """
    Calls the project's normal AI/RAG answer endpoint.
    """

    response = requests.post(
        f"{BASE_URL}/evaluation/generate/",
        json={
            "query": query
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()