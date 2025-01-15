# Generated by Django 4.2.11 on 2024-07-19 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0013_user_email_verified_user_family_name_user_given_name_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="rh_employee",
        ),
        migrations.AddField(
            model_name="user",
            name="rh_internal",
            field=models.BooleanField(default=False),
        ),
    ]
