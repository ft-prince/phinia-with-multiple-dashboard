from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    USER_TYPES = (
        ('operator', 'Operator'),
        ('shift_supervisor', 'Shift Supervisor'),
        ('quality_supervisor', 'Quality Supervisor'),
    )
    company_id=models.CharField(max_length=100,blank=True,null=True)    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)

class Shift(models.Model):
    SHIFT_CHOICES = (
        ('day', 'Day Shift (8 AM - 8 PM)'),
        ('night', 'Night Shift (8 PM - 8 AM)'),
    )
    
    date = models.DateField(auto_now=True)
    shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES)
    operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operated_shifts')
    shift_supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supervised_shifts')
    quality_supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quality_supervised_shifts')

    class Meta:
        unique_together = ('date', 'shift_type')

from django.db import models
from django.contrib.auth.models import AbstractUser

class ChecklistBase(models.Model):
    """Base checklist information filled once per shift"""
    MODEL_CHOICES = (
        ('P703', 'P703'),
        ('U704', 'U704'),
        ('FD', 'FD'),
        ('SA', 'SA'),
        ('Gnome', 'Gnome'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('supervisor_approved', 'Supervisor Approved'),
        ('quality_approved', 'Quality Approved'),
        ('rejected', 'Rejected'),
    )

    OK_NG_CHOICES = [('OK', 'OK'), ('NG', 'NG')]
    YES_NO_CHOICES = [('Yes', 'Yes'), ('No', 'No')]

    TOP_TOOL_CHOICES = [
        ('FMA-03-35-T05', 'FMA-03-35-T05 (P703/U704/SA/FD/Gnome)'),
    ]

    BOTTOM_TOOL_CHOICES = [
        ('FMA-03-35-T06', 'FMA-03-35-T06 (P703/U704/SA/FD)'),
        ('FMA-03-35-T08', 'FMA-03-35-T08 (Gnome)'),
    ]

    UV_ASSY_STAGE_CHOICES = [
        ('FMA-03-35-T07', 'FMA-03-35-T07 (P703/U704/SA/FD)'),
        ('FMA-03-35-T09', 'FMA-03-35-T09 (Gnome)'),
    ]

    RETAINER_PART_CHOICES = [
        ('42001878', '42001878 (P703/U704/SA/FD)'),
        ('42050758', '42050758 (Gnome)'),
    ]

    UV_CLIP_PART_CHOICES = [
        ('42000829', '42000829 (P703/U704/SA/FD)'),
        ('42000829', '42000829 (Gnome)'),  # Same number for both
    ]

    UMBRELLA_PART_CHOICES = [
        ('25094588', '25094588 (P703/U704/SA/FD/Gnome)'),
    ]

    shift = models.ForeignKey('Shift', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # Program selection and basic measurements
    selected_model = models.CharField(
        max_length=10, 
        choices=MODEL_CHOICES,
        verbose_name="Program selection on HMI (HMI से Program select करना है)"
    )
    
    line_pressure = models.FloatField(
        help_text="Recommended Range: 4.5 - 5.5 bar"
    )
    
    oring_condition = models.CharField(
        max_length=2,
        choices=OK_NG_CHOICES,
        verbose_name="O-ring condition (UV Flow check sealing area) (O-ring सील की स्थिति सही होनी चाहिए)"
    )
    
    uv_flow_input_pressure = models.FloatField(
        help_text="Recommended Range: 11-15 kPa",
        verbose_name="UV Flow input Test Pressure (13+/- 2 KPa)"
    )
    
    # Verifications
    master_verification_lvdt = models.CharField(
        max_length=2,
        choices=OK_NG_CHOICES,
        verbose_name="Master Verification for LVDT"
    )
    
    good_bad_master_verification = models.CharField(
        max_length=2,
        choices=OK_NG_CHOICES,
        verbose_name="Good and Bad master verification (refer EPVS)"
    )
    
    test_pressure_vacuum = models.FloatField(
        help_text="Recommended Range: 0.25 - 0.3 MPa",
        verbose_name="Test Pressure for Vacuum generation"
    )
    
    tool_alignment = models.CharField(
        max_length=2,
        choices=OK_NG_CHOICES,
        verbose_name="Tool Alignment (Top & Bottom) (Tool Alignment) सही होना चाहिए"
    )
    
    # Tool IDs and Part Numbers
    top_tool_id = models.CharField(
        max_length=100,
        choices=TOP_TOOL_CHOICES,
        verbose_name="Top Tool ID"
    )
    
    bottom_tool_id = models.CharField(
        max_length=100,
        choices=BOTTOM_TOOL_CHOICES,
        verbose_name="Bottom Tool ID"
    )
    
    uv_assy_stage_id = models.CharField(
        max_length=100,
        choices=UV_ASSY_STAGE_CHOICES,
        verbose_name="UV Assy Stage 1 ID"
    )
    
    retainer_part_no = models.CharField(
        max_length=100,
        choices=RETAINER_PART_CHOICES,
        verbose_name="Retainer Part no"
    )
    
    uv_clip_part_no = models.CharField(
        max_length=100,
        choices=UV_CLIP_PART_CHOICES,
        verbose_name="UV Clip Part No"
    )
    
    umbrella_part_no = models.CharField(
        max_length=100,
        choices=UMBRELLA_PART_CHOICES,
        verbose_name="Umbrella Part No"
    )
    
    # Additional checks
    retainer_id_lubrication = models.CharField(
        max_length=2,
        choices=OK_NG_CHOICES,
        verbose_name="Retainer ID lubrication"
    )
    
    error_proofing_verification = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES,
        verbose_name="All Error proofing / Error detection verification done"
    )

    class Meta:
        ordering = ['-created_at']

class SubgroupEntry(models.Model):
    """Repeated measurements taken every 2 hours"""
    VERIFICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('supervisor_verified', 'Supervisor Verified'),
        ('quality_verified', 'Quality Verified'),
        ('rejected', 'Rejected'),
    )    

    OK_NG_CHOICES = [('OK', 'OK'), ('NG', 'NG')]
    YES_NO_CHOICES = [('Yes', 'Yes'), ('No', 'No')]

    checklist = models.ForeignKey(ChecklistBase, on_delete=models.CASCADE, related_name='subgroup_entries')
    subgroup_number = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
        blank=True
    )

    # Repeated measurements
    uv_vacuum_test = models.FloatField(
        help_text="Recommended Range: -35 to -43 kPa",
        verbose_name="UV Vacuum Test range"
    )
    
    uv_flow_value = models.FloatField(
        help_text="Recommended Range: 30-40 LPM",
        verbose_name="UV Flow Value (HMI)"
    )
    
    umbrella_valve_assembly = models.CharField(
        max_length=2,
        choices=OK_NG_CHOICES,
        verbose_name="Umbrella Valve Assembly in Retainer in UV Assy Station"
    )
    
    uv_clip_pressing = models.CharField(
        max_length=2,
        choices=OK_NG_CHOICES,
        verbose_name="UV Clip pressing -proper locking of 2 nos snap"
    )
    
    workstation_clean = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES,
        verbose_name="All workstations are clean (वर्कस्टेशन साफ होना चाहिए)"
    )
    
    bin_contamination_check = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES,
        verbose_name="Station Operator will confirm that every bin feeded on line is free from contamination (PTGW_5.3_PC_GUR_03)"
    )

    class Meta:
        ordering = ['subgroup_number']
        unique_together = ['checklist', 'subgroup_number']    
    @property
    def current_status(self):
        """Get current verification status based on verifications"""
        latest = self.get_latest_verification()
        if not latest:
            return 'pending'
            
        if latest.verifier_type == 'supervisor':
            if latest.status == 'rejected':
                return 'rejected'
            return 'supervisor_verified'
            
        if latest.verifier_type == 'quality':
            if latest.status == 'rejected':
                return 'rejected'
            return 'quality_verified'
            
        return 'pending'

