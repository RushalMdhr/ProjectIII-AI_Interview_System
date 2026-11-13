from django.http import JsonResponse
from rest_framework.decorators import api_view

from ai_app.ai.llm import ai


@api_view(["POST"])
def evaluation_generate(request):
    try:
        question = request.data.get("query", "").strip()

        if not question:
            return JsonResponse({
                "success": False,
                "error": "Question is required."
            }, status=400)

        msg = [
            {
                "role": "system",
                "content": (
                    "You are a technical interview preparation assistant. "
                    "Answer the interview question accurately, clearly, "
                    "and professionally. Provide a concise but complete answer."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ]

        answer = ai(msg=msg, temperature=0.1)

        return JsonResponse({
            "success": True,
            "query": question,
            "answer": answer,
            "model": "llama3.2:latest"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)