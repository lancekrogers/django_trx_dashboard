# Generated by Django 4.2.7 on 2025-06-17 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wallets", "0004_add_dark_theme_preference"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="usersettings",
            name="dark_theme",
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="mock_data_enabled",
            field=models.BooleanField(default=True),
        ),
    ]
