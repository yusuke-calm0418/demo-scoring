# Generated by Django 5.0.4 on 2024-10-16 02:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('line_management', '0007_linesettings_liff_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='linesettings',
            name='destination',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]