from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_app", "0003_airequestlog_session"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIUseCaseConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "use_case",
                    models.CharField(
                        choices=[
                            ("general_chat", "General Chat"),
                            ("career_guidance", "Career Guidance"),
                            ("interview_assessment", "Interview Assessment"),
                        ],
                        max_length=30,
                        unique=True,
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[("groq", "Groq"), ("ollama", "Ollama")],
                        max_length=20,
                    ),
                ),
                ("model", models.CharField(max_length=150)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("use_case",)},
        ),
    ]