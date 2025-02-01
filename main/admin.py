from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Shift, ChecklistBase, SubgroupEntry, Verification, Concern

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Role', {'fields': ('user_type',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'shift_type', 'operator', 'shift_supervisor', 'quality_supervisor')
    list_filter = ('date', 'shift_type')
    search_fields = ('operator__username', 'shift_supervisor__username', 'quality_supervisor__username')
    date_hierarchy = 'date'

class SubgroupEntryInline(admin.TabularInline):
    model = SubgroupEntry
    extra = 0
    max_num = 6

class VerificationInline(admin.TabularInline):
    model = Verification
    extra = 0

class ConcernInline(admin.TabularInline):
    model = Concern
    extra = 0

@admin.register(ChecklistBase)
class ChecklistBaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'status', 'selected_model', 'created_at')
    list_filter = ('status', 'selected_model', 'shift__date')
    search_fields = ('shift__operator__username',)
    date_hierarchy = 'created_at'
    inlines = [SubgroupEntryInline, VerificationInline, ConcernInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shift', 'status', 'selected_model')
        }),
        ('One-time Measurements', {
            'fields': ('line_pressure', 'uv_flow_input_pressure', 'test_pressure_vacuum')
        }),
        ('Status Checks', {
            'fields': ('oring_condition', 'master_verification_lvdt', 'good_bad_master_verification',
                      'tool_alignment')
        }),
        ('Tool Information', {
            'fields': ('top_tool_id', 'bottom_tool_id', 'uv_assy_stage_id', 'retainer_part_no',
                      'uv_clip_part_no', 'umbrella_part_no')
        })
    )

@admin.register(SubgroupEntry)
class SubgroupEntryAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'subgroup_number', 'timestamp', 'uv_vacuum_test', 'uv_flow_value')
    list_filter = ('checklist__status', 'subgroup_number')
    search_fields = ('checklist__shift__operator__username',)
    date_hierarchy = 'timestamp'

@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'team_leader', 'shift_supervisor', 'quality_supervisor', 'verified_at')  # Changed from 'subgroup' to 'checklist'
    list_filter = ('verified_at',)
    search_fields = ('team_leader__username', 'shift_supervisor__username', 'quality_supervisor__username')
    date_hierarchy = 'verified_at'

@admin.register(Concern)
class ConcernAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'concern_identified', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('concern_identified', 'cause_if_known', 'action_taken')
    date_hierarchy = 'created_at'

# Customize admin site
admin.site.site_header = 'Checklist System Administration'
admin.site.site_title = 'Checklist System Admin'
admin.site.index_title = 'Checklist Management'