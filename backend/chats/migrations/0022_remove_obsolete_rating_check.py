from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chats", "0021_alter_interviewfeedback_feedback_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE "chats_interviewfeedback" '
                'DROP CONSTRAINT IF EXISTS '
                '"chats_interviewfeedback_rating_check"'
            ),
            reverse_sql=None,
        ),
    ]
