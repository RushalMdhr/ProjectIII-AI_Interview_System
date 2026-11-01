from ai_app.ai.utils.request_ollama import ollama_client
from .utils.request_groq import groq_client

def ai(msg,model="llama3.2:latest",tools='auto'):
    response = ollama_client.chat(
            model=model,
            messages=msg,
            options={
                "temperature": 0.1,      # Creative but not wild
                # "top_p": 0.9,            # Standard
                # "num_predict": 200,      # Short story (~200 tokens)
                # "num_ctx": 4096,         # Enough for context
                # "repeat_penalty": 1.1,   # Avoid repetition
                # "seed": 123,             # Reproducible
                # "mirostat": 1            # Adaptive creativity
            }
            )
    return response["message"]["content"]

def groq_ai(msg, model="openai/gpt-oss-120b"):
    response = groq_client.chat.completions.create(
        model=model,
        messages=msg,
        temperature=0.7,
    )

    return response.choices[0].message.content
