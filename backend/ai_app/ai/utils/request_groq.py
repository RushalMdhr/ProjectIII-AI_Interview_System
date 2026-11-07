from groq import Groq
from django.conf import settings


def get_groq_client():
    api_key = getattr(settings, "GROQ_API_KEY", None)
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Set it before using the Groq provider."
        )
    return Groq(api_key=api_key)