from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chats", "0025_chatsession_current_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="interviewfeedback",
            name="average_overall_score",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
