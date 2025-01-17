# Generated by Django 5.0.4 on 2024-10-16 04:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('line_management', '0010_remove_linesettings_destination'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='linesettings',
            name='user',
            field=models.OneToOneField(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='line_settings', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
