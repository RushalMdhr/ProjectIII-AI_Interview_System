from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ModelPricing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(choices=[("groq", "Groq"), ("ollama", "Ollama")], max_length=20)),
                ("model", models.CharField(max_length=150)),
                ("input_cost_per_million_tokens", models.DecimalField(decimal_places=8, default=0, max_digits=12)),
                ("output_cost_per_million_tokens", models.DecimalField(decimal_places=8, default=0, max_digits=12)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("provider", "model")},
        ),
        migrations.CreateModel(
            name="AIRequestLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(choices=[("groq", "Groq"), ("ollama", "Ollama")], db_index=True, max_length=20)),
                ("model", models.CharField(db_index=True, max_length=150)),
                ("use_case", models.CharField(choices=[("general_chat", "General Chat"), ("career_guidance", "Career Guidance"), ("interview_assessment", "Interview Assessment")], db_index=True, default="general_chat", max_length=30)),
                ("input_tokens", models.PositiveIntegerField(default=0)),
                ("output_tokens", models.PositiveIntegerField(default=0)),
                ("total_tokens", models.PositiveIntegerField(default=0)),
                ("estimated_cost", models.DecimalField(blank=True, decimal_places=8, max_digits=12, null=True)),
                ("response_time_ms", models.PositiveIntegerField(blank=True, null=True)),
                ("success", models.BooleanField(db_index=True, default=False)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ai_request_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddConstraint(
            model_name="modelpricing",
            constraint=models.UniqueConstraint(fields=("provider", "model"), name="unique_ai_model_pricing"),
        ),
        migrations.AddIndex(
            model_name="airequestlog",
            index=models.Index(fields=("provider", "model", "created_at"), name="ai_app_aireq_provide_3c1a6e_idx"),
        ),
        migrations.AddIndex(
            model_name="airequestlog",
            index=models.Index(fields=("use_case", "created_at"), name="ai_app_aireq_use_case_97df9a_idx"),
        ),
    ]
