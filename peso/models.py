import datetime
from django.db import models
from django.utils import timezone
from django.conf import settings


def generate_sequential_code(prefix, model_class, code_field, date_ref=None):
    """
    Generate sequential code format: PREFIX-YYYYMM-XXXXX (e.g. JS-202611-00001).
    Ensures unique incrementing per month.
    """
    target_date = date_ref or timezone.localdate()
    ym_str = target_date.strftime('%Y%m')
    prefix_pattern = f"{prefix}-{ym_str}-"

    lookup = {f"{code_field}__startswith": prefix_pattern}
    latest_obj = model_class.objects.filter(**lookup).order_by(f"-{code_field}").first()

    if latest_obj:
        val = getattr(latest_obj, code_field, '')
        try:
            current_num = int(val.split('-')[-1])
            new_num = current_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1

    candidate = f"{prefix_pattern}{new_num:05d}"
    while model_class.objects.filter(**{code_field: candidate}).exists():
        new_num += 1
        candidate = f"{prefix_pattern}{new_num:05d}"

    return candidate


# ==============================================================================
# 0. LOOKUP CHOICES (Replaces Excel 'Lists' Sheet)
# ==============================================================================
class LookupChoice(models.Model):
    """
    Centralized table storing editable dropdown values replacing the Excel 'Lists' sheet.
    """
    category = models.CharField(max_length=50, db_index=True, verbose_name="Category")
    value = models.CharField(max_length=150, verbose_name="Value")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Sort Order")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'sort_order', 'value']
        constraints = [
            models.UniqueConstraint(fields=['category', 'value'], name='unique_category_lookup_value')
        ]
        verbose_name = "Lookup Choice"
        verbose_name_plural = "Lookup Choices"

    def __str__(self):
        return f"{self.category}: {self.value}"

    @classmethod
    def get_choices(cls, category):
        items = cls.objects.filter(category=category, is_active=True).values_list('value', flat=True)
        return [(item, item) for item in items]


# ==============================================================================
# 1. PESO OFFICE MASTER LIST
# ==============================================================================
class PESOOffice(models.Model):
    """
    Provincial, City, and Municipal PESO offices across Masbate.
    """
    office_id = models.CharField(max_length=50, unique=True, verbose_name="PESO Office ID")
    name = models.CharField(max_length=150, unique=True, db_index=True, verbose_name="PESO Office Name")
    lgu_type = models.CharField(max_length=50, default="Municipality", db_index=True, verbose_name="LGU Type")
    province = models.CharField(max_length=100, default="Masbate", verbose_name="Province")
    head = models.CharField(max_length=150, blank=True, verbose_name="PESO Manager / Head")
    contact_no = models.CharField(max_length=100, blank=True, verbose_name="Contact No.")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Office Address")
    status = models.CharField(max_length=50, default="Active", db_index=True, verbose_name="Status")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'status']),
        ]
        verbose_name = "PESO Office"
        verbose_name_plural = "PESO Offices"

    def __str__(self):
        return self.name

    def clean(self):
        if self.name:
            self.name = self.name.strip()
            if not self.office_id:
                self.office_id = self.name.upper().replace(' ', '_')


# ==============================================================================
# 2. EMPLOYER MASTER REGISTRY
# ==============================================================================
class Employer(models.Model):
    """
    Employer / Establishment Registry.
    NOTE: Company name and permit no are NOT unique per user requirement:
    Excel contains duplicate names and permit numbers across branches/registrations.
    """
    employer_code = models.CharField(max_length=50, db_index=True, verbose_name="Employer ID / Code")
    registration_date = models.DateField(default=timezone.now, db_index=True, verbose_name="Registration Date")
    permit_no = models.CharField(max_length=100, blank=True, db_index=True, verbose_name="Permit No.")
    company_name = models.CharField(max_length=255, db_index=True, verbose_name="Employer / Company Name")
    industry = models.CharField(max_length=150, blank=True, db_index=True, verbose_name="Industry")
    establishment_size = models.CharField(max_length=50, blank=True, verbose_name="Establishment Size")
    contact_person = models.CharField(max_length=150, blank=True, verbose_name="Contact Person")
    position = models.CharField(max_length=100, blank=True, verbose_name="Position")
    contact_no = models.CharField(max_length=100, blank=True, verbose_name="Contact No.")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Address")
    municipality = models.CharField(max_length=100, default="City of Masbate", db_index=True, verbose_name="Municipality / City")
    province = models.CharField(max_length=100, default="Masbate", verbose_name="Province")
    status = models.CharField(max_length=50, default="Active", db_index=True, verbose_name="Status")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name']
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['permit_no']),
            models.Index(fields=['status']),
            models.Index(fields=['registration_date']),
            models.Index(fields=['municipality']),
        ]
        verbose_name = "Employer"
        verbose_name_plural = "Employers"

    def __str__(self):
        return f"{self.employer_code} - {self.company_name}"

    def save(self, *args, **kwargs):
        if self.company_name:
            self.company_name = self.company_name.strip()
        if self.permit_no:
            self.permit_no = self.permit_no.strip()
        if not self.employer_code:
            self.employer_code = generate_sequential_code('EMP', Employer, 'employer_code', self.registration_date)
        super().save(*args, **kwargs)


