from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    USER_TYPES = (
        ('operator', 'Operator'),
        ('shift_supervisor', 'Shift Supervisor'),
        ('quality_supervisor', 'Quality Supervisor'),
    )
    
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

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # One-time entries
    selected_model = models.CharField(max_length=10, choices=MODEL_CHOICES)
    line_pressure = models.FloatField(
        validators=[MinValueValidator(4.5), MaxValueValidator(5.5)],
        help_text="Range: 4.5 - 5.5 bar"
    )
    oring_condition = models.CharField(max_length=2, choices=[('OK', 'OK'), ('NG', 'NG')])
    uv_flow_input_pressure = models.FloatField(
        validators=[MinValueValidator(11), MaxValueValidator(15)],
        help_text="Range: 11-15 kPa"
    )
    master_verification_lvdt = models.CharField(max_length=2, choices=[('OK', 'OK'), ('NG', 'NG')])
    good_bad_master_verification = models.CharField(max_length=2, choices=[('OK', 'OK'), ('NG', 'NG')])
    test_pressure_vacuum = models.FloatField(
        validators=[MinValueValidator(0.25), MaxValueValidator(0.3)],
        help_text="Range: 0.25 - 0.3 MPa"
    )
    tool_alignment = models.CharField(max_length=2, choices=[('OK', 'OK'), ('NG', 'NG')])
    
    # Tool IDs and Part Numbers
    top_tool_id = models.CharField(max_length=100)
    bottom_tool_id = models.CharField(max_length=100)
    uv_assy_stage_id = models.CharField(max_length=100)
    retainer_part_no = models.CharField(max_length=100)
    uv_clip_part_no = models.CharField(max_length=100)
    umbrella_part_no = models.CharField(max_length=100)
    
    # Additional one-time checks
    retainer_id_lubrication = models.CharField(max_length=2, choices=[('OK', 'OK'), ('NG', 'NG')])
    error_proofing_verification = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')])

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
    checklist = models.ForeignKey(ChecklistBase, on_delete=models.CASCADE, related_name='subgroup_entries')
    subgroup_number = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending', blank=True
    )

    # Repeated measurements
    uv_vacuum_test = models.FloatField(
        validators=[MinValueValidator(-43), MaxValueValidator(-35)],
        help_text="Range: -35 to -43 kPa"
    )
    uv_flow_value = models.FloatField(
        validators=[MinValueValidator(30), MaxValueValidator(40)],
        help_text="Range: 30-40 LPM"
    )
    umbrella_valve_assembly = models.CharField(max_length=2, choices=[('OK', 'OK'), ('NG', 'NG')])
    uv_clip_pressing = models.CharField(max_length=2, choices=[('OK', 'OK'), ('NG', 'NG')])
    workstation_clean = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')])
    bin_contamination_check = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')])

    class Meta:
        ordering = ['subgroup_number']
        unique_together = ['checklist', 'subgroup_number']

    def get_latest_verification(self):
        return self.verifications.order_by('-verified_at').first()
    
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
