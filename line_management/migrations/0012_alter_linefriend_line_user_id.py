# Generated by Django 5.0.4 on 2024-10-16 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('line_management', '0011_alter_linesettings_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linefriend',
            name='line_user_id',
            field=models.CharField(max_length=255),
        ),
    ]
