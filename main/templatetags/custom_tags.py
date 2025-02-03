# main/templatetags/custom_tags.py

from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calculates percentage"""
    try:
        return round((float(value) / float(total)) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
    
@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def status_class(status):
    status_classes = {
        'pending': 'bg-warning',
        'supervisor_approved': 'bg-info',
        'quality_approved': 'bg-success',
        'rejected': 'bg-danger'
    }
    return status_classes.get(status, 'bg-secondary')


@register.filter
def timedelta_format(td):
    if not isinstance(td, timedelta):
        return ""
    
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


@register.filter
def divisibleby(queryset, verifier_type):
    """Filter verifications by verifier type"""
    return queryset.filter(verifier_type=verifier_type).first()
