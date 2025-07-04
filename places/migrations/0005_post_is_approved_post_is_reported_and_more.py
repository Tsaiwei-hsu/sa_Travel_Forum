# Generated by Django 5.1.1 on 2025-06-07 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('places', '0004_post_address_alter_post_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='post',
            name='is_reported',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='post',
            name='manual_reviewed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='post',
            name='report_reason',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='takedown_reason',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
