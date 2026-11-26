from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import User
from peso.models import (
    Jobseeker,
    Employer,
    Vacancy,
    Referral,
    Placement,
    Service,
    Program,
    JobFair,
    PESOOffice,
    LookupChoice,
    UserProfile,
)


class BaseStyledForm(forms.ModelForm):
    """Base form that injects modern SaaS form classes automatically."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select modern-input'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-control modern-input'
                if 'rows' not in field.widget.attrs:
                    field.widget.attrs['rows'] = 3
            else:
                field.widget.attrs['class'] = 'form-control modern-input'


class JobseekerForm(BaseStyledForm):
    class Meta:
        model = Jobseeker
        exclude = ('jobseeker_code', 'created_at', 'updated_at')
        widgets = {
            'registration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'other_skills': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g. Carpentry, Typing, Computer literate'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Additional notes...'}),
            'mobile_no': forms.TextInput(attrs={'placeholder': '09XXXXXXXXX'}),
            'primary_skill': forms.TextInput(attrs={'placeholder': 'e.g. Driving, Cooking, Accounting'}),
            'preferred_occupation': forms.TextInput(attrs={'placeholder': 'e.g. Administrative Assistant, Driver'}),
            'school': forms.TextInput(attrs={'placeholder': 'School / University attended'}),
            'course': forms.TextInput(attrs={'placeholder': 'Course or vocational program'}),
            'barangay': forms.TextInput(attrs={'placeholder': 'Barangay'}),
            'municipality': forms.TextInput(attrs={'placeholder': 'Municipality / City'}),
            'province': forms.TextInput(attrs={'placeholder': 'Province (e.g. Masbate)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamic choices from LookupChoice if available
        sex_choices = LookupChoice.get_choices('Sex')
        if sex_choices:
            self.fields['sex'].widget = forms.Select(choices=sex_choices, attrs={'class': 'form-select modern-input'})

        civil_choices = LookupChoice.get_choices('Civil Status')
        if civil_choices:
            self.fields['civil_status'].widget = forms.Select(choices=civil_choices, attrs={'class': 'form-select modern-input'})

        edu_choices = LookupChoice.get_choices('Education Level')
        if edu_choices:
            self.fields['highest_education'].widget = forms.Select(choices=edu_choices, attrs={'class': 'form-select modern-input'})

        emp_choices = LookupChoice.get_choices('Employment Status')
        if emp_choices:
            self.fields['employment_status'].widget = forms.Select(choices=emp_choices, attrs={'class': 'form-select modern-input'})

        status_choices = LookupChoice.get_choices('Jobseeker Status')
        if status_choices:
            self.fields['jobseeker_status'].widget = forms.Select(choices=status_choices, attrs={'class': 'form-select modern-input'})


class EmployerForm(BaseStyledForm):
    class Meta:
        model = Employer
        exclude = ('employer_code', 'created_at', 'updated_at')
        widgets = {
            'registration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Complete establishment address...'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Additional remarks...'}),
            'contact_no': forms.TextInput(attrs={'placeholder': 'Contact phone/mobile number'}),
            'permit_no': forms.TextInput(attrs={'placeholder': 'Business permit number'}),
            'company_name': forms.TextInput(attrs={'placeholder': 'Company or trade name'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        emp_status_choices = LookupChoice.get_choices('Employer Status')
        if emp_status_choices:
            self.fields['status'].widget = forms.Select(choices=emp_status_choices, attrs={'class': 'form-select modern-input'})


class VacancyForm(BaseStyledForm):
    class Meta:
        model = Vacancy
        exclude = ('vacancy_code', 'created_at', 'updated_at')
        widgets = {
            'date_posted': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'closing_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'skills_requirement': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Required skills and qualifications...'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Internal notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type_choices = LookupChoice.get_choices('Employment Type')
        if type_choices:
            self.fields['employment_type'].widget = forms.Select(choices=type_choices, attrs={'class': 'form-select modern-input'})

        vac_status_choices = LookupChoice.get_choices('Vacancy Status')
        if vac_status_choices:
            self.fields['status'].widget = forms.Select(choices=vac_status_choices, attrs={'class': 'form-select modern-input'})


class ReferralForm(BaseStyledForm):
    class Meta:
        model = Referral
        exclude = ('referral_code', 'created_at', 'updated_at')
        widgets = {
            'referral_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'interview_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'result_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        result_choices = LookupChoice.get_choices('Referral Result')
        if result_choices:
            self.fields['result'].widget = forms.Select(choices=result_choices, attrs={'class': 'form-select modern-input'})


class PlacementForm(BaseStyledForm):
    class Meta:
        model = Placement
        exclude = ('placement_code', 'created_at', 'updated_at')
        widgets = {
            'date_hired': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }


class ServiceForm(BaseStyledForm):
    class Meta:
        model = Service
        exclude = ('service_code', 'created_at', 'updated_at')
        widgets = {
            'service_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'outcome': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        svc_choices = LookupChoice.get_choices('Service Type')
        if svc_choices:
            self.fields['service_type'].widget = forms.Select(choices=svc_choices, attrs={'class': 'form-select modern-input'})


class ProgramForm(BaseStyledForm):
    class Meta:
        model = Program
        exclude = ('program_code', 'created_at', 'updated_at')
        widgets = {
            'date_enrolled': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'assistance': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        prg_choices = LookupChoice.get_choices('Program')
        if prg_choices:
            self.fields['program_name'].widget = forms.Select(choices=prg_choices, attrs={'class': 'form-select modern-input'})


class JobFairForm(BaseStyledForm):
    class Meta:
        model = JobFair
        exclude = ('job_fair_code', 'created_at', 'updated_at')
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control modern-input'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        status_choices = LookupChoice.get_choices('Job Fair Status')
        if status_choices:
            self.fields['status'].widget = forms.Select(choices=status_choices, attrs={'class': 'form-select modern-input'})


# ==============================================================================
# MULTI-USER & ADMIN APPROVAL FORMS
# ==============================================================================

class UserRegistrationForm(forms.Form):
    """
    Self-service registration form for PESO Staff and Municipal Encoders.
    Accounts are created with is_active=False and approval_status=PENDING.
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'e.g. Juan'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'e.g. Dela Cruz'})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Desired Username",
        widget=forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': 'e.g. jdelacruz'})
    )
    email = forms.EmailField(
        required=True,
        label="Official Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control modern-input', 'placeholder': 'juandelacruz@example.gov.ph'})
    )
    contact_no = forms.CharField(
        max_length=50,
        required=False,
        label="Contact / Mobile No.",
        widget=forms.TextInput(attrs={'class': 'form-control modern-input', 'placeholder': '09XXXXXXXXX'})
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        initial=UserProfile.ROLE_MUNICIPAL_ENCODER,
        label="Account Role / Designation",
        widget=forms.Select(attrs={'class': 'form-select modern-input', 'id': 'id_role'})
    )
    peso_office = forms.ModelChoiceField(
        queryset=PESOOffice.objects.filter(status='Active').order_by('name'),
        required=False,
        label="Designated PESO Office",
        empty_label="-- Select Municipal / City PESO Office --",
        widget=forms.Select(attrs={'class': 'form-select modern-input', 'id': 'id_peso_office'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control modern-input', 'placeholder': 'At least 6 characters'}),
        label="Password",
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control modern-input', 'placeholder': 'Re-enter your password'}),
        label="Confirm Password"
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ang username na ito ay ginagamit na. Pumili ng iba.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ang email na ito ay may nakarehistro nang account.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        role = cleaned_data.get('role')
        peso_office = cleaned_data.get('peso_office')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Hindi magkatugma ang Password at Confirm Password.")

        if role == UserProfile.ROLE_MUNICIPAL_ENCODER and not peso_office:
            self.add_error('peso_office', "Kailangan pumili ng Designated PESO Office para sa Municipal Encoder.")

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        user = User.objects.create_user(
            username=cleaned_data['username'],
            email=cleaned_data['email'],
            password=cleaned_data['password'],
            first_name=cleaned_data['first_name'],
            last_name=cleaned_data['last_name'],
            is_active=False  # Requires admin approval before activation
        )
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': cleaned_data['role'],
                'peso_office': cleaned_data.get('peso_office'),
                'contact_no': cleaned_data.get('contact_no', ''),
                'approval_status': UserProfile.STATUS_PENDING,
            }
        )
        if not created:
            profile.role = cleaned_data['role']
            profile.peso_office = cleaned_data.get('peso_office')
            profile.contact_no = cleaned_data.get('contact_no', '')
            profile.approval_status = UserProfile.STATUS_PENDING
            profile.save()
        return user


class CustomAuthenticationForm(forms.Form):
    """
    Login form that provides crystal-clear messaging for accounts pending approval or rejected.
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control bg-light border-start-0', 'placeholder': 'Enter username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control bg-light border-start-0', 'placeholder': 'Enter password'})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username', '').strip()
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                # Check if account exists with this password but is inactive (pending/rejected)
                inactive_user = User.objects.filter(username__iexact=username).first()
                if inactive_user and inactive_user.check_password(password) and not inactive_user.is_active:
                    profile = getattr(inactive_user, 'peso_profile', None)
                    if profile and profile.approval_status == UserProfile.STATUS_PENDING:
                        raise forms.ValidationError(
                            "Ang iyong account ay kasalukuyang PENDING APPROVAL pa mula sa Provincial PESO Admin. "
                            "Mangyaring hintayin na maaprubahan ito bago makapag-log in.",
                            code='pending_approval'
                        )
                    elif profile and profile.approval_status == UserProfile.STATUS_REJECTED:
                        reason = f" Dahilan: {profile.rejection_reason}" if profile.rejection_reason else ""
                        raise forms.ValidationError(
                            f"Ang iyong account ay hindi naaprubahan o na-deactivate ng Provincial Admin.{reason}",
                            code='account_rejected'
                        )
                    else:
                        raise forms.ValidationError(
                            "Ang account na ito ay kasalukuyang hindi aktibo. Makipag-ugnayan sa Provincial PESO Admin.",
                            code='inactive'
                        )
                raise forms.ValidationError(
                    "Maling username o password. Pakisubukang muli.",
                    code='invalid_login'
                )

        return self.cleaned_data

    def get_user(self):
        return self.user_cache