# ==============================================================================
# 3. JOBSEEKER MASTER REGISTRY
# ==============================================================================
class Jobseeker(models.Model):
    """
    Jobseeker Registry conforming to DOLE/PEIS standards and RA 10173 Data Privacy Act.
    Age is auto-computed from birth_date.
    """
    jobseeker_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Jobseeker ID / Code"
    )
    registration_date = models.DateField(default=timezone.now, db_index=True, verbose_name="Registration Date")
    originating_peso = models.ForeignKey(
        PESOOffice,
        on_delete=models.PROTECT,
        related_name='jobseekers',
        db_index=True,
        verbose_name="Originating PESO"
    )
    last_name = models.CharField(max_length=100, db_index=True, verbose_name="Last Name")
    first_name = models.CharField(max_length=100, db_index=True, verbose_name="First Name")
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Middle Name")
    sex = models.CharField(max_length=20, default="Male", verbose_name="Sex")
    birth_date = models.DateField(db_index=True, verbose_name="Birth Date")
    civil_status = models.CharField(max_length=50, default="Single", verbose_name="Civil Status")
    barangay = models.CharField(max_length=150, verbose_name="Barangay")
    municipality = models.CharField(max_length=150, verbose_name="Municipality / City")
    province = models.CharField(max_length=100, default="Masbate", verbose_name="Province")
    mobile_no = models.CharField(max_length=50, blank=True, verbose_name="Mobile No.")
    highest_education = models.CharField(max_length=100, verbose_name="Highest Education")
    course = models.CharField(max_length=200, blank=True, verbose_name="Course / Program")
    school = models.CharField(max_length=200, blank=True, verbose_name="School")
    primary_skill = models.CharField(max_length=200, blank=True, verbose_name="Primary Skill")
    other_skills = models.TextField(blank=True, verbose_name="Other Skills")
    preferred_occupation = models.CharField(max_length=200, blank=True, verbose_name="Preferred Occupation")
    employment_status = models.CharField(max_length=100, default="Unemployed", db_index=True, verbose_name="Employment Status")
    jobseeker_status = models.CharField(max_length=50, default="Active", db_index=True, verbose_name="Jobseeker Status")

    # Priority demographic categories
    is_pwd = models.BooleanField(default=False, verbose_name="PWD")
    is_returning_ofw = models.BooleanField(default=False, verbose_name="Returning OFW")
    is_displaced_worker = models.BooleanField(default=False, verbose_name="Displaced Worker")
    is_osy = models.BooleanField(default=False, verbose_name="Out-of-School Youth")

    # Extra fields required
    data_privacy_consent = models.BooleanField(
        default=True,
        verbose_name="Data Privacy Consent (RA 10173)",
        help_text="Consent given for processing personal information under RA 10173."
    )
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-registration_date', 'last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['registration_date']),
            models.Index(fields=['jobseeker_status']),
            models.Index(fields=['originating_peso']),
        ]
        verbose_name = "Jobseeker"
        verbose_name_plural = "Jobseekers"

    def __str__(self):
        return f"{self.jobseeker_code} - {self.full_name}"

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.last_name}, {self.first_name} {self.middle_name}"
        return f"{self.last_name}, {self.first_name}"

    @property
    def age(self):
        """Auto-computed property from birth_date (not stored)."""
        if not self.birth_date:
            return None
        today = timezone.localdate()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    def save(self, *args, **kwargs):
        if self.first_name:
            self.first_name = self.first_name.strip()
        if self.last_name:
            self.last_name = self.last_name.strip()
        if self.middle_name:
            self.middle_name = self.middle_name.strip()
        if not self.jobseeker_code:
            self.jobseeker_code = generate_sequential_code('JS', Jobseeker, 'jobseeker_code', self.registration_date)
        super().save(*args, **kwargs)


