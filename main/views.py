from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time, timedelta
from .models import ChecklistBase, SubgroupEntry, Verification, Shift, User
from .forms import ChecklistBaseForm, SubgroupEntryForm, VerificationForm, ConcernForm, UserRegistrationForm
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, Avg
from datetime import timedelta
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta
from itertools import chain
import json
from django.shortcuts import render
# Authentication Views
def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'main/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'main/login.html')

# Utility Functions
def get_current_shift(user):
    """Get or create current shift for user"""
    current_time = timezone.localtime()
    shift_type = 'day' if 8 <= current_time.hour < 20 else 'night'
    
    try:
        # Try to get existing shift
        shift = Shift.objects.get(
            date=current_time.date(),
            shift_type=shift_type
        )
    except Shift.DoesNotExist:
        # Get supervisors (or create dummy ones if needed)
        shift_supervisor = User.objects.filter(user_type='shift_supervisor').first()
        quality_supervisor = User.objects.filter(user_type='quality_supervisor').first()
        
        # If no supervisors exist, create default ones
        if not shift_supervisor:
            shift_supervisor = User.objects.create_user(
                username='default_shift_supervisor',
                password='defaultpass123',
                user_type='shift_supervisor'
            )
        
        if not quality_supervisor:
            quality_supervisor = User.objects.create_user(
                username='default_quality_supervisor',
                password='defaultpass123',
                user_type='quality_supervisor'
            )
        
        # Create new shift
        shift = Shift.objects.create(
            date=current_time.date(),
            shift_type=shift_type,
            operator=user,
            shift_supervisor=shift_supervisor,
            quality_supervisor=quality_supervisor
        )
    
    return shift

def check_time_gap(last_subgroup):
    """Check if enough time (2 hours) has passed since last subgroup"""
    if not last_subgroup:
        return True
    
    time_difference = timezone.now() - last_subgroup.timestamp
    return time_difference >= timedelta(hours=2)

# Main Views
@login_required
def dashboard(request):
    """Route to appropriate dashboard based on user type"""
    try:
        if request.user.user_type == 'operator':
            return operator_dashboard(request)
        elif request.user.user_type == 'shift_supervisor':
            return supervisor_dashboard(request)
        elif request.user.user_type == 'quality_supervisor':
            return quality_dashboard(request)
        else:
            # Default to operator dashboard if user_type is not set
            return operator_dashboard(request)
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return render(request, 'main/error.html', {'error': str(e)})

from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

@login_required
def operator_dashboard(request):
    current_date = timezone.now().date()
    current_time = timezone.now().time()
    
    # More robust shift determination
    is_day_shift = (8 <= current_time.hour < 20)
    current_shift = 'day' if is_day_shift else 'night'
    current_shift_display = 'Day Shift (8 AM - 8 PM)' if is_day_shift else 'Night Shift (8 PM - 8 AM)'
    
    # Get active checklist
    active_checklist = ChecklistBase.objects.filter(
        shift__operator=request.user,
        shift__date=current_date,
        shift__shift_type=current_shift,
        status='pending'
    ).first()
    
    # Get recent entries (including subgroups)
    recent_entries = SubgroupEntry.objects.filter(
        checklist__shift__operator=request.user
    ).select_related(
        'checklist',
        'checklist__shift'
    ).exclude(
        checklist_id=active_checklist.id if active_checklist else None
    ).order_by('-timestamp')[:10]
    
    # Check if can create new checklist
    can_create_new = not active_checklist
    
    # Check if can add subgroup
    can_add_subgroup = False
    if active_checklist:
        subgroup_count = active_checklist.subgroup_entries.count()
        if subgroup_count < 6:
            last_subgroup = active_checklist.subgroup_entries.order_by('-timestamp').first()
            if not last_subgroup:
                can_add_subgroup = True
            else:
                # Check if 2 hours have passed since last subgroup
                time_difference = timezone.now() - last_subgroup.timestamp
                can_add_subgroup = time_difference >= timedelta(hours=2)

    context = {
        'current_date': current_date,
        'current_shift': current_shift_display,
        'active_checklist': active_checklist,
        'recent_entries': recent_entries,
        'can_create_new': can_create_new,
        'can_add_subgroup': can_add_subgroup,
        'dashboard_stats': {
            'total_checklists': ChecklistBase.objects.filter(
                shift__operator=request.user
            ).count(),
            'approved_checklists': ChecklistBase.objects.filter(
                shift__operator=request.user,
                status='quality_approved'
            ).count(),
            'rejected_checklists': ChecklistBase.objects.filter(
                shift__operator=request.user,
                status='rejected'
            ).count(),
            'pending_verification': ChecklistBase.objects.filter(
                shift__operator=request.user,
                status__in=['supervisor_approved', 'pending']
            ).count()
        }
    }
    
    return render(request, 'main/operator_dashboard.html', context)

def check_time_gap(last_subgroup):
    """Helper function to check if enough time has passed since last subgroup"""
    if not last_subgroup:
        return True
    time_difference = timezone.now() - last_subgroup.timestamp
    return time_difference >= timedelta(hours=2)




