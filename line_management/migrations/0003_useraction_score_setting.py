# Generated by Django 5.0.4 on 2024-10-15 02:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('line_management', '0002_useraction_line_friend'),
        ('score_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraction',
            name='score_setting',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='score_management.scoresetting'),
        ),
    ]