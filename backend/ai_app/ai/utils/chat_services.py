from ai_app.ai.llm import ai, groq_ai

def generate_response(use_case,message):
    if use_case == "general_chat":
        return ai(message)
    elif use_case == "career_guidance":
        return groq_ai(message)
    elif use_case == "interview_assessment":
        return ai(message)

    raise ValueError(f"Unknown use case: {use_case}")