@login_required
@user_passes_test(lambda u: u.user_type == 'operator')
def create_checklist(request):
    """Create initial checklist with one-time entries"""
    current_shift = get_current_shift(request.user)
    
    # Check if checklist already exists for current shift
    if ChecklistBase.objects.filter(shift=current_shift).exists():
        messages.error(request, 'A checklist already exists for this shift')
        return redirect('operator_dashboard')
    
    if request.method == 'POST':
        form = ChecklistBaseForm(request.POST)
        if form.is_valid():
            try:
                checklist = form.save(commit=False)
                checklist.shift = current_shift
                checklist.save()
                messages.success(request, 'Checklist created successfully!')
                return redirect('add_subgroup', checklist_id=checklist.id)
            except Exception as e:
                messages.error(request, f'Error creating checklist: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChecklistBaseForm()
    
    return render(request, 'main/create_checklist.html', {
        'form': form,
        'current_shift': current_shift
    })
    
@login_required
@user_passes_test(lambda u: u.user_type == 'operator')
def add_subgroup(request, checklist_id):
    checklist = get_object_or_404(ChecklistBase, id=checklist_id)
    
    # Verify ownership and status
    if checklist.shift.operator != request.user:
        messages.error(request, 'You do not have permission to modify this checklist')
        return redirect('operator_dashboard')
    
    if checklist.status != 'pending':
        messages.error(request, 'Cannot add subgroups to a verified checklist')
        return redirect('checklist_detail', checklist_id=checklist.id)
    
    current_subgroup = checklist.subgroup_entries.count() + 1
    
    if current_subgroup > 6:
        messages.error(request, 'Maximum number of subgroups (6) reached')
        return redirect('checklist_detail', checklist_id=checklist.id)
    
    last_subgroup = checklist.subgroup_entries.last()
    
    if last_subgroup:
        time_since_last = timezone.now() - last_subgroup.timestamp
        if time_since_last < timedelta(hours=2):
            remaining_time = timedelta(hours=2) - time_since_last
            messages.error(request, f'Please wait {remaining_time.seconds//60} minutes before adding next subgroup')
            return redirect('checklist_detail', checklist_id=checklist.id)
    
    if request.method == 'POST':
        form = SubgroupEntryForm(request.POST)
        if form.is_valid():
            subgroup = form.save(commit=False)
            subgroup.checklist = checklist
            subgroup.subgroup_number = current_subgroup
            subgroup.save()
            messages.success(request, f'Subgroup {current_subgroup} added successfully')
            return redirect('checklist_detail', checklist_id=checklist.id)
    else:
        form = SubgroupEntryForm()
    
    return render(request, 'main/add_subgroup.html', {
        'form': form,
        'checklist': checklist,
        'current_subgroup': current_subgroup
    })
    
    


@login_required
def validate_subgroup(request):
    """API endpoint for validating subgroup data"""
    if request.method == 'POST':
        data = request.POST
        errors = []
        
        # Validate UV vacuum test
        uv_vacuum = float(data.get('uv_vacuum_test', 0))
        if not (-43 <= uv_vacuum <= -35):
            errors.append("UV vacuum test must be between -43 and -35 kPa")
        
        # Validate UV flow value
        uv_flow = float(data.get('uv_flow_value', 0))
        if not (30 <= uv_flow <= 40):
            errors.append("UV flow value must be between 30 and 40 LPM")
        
        return JsonResponse({
            'is_valid': len(errors) == 0,
            'errors': errors
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def add_concern(request, checklist_id):
    checklist = get_object_or_404(ChecklistBase, id=checklist_id)
    
    # Only allow adding concerns if checklist is still pending
    if checklist.status not in ['pending', 'supervisor_approved']:
        messages.error(request, 'Cannot add concerns to a completed checklist')
        return redirect('checklist_detail', checklist_id=checklist.id)
    
    if request.method == 'POST':
        form = ConcernForm(request.POST)
        if form.is_valid():
            concern = form.save(commit=False)
            concern.checklist = checklist
            concern.save()
            messages.success(request, 'Concern added successfully')
            return redirect('checklist_detail', checklist_id=checklist.id)
    else:
        form = ConcernForm()
    
    return render(request, 'main/add_concern.html', {
        'form': form,
        'checklist': checklist
    })
    
@login_required
@user_passes_test(lambda u: u.user_type == 'operator')
def edit_subgroup(request, checklist_id, subgroup_id):
    checklist = get_object_or_404(ChecklistBase, id=checklist_id)
    subgroup = get_object_or_404(SubgroupEntry, id=subgroup_id, checklist=checklist)
    
    # Verify ownership and status
    if checklist.shift.operator != request.user:
        messages.error(request, 'You do not have permission to modify this subgroup')
        return redirect('checklist_detail', checklist_id=checklist.id)
    
    if checklist.status != 'pending':
        messages.error(request, 'Cannot edit subgroups of a verified checklist')
        return redirect('checklist_detail', checklist_id=checklist.id)
    
    if request.method == 'POST':
        form = SubgroupEntryForm(request.POST, instance=subgroup)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subgroup updated successfully')
            return redirect('checklist_detail', checklist_id=checklist.id)
    else:
        form = SubgroupEntryForm(instance=subgroup)
    
    return render(request, 'main/edit_subgroup.html', {
        'form': form,
        'checklist': checklist,
        'subgroup': subgroup
    })
        
@login_required
@user_passes_test(lambda u: u.user_type == 'shift_supervisor')
def supervisor_dashboard(request):
    current_date = timezone.now().date()
    current_time = timezone.now().time()
    current_shift = 'day' if 8 <= current_time.hour < 20 else 'night'
    
    # Get all pending checklists
    pending_entries = ChecklistBase.objects.filter(
        status='pending'  # Get all pending checklists
    ).annotate(
        subgroup_count=Count('subgroup_entries')
    ).prefetch_related(
        'subgroup_entries',
        'shift__operator'
    ).order_by('-created_at')

    # Get all verified entries for today first
    todays_verifications = ChecklistBase.objects.filter(
        shift__date=current_date,
        shift__shift_supervisor=request.user,
        status__in=['supervisor_approved', 'quality_approved', 'rejected']
    )
    
    # Then get recent verifications
    recent_verified = ChecklistBase.objects.filter(
        shift__shift_supervisor=request.user,
        status__in=['supervisor_approved', 'quality_approved', 'rejected']
    ).order_by('-created_at')[:10]
    
    # Calculate today's statistics
    total_today = ChecklistBase.objects.filter(
        shift__date=current_date,
        shift__shift_supervisor=request.user
    ).count()
    
    approved_today = todays_verifications.filter(
        status='supervisor_approved'
    ).count()
    
    # Calculate approval rate
    approval_rate = (
        round((approved_today / total_today) * 100)
        if total_today > 0
        else 0
    )

    # Add verification status to each pending entry
    for entry in pending_entries:
        # Check if all 6 subgroups are completed
        entry.is_complete = entry.subgroup_count >= 6
        # Get the latest subgroup
        entry.latest_subgroup = entry.subgroup_entries.order_by('-timestamp').first()
        # Add measurement validation
        entry.measurements_ok = True
        if entry.subgroup_count > 0:
            for subgroup in entry.subgroup_entries.all():
                if not (-43 <= subgroup.uv_vacuum_test <= -35) or \
                   not (30 <= subgroup.uv_flow_value <= 40):
                    entry.measurements_ok = False
                    break
    # Get all pending checklists with their subgroup counts
    pending_entries = ChecklistBase.objects.filter(
        status='pending'
    ).annotate(
        subgroup_count=Count('subgroup_entries')
    ).prefetch_related(
        'subgroup_entries',
        'shift__operator'
    ).order_by('-created_at')

    # Split into complete and incomplete
    complete_pending = [entry for entry in pending_entries if entry.subgroup_count == 6]
    incomplete_pending = [entry for entry in pending_entries if entry.subgroup_count < 6]


    context = {
        'current_date': current_date,
        'current_shift': current_shift,
        'pending_entries': pending_entries,
        'recent_verified': recent_verified,
        'total_today': total_today,
        'approved_today': approved_today,
        'approval_rate': approval_rate,
        'pending_count': pending_entries.count(),
        'verified_count': recent_verified.count(),
        

        'complete_pending': complete_pending,
        'incomplete_pending': incomplete_pending,

    }
    
    return render(request, 'main/supervisor_dashboard.html', context)






def calculate_average_verification_time(entries):
    """Calculate average time taken for verification"""
    verified_entries = entries.filter(status='supervisor_approved')
    if not verified_entries:
        return 0
        
    total_time = timedelta()
    count = 0
    
    for entry in verified_entries:
        if entry.created_at and entry.supervisor_verified_at:
            time_diff = entry.supervisor_verified_at - entry.created_at
            total_time += time_diff
            count += 1
            
    if count == 0:
        return 0
        
    average_seconds = total_time.total_seconds() / count
    return round(average_seconds / 60)  # Return in minutes

def calculate_completion_rate(entries):
    """Calculate the rate of checklists that have all 6 subgroups"""
    total = entries.count()
    if total == 0:
        return 0
        
    completed = entries.annotate(
        subgroup_count=Count('subgroup_entries')
    ).filter(subgroup_count=6).count()
    
    return round((completed / total) * 100)

@login_required
@user_passes_test(lambda u: u.user_type == 'shift_supervisor')
def verify_checklist(request, checklist_id):
    checklist = get_object_or_404(ChecklistBase, id=checklist_id)
    
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.checklist = checklist
            verification.supervisor = request.user
            verification.save()
            
            checklist.status = 'supervisor_approved'
            checklist.save()
            
            messages.success(request, 'Checklist verified successfully')
            return redirect('supervisor_dashboard')
    else:
        form = VerificationForm()
    
    return render(request, 'main/verify_checklist.html', {
        'form': form,
        'checklist': checklist
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'quality_supervisor')
def quality_dashboard(request):
    current_date = timezone.now().date()
    current_time = timezone.now().time()
    is_day_shift = 8 <= current_time.hour < 20
    current_shift = 'day' if is_day_shift else 'night'
    current_shift_display = 'Day Shift (8 AM - 8 PM)' if is_day_shift else 'Night Shift (8 PM - 8 AM)'

    # Get in-progress checklists
    in_progress_checklists = ChecklistBase.objects.filter(
        status='pending',
        shift__date=current_date
    ).prefetch_related(
        'subgroup_entries',
        'shift__operator',
        'shift__shift_supervisor'
    ).order_by('-created_at')

    # Get pending verifications (supervisor approved)
    pending_verifications = ChecklistBase.objects.filter(
        status='supervisor_approved'
    ).prefetch_related(
        'subgroup_entries',
        'shift__operator',
        'shift__shift_supervisor'
    ).order_by('-created_at')

    # Get today's entries
    todays_entries = ChecklistBase.objects.filter(
        shift__date=current_date,
        shift__quality_supervisor=request.user
    )
    
    # Get recent verifications with comments
    recent_verifications = ChecklistBase.objects.filter(
        status__in=['quality_approved', 'rejected']
    ).prefetch_related(
        'subgroup_entries',
        'shift__operator',
        'verifications'  # Include verification comments
    ).order_by('-created_at')[:10]

    # Calculate statistics
    stats = calculate_quality_stats(todays_entries)
    
    # Process measurement validations
    process_measurements(pending_verifications)
    process_measurements(in_progress_checklists)

    # Calculate model-wise statistics
    model_stats = calculate_model_stats(todays_entries)

    # Calculate 7-day trend
    trend_data = calculate_trend_data(current_date)

    # Calculate average verification times
    avg_verification_time = calculate_average_verification_time(recent_verifications)

    context = {
        'current_date': current_date,
        'current_shift': current_shift_display,
        'in_progress_checklists': in_progress_checklists,
        'pending_verifications': pending_verifications,
        'recent_verifications': recent_verifications,
        'quality_approved': stats['approved'],
        'quality_rejected': stats['rejected'],
        'quality_pending': stats['pending'],
        'approval_rate': stats['approval_rate'],
        'model_stats': model_stats,
        'trend_dates': json.dumps(trend_data['dates']),
        'trend_rates': json.dumps(trend_data['rates']),
        'avg_verification_time': avg_verification_time,
        'critical_issues': get_critical_issues(in_progress_checklists, pending_verifications),
    }
    
    return render(request, 'main/quality_dashboard.html', context)

def calculate_model_stats(entries):
    """Calculate statistics for each model"""
    model_stats = []
    for model_code, model_name in ChecklistBase.MODEL_CHOICES:
        model_entries = entries.filter(selected_model=model_code)
        model_total = model_entries.count()
        
        if model_total > 0:
            stats = {
                'model': model_code,
                'total': model_total,
                'approved': model_entries.filter(status='quality_approved').count(),
                'rejected': model_entries.filter(status='rejected').count()
            }
            stats['rate'] = round((stats['approved'] / model_total) * 100)
            model_stats.append(stats)
    
    return model_stats

def calculate_trend_data(current_date):
    """Calculate 7-day trend data"""
    trend_dates = []
    trend_rates = []
    
    for i in range(7, -1, -1):
        date = current_date - timedelta(days=i)
        entries = ChecklistBase.objects.filter(
            shift__date=date,
            status__in=['quality_approved', 'rejected']
        )
        total = entries.count()
        if total > 0:
            approved = entries.filter(status='quality_approved').count()
            rate = round((approved / total) * 100)
        else:
            rate = 0
        trend_dates.append(date.strftime('%Y-%m-%d'))
        trend_rates.append(rate)
    
    return {
        'dates': trend_dates,
        'rates': trend_rates
    }

def calculate_average_verification_time(verifications):
    """Calculate average time taken for quality verification"""
    total_time = timedelta()
    count = 0
    
    for verification in verifications:
        if hasattr(verification, 'verifications'):
            for v in verification.verifications.all():
                if hasattr(v, 'supervisor_verified_at') and v.quality_supervisor_verified_at:
                    time_diff = v.quality_supervisor_verified_at - v.supervisor_verified_at
                    total_time += time_diff
                    count += 1
            
    if count == 0:
        return 0
        
    return round(total_time.total_seconds() / count / 60)  # Return in minutes

def calculate_quality_stats(entries):
    """Calculate quality statistics"""
    approved = entries.filter(status='quality_approved').count()
    rejected = entries.filter(status='rejected').count()
    pending = entries.filter(status='pending').count()
    total_processed = approved + rejected
    
    return {
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'approval_rate': round((approved / total_processed * 100) if total_processed > 0 else 0)
    }

def process_measurements(entries):
    """Process measurements and add validation flags"""
    for entry in entries:
        entry.subgroup_count = entry.subgroup_entries.count()
        entry.all_measurements_ok = True
        entry.measurement_issues = []
        entry.critical_issues = []
        
        # Check base measurements
        validate_base_measurements(entry)
        
        # Check subgroup measurements
        validate_subgroup_measurements(entry)

def validate_base_measurements(entry):
    """Validate base measurements"""
    if not (4.5 <= entry.line_pressure <= 5.5):
        entry.all_measurements_ok = False
        entry.critical_issues.append(f"Line pressure critical: {entry.line_pressure}")
            
    if not (11 <= entry.uv_flow_input_pressure <= 15):
        entry.all_measurements_ok = False
        entry.critical_issues.append(f"UV flow input pressure critical: {entry.uv_flow_input_pressure}")

def validate_subgroup_measurements(entry):
    """Validate subgroup measurements"""
    for subgroup in entry.subgroup_entries.all():
        if not (-43 <= subgroup.uv_vacuum_test <= -35):
            entry.all_measurements_ok = False
            entry.measurement_issues.append(
                f"Subgroup {subgroup.subgroup_number}: UV vacuum test out of range ({subgroup.uv_vacuum_test})"
            )
        if not (30 <= subgroup.uv_flow_value <= 40):
            entry.all_measurements_ok = False
            entry.measurement_issues.append(
                f"Subgroup {subgroup.subgroup_number}: UV flow value out of range ({subgroup.uv_flow_value})"
            )

def get_critical_issues(in_progress, pending):
    """Get critical issues from both in-progress and pending checklists"""
    critical_issues = []
    
    for checklist in chain(in_progress, pending):
        if hasattr(checklist, 'critical_issues') and checklist.critical_issues:
            critical_issues.append({
                'checklist_id': checklist.id,
                'operator': checklist.shift.operator.username,
                'model': checklist.selected_model,
                'issues': checklist.critical_issues
            })
    
    return critical_issues


@login_required
def reports_dashboard(request):
    current_date = timezone.now().date()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    start_of_month = current_date.replace(day=1)

    # Get statistics
    daily_stats = ChecklistBase.objects.filter(
        shift__date=current_date
    ).aggregate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='quality_approved')),
        rejected=Count('id', filter=Q(status='rejected')),
        pending=Count('id', filter=Q(status='pending'))
    )

    weekly_stats = ChecklistBase.objects.filter(
        shift__date__gte=start_of_week,
        shift__date__lte=current_date
    ).aggregate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='quality_approved')),
        rejected=Count('id', filter=Q(status='rejected'))
    )

    monthly_stats = ChecklistBase.objects.filter(
        shift__date__gte=start_of_month,
        shift__date__lte=current_date
    ).aggregate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='quality_approved')),
        rejected=Count('id', filter=Q(status='rejected'))
    )

    # Get model-wise statistics
    model_stats = ChecklistBase.objects.values('selected_model').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='quality_approved')),
        rejected=Count('id', filter=Q(status='rejected'))
    )

    # Calculate approval rates
    for stats in [daily_stats, weekly_stats, monthly_stats]:
        total_verified = stats['approved'] + stats['rejected']
        stats['approval_rate'] = (
            round((stats['approved'] / total_verified) * 100)
            if total_verified > 0 else 0
        )

    # Get recent activity
    recent_activity = ChecklistBase.objects.filter(
        status__in=['quality_approved', 'rejected']
    ).order_by('-created_at')[:10]

    context = {
        'daily_stats': daily_stats,
        'weekly_stats': weekly_stats,
        'monthly_stats': monthly_stats,
        'model_stats': model_stats,
        'recent_activity': recent_activity,
        'current_date': current_date
    }

    return render(request, 'main/reports/reports_dashboard.html', context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count
from .models import ChecklistBase, SubgroupEntry, Verification, Concern

@login_required
def checklist_detail(request, checklist_id):
    # Get checklist with related data
    checklist = get_object_or_404(
        ChecklistBase.objects.select_related(
            'shift__operator',
            'shift__shift_supervisor',
            'shift__quality_supervisor'
        ).prefetch_related(
            'subgroup_entries',
            'verifications',
            'concern_set'
        ), 
        id=checklist_id
    )
    
    # Get subgroups with validation status
    subgroups = process_subgroups(checklist.subgroup_entries.all().order_by('subgroup_number'))
    
    # Calculate subgroup metrics
    subgroup_metrics = calculate_subgroup_metrics(subgroups)
    
    # Check if new subgroup can be added
    can_add_subgroup = check_subgroup_addition(checklist, subgroups)
    
    # Get verification status and permissions
    verification_status = get_verification_status(request.user, checklist, subgroups)
    
    # Process measurement validations
    measurement_validation = validate_measurements(checklist, subgroups)
    
    # Get concerns with metadata
    concerns = process_concerns(checklist.concern_set.all())
    
    # Calculate timing metrics
    timing_metrics = calculate_timing_metrics(checklist, subgroups)
    
    context = {
        'checklist': checklist,
        'subgroups': subgroups,
        'can_add_subgroup': can_add_subgroup,
        'total_subgroups': len(subgroups),
        'remaining_subgroups': 6 - len(subgroups),
        'subgroup_metrics': subgroup_metrics,
        'verification_status': verification_status,
        'measurement_validation': measurement_validation,
        'concerns': concerns,
        'timing_metrics': timing_metrics,
        'user_permissions': get_user_permissions(request.user, checklist)
    }
    
    return render(request, 'main/checklist_detail.html', context)

def process_subgroups(subgroups):
    """Process and validate subgroups"""
    processed_subgroups = []
    for subgroup in subgroups:
        subgroup.validation_status = {
            'uv_vacuum_test_ok': -43 <= subgroup.uv_vacuum_test <= -35,
            'uv_flow_value_ok': 30 <= subgroup.uv_flow_value <= 40,
            'assembly_ok': subgroup.umbrella_valve_assembly == 'OK',
            'pressing_ok': subgroup.uv_clip_pressing == 'OK',
            'cleanliness_ok': subgroup.workstation_clean == 'Yes',
            'contamination_ok': subgroup.bin_contamination_check == 'Yes'
        }
        subgroup.all_checks_passed = all(subgroup.validation_status.values())
        processed_subgroups.append(subgroup)
    return processed_subgroups

def calculate_subgroup_metrics(subgroups):
    """Calculate metrics for subgroups"""
    return {
        'total_count': len(subgroups),
        'passed_count': sum(1 for s in subgroups if s.all_checks_passed),
        'vacuum_test_issues': sum(1 for s in subgroups if not s.validation_status['uv_vacuum_test_ok']),
        'flow_value_issues': sum(1 for s in subgroups if not s.validation_status['uv_flow_value_ok']),
        'completion_percentage': (len(subgroups) / 6) * 100 if subgroups else 0
    }

def check_subgroup_addition(checklist, subgroups):
    """Check if new subgroup can be added"""
    if checklist.status != 'pending':
        return False
        
    current_count = len(subgroups)
    if current_count >= 6:
        return False
        
    if not subgroups:
        return True
        
    last_subgroup = subgroups[-1]
    time_since_last = timezone.now() - last_subgroup.timestamp
    return time_since_last >= timedelta(hours=2)

def get_verification_status(user, checklist, subgroups):
    """Get verification status and permissions"""
    return {
        'can_verify_supervisor': (
            user.user_type == 'shift_supervisor' and 
            checklist.status == 'pending' and 
            len(subgroups) == 6
        ),
        'can_verify_quality': (
            user.user_type == 'quality_supervisor' and 
            checklist.status == 'supervisor_approved'
        ),
        'last_verification': checklist.verifications.last(),
        'verification_count': checklist.verifications.count()
    }

def validate_measurements(checklist, subgroups):
    """Validate all measurements"""
    base_measurements = {
        'line_pressure_ok': 4.5 <= checklist.line_pressure <= 5.5,
        'uv_flow_input_ok': 11 <= checklist.uv_flow_input_pressure <= 15,
        'test_pressure_ok': 0.25 <= checklist.test_pressure_vacuum <= 0.3
    }
    
    return {
        'base_measurements': base_measurements,
        'all_base_ok': all(base_measurements.values()),
        'subgroup_measurements_ok': all(s.all_checks_passed for s in subgroups),
        'critical_issues': [
            issue for issue in get_critical_issues(checklist, subgroups)
            if issue['severity'] == 'critical'
        ]
    }

def process_concerns(concerns):
    """Process concerns with additional metadata"""
    return [{
        'concern': concern,
        'is_resolved': bool(concern.action_taken),
        'requires_attention': not concern.action_taken
    } for concern in concerns]
    

def calculate_timing_metrics(checklist, subgroups):
    """Calculate timing related metrics"""
    if not subgroups:
        return None
        
    return {
        'total_duration': (subgroups[-1].timestamp - checklist.created_at).total_seconds() / 3600,
        'average_interval': calculate_average_interval(subgroups),
        'completion_rate': len(subgroups) / ((timezone.now() - checklist.created_at).total_seconds() / 3600)
    }

def get_user_permissions(user, checklist):
    """Get user-specific permissions"""
    return {
        'can_edit': user.user_type == 'operator' and checklist.status == 'pending',
        'can_verify': user.user_type in ['shift_supervisor', 'quality_supervisor'],
        'can_add_concern': checklist.status != 'quality_approved',
        'can_view_all': user.user_type in ['shift_supervisor', 'quality_supervisor']
    }

def calculate_average_interval(subgroups):
    """Calculate average time interval between subgroups"""
    if len(subgroups) < 2:
        return None
        
    intervals = []
    for i in range(1, len(subgroups)):
        interval = (subgroups[i].timestamp - subgroups[i-1].timestamp).total_seconds() / 3600
        intervals.append(interval)
    
    return sum(intervals) / len(intervals)

def get_critical_issues(checklist, subgroups):
    """Identify critical issues in measurements"""
    issues = []
    
    # Check base measurements
    if not (4.5 <= checklist.line_pressure <= 5.5):
        issues.append({
            'type': 'base_measurement',
            'measurement': 'line_pressure',
            'value': checklist.line_pressure,
            'severity': 'critical'
        })
    
    # Check subgroup measurements
    for subgroup in subgroups:
        if not (-43 <= subgroup.uv_vacuum_test <= -35):
            issues.append({
                'type': 'subgroup',
                'subgroup': subgroup.subgroup_number,
                'measurement': 'uv_vacuum_test',
                'value': subgroup.uv_vacuum_test,
                'severity': 'critical'
            })
    
    return issues
    
    
    
# Verification Views
@login_required
@user_passes_test(lambda u: u.user_type == 'shift_supervisor')
def supervisor_verify(request, checklist_id):
    checklist = get_object_or_404(ChecklistBase, id=checklist_id)
    
    # Verify if checklist can be verified
    if checklist.status != 'pending':
        messages.error(request, 'This checklist has already been verified')
        return redirect('supervisor_dashboard')
        
    if checklist.subgroup_entries.count() < 6:
        messages.error(request, 'Cannot verify incomplete checklist. All 6 subgroups must be completed.')
        return redirect('checklist_detail', checklist_id=checklist.id)
    
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            action = request.POST.get('action', 'approve')
            
            # Perform validation checks
            measurements_ok = all([
                4.5 <= checklist.line_pressure <= 5.5,
                11 <= checklist.uv_flow_input_pressure <= 15,
                0.25 <= checklist.test_pressure_vacuum <= 0.3,
                checklist.oring_condition == 'OK',
                checklist.master_verification_lvdt == 'OK',
                checklist.good_bad_master_verification == 'OK',
                checklist.tool_alignment == 'OK'
            ])
            
            # Check subgroup measurements
            subgroups_ok = True
            measurement_issues = []
            for subgroup in checklist.subgroup_entries.all():
                if not (-43 <= subgroup.uv_vacuum_test <= -35):
                    subgroups_ok = False
                    measurement_issues.append(f"Subgroup {subgroup.subgroup_number}: UV vacuum test out of range")
                if not (30 <= subgroup.uv_flow_value <= 40):
                    subgroups_ok = False
                    measurement_issues.append(f"Subgroup {subgroup.subgroup_number}: UV flow value out of range")
            
            if action == 'approve':
                if not measurements_ok or not subgroups_ok:
                    message = "Warning: Some measurements are out of range:\n"
                    if not measurements_ok:
                        message += "- Initial measurements are out of range\n"
                    if measurement_issues:
                        message += "\n".join(measurement_issues)
                    messages.warning(request, message)
                    return render(request, 'main/verify_checklist.html', {
                        'form': form,
                        'checklist': checklist,
                        'verification_type': 'Supervisor',
                        'measurements_ok': measurements_ok,
                        'subgroups_ok': subgroups_ok,
                        'measurement_issues': measurement_issues
                    })
                
                checklist.status = 'supervisor_approved'
                success_message = 'Checklist approved successfully'
            else:
                checklist.status = 'rejected'
                success_message = 'Checklist rejected'
            
            checklist.supervisor_verified_at = timezone.now()
            checklist.supervisor_comments = form.cleaned_data['comments']
            checklist.save()
            
            # Create verification record
            Verification.objects.create(
                checklist=checklist,
                verified_by=request.user,
                verifier_type='supervisor',
                status=checklist.status,
                comments=form.cleaned_data['comments']
            )
            
            messages.success(request, success_message)
            return redirect('supervisor_dashboard')
    else:
        form = VerificationForm()
    
    # Pre-check measurements for the template
    measurements_ok = all([
        4.5 <= checklist.line_pressure <= 5.5,
        11 <= checklist.uv_flow_input_pressure <= 15,
        0.25 <= checklist.test_pressure_vacuum <= 0.3,
        checklist.oring_condition == 'OK',
        checklist.master_verification_lvdt == 'OK',
        checklist.good_bad_master_verification == 'OK',
        checklist.tool_alignment == 'OK'
    ])
    
    measurement_issues = []
    for subgroup in checklist.subgroup_entries.all():
        if not (-43 <= subgroup.uv_vacuum_test <= -35):
            measurement_issues.append(f"Subgroup {subgroup.subgroup_number}: UV vacuum test out of range")
        if not (30 <= subgroup.uv_flow_value <= 40):
            measurement_issues.append(f"Subgroup {subgroup.subgroup_number}: UV flow value out of range")
    
    return render(request, 'main/verify_checklist.html', {
        'form': form,
        'checklist': checklist,
        'verification_type': 'Supervisor',
        'measurements_ok': measurements_ok,
        'measurement_issues': measurement_issues,
        'subgroups': checklist.subgroup_entries.all().order_by('subgroup_number')
    })
    
@login_required
@user_passes_test(lambda u: u.user_type == 'quality_supervisor')
def quality_verify(request, checklist_id):
    checklist = get_object_or_404(ChecklistBase, id=checklist_id)
    
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            checklist.status = 'quality_approved'
            checklist.quality_verified_at = timezone.now()
            checklist.quality_comments = form.cleaned_data['comments']
            checklist.save()
            
            messages.success(request, 'Quality verification completed')
            return redirect('quality_dashboard')
    else:
        form = VerificationForm()
    
    return render(request, 'main/verify_checklist.html', {
        'form': form,
        'checklist': checklist,
        'verification_type': 'Quality'
    })

# Report Views
@login_required
def daily_report(request):
    date = request.GET.get('date', timezone.now().date())
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()
    
    checklists = ChecklistBase.objects.filter(shift__date=date)
    
    summary = {
        'total': checklists.count(),
        'pending': checklists.filter(status='pending').count(),
        'supervisor_approved': checklists.filter(status='supervisor_approved').count(),
        'quality_approved': checklists.filter(status='quality_approved').count(),
        'rejected': checklists.filter(status='rejected').count(),
    }
    
    return render(request, 'main/reports/daily_report.html', {
        'date': date,
        'checklists': checklists,
        'summary': summary
    })

@login_required
def weekly_report(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    checklists = ChecklistBase.objects.filter(
        shift__date__range=[start_date, end_date]
    ).order_by('shift__date')
    
    daily_stats = {}
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        daily_checklists = checklists.filter(shift__date=current_date)
        
        daily_stats[current_date] = {
            'total': daily_checklists.count(),
            'approved': daily_checklists.filter(status='quality_approved').count(),
            'rejected': daily_checklists.filter(status='rejected').count(),
        }
    
    return render(request, 'main/reports/weekly_report.html', {
        'start_date': start_date,
        'end_date': end_date,
        'daily_stats': daily_stats
    })

@login_required
def monthly_report(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    checklists = ChecklistBase.objects.filter(
        shift__date__range=[start_date, end_date]
    )
    
    # Calculate statistics by model
    model_stats = {}
    for model in ChecklistBase.MODEL_CHOICES:
        model_checklists = checklists.filter(selected_model=model[0])
        model_stats[model[0]] = {
            'total': model_checklists.count(),
            'approved': model_checklists.filter(status='quality_approved').count(),
            'rejected': model_checklists.filter(status='rejected').count(),
        }
    
    return render(request, 'main/reports/monthly_report.html', {
        'start_date': start_date,
        'end_date': end_date,
        'model_stats': model_stats
    })

# Profile Views
@login_required
def user_profile(request):
    return render(request, 'main/profile/user_profile.html', {
        'user': request.user
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'main/profile/edit_profile.html', {
        'form': form
    })

# API Views
@login_required
def validate_checklist(request):
    """API endpoint for validating checklist data"""
    if request.method == 'POST':
        data = request.POST
        errors = []
        
        # Validate line pressure
        line_pressure = float(data.get('line_pressure', 0))
        if not (4.5 <= line_pressure <= 5.5):
            errors.append("Line pressure must be between 4.5 and 5.5 bar")
        
        # Validate UV flow test pressure
        uv_pressure = float(data.get('uv_flow_test_pressure', 0))
        if not (11 <= uv_pressure <= 15):
            errors.append("UV flow test pressure must be between 11 and 15 kPa")
        
        # Validate UV vacuum test
        uv_vacuum = float(data.get('uv_vacuum_test', 0))
        if not (-43 <= uv_vacuum <= -35):
            errors.append("UV vacuum test must be between -43 and -35 kPa")
        
        return JsonResponse({
            'is_valid': len(errors) == 0,
            'errors': errors
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

    
@login_required
def operator_history(request):
    # Get all checklists grouped by date
    checklists = ChecklistBase.objects.filter(
        shift__operator=request.user
    ).annotate(
        subgroup_count=Count('subgroup_entries')
    ).order_by('-created_at')
    
    # Group by status
    pending_checklists = checklists.filter(status='pending')
    verified_checklists = checklists.filter(status__in=['supervisor_approved', 'quality_approved'])
    rejected_checklists = checklists.filter(status='rejected')
    
    context = {
        'title': 'Operator History',
        'pending_checklists': pending_checklists,
        'verified_checklists': verified_checklists,
        'rejected_checklists': rejected_checklists,
        'total_checklists': checklists.count()
    }
    
    return render(request, 'main/history/operator_history.html', context)
@login_required
@user_passes_test(lambda u: u.user_type == 'shift_supervisor')
def supervisor_history(request):
    entries = ChecklistBase.objects.filter(
        shift__shift_supervisor=request.user
    ).order_by('-created_at')
    
    pending_verifications = entries.filter(status='pending')
    verified_entries = entries.filter(status__in=['supervisor_approved', 'quality_approved', 'rejected'])
    
    return render(request, 'main/history/supervisor_history.html', {
        'pending_verifications': pending_verifications,
        'verified_entries': verified_entries,
        'title': 'Supervisor History'
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'quality_supervisor')
def quality_history(request):
    entries = ChecklistBase.objects.filter(
        shift__quality_supervisor=request.user
    ).order_by('-created_at')
    
    pending_verifications = entries.filter(status='supervisor_approved')
    verified_entries = entries.filter(status__in=['quality_approved', 'rejected'])
    
    return render(request, 'main/history/quality_history.html', {
        'pending_verifications': pending_verifications,
        'verified_entries': verified_entries,
        'title': 'Quality History'
    })    
    
    

@login_required
def user_settings(request):
    if request.method == 'POST':
        # Handle settings update
        notification_settings = request.POST.get('notification_settings', False)
        theme_preference = request.POST.get('theme_preference', 'light')
        
        # Save settings to user profile or settings model
        profile = request.user
        profile.email_notifications = notification_settings == 'on'
        profile.theme_preference = theme_preference
        profile.save()
        
        messages.success(request, 'Settings updated successfully')
        return redirect('user_settings')
    
    return render(request, 'main/profile/user_settings.html', {
        'user': request.user
    })
    
@login_required
def notification_settings(request):
    if request.method == 'POST':
        # Handle notification settings update
        request.user.email_notifications = request.POST.get('email_notifications') == 'on'
        request.user.save()
        messages.success(request, 'Notification settings updated successfully.')
        return redirect('user_settings')
        
    return render(request, 'main/settings/notifications.html', {
        'user': request.user,
        'active_tab': 'notifications'
    })

@login_required
def user_preferences(request):
    if request.method == 'POST':
        # Handle user preferences update
        messages.success(request, 'Preferences updated successfully.')
        return redirect('user_settings')
        
    return render(request, 'main/settings/preferences.html', {
        'user': request.user,
        'active_tab': 'preferences'
    })    