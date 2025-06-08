from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0006_post_report_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='audit_status',
        ),
    ]
