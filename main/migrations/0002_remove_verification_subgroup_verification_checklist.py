# Generated by Django 5.1.5 on 2025-01-31 14:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="verification",
            name="subgroup",
        ),
        migrations.AddField(
            model_name="verification",
            name="checklist",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="verifications",
                to="main.checklistbase",
            ),
            preserve_default=False,
        ),
    ]
