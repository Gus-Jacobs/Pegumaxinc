# Generated by Django 5.2.2 on 2025-06-18 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_monitor', '0002_botstatus_botactivitylog_acknowledged_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='botactivitylog',
            name='bot_id',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='botstatus',
            name='bot_id',
            field=models.CharField(default='freelance-bot-main', max_length=100, unique=True),
        ),
    ]