class SubgroupVerification(models.Model):
    """Verification records for each subgroup entry"""
    VERIFIER_TYPES = (
        ('supervisor', 'Shift Supervisor'),
        ('quality', 'Quality Supervisor'),
    )
    
    subgroup = models.ForeignKey(SubgroupEntry, on_delete=models.CASCADE, related_name='verifications')
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE)
    verifier_type = models.CharField(max_length=20, choices=VERIFIER_TYPES)
    verified_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=SubgroupEntry.VERIFICATION_STATUS_CHOICES
    )
    comments = models.TextField(blank=True)

    class Meta:
        unique_together = ['subgroup', 'verifier_type']
        ordering = ['verified_at']

class Verification(models.Model):
    checklist = models.ForeignKey(ChecklistBase, on_delete=models.CASCADE, related_name='verifications')  # Changed from subgroup
    team_leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_leader_verifications')
    shift_supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shift_supervisor_verifications')
    quality_supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quality_supervisor_verifications')
    verified_at = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)

class Concern(models.Model):
    """Concerns and actions taken"""
    checklist = models.ForeignKey(ChecklistBase, on_delete=models.CASCADE)
    subgroup = models.ForeignKey(SubgroupEntry, on_delete=models.CASCADE, null=True, blank=True)
    concern_identified = models.TextField()
    cause_if_known = models.TextField(blank=True)
    action_taken = models.TextField()
    manufacturing_approval = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='manufacturing_approvals', 
        null=True
    )
    quality_approval = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='quality_approvals', 
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
