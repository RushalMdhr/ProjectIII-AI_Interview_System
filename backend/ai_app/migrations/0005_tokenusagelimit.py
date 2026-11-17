from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("ai_app", "0004_aiusecaseconfig"),
    ]

    operations = [
        migrations.CreateModel(
            name="TokenUsageLimit",
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
                    "token_limit",
                    models.PositiveIntegerField(default=100000),
                ),
                (
                    "window_minutes",
                    models.PositiveIntegerField(default=1440),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Token usage limit",
                "verbose_name_plural": "Token usage limit",
            },
        ),
    ]
