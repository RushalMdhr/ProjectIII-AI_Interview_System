
# views.py

import os

from django.http import JsonResponse
from django.db import connection
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import *
from ai_app.ai.utils.embeddings import embed_text
from ai_app.ai.llm import ai


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]

            cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
            vector_version = cursor.fetchone()

        return JsonResponse({
            "backend": "connected",
            "database": "connected",
            "postgres_version": db_version,
            "pgvector": vector_version[0] if vector_version else None,
        })

    except Exception:
        return JsonResponse({
            "backend": "connected",
            "database": "error",
            "error": "Internal server error",
        }, status=500)

def say_hello(request):
    try:
        return JsonResponse({
            "backend": "connected",
            "database": "connected",
            "Intern": "404 not found yet... 💀",
        })

    except Exception:
        return JsonResponse({
            "backend": "connected",
            "database": "error",
            "error": "Internal server error",
        }, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def chat(request):
    try:
        data = request.data
        content = data.get("content") or data.get("message", "") #yo ta fix hunxa timro colum sanga
        title = (data.get("title") or content[:255]).strip()

        if not content.strip():
            return JsonResponse({
                "success": False,
                "error": "Chat content is required."
            }, status=400)

        if not title:
            title = "Untitled chat"

        chat_message = ChatMessage.objects.create(
            user=request.user,
            title=title[:255],
            content=content,
        )

        # Here you can implement your chat logic, for example, calling an AI model or processing the message.
        
        # For demonstration purposes, we'll just echo the message back.
        response_message = f"Echo: {content}"

        return JsonResponse({
            "success": True,
            # "id": chat_message.id,
            "userId": request.user.id,
            "title": chat_message.title,
            "content": chat_message.content,
            "response": response_message,
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


# ========================================= simple embedding test ===========================
@api_view(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
def SimpleSave(request):
    try:
        print("Request reached here", flush=True)
        text = request.data.get("text")

        if not text.strip():
            return JsonResponse({
                "success": False,
                "error": "no text to embed"
            }, status=400)

        chat_message = SimpleTextEmbedding.objects.create(
            text=text,
            embedding=embed_text(text)
        )

        response_message = f"Echo: {text}"

        return JsonResponse({
            "success": True,
            "embeding": chat_message.text,
            "response": response_message,
        })
    except Exception as e:
        print(f'error __ : {e}')
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

# ========================================= simple query request to llama 3.2 ===========================

@api_view(['POST'])
def TalkToAi(request):
    try:
        print("Request reached here", flush=True)
        text = request.data.get("query")
        print("=================================")

        if not text.strip():
            return JsonResponse({
                "success": False,
                "error": "no text to embed"
            }, status=400)
        
        entries = SimpleTextEmbedding.objects.all()
        context = "\n".join([f"ID: {obj.id}, Text: {obj.text}" for obj in entries])

        dotenv_system_prompt = os.getenv("SYSTEM_CHAT_PROMPT","you are a helpful assistant")
        print(f"dotenv_system_prompt : {dotenv_system_prompt} , context : {context}", flush=True)
        sys_prompt= f"""prompt : {dotenv_system_prompt} , given the context : {context}"""

        msg = [
            {'role' : 'system' ,
              'content' : sys_prompt
            },
            {
                'role':'user',
                'content' : text
            },
            {
                'role':'assistent',
                'content' : text
            },
            {
                'role':'user',
                'content' : text
            },
            {
                'role':'user',
                'content' : text
            },
            {
                'role':'user',
                'content' : text
            },
              ]
        res = ai(msg=msg)


        return JsonResponse({
            "success": True,
            'res' : res.message.content,
            'dotenv_system_prompt' : dotenv_system_prompt,
        })
    except Exception as e:
        print(f'error __ : {e}')
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

