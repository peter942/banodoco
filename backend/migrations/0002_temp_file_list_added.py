# Generated by Django 4.2.1 on 2023-07-26 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0001_initial_setup"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="temp_file_list",
            field=models.TextField(default=None, null=True),
        ),
    ]
