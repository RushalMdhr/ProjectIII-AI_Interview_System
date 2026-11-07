from ai_app.ai.llm import ai, groq_ai
from ai_app.models import AIUseCaseConfig

def generate_response(use_case, message, user=None, session=None):
    configured = AIUseCaseConfig.objects.filter(use_case=use_case).first()
    provider = configured.provider if configured else (
        "groq" if use_case == "career_guidance" else "ollama"
    )
    model = configured.model if configured else None

    if provider == "groq":
        return groq_ai(
            message,
            model=model or "openai/gpt-oss-120b",
            user=user,
            use_case=use_case,
            session=session,
        )
    if provider == "ollama":
        return ai(
            message,
            model=model or "llama3.2:latest",
            user=user,
            use_case=use_case,
            session=session,
        )

    raise ValueError(f"Unknown use case: {use_case}")