from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register_user, name='register'),

    # Dashboard URLs
    path('', views.dashboard, name='dashboard'),
    path('operator/', views.operator_dashboard, name='operator_dashboard'),
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('quality/', views.quality_dashboard, name='quality_dashboard'),

    # History URLs
    path('history/operator/', views.operator_history, name='operator_history'),
    path('history/supervisor/', views.supervisor_history, name='supervisor_history'),
    path('history/quality/', views.quality_history, name='quality_history'),
path('checklist/<int:checklist_id>/export/', views.export_checklist_excel, name='export_checklist_excel'),
    # Checklist URLs
    path('checklist/create/', views.create_checklist, name='create_checklist'),
    path('checklist/<int:checklist_id>/', views.checklist_detail, name='checklist_detail'),
    path('checklist/<int:checklist_id>/subgroup/add/', views.add_subgroup, name='add_subgroup'),
    path('checklist/<int:checklist_id>/subgroup/<int:subgroup_id>/edit/', views.edit_subgroup, name='edit_subgroup'),  # New
    path('checklist/<int:checklist_id>/concern/add/', views.add_concern, name='add_concern'),  # New

   path('verification/<int:verification_id>/edit/', views.edit_verification, name='edit_verification'), 
    # Verification URLs
    path('checklist/<int:checklist_id>/verify/supervisor/', views.supervisor_verify, name='supervisor_verify'),
    path('checklist/<int:checklist_id>/verify/quality/', views.quality_verify, name='quality_verify'),

    # Reports URLs
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/daily/', views.daily_report, name='daily_report'),
    path('reports/weekly/', views.weekly_report, name='weekly_report'),
    path('reports/monthly/', views.monthly_report, name='monthly_report'),

    # Profile URLs
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # API URLs
    path('api/checklist/validate/', views.validate_checklist, name='validate_checklist'),
    path('api/subgroup/validate/', views.validate_subgroup, name='validate_subgroup'),  # New

    
        # User Settings URLs
    path('settings/', views.user_settings, name='user_settings'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    path('settings/preferences/', views.user_preferences, name='user_preferences'),
    
    path('subgroup/<int:subgroup_id>/verify/', 
         views.verify_subgroup_measurement, 
         name='verify_subgroup_measurement'),
    

]