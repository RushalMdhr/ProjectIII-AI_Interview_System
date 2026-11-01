# chat/serializers.py

from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'session',
            'user_content',
            'assistant_content',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'assistant_content',
            'created_at',
        ]


class ChatSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatSession
        fields = [
            'id',
            'title',
            'use_case',
            'interview_difficulty',
            'current_difficulty',
            'max_questions',
            'question_count',
            'interview_role',
            'halted',
            'created_at',
            'updated_at',
            'archived',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]