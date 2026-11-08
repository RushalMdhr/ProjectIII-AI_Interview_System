from django.db import models
from pgvector.django import VectorField
from common.RAG_models import InterviewQuestions

class ChatSession(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]
    STATE_CHOICES = [
        ("introduction", "introduction"),
        ("experience", "experience"),
        ("behavioral", "behavioral"),
        ("situational", "situational"),
        ("technical", "technical"),
    ]
    USE_CASE_CHOICES = [
        ("general_chat", "General Chat"),
        ("career_guidance", "Career Guidance"),
        ("interview_assessment", "Interview Assessment"),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, default='New Chat Session')
    use_case = models.CharField(max_length=30, choices=USE_CASE_CHOICES, default="general_chat", db_index=True)
    
    current_state = models.CharField(max_length=30, choices=STATE_CHOICES, default="INTRODUCTION", db_index=True)
    # Interview-only fields
    interview_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="medium")
    current_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="easy")

    # current_state = models.CharField(max_length=10, choices=STATE_CHOICES, default="welcome") # adding an attribute to know in which state the interview is in

    max_questions = models.PositiveSmallIntegerField(default=8)
    question_count = models.PositiveSmallIntegerField(default=0)
    interview_role = models.CharField(max_length=150, null=True, blank=True)
    halted = models.BooleanField(default=False)
    average_overall_score = models.FloatField(null=True, blank=True)
    average_introduction_score = models.FloatField(null=True, blank=True)
    average_experience_score = models.FloatField(null=True, blank=True)
    average_behavioral_score = models.FloatField(null=True, blank=True)
    average_situational_score = models.FloatField(null=True, blank=True)
    average_technical_score = models.FloatField(null=True, blank=True)

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

class InterviewFeedback(models.Model):
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='interview_feedbacks'
    )
    asked_questions = models.ForeignKey(InterviewQuestions, null=True, on_delete=models.SET_NULL)
    question_text = models.TextField(blank=True) #hamro question sodheko wala
    # question_answer = models.TextField(blank=True) # expected answer from the question
    candidate_answer = models.TextField(blank=True) # answer from the candidate
    category = models.CharField(
        max_length=30,
        choices=ChatSession.STATE_CHOICES,
        blank=True,
        default="",
    )
    
    prefetched_question_ids = models.JSONField(default=list, blank=True)
    rating = models.JSONField(null=True, blank=True)
    average_overall_score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    question_difficulty = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        unique_together = ('session','asked_questions')

    def __str__(self):
        return f"Feedback {self.id} - Session {self.session_id}"