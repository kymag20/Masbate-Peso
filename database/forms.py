from django import forms
from .models import (
    Jobseeker,
    Employer,
    Vacancy,
    Referral,
    Placement,
    Service,
    Program,
    JobFair,
    PESOOffice,
    DropdownChoice,
)


class BaseStyledForm(forms.ModelForm):
    """Base form that injects Bootstrap 5 form classes automatically."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class JobseekerForm(BaseStyledForm):
    class Meta:
        model = Jobseeker
        exclude = ('jobseeker_id', 'created_by', 'updated_by')
        widgets = {
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'other_skills': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate dynamic choices from DropdownChoice table
        sex_choices = DropdownChoice.get_choices('SEX')
        if sex_choices:
            self.fields['sex'].widget = forms.Select(choices=sex_choices, attrs={'class': 'form-select'})

        civil_choices = DropdownChoice.get_choices('CIVIL_STATUS')
        if civil_choices:
            self.fields['civil_status'].widget = forms.Select(choices=civil_choices, attrs={'class': 'form-select'})

        edu_choices = DropdownChoice.get_choices('EDUCATION_LEVEL')
        if edu_choices:
            self.fields['highest_education'].widget = forms.Select(choices=edu_choices, attrs={'class': 'form-select'})

        emp_choices = DropdownChoice.get_choices('EMPLOYMENT_STATUS')
        if emp_choices:
            self.fields['employment_status'].widget = forms.Select(choices=emp_choices, attrs={'class': 'form-select'})

        status_choices = DropdownChoice.get_choices('JOBSEEKER_STATUS')
        if status_choices:
            self.fields['jobseeker_status'].widget = forms.Select(choices=status_choices, attrs={'class': 'form-select'})


class EmployerForm(BaseStyledForm):
    class Meta:
        model = Employer
        exclude = ('created_by', 'updated_by')
        widgets = {
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        emp_status_choices = DropdownChoice.get_choices('EMPLOYER_STATUS')
        if emp_status_choices:
            self.fields['status'].widget = forms.Select(choices=emp_status_choices, attrs={'class': 'form-select'})


class VacancyForm(BaseStyledForm):
    class Meta:
        model = Vacancy
        exclude = ('vacancy_id', 'created_by', 'updated_by')
        widgets = {
            'date_posted': forms.DateInput(attrs={'type': 'date'}),
            'closing_date': forms.DateInput(attrs={'type': 'date'}),
            'skills_requirement': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type_choices = DropdownChoice.get_choices('EMPLOYMENT_TYPE')
        if type_choices:
            self.fields['employment_type'].widget = forms.Select(choices=type_choices, attrs={'class': 'form-select'})

        vac_status_choices = DropdownChoice.get_choices('VACANCY_STATUS')
        if vac_status_choices:
            self.fields['status'].widget = forms.Select(choices=vac_status_choices, attrs={'class': 'form-select'})


class ReferralForm(BaseStyledForm):
    class Meta:
        model = Referral
        exclude = ('referral_id', 'created_by', 'updated_by')
        widgets = {
            'referral_date': forms.DateInput(attrs={'type': 'date'}),
            'interview_date': forms.DateInput(attrs={'type': 'date'}),
            'result_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        res_choices = DropdownChoice.get_choices('REFERRAL_RESULT')
        if res_choices:
            self.fields['result'].widget = forms.Select(choices=res_choices, attrs={'class': 'form-select'})


class PlacementForm(BaseStyledForm):
    class Meta:
        model = Placement
        exclude = ('placement_id', 'created_by', 'updated_by')
        widgets = {
            'date_hired': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type_choices = DropdownChoice.get_choices('EMPLOYMENT_TYPE')
        if type_choices:
            self.fields['employment_type'].widget = forms.Select(choices=type_choices, attrs={'class': 'form-select'})


class ServiceForm(BaseStyledForm):
    class Meta:
        model = Service
        exclude = ('service_id', 'created_by', 'updated_by')
        widgets = {
            'service_date': forms.DateInput(attrs={'type': 'date'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
            'outcome': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        svc_choices = DropdownChoice.get_choices('SERVICE_TYPE')
        if svc_choices:
            self.fields['service_type'].widget = forms.Select(choices=svc_choices, attrs={'class': 'form-select'})


class ProgramForm(BaseStyledForm):
    class Meta:
        model = Program
        exclude = ('program_id', 'created_by', 'updated_by')
        widgets = {
            'date_enrolled': forms.DateInput(attrs={'type': 'date'}),
            'completion_date': forms.DateInput(attrs={'type': 'date'}),
            'assistance': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        prg_choices = DropdownChoice.get_choices('PROGRAM')
        if prg_choices:
            self.fields['program_name'].widget = forms.Select(choices=prg_choices, attrs={'class': 'form-select'})


class JobFairForm(BaseStyledForm):
    class Meta:
        model = JobFair
        exclude = ('job_fair_id', 'created_by', 'updated_by')
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        jf_choices = DropdownChoice.get_choices('JOB_FAIR_STATUS')
        if jf_choices:
            self.fields['status'].widget = forms.Select(choices=jf_choices, attrs={'class': 'form-select'})


class PESOOfficeForm(BaseStyledForm):
    class Meta:
        model = PESOOffice
        exclude = ('created_by', 'updated_by')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
