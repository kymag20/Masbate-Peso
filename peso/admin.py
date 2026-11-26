from django.contrib import admin
from .models import (
    LookupChoice,
    PESOOffice,
    Employer,
    Jobseeker,
    Vacancy,
    Referral,
    Placement,
    Service,
    Program,
    JobFair,
    UserProfile,
)

admin.site.site_header = "Masbate Provincial PESO Database"
admin.site.site_title = "Masbate PESO Admin"
admin.site.index_title = "PESO Database Administration"

@admin.register(LookupChoice)
class LookupChoiceAdmin(admin.ModelAdmin):
    list_display = ('category', 'value', 'sort_order', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active')
    search_fields = ('value',)
    list_editable = ('sort_order', 'is_active')

@admin.register(PESOOffice)
class PESOOfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'lgu_type', 'head', 'contact_no', 'email', 'status')
    list_filter = ('lgu_type', 'status')
    search_fields = ('name', 'head', 'email')

@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ('employer_code', 'company_name', 'permit_no', 'industry', 'municipality', 'status')
    list_filter = ('status', 'municipality', 'industry')
    search_fields = ('employer_code', 'company_name', 'permit_no', 'contact_person')

@admin.register(Jobseeker)
class JobseekerAdmin(admin.ModelAdmin):
    list_display = ('jobseeker_code', 'full_name', 'sex', 'birth_date', 'age', 'highest_education', 'jobseeker_status', 'data_privacy_consent')
    list_filter = ('originating_peso', 'sex', 'jobseeker_status', 'highest_education', 'data_privacy_consent')
    search_fields = ('jobseeker_code', 'last_name', 'first_name', 'mobile_no')
    readonly_fields = ('jobseeker_code', 'age', 'created_at', 'updated_at')

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('vacancy_code', 'position_title', 'employer', 'peso_office', 'no_required', 'no_referred', 'no_hired', 'status')
    list_filter = ('status', 'peso_office', 'employment_type')
    search_fields = ('vacancy_code', 'position_title', 'employer__company_name')
    readonly_fields = ('vacancy_code', 'no_referred', 'no_hired', 'created_at', 'updated_at')

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referral_code', 'referral_date', 'jobseeker', 'position_referred', 'employer', 'peso_office', 'result')
    list_filter = ('result', 'peso_office', 'referral_date')
    search_fields = ('referral_code', 'jobseeker__last_name', 'position_referred', 'employer__company_name')
    readonly_fields = ('referral_code', 'created_at', 'updated_at')

@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ('placement_code', 'date_hired', 'jobseeker', 'position', 'employer', 'peso_office', 'verified')
    list_filter = ('verified', 'peso_office', 'date_hired')
    search_fields = ('placement_code', 'jobseeker__last_name', 'position', 'employer__company_name')
    readonly_fields = ('placement_code', 'created_at', 'updated_at')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_code', 'service_date', 'jobseeker', 'service_type', 'peso_office')
    list_filter = ('service_type', 'peso_office', 'service_date')
    search_fields = ('service_code', 'jobseeker__last_name', 'service_type')
    readonly_fields = ('service_code', 'created_at', 'updated_at')

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('program_code', 'date_enrolled', 'program_name', 'beneficiary', 'peso_office', 'status', 'amount')
    list_filter = ('program_name', 'status', 'peso_office')
    search_fields = ('program_code', 'beneficiary__last_name', 'program_name')
    readonly_fields = ('program_code', 'created_at', 'updated_at')

@admin.register(JobFair)
class JobFairAdmin(admin.ModelAdmin):
    list_display = ('job_fair_code', 'name', 'event_date', 'venue', 'status', 'participating_employers', 'total_hired')
    list_filter = ('status', 'peso_office', 'event_date')
    search_fields = ('job_fair_code', 'name', 'venue')
    readonly_fields = ('job_fair_code', 'total_hired', 'created_at', 'updated_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'peso_office', 'approval_status', 'approved_by', 'approved_at', 'created_at')
    list_filter = ('role', 'approval_status', 'peso_office')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    actions = ['approve_users', 'reject_users']

    def approve_users(self, request, queryset):
        for profile in queryset:
            profile.approve(request.user)
        self.message_user(request, f"Approved {queryset.count()} user(s).")
    approve_users.short_description = "Approve selected user accounts"

    def reject_users(self, request, queryset):
        for profile in queryset:
            profile.reject(request.user, "Rejected via admin action")
        self.message_user(request, f"Rejected {queryset.count()} user(s).")
    reject_users.short_description = "Reject selected user accounts"

