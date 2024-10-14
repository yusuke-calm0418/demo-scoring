# Generated by Django 5.0.4 on 2024-10-14 07:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('score_management', '0015_delete_userscore'),
        # ('user_management', '0002_company_customuser_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='scoresetting',
            name='company',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='score_settings', to='user_management.company'),
            preserve_default=False,
        ),
    ]