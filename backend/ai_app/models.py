from django.db import models
from django.conf import settings


class ModelPricing(models.Model):
    PROVIDER_CHOICES = (
        ("groq", "Groq"),
        ("ollama", "Ollama"),
    )

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    model = models.CharField(max_length=150)
    input_cost_per_million_tokens = models.DecimalField(
        max_digits=12, decimal_places=8, default=0
    )
    output_cost_per_million_tokens = models.DecimalField(
        max_digits=12, decimal_places=8, default=0
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "model"),
                name="unique_ai_model_pricing",
            ),
        ]
        ordering = ("provider", "model")

    def __str__(self):
        return f"{self.provider}/{self.model}"


class AIUseCaseConfig(models.Model):
    PROVIDER_CHOICES = ModelPricing.PROVIDER_CHOICES
    USE_CASE_CHOICES = (
        ("general_chat", "General Chat"),
        ("career_guidance", "Career Guidance"),
        ("interview_assessment", "Interview Assessment"),
    )

    use_case = models.CharField(max_length=30, choices=USE_CASE_CHOICES, unique=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    model = models.CharField(max_length=150)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("use_case",)

    def __str__(self):
        return f"{self.use_case}: {self.provider}/{self.model}"


class AIRequestLog(models.Model):
    PROVIDER_CHOICES = ModelPricing.PROVIDER_CHOICES
    USE_CASE_CHOICES = (
        ("general_chat", "General Chat"),
        ("career_guidance", "Career Guidance"),
        ("interview_assessment", "Interview Assessment"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_request_logs",
    )
    session = models.ForeignKey(
        "chats.ChatSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_request_logs",
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, db_index=True)
    model = models.CharField(max_length=150, db_index=True)
    use_case = models.CharField(
        max_length=30, choices=USE_CASE_CHOICES, default="general_chat", db_index=True
    )
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=8, null=True, blank=True
    )
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    success = models.BooleanField(default=False, db_index=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("provider", "model", "created_at")),
            models.Index(fields=("use_case", "created_at")),
        ]

    def __str__(self):
        return f"{self.provider}/{self.model} ({self.created_at:%Y-%m-%d %H:%M})"

# Create your models here.
