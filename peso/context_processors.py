from peso.models import PESOOffice, Employer, Jobseeker, Vacancy, UserProfile

def peso_global_context(request):
    """
    Supplies global context for the modern sidebar, user profile card,
    and top bar filter dropdowns across all pages.
    """
    try:
        user = getattr(request, 'user', None)
        profile = getattr(user, 'peso_profile', None) if user and user.is_authenticated else None
        
        pending_count = 0
        if user and user.is_authenticated and (user.is_superuser or (profile and profile.is_provincial_admin)):
            pending_count = UserProfile.objects.filter(approval_status=UserProfile.STATUS_PENDING).count()

        return {
            'peso_offices_list': PESOOffice.objects.filter(status='Active').order_by('name'),
            'total_employers_badge': Employer.objects.count(),
            'total_offices_badge': PESOOffice.objects.count(),
            'total_jobseekers_badge': Jobseeker.objects.count(),
            'total_vacancies_badge': Vacancy.objects.count(),
            'user_profile': profile,
            'pending_approvals_count': pending_count,
        }
    except Exception:
        return {
            'peso_offices_list': [],
            'total_employers_badge': 0,
            'total_offices_badge': 0,
            'total_jobseekers_badge': 0,
            'total_vacancies_badge': 0,
            'user_profile': None,
            'pending_approvals_count': 0,
        }
