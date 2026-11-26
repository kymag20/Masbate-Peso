import os
import re
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import openpyxl
from dateutil import parser as date_parser

from peso.models import (
    LookupChoice,
    PESOOffice,
    Employer,
    Jobseeker,
)


def clean_str(val):
    if val is None:
        return ""
    s = str(val).strip()
    return s


def clean_address(val):
    if not val:
        return ""
    s = str(val).strip()
    # Remove leading dashes or bullets
    s = re.sub(r'^[\s\-_•*]+', '', s)
    # Replace stray newlines and carriage returns with comma space
    s = re.sub(r'[\r\n]+', ', ', s)
    # Collapse multiple spaces or multiple commas
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r',\s*,', ',', s)
    return s.strip(' ,-')


def clean_phone(val):
    if not val:
        return ""
    s = str(val).strip()
    # Remove decimal .0 if read as float
    if s.endswith('.0'):
        s = s[:-2]
    # Digits only
    digits = re.sub(r'\D', '', s)
    if digits.startswith('63') and len(digits) == 12:
        return '0' + digits[2:]
    if len(digits) == 10 and digits.startswith('9'):
        return '0' + digits
    if len(digits) == 11 and digits.startswith('09'):
        return digits
    return s


def parse_date_safe(val, default_date=None):
    if not val:
        return default_date or timezone.localdate()
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    s = str(val).strip()
    try:
        dt = date_parser.parse(s, dayfirst=False)
        return dt.date()
    except Exception:
        try:
            dt = datetime.datetime.strptime(s, '%m/%d/%Y')
            return dt.date()
        except Exception:
            return default_date or timezone.localdate()


def to_bool(val):
    if val is None:
        return False
    s = str(val).strip().upper()
    return s in ('YES', 'TRUE', '1', 'Y')


def title_case(val):
    if not val:
        return ""
    return str(val).strip().title()