# ==============================================================================
# 4. JOB VACANCY REGISTRY
# ==============================================================================
class Vacancy(models.Model):
    """
    Employer Job Vacancies.
    'no_referred' and 'no_hired' are computed from Referrals and Placements.
    """
    vacancy_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Vacancy ID / Code"
    )
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='vacancies', db_index=True, verbose_name="Employer")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='vacancies', db_index=True, verbose_name="PESO Office")
    position_title = models.CharField(max_length=200, db_index=True, verbose_name="Position Title")
    no_required = models.PositiveIntegerField(default=1, verbose_name="No. Required")
    education_requirement = models.CharField(max_length=150, blank=True, verbose_name="Education Requirement")
    experience_requirement = models.CharField(max_length=200, blank=True, verbose_name="Experience Requirement")
    skills_requirement = models.TextField(blank=True, verbose_name="Skills / Qualifications")
    employment_type = models.CharField(max_length=50, default="Permanent", verbose_name="Employment Type")
    work_location = models.CharField(max_length=200, blank=True, verbose_name="Work Location")
    salary = models.CharField(max_length=100, blank=True, verbose_name="Salary / Rate")
    date_posted = models.DateField(default=timezone.now, db_index=True, verbose_name="Date Posted")
    closing_date = models.DateField(null=True, blank=True, verbose_name="Closing Date")
    status = models.CharField(max_length=50, default="Open", db_index=True, verbose_name="Status")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_posted', 'position_title']
        indexes = [
            models.Index(fields=['date_posted']),
            models.Index(fields=['status']),
            models.Index(fields=['peso_office']),
            models.Index(fields=['position_title']),
        ]
        verbose_name = "Job Vacancy"
        verbose_name_plural = "Job Vacancies"

    def __str__(self):
        return f"{self.vacancy_code} - {self.position_title} ({self.employer.company_name})"

    @property
    def no_referred(self):
        """Computed count of applicant referrals."""
        return self.referrals.count()

    @property
    def no_hired(self):
        """Computed count of confirmed hires."""
        return self.placements.count()

    def save(self, *args, **kwargs):
        if not self.vacancy_code:
            self.vacancy_code = generate_sequential_code('VAC', Vacancy, 'vacancy_code', self.date_posted)
        super().save(*args, **kwargs)


# ==============================================================================
# 5. REFERRAL TRANSACTIONS
# ==============================================================================
class Referral(models.Model):
    """
    Applicant Referral transactions linking Jobseekers to Vacancies.
    """
    referral_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Referral ID / Code"
    )
    jobseeker = models.ForeignKey(Jobseeker, on_delete=models.PROTECT, related_name='referrals', db_index=True, verbose_name="Jobseeker")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='referrals', db_index=True, verbose_name="Vacancy")
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='referrals', db_index=True, verbose_name="Employer")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='referrals', db_index=True, verbose_name="PESO Office")
    referral_date = models.DateField(default=timezone.now, db_index=True, verbose_name="Referral Date")
    position_referred = models.CharField(max_length=200, verbose_name="Position Referred")
    result = models.CharField(max_length=50, default="Referred", db_index=True, verbose_name="Referral Result")
    interview_date = models.DateField(null=True, blank=True, verbose_name="Interview Date")
    result_date = models.DateField(null=True, blank=True, verbose_name="Result Date")
    follow_up_needed = models.BooleanField(default=False, verbose_name="Follow-up Needed")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-referral_date']
        indexes = [
            models.Index(fields=['referral_date']),
            models.Index(fields=['result']),
            models.Index(fields=['peso_office']),
        ]
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"

    def __str__(self):
        return f"{self.referral_code}: {self.jobseeker.full_name} -> {self.position_referred}"

    def clean(self):
        if self.vacancy and not self.employer_id:
            self.employer = self.vacancy.employer
        if self.vacancy and not self.position_referred:
            self.position_referred = self.vacancy.position_title

    def save(self, *args, **kwargs):
        self.clean()
        if not self.referral_code:
            self.referral_code = generate_sequential_code('REF', Referral, 'referral_code', self.referral_date)
        super().save(*args, **kwargs)


