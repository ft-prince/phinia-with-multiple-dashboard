# Generated by Django 5.1.5 on 2025-02-03 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_user_company_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="checklistbase",
            name="bottom_tool_id",
            field=models.CharField(
                choices=[
                    ("FMA-03-35-T06", "FMA-03-35-T06 (P703/U704/SA/FD)"),
                    ("FMA-03-35-T08", "FMA-03-35-T08 (Gnome)"),
                ],
                max_length=100,
                verbose_name="Bottom Tool ID",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="error_proofing_verification",
            field=models.CharField(
                choices=[("Yes", "Yes"), ("No", "No")],
                max_length=3,
                verbose_name="All Error proofing / Error detection verification done",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="good_bad_master_verification",
            field=models.CharField(
                choices=[("OK", "OK"), ("NG", "NG")],
                max_length=2,
                verbose_name="Good and Bad master verification (refer EPVS)",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="line_pressure",
            field=models.FloatField(help_text="Recommended Range: 4.5 - 5.5 bar"),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="master_verification_lvdt",
            field=models.CharField(
                choices=[("OK", "OK"), ("NG", "NG")],
                max_length=2,
                verbose_name="Master Verification for LVDT",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="oring_condition",
            field=models.CharField(
                choices=[("OK", "OK"), ("NG", "NG")],
                max_length=2,
                verbose_name="O-ring condition (UV Flow check sealing area) (O-ring सील की स्थिति सही होनी चाहिए)",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="retainer_id_lubrication",
            field=models.CharField(
                choices=[("OK", "OK"), ("NG", "NG")],
                max_length=2,
                verbose_name="Retainer ID lubrication",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="retainer_part_no",
            field=models.CharField(
                choices=[
                    ("42001878", "42001878 (P703/U704/SA/FD)"),
                    ("42050758", "42050758 (Gnome)"),
                ],
                max_length=100,
                verbose_name="Retainer Part no",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="selected_model",
            field=models.CharField(
                choices=[
                    ("P703", "P703"),
                    ("U704", "U704"),
                    ("FD", "FD"),
                    ("SA", "SA"),
                    ("Gnome", "Gnome"),
                ],
                max_length=10,
                verbose_name="Program selection on HMI (HMI से Program select करना है)",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="test_pressure_vacuum",
            field=models.FloatField(
                help_text="Recommended Range: 0.25 - 0.3 MPa",
                verbose_name="Test Pressure for Vacuum generation",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="tool_alignment",
            field=models.CharField(
                choices=[("OK", "OK"), ("NG", "NG")],
                max_length=2,
                verbose_name="Tool Alignment (Top & Bottom) (Tool Alignment) सही होना चाहिए",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="top_tool_id",
            field=models.CharField(
                choices=[("FMA-03-35-T05", "FMA-03-35-T05 (P703/U704/SA/FD/Gnome)")],
                max_length=100,
                verbose_name="Top Tool ID",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="umbrella_part_no",
            field=models.CharField(
                choices=[("25094588", "25094588 (P703/U704/SA/FD/Gnome)")],
                max_length=100,
                verbose_name="Umbrella Part No",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="uv_assy_stage_id",
            field=models.CharField(
                choices=[
                    ("FMA-03-35-T07", "FMA-03-35-T07 (P703/U704/SA/FD)"),
                    ("FMA-03-35-T09", "FMA-03-35-T09 (Gnome)"),
                ],
                max_length=100,
                verbose_name="UV Assy Stage 1 ID",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="uv_clip_part_no",
            field=models.CharField(
                choices=[
                    ("42000829", "42000829 (P703/U704/SA/FD)"),
                    ("42000829", "42000829 (Gnome)"),
                ],
                max_length=100,
                verbose_name="UV Clip Part No",
            ),
        ),
        migrations.AlterField(
            model_name="checklistbase",
            name="uv_flow_input_pressure",
            field=models.FloatField(
                help_text="Recommended Range: 11-15 kPa",
                verbose_name="UV Flow input Test Pressure (13+/- 2 KPa)",
            ),
        ),
        migrations.AlterField(
            model_name="subgroupentry",
            name="bin_contamination_check",
            field=models.CharField(
                choices=[("Yes", "Yes"), ("No", "No")],
                max_length=3,
                verbose_name="Station Operator will confirm that every bin feeded on line is free from contamination (PTGW_5.3_PC_GUR_03)",
            ),
        ),
        migrations.AlterField(
            model_name="subgroupentry",
            name="umbrella_valve_assembly",
            field=models.CharField(
                choices=[("OK", "OK"), ("NG", "NG")],
                max_length=2,
                verbose_name="Umbrella Valve Assembly in Retainer in UV Assy Station",
            ),
        ),
        migrations.AlterField(
            model_name="subgroupentry",
            name="uv_clip_pressing",
            field=models.CharField(
                choices=[("OK", "OK"), ("NG", "NG")],
                max_length=2,
                verbose_name="UV Clip pressing -proper locking of 2 nos snap",
            ),
        ),
        migrations.AlterField(
            model_name="subgroupentry",
            name="uv_flow_value",
            field=models.FloatField(
                help_text="Recommended Range: 30-40 LPM",
                verbose_name="UV Flow Value (HMI)",
            ),
        ),
        migrations.AlterField(
            model_name="subgroupentry",
            name="uv_vacuum_test",
            field=models.FloatField(
                help_text="Recommended Range: -35 to -43 kPa",
                verbose_name="UV Vacuum Test range",
            ),
        ),
        migrations.AlterField(
            model_name="subgroupentry",
            name="workstation_clean",
            field=models.CharField(
                choices=[("Yes", "Yes"), ("No", "No")],
                max_length=3,
                verbose_name="All workstations are clean (वर्कस्टेशन साफ होना चाहिए)",
            ),
        ),
    ]
