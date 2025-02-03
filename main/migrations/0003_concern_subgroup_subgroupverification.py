# Generated by Django 5.1.5 on 2025-02-03 06:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_remove_verification_subgroup_verification_checklist"),
    ]

    operations = [
        migrations.AddField(
            model_name="concern",
            name="subgroup",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="main.subgroupentry",
            ),
        ),
        migrations.CreateModel(
            name="SubgroupVerification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "verifier_type",
                    models.CharField(
                        choices=[
                            ("supervisor", "Shift Supervisor"),
                            ("quality", "Quality Supervisor"),
                        ],
                        max_length=20,
                    ),
                ),
                ("verified_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("supervisor_verified", "Supervisor Verified"),
                            ("quality_verified", "Quality Verified"),
                            ("rejected", "Rejected"),
                        ],
                        max_length=20,
                    ),
                ),
                ("comments", models.TextField(blank=True)),
                (
                    "subgroup",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verifications",
                        to="main.subgroupentry",
                    ),
                ),
                (
                    "verified_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["verified_at"],
                "unique_together": {("subgroup", "verifier_type")},
            },
        ),
    ]
