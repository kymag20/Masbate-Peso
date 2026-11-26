from django.urls import path
from .views import (
    DashboardView,
    ProvincialReportView,
    JobseekerListView,
    EmployerListView,
    VacancyListView,
    ReferralListView,
    PlacementListView,
    ServiceListView,
    ProgramListView,
    JobFairListView,
    PESOOfficeListView,
)

app_name = 'database'

urlpatterns = [
    # Dashboard & Reports
    path('', DashboardView.as_view(), name='dashboard'),
    path('dashboard/', DashboardView.as_view(), name='dashboard_alt'),
    path('reports/', ProvincialReportView.as_view(), name='provincial_report'),

    # Registries
    path('jobseekers/', JobseekerListView.as_view(), name='jobseeker_list'),
    path('employers/', EmployerListView.as_view(), name='employer_list'),
    path('vacancies/', VacancyListView.as_view(), name='vacancy_list'),

    # Transactions
    path('referrals/', ReferralListView.as_view(), name='referral_list'),
    path('placements/', PlacementListView.as_view(), name='placement_list'),

    # Programs & Events
    path('services/', ServiceListView.as_view(), name='service_list'),
    path('programs/', ProgramListView.as_view(), name='program_list'),
    path('job-fairs/', JobFairListView.as_view(), name='jobfair_list'),

    # System
    path('offices/', PESOOfficeListView.as_view(), name='office_list'),
]
