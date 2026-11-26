from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DropdownChoice,
    PESOOffice,
    UserProfile,
    Jobseeker,
    Employer,
    Vacancy,
    Referral,
    Placement,
    Service,
    Program,
    JobFair,
)

# Custom branding for Masbate Provincial PESO Database
admin.site.site_header = "Masbate Provincial PESO Database"
admin.site.site_title = "Masbate PESO Admin Portal"
admin.site.index_title = "Provincial Employment Service Office (PESO) Administration"


# ==============================================================================
# 0. DROPDOWN CHOICES / REFERENCE LISTS ADMIN
# ==============================================================================
@admin.register(DropdownChoice)
class DropdownChoiceAdmin(admin.ModelAdmin):
    list_display = ('category', 'value', 'order', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active')
    search_fields = ('value', 'description')
    list_editable = ('order', 'is_active')
    ordering = ('category', 'order', 'value')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ("Option Details", {
            'fields': ('category', 'value', 'order', 'is_active', 'description')
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# ==============================================================================
# 1. PESO OFFICE MASTER LIST ADMIN
# ==============================================================================
@admin.register(PESOOffice)
class PESOOfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'lgu_type', 'head', 'contact_no', 'email', 'status', 'jobseekers_count', 'vacancies_count')
    list_filter = ('lgu_type', 'status', 'province')
    search_fields = ('name', 'head', 'email', 'contact_no', 'address')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ("Office Information", {
            'fields': ('office_id', 'name', 'lgu_type', 'province', 'status')
        }),
        ("Contact & Leadership", {
            'fields': ('head', 'contact_no', 'email', 'address')
        }),
        ("Additional Notes", {
            'fields': ('remarks',)
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def jobseekers_count(self, obj):
        return obj.jobseekers.count()
    jobseekers_count.short_description = "Jobseekers"

    def vacancies_count(self, obj):
        return obj.vacancies.count()
    vacancies_count.short_description = "Vacancies"


# ==============================================================================
# USER PESO PROFILE ADMIN
# ==============================================================================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'peso_office', 'contact_no', 'created_at')
    list_filter = ('role', 'peso_office')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'contact_no')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ("User & Role Mapping", {
            'fields': ('user', 'role', 'peso_office', 'contact_no')
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# ==============================================================================
# 2. JOBSEEKER ADMIN
# ==============================================================================
@admin.register(Jobseeker)
class JobseekerAdmin(admin.ModelAdmin):
    list_display = (
        'jobseeker_id',
        'full_name',
        'sex',
        'birth_date',
        'computed_age',
        'originating_peso',
        'highest_education',
        'employment_status',
        'jobseeker_status',
        'dpa_consent_badge',
    )
    list_filter = (
        'originating_peso',
        'sex',
        'civil_status',
        'highest_education',
        'employment_status',
        'jobseeker_status',
        'is_pwd',
        'is_returning_ofw',
        'is_displaced_worker',
        'is_osy',
        'privacy_consent',
        'registration_date',
    )
    search_fields = (
        'jobseeker_id',
        'last_name',
        'first_name',
        'middle_name',
        'mobile_no',
        'preferred_occupation',
        'primary_skill',
        'course',
        'school',
    )
    readonly_fields = (
        'jobseeker_id',
        'computed_age',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    fieldsets = (
        ("System Identification", {
            'fields': ('jobseeker_id', 'registration_date', 'originating_peso')
        }),
        ("Personal Profile", {
            'fields': (
                ('last_name', 'first_name', 'middle_name'),
                ('sex', 'birth_date', 'computed_age', 'civil_status'),
            )
        }),
        ("Residence & Contact", {
            'fields': (
                ('barangay', 'municipality', 'province'),
                ('mobile_no',),
            )
        }),
        ("Education & Skills", {
            'fields': (
                ('highest_education', 'course', 'school'),
                ('primary_skill', 'other_skills', 'preferred_occupation'),
            )
        }),
        ("Employment & Registry Status", {
            'fields': (
                ('employment_status', 'jobseeker_status'),
            )
        }),
        ("Special / Priority Client Categories", {
            'fields': (
                ('is_pwd', 'is_returning_ofw', 'is_displaced_worker', 'is_osy'),
            )
        }),
        ("Data Privacy Act (RA 10173) Compliance", {
            'fields': ('privacy_consent', 'remarks'),
            'description': "Requires explicit consent from applicant for DOLE/PEIS profiling."
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def computed_age(self, obj):
        return obj.age
    computed_age.short_description = "Age"

    def dpa_consent_badge(self, obj):
        if obj.privacy_consent:
            return format_html('<span style="color: green; font-weight: bold;">&#10004; Consented</span>')
        return format_html('<span style="color: red; font-weight: bold;">&#10008; Missing</span>')
    dpa_consent_badge.short_description = "RA 10173 Consent"


# ==============================================================================
# 3. EMPLOYER ADMIN
# ==============================================================================
@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = (
        'employer_id',
        'company_name',
        'permit_no',
        'industry',
        'establishment_size',
        'contact_person',
        'contact_no',
        'municipality',
        'status',
    )
    list_filter = ('industry', 'establishment_size', 'status', 'municipality', 'registration_date')
    search_fields = ('employer_id', 'company_name', 'permit_no', 'contact_person', 'email', 'contact_no')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ("Establishment Information", {
            'fields': ('employer_id', 'registration_date', 'permit_no', 'company_name', 'industry', 'establishment_size', 'status')
        }),
        ("Contact & Location Details", {
            'fields': ('contact_person', 'position', 'contact_no', 'email', 'address', 'municipality', 'province')
        }),
        ("Additional Remarks", {
            'fields': ('remarks',)
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# ==============================================================================
# 4. VACANCY ADMIN
# ==============================================================================
class ReferralInline(admin.TabularInline):
    model = Referral
    extra = 0
    fields = ('referral_id', 'jobseeker', 'referral_date', 'result')
    readonly_fields = ('referral_id', 'jobseeker', 'referral_date')
    show_change_link = True


class PlacementInline(admin.TabularInline):
    model = Placement
    extra = 0
    fields = ('placement_id', 'jobseeker', 'date_hired', 'position', 'verified')
    readonly_fields = ('placement_id', 'jobseeker', 'date_hired', 'position')
    show_change_link = True


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = (
        'vacancy_id',
        'position_title',
        'employer',
        'peso_office',
        'no_required',
        'computed_referred',
        'computed_hired',
        'employment_type',
        'date_posted',
        'status',
    )
    list_filter = ('peso_office', 'employment_type', 'status', 'date_posted')
    search_fields = ('vacancy_id', 'position_title', 'employer__company_name', 'skills_requirement')
    readonly_fields = ('vacancy_id', 'computed_referred', 'computed_hired', 'created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = [ReferralInline, PlacementInline]

    fieldsets = (
        ("Vacancy Overview", {
            'fields': ('vacancy_id', 'employer', 'peso_office', 'position_title', 'no_required', 'status')
        }),
        ("Requirements & Terms", {
            'fields': (
                'employment_type',
                'work_location',
                'salary',
                'education_requirement',
                'experience_requirement',
                'skills_requirement',
            )
        }),
        ("Posting Schedule", {
            'fields': ('date_posted', 'closing_date', 'remarks')
        }),
        ("Referral & Placement Counters (Computed)", {
            'fields': ('computed_referred', 'computed_hired'),
            'description': "Dynamically computed based on transaction records."
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def computed_referred(self, obj):
        return obj.no_referred
    computed_referred.short_description = "No. Referred"

    def computed_hired(self, obj):
        return obj.no_hired
    computed_hired.short_description = "No. Hired"


# ==============================================================================
# 5. REFERRAL ADMIN
# ==============================================================================
@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        'referral_id',
        'referral_date',
        'jobseeker',
        'vacancy',
        'employer',
        'peso_office',
        'result',
        'follow_up_needed',
    )
    list_filter = ('peso_office', 'result', 'follow_up_needed', 'referral_date')
    search_fields = (
        'referral_id',
        'jobseeker__last_name',
        'jobseeker__first_name',
        'vacancy__position_title',
        'employer__company_name',
        'position_referred',
    )
    readonly_fields = ('referral_id', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ("Transaction Details", {
            'fields': ('referral_id', 'referral_date', 'peso_office')
        }),
        ("Matched Entities", {
            'fields': ('jobseeker', 'vacancy', 'employer', 'position_referred')
        }),
        ("Outcome & Follow-up", {
            'fields': ('result', 'interview_date', 'result_date', 'follow_up_needed', 'remarks')
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# ==============================================================================
# 6. PLACEMENT ADMIN
# ==============================================================================
@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = (
        'placement_id',
        'date_hired',
        'jobseeker',
        'position',
        'employer',
        'peso_office',
        'employment_type',
        'verified',
    )
    list_filter = ('peso_office', 'employment_type', 'verified', 'date_hired')
    search_fields = (
        'placement_id',
        'jobseeker__last_name',
        'jobseeker__first_name',
        'position',
        'employer__company_name',
    )
    readonly_fields = ('placement_id', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ("Placement Identification", {
            'fields': ('placement_id', 'date_hired', 'peso_office', 'verified')
        }),
        ("Hired Details", {
            'fields': ('jobseeker', 'vacancy', 'employer', 'position', 'employment_type', 'work_location', 'starting_salary')
        }),
        ("Remarks", {
            'fields': ('remarks',)
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# ==============================================================================
# 7. SERVICE DELIVERED ADMIN
# ==============================================================================
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_id', 'service_date', 'jobseeker', 'peso_office', 'service_type', 'referred_to', 'follow_up_date')
    list_filter = ('peso_office', 'service_type', 'service_date')
    search_fields = ('service_id', 'jobseeker__last_name', 'jobseeker__first_name', 'service_type', 'outcome')
    readonly_fields = ('service_id', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ("Service Record", {
            'fields': ('service_id', 'service_date', 'peso_office', 'jobseeker', 'service_type')
        }),
        ("Action & Outcomes", {
            'fields': ('outcome', 'referred_to', 'follow_up_date', 'remarks')
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# ==============================================================================
# 8. PROGRAM MONITORING ADMIN
# ==============================================================================
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        'program_id',
        'date_enrolled',
        'program_name',
        'beneficiary',
        'peso_office',
        'target_group',
        'amount',
        'status',
        'completion_date',
    )
    list_filter = ('peso_office', 'program_name', 'status', 'date_enrolled')
    search_fields = (
        'program_id',
        'program_name',
        'beneficiary__last_name',
        'beneficiary__first_name',
        'target_group',
        'assistance',
    )
    readonly_fields = ('program_id', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ("Program Identification", {
            'fields': ('program_id', 'date_enrolled', 'peso_office', 'program_name', 'status')
        }),
        ("Beneficiary & Assistance", {
            'fields': ('beneficiary', 'target_group', 'assistance', 'amount', 'completion_date', 'remarks')
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# ==============================================================================
# 9. JOB FAIR MONITORING ADMIN
# ==============================================================================
@admin.register(JobFair)
class JobFairAdmin(admin.ModelAdmin):
    list_display = (
        'job_fair_id',
        'name',
        'event_date',
        'peso_office',
        'venue',
        'status',
        'participating_employers',
        'registered_applicants',
        'hired_on_the_spot',
        'computed_total_hired',
    )
    list_filter = ('peso_office', 'status', 'event_date')
    search_fields = ('job_fair_id', 'name', 'organizer', 'venue')
    readonly_fields = ('job_fair_id', 'computed_total_hired', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ("Event Overview", {
            'fields': ('job_fair_id', 'event_date', 'name', 'peso_office', 'organizer', 'venue', 'status')
        }),
        ("Key Accomplishment Indicators", {
            'fields': (
                ('participating_employers', 'vacancies_offered'),
                ('registered_applicants', 'applicants_referred'),
                ('hired_on_the_spot', 'hired_after_event', 'computed_total_hired'),
            )
        }),
        ("Remarks", {
            'fields': ('remarks',)
        }),
        ("Audit Trail", {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def computed_total_hired(self, obj):
        return obj.total_hired
    computed_total_hired.short_description = "Total Hired"
