import time

from ai_app.ai.utils.request_ollama import ollama_client
from .utils.request_groq import get_groq_client
from ai_app.services import record_request


def ai(msg, model="llama3.2:latest", tools="auto", user=None, use_case="general_chat", session=None):
    started_at = time.perf_counter()
    try:
        response = ollama_client.chat(
            model=model,
            messages=msg,
            options={"temperature": 0.1},
        )
    except Exception as error:
        record_request(
            provider="ollama", model=model, use_case=use_case,
            started_at=started_at, error=error, user=user,
            session=session,
        )
        raise
    record_request(
        provider="ollama", model=model, use_case=use_case,
        started_at=started_at, response=response, user=user,
        session=session,
    )
    return response["message"]["content"]


def groq_ai(msg, model="openai/gpt-oss-120b", user=None, use_case="general_chat", session=None):
    started_at = time.perf_counter()
    try:
        response = get_groq_client().chat.completions.create(
            model=model,
            messages=msg,
            temperature=0.7,
        )
    except Exception as error:
        record_request(
            provider="groq", model=model, use_case=use_case,
            started_at=started_at, error=error, user=user,
            session=session,
        )
        raise
    record_request(
        provider="groq", model=model, use_case=use_case,
        started_at=started_at, response=response, user=user,
        session=session,
    )
    return response.choices[0].message.content