class Command(BaseCommand):
    help = 'Import data from Masbate Provincial PESO Excel workbook into PostgreSQL / Supabase.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Masbate_Provincial_PESO_Database.xlsx file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        if not os.path.exists(file_path):
            raise CommandError(f"Excel file not found at: {file_path}")

        self.stdout.write(self.style.NOTICE(f"Loading workbook: {file_path}..."))
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        except Exception as e:
            raise CommandError(f"Failed to load workbook: {e}")

        # ----------------------------------------------------------------------
        # 1. IMPORT LOOKUP CHOICES (Lists sheet)
        # ----------------------------------------------------------------------
        self.stdout.write(self.style.NOTICE("\n[1/4] Processing 'Lists' sheet -> LookupChoice..."))
        lists_read = 0
        lists_imported = 0
        lists_skipped = 0

        if 'Lists' in wb.sheetnames:
            sheet_lists = wb['Lists']
            headers = [c for c in next(sheet_lists.iter_rows(min_row=4, max_row=4, values_only=True))]
            
            for col_idx, raw_cat in enumerate(headers):
                if not raw_cat:
                    continue
                category = str(raw_cat).strip()
                # Skip the office column from lists as it belongs to PESOOffice
                if 'PESO Office' in category:
                    continue

                order = 0
                for row in sheet_lists.iter_rows(min_row=5, values_only=True):
                    if col_idx < len(row) and row[col_idx] is not None:
                        val = str(row[col_idx]).strip()
                        if val:
                            lists_read += 1
                            order += 10
                            obj, created = LookupChoice.objects.get_or_create(
                                category=category,
                                value=val,
                                defaults={'sort_order': order, 'is_active': True}
                            )
                            if created:
                                lists_imported += 1
                            else:
                                lists_skipped += 1
            self.stdout.write(self.style.SUCCESS(
                f" -> Lists processed: Read={lists_read}, Imported={lists_imported}, Existing/Skipped={lists_skipped}"
            ))
        else:
            self.stdout.write(self.style.WARNING(" -> 'Lists' sheet not found in workbook."))

        # ----------------------------------------------------------------------
        # 2. IMPORT PESO OFFICES (PESO Offices sheet or Lists sheet)
        # ----------------------------------------------------------------------
        self.stdout.write(self.style.NOTICE("\n[2/4] Processing PESO Offices (22 offices)..."))
        offices_read = 0
        offices_imported = 0
        offices_skipped = 0

        # Known standard 22 Masbate LGU Offices
        # If 'PESO Offices' sheet has data, use it; otherwise fallback to standard 22 list
        office_names = []
        if 'PESO Offices' in wb.sheetnames:
            sheet_offices = wb['PESO Offices']
            for row in sheet_offices.iter_rows(min_row=5, values_only=True):
                if row and row[0]:
                    name = str(row[0]).strip()
                    if name and name not in office_names:
                        office_names.append(name)

        if not office_names and 'Lists' in wb.sheetnames:
            sheet_lists = wb['Lists']
            for row in sheet_lists.iter_rows(min_row=5, values_only=True):
                if row and row[0]:
                    name = str(row[0]).strip()
                    if name and name not in office_names:
                        office_names.append(name)

        for name in office_names:
            offices_read += 1
            if name.lower() == 'masbate province':
                lgu_type = 'Province'
            elif 'city' in name.lower():
                lgu_type = 'City'
            else:
                lgu_type = 'Municipality'

            office_id = name.upper().replace(' ', '_').replace('.', '')
            obj, created = PESOOffice.objects.get_or_create(
                name=name,
                defaults={
                    'office_id': office_id,
                    'lgu_type': lgu_type,
                    'province': 'Masbate',
                    'status': 'Active',
                }
            )
            if created:
                offices_imported += 1
            else:
                offices_skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f" -> PESO Offices: Read={offices_read}, Imported={offices_imported}, Existing/Skipped={offices_skipped} (Total in DB: {PESOOffice.objects.count()})"
        ))

        # Helper mapping for offices (case-insensitive lookup)
        office_map = {o.name.lower(): o for o in PESOOffice.objects.all()}

        # ----------------------------------------------------------------------
        # 3. IMPORT JOBSEEKERS (Jobseekers sheet)
        # ----------------------------------------------------------------------
        self.stdout.write(self.style.NOTICE("\n[3/4] Processing 'Jobseekers' sheet..."))
        js_read = 0
        js_imported = 0
        js_skipped = 0

        if 'Jobseekers' in wb.sheetnames:
            sheet_js = wb['Jobseekers']
            for row in sheet_js.iter_rows(min_row=5, values_only=True):
                if not any(row):
                    continue
                js_read += 1
                excel_id = clean_str(row[0])  # '000-001'
                reg_date = parse_date_safe(row[1])
                office_str = clean_str(row[2]).lower()
                last_name = clean_str(row[3]).title()
                first_name = clean_str(row[4]).title()
                middle_name = clean_str(row[5]).title()
                sex = title_case(clean_str(row[6])) or 'Male'
                bdate = parse_date_safe(row[7], default_date=datetime.date(1990, 1, 1))
                civil_stat = title_case(clean_str(row[9])) or 'Single'
                brgy = clean_str(row[10]).title()
                mun = clean_str(row[11]).title() or 'City of Masbate'
                prov = clean_str(row[12]).title() or 'Masbate'
                mob = clean_phone(row[13])
                edu = title_case(clean_str(row[14])) or 'College Graduate'
                course = clean_str(row[15])
                school = clean_str(row[16])
                prim_skill = clean_str(row[17])
                oth_skills = clean_str(row[18])
                pref_occ = clean_str(row[19])
                emp_stat = title_case(clean_str(row[20])) or 'Unemployed'
                js_stat = title_case(clean_str(row[21])) or 'Active'
                pwd = to_bool(row[22])
                ofw = to_bool(row[23])
                disp = to_bool(row[24])
                osy = to_bool(row[25])
                remarks = clean_str(row[26])

                # Match originating PESO
                orig_office = office_map.get(office_str)
                if not orig_office:
                    # Try partial match or fallback
                    for k, o in office_map.items():
                        if office_str in k or k in office_str:
                            orig_office = o
                            break
                if not orig_office:
                    orig_office = office_map.get('masbate province') or PESOOffice.objects.first()

                # Generate code e.g. JS-202608-00001
                ym_str = reg_date.strftime('%Y%m')
                try:
                    seq_num = int(excel_id.split('-')[-1])
                except Exception:
                    seq_num = js_read
                code = f"JS-{ym_str}-{seq_num:05d}"

                if Jobseeker.objects.filter(jobseeker_code=code).exists():
                    js_skipped += 1
                else:
                    Jobseeker.objects.create(
                        jobseeker_code=code,
                        registration_date=reg_date,
                        originating_peso=orig_office,
                        last_name=last_name,
                        first_name=first_name,
                        middle_name=middle_name,
                        sex=sex,
                        birth_date=bdate,
                        civil_status=civil_stat,
                        barangay=brgy,
                        municipality=mun,
                        province=prov,
                        mobile_no=mob,
                        highest_education=edu,
                        course=course,
                        school=school,
                        primary_skill=prim_skill,
                        other_skills=oth_skills,
                        preferred_occupation=pref_occ,
                        employment_status=emp_stat,
                        jobseeker_status=js_stat,
                        is_pwd=pwd,
                        is_returning_ofw=ofw,
                        is_displaced_worker=disp,
                        is_osy=osy,
                        data_privacy_consent=True,
                        remarks=remarks,
                    )
                    js_imported += 1

            self.stdout.write(self.style.SUCCESS(
                f" -> Jobseekers: Read={js_read}, Imported={js_imported}, Existing/Skipped={js_skipped} (Total in DB: {Jobseeker.objects.count()})"
            ))
        else:
            self.stdout.write(self.style.WARNING(" -> 'Jobseekers' sheet not found in workbook."))

        # ----------------------------------------------------------------------
        # 4. IMPORT EMPLOYERS (Employers sheet, 2,887 rows)
        # ----------------------------------------------------------------------
        self.stdout.write(self.style.NOTICE("\n[4/4] Processing 'Employers' sheet (2,887 rows)..."))
        emp_read = 0
        emp_imported = 0
        emp_skipped = 0

        if 'Employers' in wb.sheetnames:
            sheet_emp = wb['Employers']
            rows_to_create = []
            
            # Pre-load existing employer codes to prevent duplicate insertion
            existing_codes = set(Employer.objects.values_list('employer_code', flat=True))

            for row in sheet_emp.iter_rows(min_row=5, values_only=True):
                if not any(row):
                    continue
                emp_read += 1
                excel_id = clean_str(row[0])  # '000-001'
                reg_date = parse_date_safe(row[1])
                permit_no = clean_str(row[2])
                company_name = clean_str(row[3])
                industry = clean_str(row[4])
                est_size = clean_str(row[5])
                contact_person = clean_str(row[6])
                pos = clean_str(row[7])
                contact_no = clean_phone(row[8])
                email = clean_str(row[9])
                address = clean_address(row[10])
                municipality = clean_str(row[11]) or 'City of Masbate'
                province = clean_str(row[12]) or 'Masbate'
                status = title_case(clean_str(row[13])) or 'Active'
                remarks = clean_str(row[15])

                # Build sequential code: EMP-YYYYMM-00001
                ym_str = reg_date.strftime('%Y%m')
                try:
                    seq_num = int(excel_id.split('-')[-1])
                except Exception:
                    seq_num = emp_read
                code = f"EMP-{ym_str}-{seq_num:05d}"

                if code in existing_codes:
                    emp_skipped += 1
                    continue

                employer_obj = Employer(
                    employer_code=code,
                    registration_date=reg_date,
                    permit_no=permit_no,
                    company_name=company_name,
                    industry=industry,
                    establishment_size=est_size,
                    contact_person=contact_person,
                    position=pos,
                    contact_no=contact_no,
                    email=email,
                    address=address,
                    municipality=municipality,
                    province=province,
                    status=status,
                    remarks=remarks,
                )
                rows_to_create.append(employer_obj)
                existing_codes.add(code)

                # Batch commit every 500 records
                if len(rows_to_create) >= 500:
                    with transaction.atomic():
                        Employer.objects.bulk_create(rows_to_create, batch_size=500)
                    emp_imported += len(rows_to_create)
                    self.stdout.write(f"   Processed {emp_imported}/{emp_read} employers...")
                    rows_to_create = []

            # Remaining batch
            if rows_to_create:
                with transaction.atomic():
                    Employer.objects.bulk_create(rows_to_create, batch_size=500)
                emp_imported += len(rows_to_create)

            self.stdout.write(self.style.SUCCESS(
                f" -> Employers: Read={emp_read}, Imported={emp_imported}, Existing/Skipped={emp_skipped} (Total in DB: {Employer.objects.count()})"
            ))
        else:
            self.stdout.write(self.style.WARNING(" -> 'Employers' sheet not found in workbook."))

        # ----------------------------------------------------------------------
        # FINAL SUMMARY
        # ----------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(self.style.SUCCESS("        IMPORT COMPLETED SUCCESSFULLY"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"Lookup Choices : {LookupChoice.objects.count()}")
        self.stdout.write(f"PESO Offices   : {PESOOffice.objects.count()} (Expected: 22)")
        self.stdout.write(f"Jobseekers     : {Jobseeker.objects.count()} (Expected: 1)")
        self.stdout.write(f"Employers      : {Employer.objects.count()} (Expected: 2,887)")
        self.stdout.write(self.style.SUCCESS("=" * 50))
