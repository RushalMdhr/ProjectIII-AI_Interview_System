from django.db import models
from pgvector.django import VectorField
from common.RAG_models import InterviewQuestions

class ChatSession(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]
    USE_CASE_CHOICES = [
        ("general_chat", "General Chat"),
        ("career_guidance", "Career Guidance"),
        ("interview_assessment", "Interview Assessment"),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, default='New Chat Session')
    use_case = models.CharField(max_length=30, choices=USE_CASE_CHOICES, default="general_chat", db_index=True)
    
    # Interview-only fields
    interview_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="medium")
    current_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="easy")
    max_questions = models.PositiveSmallIntegerField(default=8)
    question_count = models.PositiveSmallIntegerField(default=0)
    interview_role = models.CharField(max_length=150, null=True, blank=True)
    halted = models.BooleanField(default=False)
    
    archived = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'archived']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user}"


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    user_content = models.TextField(blank=True, null=True)
    assistant_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user_content_embedding = VectorField(dimensions=768, null=True, blank=True)

    def __str__(self):
        return f"Message {self.id} - Session {self.session.id}"


# class AskedQuestions(models.Model):
#     session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='asked_questions')
    
#     asked_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('session', 'question')
#         # db_table = 'AskedQuestions'

#     def __str__(self):
#         return f"Session {self.session.id} - Question {self.question.id}"

class InterviewFeedback(models.Model):
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='interview_feedbacks'
    )
    asked_questions = models.ForeignKey(InterviewQuestions, null=True, on_delete=models.SET_NULL)
    question_text = models.TextField(blank=True)
    question_answer = models.TextField(blank=True)
    candidate_answer = models.TextField(blank=True)
    # question_number = models.PositiveSmallIntegerField(null=True, blank=True)
    # message = models.ForeignKey(
    #     ChatMessage,
    #     on_delete=models.CASCADE,
    #     related_name='interview_feedbacks'
    # )
    # answer_message = models.ForeignKey(
    #     ChatMessage,
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name='interview_answers',
    # )
    prefetched_question_ids = models.JSONField(default=list, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    question_difficulty = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        unique_together = ('session','asked_questions')

    def __str__(self):
        return f"Feedback {self.id} - Session {self.session_id} - Message {self.message_id}"