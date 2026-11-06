from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("ai_app", "0002_rename_ai_app_aireq_provide_3c1a6e_idx_ai_app_aire_provide_637aa0_idx_and_more"),
        ("chats", "0013_interviewfeedback_question_number_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="airequestlog",
            name="session",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ai_request_logs",
                to="chats.chatsession",
            ),
        ),
    ]