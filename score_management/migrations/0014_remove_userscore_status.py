# Generated by Django 5.0.4 on 2024-10-10 08:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('score_management', '0013_remove_link_short_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userscore',
            name='status',
        ),
    ]