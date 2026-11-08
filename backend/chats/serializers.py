# chat/serializers.py

from rest_framework import serializers
from .models import ChatSession, ChatMessage, InterviewFeedback


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    expected_answer = serializers.SerializerMethodField()

    def get_expected_answer(self, instance):
        if instance.asked_questions_id:
            return instance.asked_questions.answer
        return ''

    class Meta:
        model = InterviewFeedback
        fields = [
            'id',
            'session',
            'question_text',
            'expected_answer',
            'candidate_answer',
            'category',
            'rating',
            'average_overall_score',
            'feedback',
            'question_difficulty',
            'created_at',
        ]
        read_only_fields = fields


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
            'average_overall_score',
            'average_introduction_score',
            'average_experience_score',
            'average_behavioral_score',
            'average_situational_score',
            'average_technical_score',
            'created_at',
            'updated_at',
            'archived',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'average_overall_score',
            'average_introduction_score',
            'average_experience_score',
            'average_behavioral_score',
            'average_situational_score',
            'average_technical_score',
        ]