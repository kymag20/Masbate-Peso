import json
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone

from .models import (
    PESOOffice,
    Jobseeker,
    Employer,
    Vacancy,
    Referral,
    Placement,
    Service,
    Program,
    JobFair,
    UserProfile,
    DropdownChoice,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Consolidated Provincial PESO Management Dashboard replicating
    the official Excel 'Dashboard' sheet and modern SaaS dashboard design.
    """
    template_name = 'database/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = getattr(user, 'peso_profile', None)

        # Filters from query params
        office_filter_id = self.request.GET.get('office', '')
        period_filter = self.request.GET.get('period', '2026')

        # Municipal Encoder role scoping
        assigned_office = None
        if profile and profile.is_municipal_encoder and profile.peso_office:
            assigned_office = profile.peso_office
            office_filter_id = str(assigned_office.id)

        # Base querysets
        js_qs = Jobseeker.objects.all()
        emp_qs = Employer.objects.all()
        vac_qs = Vacancy.objects.all()
        ref_qs = Referral.objects.all()
        plc_qs = Placement.objects.all()
        svc_qs = Service.objects.all()
        prg_qs = Program.objects.all()
        jf_qs = JobFair.objects.all()

        # Apply office filter
        selected_office = None
        if office_filter_id:
            try:
                selected_office = PESOOffice.objects.get(pk=office_filter_id)
                js_qs = js_qs.filter(originating_peso=selected_office)
                vac_qs = vac_qs.filter(peso_office=selected_office)
                ref_qs = ref_qs.filter(peso_office=selected_office)
                plc_qs = plc_qs.filter(peso_office=selected_office)
                svc_qs = svc_qs.filter(peso_office=selected_office)
                prg_qs = prg_qs.filter(peso_office=selected_office)
                jf_qs = jf_qs.filter(peso_office=selected_office)
            except PESOOffice.DoesNotExist:
                pass

        # Apply year filter
        target_year = 2026
        if period_filter in ('2025', '2026'):
            target_year = int(period_filter)
            js_qs = js_qs.filter(registration_date__year=target_year)
            vac_qs = vac_qs.filter(date_posted__year=target_year)
            ref_qs = ref_qs.filter(referral_date__year=target_year)
            plc_qs = plc_qs.filter(date_hired__year=target_year)
            svc_qs = svc_qs.filter(service_date__year=target_year)
            prg_qs = prg_qs.filter(date_enrolled__year=target_year)
            jf_qs = jf_qs.filter(event_date__year=target_year)

        # -------------------------------------------------------------
        # 1. KPI Metrics
        # -------------------------------------------------------------
        total_jobseekers = js_qs.count()
        active_jobseekers = js_qs.filter(jobseeker_status__iexact='Active').count()
        
        total_employers = emp_qs.count()
        active_employers = emp_qs.filter(status__iexact='Active').count()
        
        open_vacancies = vac_qs.filter(status__iexact='Open').count()
        total_demand = vac_qs.aggregate(total=Sum('no_required'))['total'] or 0

        total_referrals = ref_qs.count()
        total_placements = plc_qs.count()

        # Placement Rate = confirmed placements / applicant referrals
        if total_referrals > 0:
            placement_rate = round((total_placements / total_referrals) * 100, 1)
        elif total_placements > 0:
            placement_rate = 100.0
        else:
            placement_rate = 0.0

        # -------------------------------------------------------------
        # 2. Sector / Demographic Breakdown (Horizontal Bars)
        # -------------------------------------------------------------
        male_count = js_qs.filter(sex__iexact='Male').count()
        female_count = js_qs.filter(sex__iexact='Female').count()
        
        pwd_count = js_qs.filter(Q(is_pwd__iexact='YES') | Q(is_pwd='1')).count()
        ofw_count = js_qs.filter(Q(is_returning_ofw__iexact='YES') | Q(is_returning_ofw='1')).count()
        displaced_count = js_qs.filter(Q(is_displaced_worker__iexact='YES') | Q(is_displaced_worker='1')).count()
        osy_count = js_qs.filter(Q(is_osy__iexact='YES') | Q(is_osy='1')).count()

        def pct(part, whole):
            return round((part / whole * 100), 1) if whole > 0 else 0

        demographics = {
            'male': {'count': male_count, 'pct': pct(male_count, total_jobseekers)},
            'female': {'count': female_count, 'pct': pct(female_count, total_jobseekers)},
            'pwd': {'count': pwd_count, 'pct': pct(pwd_count, total_jobseekers)},
            'ofw': {'count': ofw_count, 'pct': pct(ofw_count, total_jobseekers)},
            'displaced': {'count': displaced_count, 'pct': pct(displaced_count, total_jobseekers)},
            'osy': {'count': osy_count, 'pct': pct(osy_count, total_jobseekers)},
        }

        # -------------------------------------------------------------
        # 3. Monthly Activity Trend for Chart.js (Jan - Dec)
        # -------------------------------------------------------------
        chart_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_jobseekers = [0] * 12
        monthly_referrals = [0] * 12
        monthly_placements = [0] * 12

        # Group Jobseekers
        js_monthly = js_qs.values('registration_date__month').annotate(count=Count('id'))
        for item in js_monthly:
            m = item['registration_date__month']
            if m and 1 <= m <= 12:
                monthly_jobseekers[m - 1] = item['count']

        # Group Referrals
        ref_monthly = ref_qs.values('referral_date__month').annotate(count=Count('id'))
        for item in ref_monthly:
            m = item['referral_date__month']
            if m and 1 <= m <= 12:
                monthly_referrals[m - 1] = item['count']

        # Group Placements
        plc_monthly = plc_qs.values('date_hired__month').annotate(count=Count('id'))
        for item in plc_monthly:
            m = item['date_hired__month']
            if m and 1 <= m <= 12:
                monthly_placements[m - 1] = item['count']

        # -------------------------------------------------------------
        # 4. PESO Office Summary Table
        # -------------------------------------------------------------
        offices = PESOOffice.objects.all().order_by('name')
        if selected_office:
            offices = offices.filter(pk=selected_office.pk)

        office_summary = []
        for off in offices:
            # Scoped counts per office
            o_js = Jobseeker.objects.filter(originating_peso=off)
            o_ref = Referral.objects.filter(peso_office=off)
            o_plc = Placement.objects.filter(peso_office=off)

            if period_filter in ('2025', '2026'):
                o_js = o_js.filter(registration_date__year=target_year)
                o_ref = o_ref.filter(referral_date__year=target_year)
                o_plc = o_plc.filter(date_hired__year=target_year)

            js_cnt = o_js.count()
            ref_cnt = o_ref.count()
            plc_cnt = o_plc.count()

            if ref_cnt > 0:
                rate = round((plc_cnt / ref_cnt) * 100, 1)
            elif plc_cnt > 0:
                rate = 100.0
            else:
                rate = 0.0

            office_summary.append({
                'office': off,
                'jobseekers': js_cnt,
                'referrals': ref_cnt,
                'placements': plc_cnt,
                'placement_rate': rate,
            })

        # Inject into context
        context.update({
            'active_menu': 'dashboard',
            'selected_office_id': office_filter_id,
            'selected_period': period_filter,
            'selected_office': selected_office,
            'target_year': target_year,
            
            # KPI Counters
            'total_jobseekers': total_jobseekers,
            'active_jobseekers': active_jobseekers,
            'total_employers': total_employers,
            'active_employers': active_employers,
            'open_vacancies': open_vacancies,
            'total_demand': total_demand,
            'total_referrals': total_referrals,
            'total_placements': total_placements,
            'placement_rate': placement_rate,
            'total_services': svc_qs.count(),
            'total_programs': prg_qs.count(),
            'total_job_fairs': jf_qs.count(),

            # Demographics
            'demographics': demographics,

            # Office Table
            'office_summary': office_summary,

            # JSON Data for Chart.js
            'chart_months_json': json.dumps(chart_months),
            'chart_jobseekers_json': json.dumps(monthly_jobseekers),
            'chart_referrals_json': json.dumps(monthly_referrals),
            'chart_placements_json': json.dumps(monthly_placements),
        })
        return context


# ==============================================================================
# PROVINCIAL REPORT VIEW
# ==============================================================================
class ProvincialReportView(LoginRequiredMixin, TemplateView):
    template_name = 'database/provincial_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date_str = self.request.GET.get('start_date', '2026-01-01')
        end_date_str = self.request.GET.get('end_date', '2026-12-31')

        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = datetime.date(2026, 1, 1)
            end_date = datetime.date(2026, 12, 31)

        offices = PESOOffice.objects.all().order_by('name')
        report_data = []

        tot_js, tot_ref, tot_plc = 0, 0, 0

        for off in offices:
            js_count = Jobseeker.objects.filter(
                originating_peso=off,
                registration_date__range=[start_date, end_date]
            ).count()
            ref_count = Referral.objects.filter(
                peso_office=off,
                referral_date__range=[start_date, end_date]
            ).count()
            plc_count = Placement.objects.filter(
                peso_office=off,
                date_hired__range=[start_date, end_date]
            ).count()

            tot_js += js_count
            tot_ref += ref_count
            tot_plc += plc_count

            rate = round((plc_count / ref_count * 100), 1) if ref_count > 0 else (100.0 if plc_count > 0 else 0.0)

            report_data.append({
                'office': off,
                'jobseekers': js_count,
                'referrals': ref_count,
                'placements': plc_count,
                'rate': rate,
            })

        overall_rate = round((tot_plc / tot_ref * 100), 1) if tot_ref > 0 else 0.0

        context.update({
            'active_menu': 'reports',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'report_data': report_data,
            'tot_js': tot_js,
            'tot_ref': tot_ref,
            'tot_plc': tot_plc,
            'overall_rate': overall_rate,
            'tot_employers': Employer.objects.filter(registration_date__range=[start_date, end_date]).count(),
            'tot_vacancies': Vacancy.objects.filter(date_posted__range=[start_date, end_date]).count(),
        })
        return context


# ==============================================================================
# REGISTRY LIST VIEWS (Consistent Card + Search + Table UI)
# ==============================================================================
class JobseekerListView(LoginRequiredMixin, ListView):
    model = Jobseeker
    template_name = 'database/jobseeker_list.html'
    context_object_name = 'jobseekers'
    paginate_by = 25

    def get_queryset(self):
        qs = Jobseeker.objects.select_related('originating_peso').order_by('-registration_date', 'last_name')
        
        # Scoping for Municipal Encoders
        profile = getattr(self.request.user, 'peso_profile', None)
        if profile and profile.is_municipal_encoder and profile.peso_office:
            qs = qs.filter(originating_peso=profile.peso_office)

        # Search
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(jobseeker_id__icontains=q) |
                Q(mobile_no__icontains=q) |
                Q(preferred_occupation__icontains=q) |
                Q(primary_skill__icontains=q)
            )

        # Filters
        office_id = self.request.GET.get('office', '')
        if office_id and not (profile and profile.is_municipal_encoder):
            qs = qs.filter(originating_peso_id=office_id)

        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(jobseeker_status__iexact=status)

        education = self.request.GET.get('education', '')
        if education:
            qs = qs.filter(highest_education__icontains=education)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'jobseekers'
        context['q'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['selected_office_id'] = self.request.GET.get('office', '')
        return context


class EmployerListView(LoginRequiredMixin, ListView):
    model = Employer
    template_name = 'database/employer_list.html'
    context_object_name = 'employers'
    paginate_by = 25

    def get_queryset(self):
        qs = Employer.objects.all().order_by('company_name')
        
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(company_name__icontains=q) |
                Q(employer_id__icontains=q) |
                Q(permit_no__icontains=q) |
                Q(contact_person__icontains=q) |
                Q(industry__icontains=q)
            )

        industry = self.request.GET.get('industry', '')
        if industry:
            qs = qs.filter(industry__iexact=industry)

        municipality = self.request.GET.get('municipality', '')
        if municipality:
            qs = qs.filter(municipality__iexact=municipality)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'employers'
        context['q'] = self.request.GET.get('q', '')
        context['industry_filter'] = self.request.GET.get('industry', '')
        context['municipality_filter'] = self.request.GET.get('municipality', '')
        context['industries'] = Employer.objects.values_list('industry', flat=True).distinct()[:20]
        return context


class VacancyListView(LoginRequiredMixin, ListView):
    model = Vacancy
    template_name = 'database/vacancy_list.html'
    context_object_name = 'vacancies'
    paginate_by = 25

    def get_queryset(self):
        qs = Vacancy.objects.select_related('employer', 'peso_office').order_by('-date_posted')
        profile = getattr(self.request.user, 'peso_profile', None)
        if profile and profile.is_municipal_encoder and profile.peso_office:
            qs = qs.filter(peso_office=profile.peso_office)

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(position_title__icontains=q) |
                Q(vacancy_id__icontains=q) |
                Q(employer__company_name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'vacancies'
        context['q'] = self.request.GET.get('q', '')
        return context


class ReferralListView(LoginRequiredMixin, ListView):
    model = Referral
    template_name = 'database/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 25

    def get_queryset(self):
        qs = Referral.objects.select_related('jobseeker', 'vacancy', 'employer', 'peso_office').order_by('-referral_date')
        profile = getattr(self.request.user, 'peso_profile', None)
        if profile and profile.is_municipal_encoder and profile.peso_office:
            qs = qs.filter(peso_office=profile.peso_office)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'referrals'
        return context


class PlacementListView(LoginRequiredMixin, ListView):
    model = Placement
    template_name = 'database/placement_list.html'
    context_object_name = 'placements'
    paginate_by = 25

    def get_queryset(self):
        qs = Placement.objects.select_related('jobseeker', 'vacancy', 'employer', 'peso_office').order_by('-date_hired')
        profile = getattr(self.request.user, 'peso_profile', None)
        if profile and profile.is_municipal_encoder and profile.peso_office:
            qs = qs.filter(peso_office=profile.peso_office)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'placements'
        return context


class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'database/service_list.html'
    context_object_name = 'services'
    paginate_by = 25

    def get_queryset(self):
        qs = Service.objects.select_related('jobseeker', 'peso_office').order_by('-service_date')
        profile = getattr(self.request.user, 'peso_profile', None)
        if profile and profile.is_municipal_encoder and profile.peso_office:
            qs = qs.filter(peso_office=profile.peso_office)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'services'
        return context


class ProgramListView(LoginRequiredMixin, ListView):
    model = Program
    template_name = 'database/program_list.html'
    context_object_name = 'programs'
    paginate_by = 25

    def get_queryset(self):
        qs = Program.objects.select_related('beneficiary', 'peso_office').order_by('-date_enrolled')
        profile = getattr(self.request.user, 'peso_profile', None)
        if profile and profile.is_municipal_encoder and profile.peso_office:
            qs = qs.filter(peso_office=profile.peso_office)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'programs'
        return context


class JobFairListView(LoginRequiredMixin, ListView):
    model = JobFair
    template_name = 'database/jobfair_list.html'
    context_object_name = 'job_fairs'
    paginate_by = 25

    def get_queryset(self):
        qs = JobFair.objects.select_related('peso_office').order_by('-event_date')
        profile = getattr(self.request.user, 'peso_profile', None)
        if profile and profile.is_municipal_encoder and profile.peso_office:
            qs = qs.filter(peso_office=profile.peso_office)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'job_fairs'
        return context


class PESOOfficeListView(LoginRequiredMixin, ListView):
    model = PESOOffice
    template_name = 'database/office_list.html'
    context_object_name = 'offices'
    ordering = ['name']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'offices'
        return context
