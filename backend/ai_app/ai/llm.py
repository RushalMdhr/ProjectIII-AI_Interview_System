from ai_app.ai.utils.request_ollama import ollama_client
from .utils.request_groq import groq_client

def ai(msg, model="llama3.2:latest", tools=None, format=None, temperature=0.1):
    # 1. Ollama requires 'tools' to be None if not used, not 'auto'
    if tools == 'auto':
        tools = None  # Or define the actual list of tool schemas here
        
    kwargs = {
        "model": model,
        "messages": msg,
        "options": {
            "temperature": temperature,
        }
    }

    # 2. Only pass 'format' and 'tools' if they are actually provided
    if format:
        kwargs["format"] = format
    if tools:
        kwargs["tools"] = tools

    response = ollama_client.chat(**kwargs)
    
    # 3. Handle potential tool calls vs text responses
    return response["message"]["content"]

def groq_ai(msg, model="openai/gpt-oss-120b"):
    response = groq_client.chat.completions.create(
        model=model,
        messages=msg,
        temperature=0.7,
    )

    return response.choices[0].message.content