# ==============================================================================
# 6. PLACEMENT TRANSACTIONS
# ==============================================================================
class Placement(models.Model):
    """
    Confirmed hiring/placement outcomes.
    """
    placement_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Placement ID / Code"
    )
    jobseeker = models.ForeignKey(Jobseeker, on_delete=models.PROTECT, related_name='placements', db_index=True, verbose_name="Jobseeker")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.SET_NULL, null=True, blank=True, related_name='placements', verbose_name="Vacancy")
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT, related_name='placements', db_index=True, verbose_name="Employer")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='placements', db_index=True, verbose_name="PESO Office")
    date_hired = models.DateField(default=timezone.now, db_index=True, verbose_name="Date Hired")
    position = models.CharField(max_length=200, verbose_name="Position")
    employment_type = models.CharField(max_length=50, default="Permanent", verbose_name="Employment Type")
    work_location = models.CharField(max_length=200, blank=True, verbose_name="Work Location")
    starting_salary = models.CharField(max_length=100, blank=True, verbose_name="Starting Salary")
    verified = models.BooleanField(default=True, db_index=True, verbose_name="Placement Verified")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_hired']
        indexes = [
            models.Index(fields=['date_hired']),
            models.Index(fields=['verified']),
            models.Index(fields=['peso_office']),
        ]
        verbose_name = "Placement"
        verbose_name_plural = "Placements"

    def __str__(self):
        return f"{self.placement_code}: {self.jobseeker.full_name} hired at {self.employer.company_name}"

    def clean(self):
        if self.vacancy and not self.employer_id:
            self.employer = self.vacancy.employer
        if self.vacancy and not self.position:
            self.position = self.vacancy.position_title

    def save(self, *args, **kwargs):
        self.clean()
        if not self.placement_code:
            self.placement_code = generate_sequential_code('PLC', Placement, 'placement_code', self.date_hired)
        super().save(*args, **kwargs)


# ==============================================================================
# 7. PESO SERVICES DELIVERED
# ==============================================================================
class Service(models.Model):
    """
    Log of individual employment facilitation services delivered to clients.
    """
    service_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Service ID / Code"
    )
    jobseeker = models.ForeignKey(Jobseeker, on_delete=models.CASCADE, related_name='services', db_index=True, verbose_name="Jobseeker / Client")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='services', db_index=True, verbose_name="PESO Office")
    service_date = models.DateField(default=timezone.now, db_index=True, verbose_name="Service Date")
    service_type = models.CharField(max_length=100, db_index=True, verbose_name="Service Type")
    outcome = models.TextField(blank=True, verbose_name="Outcome / Action Taken")
    referred_to = models.CharField(max_length=200, blank=True, verbose_name="Referred To")
    follow_up_date = models.DateField(null=True, blank=True, verbose_name="Follow-up Date")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-service_date']
        indexes = [
            models.Index(fields=['service_date']),
            models.Index(fields=['service_type']),
            models.Index(fields=['peso_office']),
        ]
        verbose_name = "PESO Service Delivered"
        verbose_name_plural = "PESO Services Delivered"

    def __str__(self):
        return f"{self.service_code}: {self.service_type} - {self.jobseeker.full_name}"

    def save(self, *args, **kwargs):
        if not self.service_code:
            self.service_code = generate_sequential_code('SVC', Service, 'service_code', self.service_date)
        super().save(*args, **kwargs)


# ==============================================================================
# 8. PESO PROGRAM MONITORING
# ==============================================================================
class Program(models.Model):
    """
    Program monitoring (SPES, GIP, JobStart, TUPAD, Livelihood).
    """
    program_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Program ID / Code"
    )
    date_enrolled = models.DateField(default=timezone.now, db_index=True, verbose_name="Date")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='programs', db_index=True, verbose_name="PESO Office")
    program_name = models.CharField(max_length=100, db_index=True, verbose_name="Program Name")
    beneficiary = models.ForeignKey(Jobseeker, on_delete=models.CASCADE, related_name='programs', db_index=True, verbose_name="Beneficiary")
    target_group = models.CharField(max_length=100, blank=True, verbose_name="Target Group")
    assistance = models.TextField(verbose_name="Activity / Assistance")
    status = models.CharField(max_length=50, default="Active", db_index=True, verbose_name="Status")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Amount / Support Value")
    completion_date = models.DateField(null=True, blank=True, verbose_name="Completion Date")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_enrolled']
        indexes = [
            models.Index(fields=['date_enrolled']),
            models.Index(fields=['program_name']),
            models.Index(fields=['status']),
            models.Index(fields=['peso_office']),
        ]
        verbose_name = "Program Transaction"
        verbose_name_plural = "Program Monitoring"

    def __str__(self):
        return f"{self.program_code}: {self.program_name} - {self.beneficiary.full_name}"

    def save(self, *args, **kwargs):
        if not self.program_code:
            self.program_code = generate_sequential_code('PRG', Program, 'program_code', self.date_enrolled)
        super().save(*args, **kwargs)


