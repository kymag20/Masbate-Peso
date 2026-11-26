import datetime
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from .middleware import get_current_user


def generate_sequential_id(prefix, model_class, id_field, date_ref=None):
    """
    Generate sequential IDs in the format: PREFIX-YYYYMM-XXXXX (e.g., JS-202611-00001).
    Ensures sequential incrementing per month.
    """
    target_date = date_ref or timezone.localdate()
    ym_str = target_date.strftime('%Y%m')
    prefix_pattern = f"{prefix}-{ym_str}-"
    
    # Find existing records with the same month prefix
    lookup = {f"{id_field}__startswith": prefix_pattern}
    latest_obj = model_class.objects.filter(**lookup).order_by(f"-{id_field}").first()
    
    if latest_obj:
        val = getattr(latest_obj, id_field, '')
        try:
            current_num = int(val.split('-')[-1])
            new_num = current_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
        
    # Ensure no collision with existing records
    candidate_id = f"{prefix_pattern}{new_num:05d}"
    while model_class.objects.filter(**{id_field: candidate_id}).exists():
        new_num += 1
        candidate_id = f"{prefix_pattern}{new_num:05d}"
        
    return candidate_id


class AuditedModel(models.Model):
    """
    Abstract base class providing automatic audit trail tracking:
    timestamps (created_at, updated_at) and user attribution (created_by, updated_by).
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        verbose_name="Updated By"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk and not self.created_by:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)


# ==============================================================================
# 0. EDITABLE DROPDOWN CHOICES / REFERENCE LISTS
# ==============================================================================
class DropdownChoice(AuditedModel):
    """
    Centralized editable dropdown options populated from the Excel 'Reference Lists' sheet.
    Admins can add/edit choices via the admin interface without touching code.
    """
    CATEGORY_CHOICES = [
        ('SEX', 'Sex'),
        ('CIVIL_STATUS', 'Civil Status'),
        ('EDUCATION_LEVEL', 'Highest Education Level'),
        ('EMPLOYMENT_STATUS', 'Employment Status'),
        ('JOBSEEKER_STATUS', 'Jobseeker Status'),
        ('EMPLOYER_STATUS', 'Employer Status'),
        ('VACANCY_STATUS', 'Vacancy Status'),
        ('REFERRAL_RESULT', 'Referral Result'),
        ('EMPLOYMENT_TYPE', 'Employment Type'),
        ('SERVICE_TYPE', 'Service Type'),
        ('PROGRAM', 'Program Name'),
        ('JOB_FAIR_STATUS', 'Job Fair Status'),
        ('YES_NO', 'Yes/No Choice'),
        ('LGU_TYPE', 'LGU Type'),
        ('ESTABLISHMENT_SIZE', 'Establishment Size'),
    ]

    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, db_index=True)
    value = models.CharField(max_length=150, verbose_name="Choice Value")
    order = models.PositiveIntegerField(default=0, help_text="Sort order in dropdown menus")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    description = models.TextField(blank=True, verbose_name="Description / Remarks")

    class Meta:
        ordering = ['category', 'order', 'value']
        constraints = [
            models.UniqueConstraint(fields=['category', 'value'], name='unique_category_choice_value')
        ]
        verbose_name = "Dropdown Choice / Reference List"
        verbose_name_plural = "Dropdown Choices / Reference Lists"

    def __str__(self):
        return f"{self.get_category_display()} - {self.value}"

    @classmethod
    def get_choices(cls, category):
        """Helper to get a list of (value, value) tuples for forms and model fields."""
        items = cls.objects.filter(category=category, is_active=True).values_list('value', flat=True)
        return [(item, item) for item in items]


# ==============================================================================
# 1. PESO OFFICE MASTER LIST
# ==============================================================================
class PESOOffice(AuditedModel):
    """
    PESO Office Master List: Provincial, City, and Municipal PESO offices across Masbate.
    """
    office_id = models.CharField(max_length=50, unique=True, verbose_name="PESO Office ID")
    name = models.CharField(max_length=150, unique=True, verbose_name="PESO Office Name")
    lgu_type = models.CharField(max_length=50, default="Municipality", verbose_name="LGU Type")
    province = models.CharField(max_length=100, default="Masbate", verbose_name="Province")
    head = models.CharField(max_length=150, blank=True, verbose_name="PESO Manager / Head")
    contact_no = models.CharField(max_length=100, blank=True, verbose_name="Contact No.")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Office Address")
    status = models.CharField(max_length=50, default="Active", verbose_name="Status")
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        ordering = ['name']
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
# USER PROFILE & ROLE MANAGEMENT
# ==============================================================================
class UserProfile(AuditedModel):
    """
    Extends standard Django user with role-based permissions:
    - PROVINCIAL_ADMIN: Oversees all 22 PESO offices throughout Masbate.
    - MUNICIPAL_ENCODER: Confined strictly to their designated PESO Office.
    """
    ROLE_PROVINCIAL_ADMIN = 'PROVINCIAL_ADMIN'
    ROLE_MUNICIPAL_ENCODER = 'MUNICIPAL_ENCODER'

    ROLE_CHOICES = [
        (ROLE_PROVINCIAL_ADMIN, 'Provincial Admin (All Offices)'),
        (ROLE_MUNICIPAL_ENCODER, 'Municipal PESO Encoder (Own Office Only)'),
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
        verbose_name="System Role"
    )
    peso_office = models.ForeignKey(
        PESOOffice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_encoders',
        verbose_name="Assigned PESO Office",
        help_text="Required for Municipal PESO Encoders."
    )
    contact_no = models.CharField(max_length=50, blank=True, verbose_name="Contact No.")

    class Meta:
        verbose_name = "User PESO Profile"
        verbose_name_plural = "User PESO Profiles"

    def __str__(self):
        office_name = self.peso_office.name if self.peso_office else "All Offices"
        return f"{self.user.username} ({self.get_role_display()} - {office_name})"

    @property
    def is_provincial_admin(self):
        return self.role == self.ROLE_PROVINCIAL_ADMIN or self.user.is_superuser

    @property
    def is_municipal_encoder(self):
        return self.role == self.ROLE_MUNICIPAL_ENCODER and not self.user.is_superuser


# ==============================================================================
# 2. JOBSEEKER MASTER REGISTRY
# ==============================================================================
class Jobseeker(AuditedModel):
    """
    Jobseeker Registry conforming to DOLE / PEIS standards and RA 10173 Data Privacy Act.
    Age is computed dynamically; duplicate registrations (same name + birth date) are rejected.
    """
    jobseeker_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Jobseeker ID",
        help_text="Auto-generated sequential ID: JS-YYYYMM-XXXXX"
    )
    registration_date = models.DateField(default=timezone.now, verbose_name="Registration Date")
    originating_peso = models.ForeignKey(
        PESOOffice,
        on_delete=models.PROTECT,
        related_name='jobseekers',
        verbose_name="Originating PESO"
    )
    last_name = models.CharField(max_length=100, verbose_name="Last Name")
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Middle Name")
    sex = models.CharField(max_length=20, default="Male", verbose_name="Sex")
    birth_date = models.DateField(verbose_name="Birth Date")
    civil_status = models.CharField(max_length=50, default="Single", verbose_name="Civil Status")
    barangay = models.CharField(max_length=150, verbose_name="Barangay")
    municipality = models.CharField(max_length=150, verbose_name="Municipality / City")
    province = models.CharField(max_length=100, default="Masbate", verbose_name="Province")
    mobile_no = models.CharField(max_length=50, verbose_name="Mobile No.")
    highest_education = models.CharField(max_length=100, verbose_name="Highest Education")
    course = models.CharField(max_length=200, blank=True, verbose_name="Course / Program")
    school = models.CharField(max_length=200, blank=True, verbose_name="School")
    primary_skill = models.CharField(max_length=200, blank=True, verbose_name="Primary Skill")
    other_skills = models.TextField(blank=True, verbose_name="Other Skills")
    preferred_occupation = models.CharField(max_length=200, blank=True, verbose_name="Preferred Occupation")
    employment_status = models.CharField(max_length=100, default="Unemployed", verbose_name="Employment Status")
    jobseeker_status = models.CharField(max_length=50, default="Active", verbose_name="Jobseeker Status")
    
    # Priority client flags
    is_pwd = models.CharField(max_length=10, default="NO", verbose_name="PWD (Person With Disability)")
    is_returning_ofw = models.CharField(max_length=10, default="NO", verbose_name="Returning OFW")
    is_displaced_worker = models.CharField(max_length=10, default="NO", verbose_name="Displaced Worker")
    is_osy = models.CharField(max_length=10, default="NO", verbose_name="OSY (Out-of-School Youth)")
    
    # RA 10173 Data Privacy Compliance
    privacy_consent = models.BooleanField(
        default=True,
        verbose_name="Data Privacy Consent (RA 10173)",
        help_text="Explicit consent obtained from applicant for PESO database profiling."
    )
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        ordering = ['-registration_date', 'last_name', 'first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['first_name', 'last_name', 'birth_date'],
                name='unique_jobseeker_name_birthdate'
            )
        ]
        verbose_name = "Jobseeker"
        verbose_name_plural = "Jobseekers"

    def __str__(self):
        return f"{self.jobseeker_id} - {self.full_name}"

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.last_name}, {self.first_name} {self.middle_name}"
        return f"{self.last_name}, {self.first_name}"

    @property
    def age(self):
        """Auto-computes age based on current date and birth date."""
        if not self.birth_date:
            return None
        today = timezone.localdate()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    def clean(self):
        # Normalize casing and remove extra whitespaces safely
        if self.first_name:
            self.first_name = self.first_name.strip().upper()
        if self.last_name:
            self.last_name = self.last_name.strip().upper()
        if self.middle_name:
            self.middle_name = self.middle_name.strip().upper()
            
        # Prevent duplicate jobseekers (same name + birth date)
        if self.first_name and self.last_name and self.birth_date:
            qs = Jobseeker.objects.filter(
                first_name__iexact=self.first_name,
                last_name__iexact=self.last_name,
                birth_date=self.birth_date
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                existing = qs.first()
                raise ValidationError(
                    f"A jobseeker record already exists with name '{self.full_name}' and birth date {self.birth_date} (ID: {existing.jobseeker_id})."
                )

    def save(self, *args, **kwargs):
        self.clean()
        if not self.jobseeker_id:
            self.jobseeker_id = generate_sequential_id('JS', Jobseeker, 'jobseeker_id', self.registration_date)
        super().save(*args, **kwargs)


# ==============================================================================
# 3. EMPLOYER MASTER REGISTRY
# ==============================================================================
class Employer(AuditedModel):
    """
    Employer / Establishment Registry.
    Guarantees no duplicate company names or business permits.
    """
    employer_id = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Employer ID",
        help_text="Unique employer identifier (e.g. 000-001 or EMP-YYYYMM-XXXXX)"
    )
    registration_date = models.DateField(default=timezone.now, verbose_name="Registration Date")
    permit_no = models.CharField(max_length=100, blank=True, verbose_name="Mayor's / Business Permit No.")
    company_name = models.CharField(max_length=255, verbose_name="Employer / Company Name")
    industry = models.CharField(max_length=150, verbose_name="Industry")
    establishment_size = models.CharField(max_length=50, blank=True, verbose_name="Establishment Size")
    contact_person = models.CharField(max_length=150, blank=True, verbose_name="Contact Person")
    position = models.CharField(max_length=100, blank=True, verbose_name="Position")
    contact_no = models.CharField(max_length=100, blank=True, verbose_name="Contact No.")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Address")
    municipality = models.CharField(max_length=100, default="City of Masbate", verbose_name="Municipality / City")
    province = models.CharField(max_length=100, default="Masbate", verbose_name="Province")
    status = models.CharField(max_length=50, default="Active", verbose_name="Employer Status")
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        ordering = ['company_name']
        verbose_name = "Employer"
        verbose_name_plural = "Employers"

    def __str__(self):
        return f"{self.employer_id} - {self.company_name}"

    def clean(self):
        if self.company_name:
            self.company_name = self.company_name.strip()
        if self.permit_no:
            self.permit_no = self.permit_no.strip()
            
        # Prevent duplicate employer by company_name
        if self.company_name:
            company_qs = Employer.objects.filter(company_name__iexact=self.company_name)
            if self.pk:
                company_qs = company_qs.exclude(pk=self.pk)
            if company_qs.exists():
                existing = company_qs.first()
                raise ValidationError(
                    f"An employer with company name '{self.company_name}' already exists (ID: {existing.employer_id})."
                )

        # Prevent duplicate employer by permit_no if provided
        if self.permit_no:
            permit_qs = Employer.objects.filter(permit_no__iexact=self.permit_no)
            if self.pk:
                permit_qs = permit_qs.exclude(pk=self.pk)
            if permit_qs.exists():
                existing = permit_qs.first()
                raise ValidationError(
                    f"An employer with permit number '{self.permit_no}' already exists (Company: {existing.company_name})."
                )

    def save(self, *args, **kwargs):
        self.clean()
        if not self.employer_id:
            self.employer_id = generate_sequential_id('EMP', Employer, 'employer_id', self.registration_date)
        super().save(*args, **kwargs)


# ==============================================================================
# 4. JOB VACANCY REGISTRY
# ==============================================================================
class Vacancy(AuditedModel):
    """
    Job Vacancies posted by registered employers.
    Tracks demand and dynamically computes referrals and confirmed hires.
    """
    vacancy_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Vacancy ID",
        help_text="Auto-generated: VAC-YYYYMM-XXXXX"
    )
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='vacancies', verbose_name="Employer")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='vacancies', verbose_name="PESO Office")
    position_title = models.CharField(max_length=200, verbose_name="Position Title")
    no_required = models.PositiveIntegerField(default=1, verbose_name="No. Required")
    education_requirement = models.CharField(max_length=150, blank=True, verbose_name="Education Requirement")
    experience_requirement = models.CharField(max_length=200, blank=True, verbose_name="Experience Requirement")
    skills_requirement = models.TextField(blank=True, verbose_name="Skills / Qualifications")
    employment_type = models.CharField(max_length=50, default="Permanent", verbose_name="Employment Type")
    work_location = models.CharField(max_length=200, blank=True, verbose_name="Work Location")
    salary = models.CharField(max_length=100, blank=True, verbose_name="Salary / Rate")
    date_posted = models.DateField(default=timezone.now, verbose_name="Date Posted")
    closing_date = models.DateField(null=True, blank=True, verbose_name="Closing Date")
    status = models.CharField(max_length=50, default="Open", verbose_name="Vacancy Status")
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        ordering = ['-date_posted', 'position_title']
        verbose_name = "Job Vacancy"
        verbose_name_plural = "Job Vacancies"

    def __str__(self):
        return f"{self.vacancy_id} - {self.position_title} ({self.employer.company_name})"

    @property
    def no_referred(self):
        """Computed count of applicants referred to this vacancy."""
        return self.referrals.count()

    @property
    def no_hired(self):
        """Computed count of confirmed hires for this vacancy."""
        return self.placements.count()

    def save(self, *args, **kwargs):
        if not self.vacancy_id:
            self.vacancy_id = generate_sequential_id('VAC', Vacancy, 'vacancy_id', self.date_posted)
        super().save(*args, **kwargs)


# ==============================================================================
# 5. REFERRAL TRANSACTIONS
# ==============================================================================
class Referral(AuditedModel):
    """
    Applicant Referral transactions linking a jobseeker to a specific job vacancy.
    """
    referral_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Referral ID",
        help_text="Auto-generated: REF-YYYYMM-XXXXX"
    )
    jobseeker = models.ForeignKey(Jobseeker, on_delete=models.PROTECT, related_name='referrals', verbose_name="Jobseeker")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='referrals', verbose_name="Vacancy")
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='referrals', verbose_name="Employer")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='referrals', verbose_name="PESO Office")
    referral_date = models.DateField(default=timezone.now, verbose_name="Referral Date")
    position_referred = models.CharField(max_length=200, verbose_name="Position Referred")
    result = models.CharField(max_length=50, default="Referred", verbose_name="Referral Result")
    interview_date = models.DateField(null=True, blank=True, verbose_name="Interview Date")
    result_date = models.DateField(null=True, blank=True, verbose_name="Result Date")
    follow_up_needed = models.BooleanField(default=False, verbose_name="Follow-up Needed")
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        ordering = ['-referral_date', 'referral_id']
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"

    def __str__(self):
        return f"{self.referral_id}: {self.jobseeker.full_name} -> {self.vacancy.position_title}"

    def clean(self):
        if self.vacancy and not self.employer_id:
            self.employer = self.vacancy.employer
        if self.vacancy and not self.position_referred:
            self.position_referred = self.vacancy.position_title

    def save(self, *args, **kwargs):
        self.clean()
        if not self.referral_id:
            self.referral_id = generate_sequential_id('REF', Referral, 'referral_id', self.referral_date)
        super().save(*args, **kwargs)


# ==============================================================================
# 6. PLACEMENT TRANSACTIONS
# ==============================================================================
class Placement(AuditedModel):
    """
    Confirmed hiring/placement outcomes.
    Forms the numerator for the official PESO Placement Rate calculation.
    """
    placement_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Placement ID",
        help_text="Auto-generated: PLC-YYYYMM-XXXXX"
    )
    jobseeker = models.ForeignKey(Jobseeker, on_delete=models.PROTECT, related_name='placements', verbose_name="Jobseeker")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.SET_NULL, null=True, blank=True, related_name='placements', verbose_name="Vacancy")
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT, related_name='placements', verbose_name="Employer")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='placements', verbose_name="PESO Office")
    date_hired = models.DateField(default=timezone.now, verbose_name="Date Hired")
    position = models.CharField(max_length=200, verbose_name="Position")
    employment_type = models.CharField(max_length=50, default="Permanent", verbose_name="Employment Type")
    work_location = models.CharField(max_length=200, blank=True, verbose_name="Work Location")
    starting_salary = models.CharField(max_length=100, blank=True, verbose_name="Starting Salary / Rate")
    verified = models.BooleanField(default=True, verbose_name="Placement Verified")
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        ordering = ['-date_hired', 'placement_id']
        verbose_name = "Placement"
        verbose_name_plural = "Placements"

    def __str__(self):
        return f"{self.placement_id}: {self.jobseeker.full_name} hired as {self.position} by {self.employer.company_name}"

    def clean(self):
        if self.vacancy and not self.employer_id:
            self.employer = self.vacancy.employer
        if self.vacancy and not self.position:
            self.position = self.vacancy.position_title

    def save(self, *args, **kwargs):
        self.clean()
        if not self.placement_id:
            self.placement_id = generate_sequential_id('PLC', Placement, 'placement_id', self.date_hired)
        super().save(*args, **kwargs)


# ==============================================================================
# 7. PESO SERVICES DELIVERED
# ==============================================================================
class Service(AuditedModel):
    """
    Log of individual employment facilitation services delivered to clients.
    (Career Guidance, Employment Coaching, Labor Market Information, etc.)
    """
    service_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Service Transaction ID",
        help_text="Auto-generated: SVC-YYYYMM-XXXXX"
    )
    jobseeker = models.ForeignKey(Jobseeker, on_delete=models.CASCADE, related_name='services', verbose_name="Jobseeker / Client")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='services', verbose_name="PESO Office")
    service_date = models.DateField(default=timezone.now, verbose_name="Service Date")
    service_type = models.CharField(max_length=100, verbose_name="Service Type")
    outcome = models.TextField(blank=True, verbose_name="Outcome / Action Taken")
    referred_to = models.CharField(max_length=200, blank=True, verbose_name="Referred To")
    follow_up_date = models.DateField(null=True, blank=True, verbose_name="Follow-up Date")
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        ordering = ['-service_date', 'service_id']
        verbose_name = "PESO Service Delivered"
        verbose_name_plural = "PESO Services Delivered"

    def __str__(self):
        return f"{self.service_id}: {self.service_type} for {self.jobseeker.full_name}"

    def save(self, *args, **kwargs):
        if not self.service_id:
            self.service_id = generate_sequential_id('SVC', Service, 'service_id', self.service_date)
        super().save(*args, **kwargs)


# ==============================================================================
# 8. PESO PROGRAM MONITORING
# ==============================================================================
class Program(AuditedModel):
    """
    Tracks beneficiaries and support provided for government employment programs
    (e.g., SPES, GIP, JobStart, TUPAD, Livelihood Assistance).
    """
    program_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Program Transaction ID",
        help_text="Auto-generated: PRG-YYYYMM-XXXXX"
    )
    date_enrolled = models.DateField(default=timezone.now, verbose_name="Date")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='programs', verbose_name="PESO Office")
    program_name = models.CharField(max_length=100, verbose_name="Program Name")
    beneficiary = models.ForeignKey(Jobseeker, on_delete=models.CASCADE, related_name='programs', verbose_name="Beneficiary / Client")
    target_group = models.CharField(max_length=100, blank=True, verbose_name="Target Group")
    assistance = models.TextField(verbose_name="Activity / Assistance Provided")
    status = models.CharField(max_length=50, default="Active", verbose_name="Program Status")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Amount / Support Value (PHP)")
    completion_date = models.DateField(null=True, blank=True, verbose_name="Completion Date")
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        ordering = ['-date_enrolled', 'program_id']
        verbose_name = "PESO Program Transaction"
        verbose_name_plural = "PESO Program Monitoring"

    def __str__(self):
        return f"{self.program_id}: {self.program_name} - {self.beneficiary.full_name}"

    def save(self, *args, **kwargs):
        if not self.program_id:
            self.program_id = generate_sequential_id('PRG', Program, 'program_id', self.date_enrolled)
        super().save(*args, **kwargs)


# ==============================================================================
# 9. JOB FAIR MONITORING
# ==============================================================================
class JobFair(AuditedModel):
    """
    Job Fair Events monitoring and core accomplishment indicators.
    """
    job_fair_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Job Fair ID",
        help_text="Auto-generated: JF-YYYYMM-XXXXX"
    )
    event_date = models.DateField(default=timezone.now, verbose_name="Event Date")
    peso_office = models.ForeignKey(PESOOffice, on_delete=models.PROTECT, related_name='job_fairs', verbose_name="PESO Office / Host")
    organizer = models.CharField(max_length=150, verbose_name="Organizer")
    name = models.CharField(max_length=200, verbose_name="Event Name")
    venue = models.CharField(max_length=255, verbose_name="Venue")
    status = models.CharField(max_length=50, default="Planned", verbose_name="Job Fair Status")
    participating_employers = models.PositiveIntegerField(default=0, verbose_name="Participating Employers")
    vacancies_offered = models.PositiveIntegerField(default=0, verbose_name="Vacancies Offered")
    registered_applicants = models.PositiveIntegerField(default=0, verbose_name="Registered Applicants")
    applicants_referred = models.PositiveIntegerField(default=0, verbose_name="Applicants Referred")
    hired_on_the_spot = models.PositiveIntegerField(default=0, verbose_name="Hired On-The-Spot (HOTS)")
    hired_after_event = models.PositiveIntegerField(default=0, verbose_name="Hired After Event")
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        ordering = ['-event_date', 'name']
        verbose_name = "Job Fair Event"
        verbose_name_plural = "Job Fair Monitoring"

    def __str__(self):
        return f"{self.job_fair_id}: {self.name} ({self.event_date})"

    @property
    def total_hired(self):
        return self.hired_on_the_spot + self.hired_after_event

    def save(self, *args, **kwargs):
        if not self.job_fair_id:
            self.job_fair_id = generate_sequential_id('JF', JobFair, 'job_fair_id', self.event_date)
        super().save(*args, **kwargs)
