# Generated by Django 5.1.5 on 2025-02-03 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_alter_subgroupentry_verification_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="company_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
