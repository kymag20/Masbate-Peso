import os
import datetime
from dateutil import parser as date_parser
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import openpyxl

from database.models import (
    DropdownChoice,
    PESOOffice,
    Jobseeker,
    Employer,
    Vacancy,
    Referral,
    Placement,
    Service,
    Program,
    JobFair,
)

# Canonical 22 PESO Offices across Masbate Province
OFFICIAL_PESO_OFFICES = [
    ("Masbate Province", "Province", "Provincial Capitol, Masbate City"),
    ("City of Masbate", "City", "City Hall Complex, Masbate City"),
    ("Aroroy", "Municipality", "Municipal Hall, Aroroy, Masbate"),
    ("Baleno", "Municipality", "Municipal Hall, Baleno, Masbate"),
    ("Balud", "Municipality", "Municipal Hall, Balud, Masbate"),
    ("Batuan", "Municipality", "Municipal Hall, Batuan, Masbate"),
    ("Cataingan", "Municipality", "Municipal Hall, Cataingan, Masbate"),
    ("Cawayan", "Municipality", "Municipal Hall, Cawayan, Masbate"),
    ("Dimasalang", "Municipality", "Municipal Hall, Dimasalang, Masbate"),
    ("Esperanza", "Municipality", "Municipal Hall, Esperanza, Masbate"),
    ("Mandaon", "Municipality", "Municipal Hall, Mandaon, Masbate"),
    ("Milagros", "Municipality", "Municipal Hall, Milagros, Masbate"),
    ("Mobo", "Municipality", "Municipal Hall, Mobo, Masbate"),
    ("Palanas", "Municipality", "Municipal Hall, Palanas, Masbate"),
    ("Pio V. Corpuz", "Municipality", "Municipal Hall, Pio V. Corpuz, Masbate"),
    ("Placer", "Municipality", "Municipal Hall, Placer, Masbate"),
    ("Uson", "Municipality", "Municipal Hall, Uson, Masbate"),
    ("San Jacinto", "Municipality", "Municipal Hall, San Jacinto, Masbate"),
    ("San Fernando", "Municipality", "Municipal Hall, San Fernando, Masbate"),
    ("Monreal", "Municipality", "Municipal Hall, Monreal, Masbate"),
    ("Claveria", "Municipality", "Municipal Hall, Claveria, Masbate"),
    ("San Pascual", "Municipality", "Municipal Hall, San Pascual, Masbate"),
]

# Standard reference choices from the Excel 'Reference Lists' sheet
OFFICIAL_REFERENCE_LISTS = {
    'SEX': ['Male', 'Female'],
    'CIVIL_STATUS': ['Single', 'Married', 'Widowed', 'Separated', 'Other'],
    'EDUCATION_LEVEL': [
        'Elementary',
        'Junior High School',
        'Senior High School',
        'Technical-Vocational',
        'College Undergraduate',
        'College Graduate',
        'Postgraduate'
    ],
    'EMPLOYMENT_STATUS': [
        'Unemployed',
        'Employed - Seeking Better Opportunity',
        'Self-Employed',
        'Student',
        'Not in Labor Force'
    ],
    'JOBSEEKER_STATUS': ['Active', 'Inactive', 'Placed', 'For Follow-up'],
    'VACANCY_STATUS': ['Open', 'Closed', 'Filled', 'Cancelled', 'On Hold'],
    'REFERRAL_RESULT': [
        'Referred',
        'For Interview',
        'Interviewed',
        'Qualified',
        'Hired',
        'Not Selected',
        'No Show',
        'Pending',
        'Other'
    ],
    'EMPLOYMENT_TYPE': [
        'Permanent',
        'Probationary',
        'Contractual',
        'Project-Based',
        'Seasonal',
        'Part-Time',
        'Full-Time',
        'Other'
    ],
    'SERVICE_TYPE': [
        'Job Referral',
        'Career Guidance',
        'Employment Coaching',
        'Labor Market Information',
        'TUPAD Referral',
        'Training Referral',
        'Livelihood Referral',
        'Skills Profiling',
        'Job Matching',
        'Other'
    ],
    'PROGRAM': [
        'SPES',
        'GIP',
        'JobStart',
        'Livelihood',
        'Career Development',
        'Local Program',
        'Other'
    ],
    'YES_NO': ['Yes', 'No'],
    'EMPLOYER_STATUS': ['Active', 'Inactive', 'Blacklisted/Restricted', 'For Verification'],
    'JOB_FAIR_STATUS': ['Planned', 'Completed', 'Cancelled', 'Postponed'],
    'LGU_TYPE': ['Province', 'City', 'Municipality'],
    'ESTABLISHMENT_SIZE': ['Micro (1-9)', 'Small (10-99)', 'Medium (100-199)', 'Large (200+)'],
}


