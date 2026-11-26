from .models import PESOOffice, Employer, Jobseeker, Vacancy, UserProfile

def peso_global_context(request):
    """
    Supplies global context for the modern sidebar, user profile card,
    and top bar filter dropdowns across all pages.
    """
    context = {
        'peso_offices_list': PESOOffice.objects.filter(status='Active').order_by('name'),
        'total_employers_badge': Employer.objects.count(),
        'total_offices_badge': PESOOffice.objects.count(),
        'total_jobseekers_badge': Jobseeker.objects.count(),
        'total_vacancies_badge': Vacancy.objects.count(),
    }
    
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        profile = getattr(user, 'peso_profile', None)
        context['user_profile'] = profile
    else:
        context['user_profile'] = None
        
    return context