# ==============================================================================
# 9. JOB FAIR MONITORING
# ==============================================================================
class JobFair(models.Model):
    """
    Job Fair Events monitoring and accomplishments.
    """
    job_fair_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Job Fair ID / Code"
    )
    event_date = models.DateField(default=timezone.now, db_index=True, verbose_name="Event Date")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='job_fairs', db_index=True, verbose_name="PESO Office")
    organizer = models.CharField(max_length=150, verbose_name="Organizer")
    name = models.CharField(max_length=200, verbose_name="Event Name")
    venue = models.CharField(max_length=255, verbose_name="Venue")
    status = models.CharField(max_length=50, default="Planned", db_index=True, verbose_name="Status")
    participating_employers = models.PositiveIntegerField(default=0, verbose_name="Participating Employers")
    vacancies_offered = models.PositiveIntegerField(default=0, verbose_name="Vacancies Offered")
    registered_applicants = models.PositiveIntegerField(default=0, verbose_name="Registered Applicants")
    applicants_referred = models.PositiveIntegerField(default=0, verbose_name="Applicants Referred")
    hired_on_the_spot = models.PositiveIntegerField(default=0, verbose_name="Hired On-The-Spot (HOTS)")
    hired_after_event = models.PositiveIntegerField(default=0, verbose_name="Hired After Event")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['event_date']),
            models.Index(fields=['status']),
            models.Index(fields=['peso_office']),
        ]
        verbose_name = "Job Fair"
        verbose_name_plural = "Job Fairs"

    def __str__(self):
        return f"{self.job_fair_code}: {self.name} ({self.event_date})"

    @property
    def total_hired(self):
        return self.hired_on_the_spot + self.hired_after_event

    def save(self, *args, **kwargs):
        if not self.job_fair_code:
            self.job_fair_code = generate_sequential_code('JF', JobFair, 'job_fair_code', self.event_date)
        super().save(*args, **kwargs)


# Backward-compatible property aliases for templates
Jobseeker.jobseeker_id = property(lambda self: self.jobseeker_code)
Employer.employer_id = property(lambda self: self.employer_code)
Vacancy.vacancy_id = property(lambda self: self.vacancy_code)
Referral.referral_id = property(lambda self: self.referral_code)
Placement.placement_id = property(lambda self: self.placement_code)
Service.service_id = property(lambda self: self.service_code)
Program.program_id = property(lambda self: self.program_code)
JobFair.job_fair_id = property(lambda self: self.job_fair_code)


# ==============================================================================
# 10. USER PROFILE & APPROVAL SYSTEM
# ==============================================================================
class UserProfile(models.Model):
    """
    Extends Django User with role-based scoping and Admin Approval Workflow.
    New accounts require approval by a Provincial Admin before being activated.
    """
    ROLE_PROVINCIAL_ADMIN = 'PROVINCIAL_ADMIN'
    ROLE_MUNICIPAL_ENCODER = 'MUNICIPAL_ENCODER'

    ROLE_CHOICES = [
        (ROLE_PROVINCIAL_ADMIN, 'Provincial Admin (All Offices)'),
        (ROLE_MUNICIPAL_ENCODER, 'Municipal PESO Encoder (Own Office Only)'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    APPROVAL_CHOICES = [
        (STATUS_PENDING, 'Pending Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='peso_profile',
        verbose_name="User Account"
    )
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default=ROLE_MUNICIPAL_ENCODER,
        verbose_name="Role"
    )
    peso_office = models.ForeignKey(
        PESOOffice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encoders',
        verbose_name="Assigned PESO Office",
        help_text="Designated office for Municipal PESO Encoders."
    )
    contact_no = models.CharField(max_length=50, blank=True, verbose_name="Contact No.")
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name="Approval Status"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_profiles',
        verbose_name="Approved By"
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="Approved Date")
    rejection_reason = models.TextField(blank=True, verbose_name="Rejection / Deactivation Reason")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Profile & Approval"
        verbose_name_plural = "User Profiles & Approvals"

    def __str__(self):
        office_name = self.peso_office.name if self.peso_office else "All Offices"
        return f"{self.user.username} ({self.get_role_display()} - {office_name}) [{self.approval_status}]"

    @property
    def is_provincial_admin(self):
        return self.role == self.ROLE_PROVINCIAL_ADMIN or self.user.is_superuser

    @property
    def is_municipal_encoder(self):
        return self.role == self.ROLE_MUNICIPAL_ENCODER and not self.user.is_superuser

    def approve(self, admin_user):
        self.approval_status = self.STATUS_APPROVED
        self.approved_by = admin_user
        self.approved_at = timezone.now()
        self.user.is_active = True
        self.user.save()
        self.save()

    def reject(self, admin_user, reason=""):
        self.approval_status = self.STATUS_REJECTED
        self.approved_by = admin_user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.user.is_active = False
        self.user.save()
        self.save()


