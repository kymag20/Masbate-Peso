from django.urls import path
from .views import (
    DashboardView,
    ProvincialReportView,
    JobseekerListView,
    JobseekerCreateView,
    JobseekerUpdateView,
    EmployerListView,
    EmployerCreateView,
    EmployerUpdateView,
    VacancyListView,
    ReferralListView,
    PlacementListView,
    ServiceListView,
    ProgramListView,
    JobFairListView,
    PESOOfficeListView,
    UserRegisterView,
    UserManagementView,
    UserApproveView,
    UserRejectView,
    HealthCheckView,
)

app_name = 'database'

urlpatterns = [
    # Health check (safe diagnostics)
    path('health/', HealthCheckView.as_view(), name='health_check'),

    # Dashboard & Reports
    path('', DashboardView.as_view(), name='dashboard'),
    path('dashboard/', DashboardView.as_view(), name='dashboard_alt'),
    path('reports/', ProvincialReportView.as_view(), name='provincial_report'),

    # Registries & CRUD
    path('jobseekers/', JobseekerListView.as_view(), name='jobseeker_list'),
    path('jobseekers/add/', JobseekerCreateView.as_view(), name='jobseeker_add'),
    path('jobseekers/<int:pk>/edit/', JobseekerUpdateView.as_view(), name='jobseeker_edit'),

    path('employers/', EmployerListView.as_view(), name='employer_list'),
    path('employers/add/', EmployerCreateView.as_view(), name='employer_add'),
    path('employers/<int:pk>/edit/', EmployerUpdateView.as_view(), name='employer_edit'),

    path('vacancies/', VacancyListView.as_view(), name='vacancy_list'),

    # Transactions
    path('referrals/', ReferralListView.as_view(), name='referral_list'),
    path('placements/', PlacementListView.as_view(), name='placement_list'),

    # Programs & Events
    path('services/', ServiceListView.as_view(), name='service_list'),
    path('programs/', ProgramListView.as_view(), name='program_list'),
    path('job-fairs/', JobFairListView.as_view(), name='jobfair_list'),

    # User Management & Admin Approval Workflow
    path('register/', UserRegisterView.as_view(), name='register'),
    path('users/', UserManagementView.as_view(), name='user_management'),
    path('users/<int:pk>/approve/', UserApproveView.as_view(), name='user_approve'),
    path('users/<int:pk>/reject/', UserRejectView.as_view(), name='user_reject'),

    # System
    path('offices/', PESOOfficeListView.as_view(), name='office_list'),
]