class Command(BaseCommand):
    help = (
        "Imports Masbate Provincial PESO Excel workbook data (.xlsx) into the database, "
        "normalizes casing inconsistencies, ensures foreign key links, and reports duplicate/invalid rows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='Masbate_Provincial_PESO_Database.xlsx',
            help='Path to the Excel file (.xlsx) to import.'
        )
        parser.add_argument(
            '--init-defaults',
            action='store_true',
            help='Initialize official 22 PESO offices and reference lists choices without requiring an Excel file.'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        init_defaults_only = options['init_defaults']

        self.stdout.write(self.style.MIGRATE_HEADING("=== Masbate Provincial PESO Database Importer ==="))
        
        # Phase 1: Always ensure default PESO Offices & Dropdown Choices exist
        self.seed_defaults()

        if init_defaults_only:
            self.stdout.write(self.style.SUCCESS("Initialized official PESO offices and reference lists successfully."))
            return

        # Phase 2: Check if file exists
        if not os.path.exists(file_path):
            # Check alternative locations (e.g. desktop)
            desktop_alt = os.path.join(os.path.expanduser("~"), "Desktop", "Masbate Peso", file_path)
            if os.path.exists(desktop_alt):
                file_path = desktop_alt
            else:
                self.stdout.write(self.style.WARNING(
                    f"Excel file '{file_path}' was not found.\n"
                    "Default PESO offices and dropdown choices have been created.\n"
                    "Place your 'Masbate_Provincial_PESO_Database.xlsx' in the project directory and re-run:"
                    "\n  python manage.py import_peso_data --file Masbate_Provincial_PESO_Database.xlsx"
                ))
                return

        self.stdout.write(f"Loading Excel workbook: {file_path}")
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        except Exception as e:
            raise CommandError(f"Failed to open Excel workbook: {e}")

        # Import each sheet in sequence
        self.import_sheets(wb)

    def seed_defaults(self):
        """Seed all 22 official PESO offices and standard reference choices."""
        self.stdout.write("Ensuring reference choices and PESO offices are registered...")
        
        # 1. Dropdown choices
        choice_count = 0
        for category, values in OFFICIAL_REFERENCE_LISTS.items():
            for idx, val in enumerate(values):
                _, created = DropdownChoice.objects.get_or_create(
                    category=category,
                    value=val,
                    defaults={'order': idx + 1, 'is_active': True}
                )
                if created:
                    choice_count += 1
                    
        # 2. PESO Offices
        office_count = 0
        for name, lgu_type, addr in OFFICIAL_PESO_OFFICES:
            office_id = name.upper().replace(' ', '_')
            _, created = PESOOffice.objects.get_or_create(
                name=name,
                defaults={
                    'office_id': office_id,
                    'lgu_type': lgu_type,
                    'province': 'Masbate',
                    'address': addr,
                    'status': 'Active'
                }
            )
            if created:
                office_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Defaults initialized: +{choice_count} dropdown choices, +{office_count} PESO offices."
        ))

    def clean_cell(self, val):
        """Clean string cell value, strip trailing spaces, and normalize newlines."""
        if val is None:
            return ""
        if isinstance(val, (datetime.datetime, datetime.date)):
            return val
        s = str(val).strip()
        if s.lower() in ('none', 'null', 'n/a', '.'):
            return ""
        return s

    def parse_date(self, val, default=None):
        """Flexibly parse a date from Excel (datetime, date, or date string)."""
        if not val:
            return default or timezone.localdate()
        if isinstance(val, datetime.datetime):
            return val.date()
        if isinstance(val, datetime.date):
            return val
        try:
            parsed = date_parser.parse(str(val))
            return parsed.date()
        except Exception:
            return default or timezone.localdate()

    def get_peso_office(self, raw_name):
        """Match PESO office by exact name or substring (e.g. 'DIMASALANG' -> 'Dimasalang')."""
        if not raw_name:
            return PESOOffice.objects.filter(name__icontains="Masbate Province").first()
        raw_str = str(raw_name).strip()
        
        # 1. Direct match (case-insensitive)
        office = PESOOffice.objects.filter(name__iexact=raw_str).first()
        if office:
            return office
            
        # 2. Substring match
        office = PESOOffice.objects.filter(name__icontains=raw_str).first()
        if office:
            return office
            
        # 3. Fallback to provincial capital
        return PESOOffice.objects.filter(name__icontains="Masbate Province").first()

    def import_sheets(self, wb):
        """Iterate over workbook sheets and import them."""
        # Find sheet by case-insensitive name matching
        sheet_names = {s.upper(): s for s in wb.sheetnames}

        # 1. Employers
        emp_sheet_key = next((k for k in sheet_names if 'EMPLOYER' in k), None)
        if emp_sheet_key:
            self.import_employers(wb[sheet_names[emp_sheet_key]])

        # 2. Jobseekers
        js_sheet_key = next((k for k in sheet_names if 'JOBSEEKER' in k), None)
        if js_sheet_key:
            self.import_jobseekers(wb[sheet_names[js_sheet_key]])

        # 3. Vacancies
        vac_sheet_key = next((k for k in sheet_names if 'VACANCY' in k), None)
        if vac_sheet_key:
            self.import_vacancies(wb[sheet_names[vac_sheet_key]])

        # 4. Referrals
        ref_sheet_key = next((k for k in sheet_names if 'REFERRAL' in k), None)
        if ref_sheet_key:
            self.import_referrals(wb[sheet_names[ref_sheet_key]])

        # 5. Placements
        plc_sheet_key = next((k for k in sheet_names if 'PLACEMENT' in k), None)
        if plc_sheet_key:
            self.import_placements(wb[sheet_names[plc_sheet_key]])

        # 6. Services Delivered
        svc_sheet_key = next((k for k in sheet_names if 'SERVICE' in k), None)
        if svc_sheet_key:
            self.import_services(wb[sheet_names[svc_sheet_key]])

        # 7. Programs
        prg_sheet_key = next((k for k in sheet_names if 'PROGRAM' in k), None)
        if prg_sheet_key:
            self.import_programs(wb[sheet_names[prg_sheet_key]])

        # 8. Job Fairs
        jf_sheet_key = next((k for k in sheet_names if 'JOB FAIR' in k or 'JOBFAIR' in k), None)
        if jf_sheet_key:
            self.import_job_fairs(wb[sheet_names[jf_sheet_key]])

    def import_employers(self, sheet):
        """Import Employer records from sheet."""
        self.stdout.write("\nImporting Employers...")
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return

        # Find header row
        header_idx = -1
        for i, row in enumerate(rows[:10]):
            row_str = " ".join([str(c) for c in row if c is not None]).upper()
            if 'EMPLOYER ID' in row_str or 'COMPANY NAME' in row_str or 'PERMIT NO' in row_str:
                header_idx = i
                break

        if header_idx == -1:
            self.stdout.write(self.style.WARNING("Could not find employer header row, skipping."))
            return

        imported, duplicates, errors = 0, 0, 0
        error_details = []

        seen_companies = set(Employer.objects.values_list('company_name', flat=True))
        seen_permits = set(filter(None, Employer.objects.values_list('permit_no', flat=True)))

        for row_num, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
            if not any(row):
                continue
            
            # Unpack according to Excel columns
            emp_id = self.clean_cell(row[0] if len(row) > 0 else "")
            reg_date = self.parse_date(row[1] if len(row) > 1 else None)
            permit_no = self.clean_cell(row[2] if len(row) > 2 else "")
            company_name = self.clean_cell(row[3] if len(row) > 3 else "")
            industry = self.clean_cell(row[4] if len(row) > 4 else "") or "General Industry"
            size = self.clean_cell(row[5] if len(row) > 5 else "")
            contact_person = self.clean_cell(row[6] if len(row) > 6 else "")
            position = self.clean_cell(row[7] if len(row) > 7 else "")
            contact_no = self.clean_cell(row[8] if len(row) > 8 else "")
            email = self.clean_cell(row[9] if len(row) > 9 else "")
            address = self.clean_cell(row[10] if len(row) > 10 else "")
            municipality = self.clean_cell(row[11] if len(row) > 11 else "") or "City of Masbate"
            province = self.clean_cell(row[12] if len(row) > 12 else "") or "Masbate"
            status = self.clean_cell(row[13] if len(row) > 13 else "") or "Active"
            remarks = self.clean_cell(row[15] if len(row) > 15 else "")

            if not company_name:
                continue

            # Check duplicate company name or permit
            norm_name = company_name.upper()
            if norm_name in seen_companies:
                duplicates += 1
                error_details.append(f"Row {row_num}: Duplicate company name '{company_name}'")
                continue

            if permit_no and permit_no in seen_permits:
                duplicates += 1
                error_details.append(f"Row {row_num}: Duplicate permit number '{permit_no}' for '{company_name}'")
                continue

            if not emp_id:
                emp_id = f"EMP-{reg_date.strftime('%Y%m')}-{imported + 1:05d}"

            try:
                Employer.objects.create(
                    employer_id=emp_id,
                    registration_date=reg_date,
                    permit_no=permit_no,
                    company_name=company_name,
                    industry=industry,
                    establishment_size=size,
                    contact_person=contact_person,
                    position=position,
                    contact_no=contact_no,
                    email=email,
                    address=address,
                    municipality=municipality,
                    province=province,
                    status=status,
                    remarks=remarks
                )
                seen_companies.add(norm_name)
                if permit_no:
                    seen_permits.add(permit_no)
                imported += 1
            except Exception as e:
                errors += 1
                error_details.append(f"Row {row_num} ('{company_name}'): {str(e)}")

        self.stdout.write(self.style.SUCCESS(
            f"Employers: +{imported} imported, {duplicates} duplicate rows skipped, {errors} errors."
        ))
        if error_details[:5]:
            self.stdout.write(self.style.NOTICE("Sample validation notices:"))
            for err in error_details[:5]:
                self.stdout.write(f"  - {err}")
            if len(error_details) > 5:
                self.stdout.write(f"  ... and {len(error_details) - 5} more.")

    def import_jobseekers(self, sheet):
        """Import Jobseeker records from sheet."""
        self.stdout.write("\nImporting Jobseekers...")
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return

        header_idx = -1
        for i, row in enumerate(rows[:10]):
            row_str = " ".join([str(c) for c in row if c is not None]).upper()
            if 'JOBSEEKER ID' in row_str or 'LAST NAME' in row_str or 'ORIGINATING PESO' in row_str:
                header_idx = i
                break

        if header_idx == -1:
            self.stdout.write(self.style.WARNING("Could not find jobseeker header row, skipping."))
            return

        imported, duplicates, errors = 0, 0, 0
        error_details = []

        for row_num, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
            if not any(row):
                continue

            js_id = self.clean_cell(row[0] if len(row) > 0 else "")
            reg_date = self.parse_date(row[1] if len(row) > 1 else None)
            peso_name = self.clean_cell(row[2] if len(row) > 2 else "")
            last_name = self.clean_cell(row[3] if len(row) > 3 else "").upper()
            first_name = self.clean_cell(row[4] if len(row) > 4 else "").upper()
            middle_name = self.clean_cell(row[5] if len(row) > 5 else "").upper()
            sex = self.clean_cell(row[6] if len(row) > 6 else "").title() or "Male"
            birth_date = self.parse_date(row[7] if len(row) > 7 else None, default=datetime.date(1990, 1, 1))
            civil_status = self.clean_cell(row[9] if len(row) > 9 else "").title() or "Single"
            barangay = self.clean_cell(row[10] if len(row) > 10 else "") or "Poblacion"
            municipality = self.clean_cell(row[11] if len(row) > 11 else "") or "City of Masbate"
            province = self.clean_cell(row[12] if len(row) > 12 else "") or "Masbate"
            mobile_no = self.clean_cell(row[13] if len(row) > 13 else "")
            highest_education = self.clean_cell(row[14] if len(row) > 14 else "").title() or "High School"
            course = self.clean_cell(row[15] if len(row) > 15 else "")
            school = self.clean_cell(row[16] if len(row) > 16 else "")
            primary_skill = self.clean_cell(row[17] if len(row) > 17 else "")
            other_skills = self.clean_cell(row[18] if len(row) > 18 else "")
            pref_occupation = self.clean_cell(row[19] if len(row) > 19 else "")
            emp_status = self.clean_cell(row[20] if len(row) > 20 else "").title() or "Unemployed"
            js_status = self.clean_cell(row[21] if len(row) > 21 else "").title() or "Active"
            pwd = self.clean_cell(row[22] if len(row) > 22 else "NO").upper() or "NO"
            ofw = self.clean_cell(row[23] if len(row) > 23 else "NO").upper() or "NO"
            displaced = self.clean_cell(row[24] if len(row) > 24 else "NO").upper() or "NO"
            osy = self.clean_cell(row[25] if len(row) > 25 else "NO").upper() or "NO"
            remarks = self.clean_cell(row[26] if len(row) > 26 else "")

            if not first_name or not last_name:
                continue

            # Prevent duplicate jobseekers (same name + birth date)
            if Jobseeker.objects.filter(first_name=first_name, last_name=last_name, birth_date=birth_date).exists():
                duplicates += 1
                error_details.append(f"Row {row_num}: Duplicate jobseeker '{first_name} {last_name}' ({birth_date})")
                continue

            peso_office = self.get_peso_office(peso_name)

            if not js_id:
                js_id = f"JS-{reg_date.strftime('%Y%m')}-{imported + 1:05d}"

            try:
                Jobseeker.objects.create(
                    jobseeker_id=js_id,
                    registration_date=reg_date,
                    originating_peso=peso_office,
                    last_name=last_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    sex=sex,
                    birth_date=birth_date,
                    civil_status=civil_status,
                    barangay=barangay,
                    municipality=municipality,
                    province=province,
                    mobile_no=mobile_no,
                    highest_education=highest_education,
                    course=course,
                    school=school,
                    primary_skill=primary_skill,
                    other_skills=other_skills,
                    preferred_occupation=pref_occupation,
                    employment_status=emp_status,
                    jobseeker_status=js_status,
                    is_pwd=pwd,
                    is_returning_ofw=ofw,
                    is_displaced_worker=displaced,
                    is_osy=osy,
                    privacy_consent=True,
                    remarks=remarks
                )
                imported += 1
            except Exception as e:
                errors += 1
                error_details.append(f"Row {row_num}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(
            f"Jobseekers: +{imported} imported, {duplicates} duplicates skipped, {errors} errors."
        ))

    def import_vacancies(self, sheet):
        """Import Vacancy records from sheet."""
        self.stdout.write("\nImporting Vacancies...")
        rows = list(sheet.iter_rows(values_only=True))
        if len(rows) < 4:
            return

        imported, errors = 0, 0
        for row in rows[3:]:
            if not any(row):
                continue
            vac_id = self.clean_cell(row[0] if len(row) > 0 else "")
            date_posted = self.parse_date(row[1] if len(row) > 1 else None)
            peso_name = self.clean_cell(row[2] if len(row) > 2 else "")
            emp_id_or_name = self.clean_cell(row[3] if len(row) > 3 else "")
            emp_name = self.clean_cell(row[4] if len(row) > 4 else "")
            title = self.clean_cell(row[5] if len(row) > 5 else "")
            if not title:
                continue

            try:
                num_req = int(row[6]) if len(row) > 6 and row[6] is not None else 1
            except (ValueError, TypeError):
                num_req = 1

            employer = (
                Employer.objects.filter(employer_id=emp_id_or_name).first() or
                Employer.objects.filter(company_name__iexact=emp_name).first() or
                Employer.objects.first()
            )
            if not employer:
                continue

            peso_office = self.get_peso_office(peso_name)
            try:
                Vacancy.objects.create(
                    vacancy_id=vac_id or f"VAC-{date_posted.strftime('%Y%m')}-{imported + 1:05d}",
                    employer=employer,
                    peso_office=peso_office,
                    position_title=title,
                    no_required=num_req,
                    education_requirement=self.clean_cell(row[7] if len(row) > 7 else ""),
                    experience_requirement=self.clean_cell(row[8] if len(row) > 8 else ""),
                    skills_requirement=self.clean_cell(row[9] if len(row) > 9 else ""),
                    employment_type=self.clean_cell(row[10] if len(row) > 10 else "Permanent"),
                    work_location=self.clean_cell(row[11] if len(row) > 11 else ""),
                    salary=self.clean_cell(row[12] if len(row) > 12 else ""),
                    closing_date=self.parse_date(row[13], default=None) if len(row) > 13 and row[13] else None,
                    status=self.clean_cell(row[14] if len(row) > 14 else "Open") or "Open",
                    remarks=self.clean_cell(row[17] if len(row) > 17 else "")
                )
                imported += 1
            except Exception as e:
                errors += 1

        self.stdout.write(self.style.SUCCESS(f"Vacancies: +{imported} imported, {errors} errors."))

    def import_referrals(self, sheet):
        """Import Referral records from sheet."""
        self.stdout.write("\nImporting Referrals...")
        rows = list(sheet.iter_rows(values_only=True))
        if len(rows) < 4:
            return
        imported = 0
        for row in rows[3:]:
            if not any(row):
                continue
            ref_id = self.clean_cell(row[0] if len(row) > 0 else "")
            ref_date = self.parse_date(row[1] if len(row) > 1 else None)
            peso_office = self.get_peso_office(row[2] if len(row) > 2 else "")
            vac_id = self.clean_cell(row[3] if len(row) > 3 else "")
            js_id = self.clean_cell(row[4] if len(row) > 4 else "")
            emp_id = self.clean_cell(row[5] if len(row) > 5 else "")
            position = self.clean_cell(row[6] if len(row) > 6 else "")
            result = self.clean_cell(row[7] if len(row) > 7 else "Referred") or "Referred"

            jobseeker = Jobseeker.objects.filter(jobseeker_id=js_id).first() or Jobseeker.objects.first()
            vacancy = Vacancy.objects.filter(vacancy_id=vac_id).first() or Vacancy.objects.first()
            employer = Employer.objects.filter(employer_id=emp_id).first() or (vacancy.employer if vacancy else Employer.objects.first())

            if not jobseeker or not vacancy or not employer:
                continue

            try:
                Referral.objects.create(
                    referral_id=ref_id or f"REF-{ref_date.strftime('%Y%m')}-{imported + 1:05d}",
                    jobseeker=jobseeker,
                    vacancy=vacancy,
                    employer=employer,
                    peso_office=peso_office,
                    referral_date=ref_date,
                    position_referred=position or vacancy.position_title,
                    result=result,
                    interview_date=self.parse_date(row[8], default=None) if len(row) > 8 and row[8] else None,
                    result_date=self.parse_date(row[9], default=None) if len(row) > 9 and row[9] else None,
                    follow_up_needed=str(row[10]).upper() in ('YES', 'TRUE', '1') if len(row) > 10 else False,
                    remarks=self.clean_cell(row[11] if len(row) > 11 else "")
                )
                imported += 1
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS(f"Referrals: +{imported} imported."))

    def import_placements(self, sheet):
        """Import Placement records from sheet."""
        self.stdout.write("\nImporting Placements...")
        rows = list(sheet.iter_rows(values_only=True))
        if len(rows) < 4:
            return
        imported = 0
        for row in rows[3:]:
            if not any(row):
                continue
            plc_id = self.clean_cell(row[0] if len(row) > 0 else "")
            hired_date = self.parse_date(row[1] if len(row) > 1 else None)
            peso_office = self.get_peso_office(row[2] if len(row) > 2 else "")
            vac_id = self.clean_cell(row[3] if len(row) > 3 else "")
            js_id = self.clean_cell(row[4] if len(row) > 4 else "")
            emp_id = self.clean_cell(row[5] if len(row) > 5 else "")
            position = self.clean_cell(row[7] if len(row) > 7 else "")

            jobseeker = Jobseeker.objects.filter(jobseeker_id=js_id).first() or Jobseeker.objects.first()
            vacancy = Vacancy.objects.filter(vacancy_id=vac_id).first()
            employer = Employer.objects.filter(employer_id=emp_id).first() or (vacancy.employer if vacancy else Employer.objects.first())

            if not jobseeker or not employer:
                continue

            try:
                Placement.objects.create(
                    placement_id=plc_id or f"PLC-{hired_date.strftime('%Y%m')}-{imported + 1:05d}",
                    jobseeker=jobseeker,
                    vacancy=vacancy,
                    employer=employer,
                    peso_office=peso_office,
                    date_hired=hired_date,
                    position=position or (vacancy.position_title if vacancy else "Hired Applicant"),
                    employment_type=self.clean_cell(row[8] if len(row) > 8 else "Permanent"),
                    work_location=self.clean_cell(row[9] if len(row) > 9 else ""),
                    starting_salary=self.clean_cell(row[10] if len(row) > 10 else ""),
                    verified=True,
                    remarks=self.clean_cell(row[12] if len(row) > 12 else "")
                )
                imported += 1
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS(f"Placements: +{imported} imported."))

    def import_services(self, sheet):
        """Import Service delivery records from sheet."""
        self.stdout.write("\nImporting PESO Services Delivered...")
        rows = list(sheet.iter_rows(values_only=True))
        if len(rows) < 4:
            return
        imported = 0
        for row in rows[3:]:
            if not any(row):
                continue
            svc_id = self.clean_cell(row[0] if len(row) > 0 else "")
            svc_date = self.parse_date(row[1] if len(row) > 1 else None)
            peso_office = self.get_peso_office(row[2] if len(row) > 2 else "")
            js_id = self.clean_cell(row[3] if len(row) > 3 else "")
            svc_type = self.clean_cell(row[5] if len(row) > 5 else "") or "Career Guidance"

            jobseeker = Jobseeker.objects.filter(jobseeker_id=js_id).first() or Jobseeker.objects.first()
            if not jobseeker:
                continue

            try:
                Service.objects.create(
                    service_id=svc_id or f"SVC-{svc_date.strftime('%Y%m')}-{imported + 1:05d}",
                    jobseeker=jobseeker,
                    peso_office=peso_office,
                    service_date=svc_date,
                    service_type=svc_type,
                    outcome=self.clean_cell(row[6] if len(row) > 6 else ""),
                    referred_to=self.clean_cell(row[7] if len(row) > 7 else ""),
                    follow_up_date=self.parse_date(row[8], default=None) if len(row) > 8 and row[8] else None,
                    remarks=self.clean_cell(row[9] if len(row) > 9 else "")
                )
                imported += 1
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS(f"Services: +{imported} imported."))

    def import_programs(self, sheet):
        """Import PESO Program monitoring records from sheet."""
        self.stdout.write("\nImporting PESO Programs...")
        rows = list(sheet.iter_rows(values_only=True))
        if len(rows) < 4:
            return
        imported = 0
        for row in rows[3:]:
            if not any(row):
                continue
            prg_id = self.clean_cell(row[0] if len(row) > 0 else "")
            enrolled_date = self.parse_date(row[1] if len(row) > 1 else None)
            peso_office = self.get_peso_office(row[2] if len(row) > 2 else "")
            prg_name = self.clean_cell(row[3] if len(row) > 3 else "") or "SPES"
            js_id = self.clean_cell(row[4] if len(row) > 4 else "")

            jobseeker = Jobseeker.objects.filter(jobseeker_id=js_id).first() or Jobseeker.objects.first()
            if not jobseeker:
                continue

            try:
                amt = float(row[9]) if len(row) > 9 and row[9] is not None else 0.0
            except (ValueError, TypeError):
                amt = 0.0

            try:
                Program.objects.create(
                    program_id=prg_id or f"PRG-{enrolled_date.strftime('%Y%m')}-{imported + 1:05d}",
                    date_enrolled=enrolled_date,
                    peso_office=peso_office,
                    program_name=prg_name,
                    beneficiary=jobseeker,
                    target_group=self.clean_cell(row[6] if len(row) > 6 else "Youth"),
                    assistance=self.clean_cell(row[7] if len(row) > 7 else "Financial & Training Assistance"),
                    status=self.clean_cell(row[8] if len(row) > 8 else "Active") or "Active",
                    amount=amt,
                    completion_date=self.parse_date(row[10], default=None) if len(row) > 10 and row[10] else None,
                    remarks=self.clean_cell(row[11] if len(row) > 11 else "")
                )
                imported += 1
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS(f"Programs: +{imported} imported."))

    def import_job_fairs(self, sheet):
        """Import Job Fair records from sheet."""
        self.stdout.write("\nImporting Job Fairs...")
        rows = list(sheet.iter_rows(values_only=True))
        if len(rows) < 4:
            return
        imported = 0
        for row in rows[3:]:
            if not any(row):
                continue
            jf_id = self.clean_cell(row[0] if len(row) > 0 else "")
            event_date = self.parse_date(row[1] if len(row) > 1 else None)
            peso_office = self.get_peso_office(row[2] if len(row) > 2 else "")
            name = self.clean_cell(row[3] if len(row) > 3 else "") or "Masbate Provincial Job Fair"

            def safe_int(c_idx):
                try:
                    return int(row[c_idx]) if len(row) > c_idx and row[c_idx] is not None else 0
                except (ValueError, TypeError):
                    return 0

            try:
                JobFair.objects.create(
                    job_fair_id=jf_id or f"JF-{event_date.strftime('%Y%m')}-{imported + 1:05d}",
                    event_date=event_date,
                    peso_office=peso_office,
                    organizer=self.clean_cell(row[2] if len(row) > 2 else "Provincial PESO"),
                    name=name,
                    venue=self.clean_cell(row[4] if len(row) > 4 else "Masbate Social Center"),
                    status=self.clean_cell(row[5] if len(row) > 5 else "Planned") or "Planned",
                    participating_employers=safe_int(6),
                    vacancies_offered=safe_int(7),
                    registered_applicants=safe_int(8),
                    applicants_referred=safe_int(9),
                    hired_on_the_spot=safe_int(10),
                    hired_after_event=safe_int(11),
                    remarks=self.clean_cell(row[12] if len(row) > 12 else "")
                )
                imported += 1
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS(f"Job Fairs: +{imported} imported."))
