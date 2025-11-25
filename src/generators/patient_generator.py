"""
Patient data generator using Faker for synthetic PHI
"""
from faker import Faker
from datetime import datetime
import random


class PatientGenerator:
    """Generates synthetic patient data for PHI documents"""

    def __init__(self, locale='en_US', seed=None):
        self.fake = Faker(locale)
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    def generate_patient(self):
        """Generate a complete synthetic patient record"""
        dob = self.fake.date_of_birth(minimum_age=18, maximum_age=95)

        patient = {
            # Demographics
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'dob': dob,
            'age': self._calculate_age(dob),
            'ssn': self.fake.ssn(),
            'phone': self.fake.phone_number(),
            'email': self.fake.email(),
            'address': {
                'street': self.fake.street_address(),
                'city': self.fake.city(),
                'state': self.fake.state_abbr(),
                'zip': self.fake.zipcode()
            },

            # Medical identifiers
            'mrn': self._generate_mrn(),
            'insurance_id': self._generate_insurance_id(),
            'insurance_provider': self._generate_insurance_provider(),

            # Medical data
            'blood_type': random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
            'allergies': self._generate_allergies(),
            'medications': self._generate_medications(),
            'diagnoses': self._generate_diagnoses(),
            'vital_signs': self._generate_vitals(),
        }

        return patient

    def _calculate_age(self, dob):
        """Calculate age from date of birth"""
        today = datetime.now()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def _generate_mrn(self):
        """Generate Medical Record Number"""
        return f"MRN{random.randint(100000, 999999)}"

    def _generate_insurance_id(self):
        """Generate insurance member ID"""
        prefix = random.choice(['MC', 'MD', 'BC', 'UH', 'AE'])
        return f"{prefix}{random.randint(10000000, 99999999)}"

    def _generate_insurance_provider(self):
        """Generate insurance provider name"""
        providers = [
            'Medicare Part A',
            'Medicare Part B',
            'Medicaid',
            'Blue Cross Blue Shield',
            'UnitedHealthcare',
            'Aetna',
            'Cigna',
            'Humana'
        ]
        return random.choice(providers)

    def _generate_allergies(self):
        """Generate random allergies"""
        all_allergies = [
            'Penicillin', 'Sulfa drugs', 'Aspirin', 'Ibuprofen',
            'Codeine', 'Morphine', 'Latex', 'Shellfish',
            'Peanuts', 'Bee stings', 'None known'
        ]
        count = random.randint(0, 3)
        if count == 0:
            return ['None known']
        return random.sample([a for a in all_allergies if a != 'None known'], count)

    def _generate_medications(self):
        """Generate current medications"""
        all_meds = [
            'Lisinopril 10mg daily',
            'Metformin 500mg twice daily',
            'Atorvastatin 20mg daily',
            'Levothyroxine 50mcg daily',
            'Amlodipine 5mg daily',
            'Metoprolol 25mg twice daily',
            'Omeprazole 20mg daily',
            'Losartan 50mg daily',
            'Gabapentin 300mg three times daily',
            'Sertraline 50mg daily'
        ]
        count = random.randint(0, 5)
        if count == 0:
            return ['None']
        return random.sample(all_meds, count)

    def _generate_diagnoses(self):
        """Generate medical diagnoses with ICD-10 codes"""
        all_diagnoses = [
            {'name': 'Type 2 Diabetes Mellitus', 'icd10': 'E11.9'},
            {'name': 'Essential Hypertension', 'icd10': 'I10'},
            {'name': 'Hyperlipidemia', 'icd10': 'E78.5'},
            {'name': 'Chronic Kidney Disease, Stage 3', 'icd10': 'N18.3'},
            {'name': 'Coronary Artery Disease', 'icd10': 'I25.10'},
            {'name': 'Hypothyroidism', 'icd10': 'E03.9'},
            {'name': 'Osteoarthritis', 'icd10': 'M19.90'},
            {'name': 'Gastroesophageal Reflux Disease', 'icd10': 'K21.9'},
            {'name': 'Major Depressive Disorder', 'icd10': 'F33.1'},
            {'name': 'Chronic Obstructive Pulmonary Disease', 'icd10': 'J44.9'}
        ]
        count = random.randint(1, 4)
        return random.sample(all_diagnoses, count)

    def _generate_vitals(self):
        """Generate vital signs"""
        return {
            'blood_pressure': f"{random.randint(110, 160)}/{random.randint(70, 95)}",
            'heart_rate': random.randint(60, 100),
            'temperature': round(random.uniform(97.0, 99.5), 1),
            'respiratory_rate': random.randint(12, 20),
            'oxygen_saturation': random.randint(95, 100),
            'weight': random.randint(120, 280),
            'height': random.randint(60, 75)
        }

    def generate_lab_results(self, panel_type=None):
        """Generate lab test results for various panel types"""
        if panel_type is None:
            panel_type = random.choice([
                'lipid_panel', 'cbc', 'bmp', 'cmp', 'thyroid',
                'urinalysis', 'drug_screen', 'a1c'
            ])

        test_date = self.fake.date_between(start_date='-30d', end_date='today')

        panels = {
            'lipid_panel': self._generate_lipid_panel(),
            'cbc': self._generate_cbc(),
            'bmp': self._generate_bmp(),
            'cmp': self._generate_cmp(),
            'thyroid': self._generate_thyroid_panel(),
            'urinalysis': self._generate_urinalysis(),
            'drug_screen': self._generate_drug_screen(),
            'a1c': self._generate_a1c_panel(),
        }

        return {
            'test_date': test_date,
            'panel_type': panel_type,
            'panel_name': self._get_panel_name(panel_type),
            'results': panels.get(panel_type, panels['lipid_panel'])
        }

    def _get_panel_name(self, panel_type):
        """Get display name for panel type"""
        names = {
            'lipid_panel': 'Lipid Panel',
            'cbc': 'Complete Blood Count (CBC)',
            'bmp': 'Basic Metabolic Panel (BMP)',
            'cmp': 'Comprehensive Metabolic Panel (CMP)',
            'thyroid': 'Thyroid Function Panel',
            'urinalysis': 'Urinalysis',
            'drug_screen': 'Urine Drug Screen (10-Panel)',
            'a1c': 'Hemoglobin A1C'
        }
        return names.get(panel_type, 'Laboratory Panel')

    def _generate_lipid_panel(self):
        """Lipid/Cholesterol panel"""
        total_chol = random.randint(150, 280)
        ldl = random.randint(70, 190)
        hdl = random.randint(35, 80)
        trig = random.randint(50, 300)
        return [
            {'test': 'Total Cholesterol', 'value': total_chol, 'unit': 'mg/dL',
             'reference_range': '<200', 'flag': 'H' if total_chol > 200 else ''},
            {'test': 'LDL Cholesterol', 'value': ldl, 'unit': 'mg/dL',
             'reference_range': '<100', 'flag': 'H' if ldl > 100 else ''},
            {'test': 'HDL Cholesterol', 'value': hdl, 'unit': 'mg/dL',
             'reference_range': '>40', 'flag': 'L' if hdl < 40 else ''},
            {'test': 'Triglycerides', 'value': trig, 'unit': 'mg/dL',
             'reference_range': '<150', 'flag': 'H' if trig > 150 else ''},
            {'test': 'VLDL Cholesterol', 'value': trig // 5, 'unit': 'mg/dL',
             'reference_range': '5-40', 'flag': ''},
        ]

    def _generate_cbc(self):
        """Complete Blood Count"""
        wbc = round(random.uniform(4.0, 12.0), 1)
        rbc = round(random.uniform(4.0, 5.8), 2)
        hgb = round(random.uniform(11.0, 17.0), 1)
        hct = round(random.uniform(36.0, 50.0), 1)
        plt = random.randint(150, 400)
        mcv = round(random.uniform(80, 100), 1)
        mch = round(random.uniform(27, 33), 1)
        mchc = round(random.uniform(32, 36), 1)
        rdw = round(random.uniform(11.5, 15.5), 1)
        return [
            {'test': 'WBC', 'value': wbc, 'unit': 'K/uL',
             'reference_range': '4.5-11.0', 'flag': 'H' if wbc > 11.0 else ('L' if wbc < 4.5 else '')},
            {'test': 'RBC', 'value': rbc, 'unit': 'M/uL',
             'reference_range': '4.5-5.5', 'flag': 'L' if rbc < 4.5 else ''},
            {'test': 'Hemoglobin', 'value': hgb, 'unit': 'g/dL',
             'reference_range': '12.0-16.0', 'flag': 'L' if hgb < 12.0 else ('H' if hgb > 16.0 else '')},
            {'test': 'Hematocrit', 'value': hct, 'unit': '%',
             'reference_range': '37-47', 'flag': ''},
            {'test': 'Platelets', 'value': plt, 'unit': 'K/uL',
             'reference_range': '150-400', 'flag': 'L' if plt < 150 else ''},
            {'test': 'MCV', 'value': mcv, 'unit': 'fL',
             'reference_range': '80-100', 'flag': ''},
            {'test': 'MCH', 'value': mch, 'unit': 'pg',
             'reference_range': '27-33', 'flag': ''},
            {'test': 'MCHC', 'value': mchc, 'unit': 'g/dL',
             'reference_range': '32-36', 'flag': ''},
            {'test': 'RDW', 'value': rdw, 'unit': '%',
             'reference_range': '11.5-14.5', 'flag': 'H' if rdw > 14.5 else ''},
        ]

    def _generate_bmp(self):
        """Basic Metabolic Panel"""
        glucose = random.randint(70, 180)
        bun = random.randint(7, 30)
        creat = round(random.uniform(0.6, 1.8), 2)
        sodium = random.randint(136, 148)
        potassium = round(random.uniform(3.5, 5.5), 1)
        chloride = random.randint(98, 110)
        co2 = random.randint(22, 32)
        calcium = round(random.uniform(8.5, 10.5), 1)
        return [
            {'test': 'Glucose', 'value': glucose, 'unit': 'mg/dL',
             'reference_range': '70-100', 'flag': 'H' if glucose > 100 else ''},
            {'test': 'BUN', 'value': bun, 'unit': 'mg/dL',
             'reference_range': '7-20', 'flag': 'H' if bun > 20 else ''},
            {'test': 'Creatinine', 'value': creat, 'unit': 'mg/dL',
             'reference_range': '0.7-1.3', 'flag': 'H' if creat > 1.3 else ''},
            {'test': 'Sodium', 'value': sodium, 'unit': 'mEq/L',
             'reference_range': '136-145', 'flag': 'H' if sodium > 145 else ('L' if sodium < 136 else '')},
            {'test': 'Potassium', 'value': potassium, 'unit': 'mEq/L',
             'reference_range': '3.5-5.0', 'flag': 'H' if potassium > 5.0 else ('L' if potassium < 3.5 else '')},
            {'test': 'Chloride', 'value': chloride, 'unit': 'mEq/L',
             'reference_range': '98-106', 'flag': ''},
            {'test': 'CO2', 'value': co2, 'unit': 'mEq/L',
             'reference_range': '23-29', 'flag': ''},
            {'test': 'Calcium', 'value': calcium, 'unit': 'mg/dL',
             'reference_range': '8.5-10.5', 'flag': ''},
        ]

    def _generate_cmp(self):
        """Comprehensive Metabolic Panel (BMP + liver)"""
        bmp = self._generate_bmp()
        ast = random.randint(10, 80)
        alt = random.randint(10, 80)
        alp = random.randint(40, 150)
        bili_total = round(random.uniform(0.2, 2.0), 1)
        protein = round(random.uniform(6.0, 8.5), 1)
        albumin = round(random.uniform(3.5, 5.0), 1)
        liver = [
            {'test': 'AST (SGOT)', 'value': ast, 'unit': 'U/L',
             'reference_range': '10-40', 'flag': 'H' if ast > 40 else ''},
            {'test': 'ALT (SGPT)', 'value': alt, 'unit': 'U/L',
             'reference_range': '7-56', 'flag': 'H' if alt > 56 else ''},
            {'test': 'Alkaline Phosphatase', 'value': alp, 'unit': 'U/L',
             'reference_range': '44-147', 'flag': ''},
            {'test': 'Bilirubin, Total', 'value': bili_total, 'unit': 'mg/dL',
             'reference_range': '0.1-1.2', 'flag': 'H' if bili_total > 1.2 else ''},
            {'test': 'Total Protein', 'value': protein, 'unit': 'g/dL',
             'reference_range': '6.0-8.3', 'flag': ''},
            {'test': 'Albumin', 'value': albumin, 'unit': 'g/dL',
             'reference_range': '3.5-5.0', 'flag': 'L' if albumin < 3.5 else ''},
        ]
        return bmp + liver

    def _generate_thyroid_panel(self):
        """Thyroid Function Panel"""
        tsh = round(random.uniform(0.3, 6.0), 2)
        t4_free = round(random.uniform(0.8, 2.0), 2)
        t3_free = round(random.uniform(2.0, 4.5), 2)
        t4_total = round(random.uniform(5.0, 12.0), 1)
        return [
            {'test': 'TSH', 'value': tsh, 'unit': 'mIU/L',
             'reference_range': '0.4-4.0', 'flag': 'H' if tsh > 4.0 else ('L' if tsh < 0.4 else '')},
            {'test': 'Free T4', 'value': t4_free, 'unit': 'ng/dL',
             'reference_range': '0.8-1.8', 'flag': 'H' if t4_free > 1.8 else ('L' if t4_free < 0.8 else '')},
            {'test': 'Free T3', 'value': t3_free, 'unit': 'pg/mL',
             'reference_range': '2.3-4.2', 'flag': ''},
            {'test': 'Total T4', 'value': t4_total, 'unit': 'ug/dL',
             'reference_range': '5.0-12.0', 'flag': ''},
        ]

    def _generate_urinalysis(self):
        """Urinalysis Panel"""
        ph = round(random.uniform(5.0, 8.0), 1)
        sg = round(random.uniform(1.005, 1.030), 3)
        protein = random.choice(['Negative', 'Trace', '1+', '2+'])
        glucose_ua = random.choice(['Negative', 'Trace', '1+', '2+'])
        ketones = random.choice(['Negative', 'Trace', '1+'])
        blood = random.choice(['Negative', 'Trace', '1+', '2+'])
        leuk = random.choice(['Negative', 'Trace', '1+'])
        nitrite = random.choice(['Negative', 'Positive'])
        wbc_ua = random.randint(0, 15)
        rbc_ua = random.randint(0, 10)
        bacteria = random.choice(['None seen', 'Few', 'Moderate', 'Many'])
        return [
            {'test': 'pH', 'value': ph, 'unit': '',
             'reference_range': '5.0-8.0', 'flag': ''},
            {'test': 'Specific Gravity', 'value': sg, 'unit': '',
             'reference_range': '1.005-1.030', 'flag': ''},
            {'test': 'Protein', 'value': protein, 'unit': '',
             'reference_range': 'Negative', 'flag': 'A' if protein not in ['Negative', 'Trace'] else ''},
            {'test': 'Glucose', 'value': glucose_ua, 'unit': '',
             'reference_range': 'Negative', 'flag': 'A' if glucose_ua != 'Negative' else ''},
            {'test': 'Ketones', 'value': ketones, 'unit': '',
             'reference_range': 'Negative', 'flag': ''},
            {'test': 'Blood', 'value': blood, 'unit': '',
             'reference_range': 'Negative', 'flag': 'A' if blood not in ['Negative', 'Trace'] else ''},
            {'test': 'Leukocyte Esterase', 'value': leuk, 'unit': '',
             'reference_range': 'Negative', 'flag': 'A' if leuk != 'Negative' else ''},
            {'test': 'Nitrite', 'value': nitrite, 'unit': '',
             'reference_range': 'Negative', 'flag': 'A' if nitrite == 'Positive' else ''},
            {'test': 'WBC', 'value': wbc_ua, 'unit': '/HPF',
             'reference_range': '0-5', 'flag': 'H' if wbc_ua > 5 else ''},
            {'test': 'RBC', 'value': rbc_ua, 'unit': '/HPF',
             'reference_range': '0-2', 'flag': 'H' if rbc_ua > 2 else ''},
            {'test': 'Bacteria', 'value': bacteria, 'unit': '',
             'reference_range': 'None seen', 'flag': 'A' if bacteria != 'None seen' else ''},
        ]

    def _generate_drug_screen(self):
        """10-Panel Urine Drug Screen"""
        # Most results negative, occasional positive for realistic data
        def get_result():
            return 'POSITIVE' if random.random() < 0.08 else 'NEGATIVE'

        drugs = [
            ('Amphetamines (AMP)', '1000 ng/mL'),
            ('Barbiturates (BAR)', '300 ng/mL'),
            ('Benzodiazepines (BZO)', '300 ng/mL'),
            ('Cocaine (COC)', '300 ng/mL'),
            ('Marijuana (THC)', '50 ng/mL'),
            ('Methadone (MTD)', '300 ng/mL'),
            ('Opiates (OPI)', '2000 ng/mL'),
            ('Oxycodone (OXY)', '100 ng/mL'),
            ('Phencyclidine (PCP)', '25 ng/mL'),
            ('Propoxyphene (PPX)', '300 ng/mL'),
        ]

        return [
            {'test': drug[0], 'value': get_result(), 'unit': '',
             'reference_range': 'NEGATIVE', 'flag': 'A' if get_result() == 'POSITIVE' else '',
             'cutoff': drug[1]}
            for drug in drugs
        ]

    def _generate_a1c_panel(self):
        """Hemoglobin A1C with estimated average glucose"""
        a1c = round(random.uniform(4.5, 10.0), 1)
        # eAG formula: 28.7 × A1C − 46.7
        eag = round(28.7 * a1c - 46.7)
        return [
            {'test': 'Hemoglobin A1C', 'value': a1c, 'unit': '%',
             'reference_range': '<5.7', 'flag': 'H' if a1c >= 5.7 else ''},
            {'test': 'Estimated Avg Glucose (eAG)', 'value': eag, 'unit': 'mg/dL',
             'reference_range': '<117', 'flag': 'H' if eag >= 117 else ''},
        ]

    def generate_immunization_record(self):
        """Generate immunization/vaccine record"""
        vaccines = []

        # COVID vaccines
        covid_dates = [
            self.fake.date_between(start_date='-3y', end_date='-2y'),
            self.fake.date_between(start_date='-2y', end_date='-1y'),
        ]
        if random.random() > 0.3:
            covid_dates.append(self.fake.date_between(start_date='-1y', end_date='-6m'))

        covid_manufacturer = random.choice(['Pfizer-BioNTech', 'Moderna', 'Johnson & Johnson'])
        for i, date in enumerate(covid_dates):
            dose_num = 'Booster' if i >= 2 else f'Dose {i+1}'
            vaccines.append({
                'vaccine': f'COVID-19 ({covid_manufacturer})',
                'dose': dose_num,
                'date': date,
                'lot': f'{random.choice(["EL", "EN", "EP", "FF"])}{random.randint(1000, 9999)}',
                'site': random.choice(['Left Deltoid', 'Right Deltoid']),
                'administrator': self.fake.name()
            })

        # Flu vaccine (annual)
        if random.random() > 0.2:
            vaccines.append({
                'vaccine': 'Influenza (Flu)',
                'dose': 'Annual',
                'date': self.fake.date_between(start_date='-6m', end_date='today'),
                'lot': f'FL{random.randint(10000, 99999)}',
                'site': random.choice(['Left Deltoid', 'Right Deltoid']),
                'administrator': self.fake.name()
            })

        # Tdap
        if random.random() > 0.4:
            vaccines.append({
                'vaccine': 'Tdap (Tetanus, Diphtheria, Pertussis)',
                'dose': 'Booster',
                'date': self.fake.date_between(start_date='-8y', end_date='-1y'),
                'lot': f'TD{random.randint(10000, 99999)}',
                'site': random.choice(['Left Deltoid', 'Right Deltoid']),
                'administrator': self.fake.name()
            })

        # Pneumonia (older patients)
        if random.random() > 0.6:
            vaccines.append({
                'vaccine': 'Pneumococcal (PPSV23)',
                'dose': 'Single',
                'date': self.fake.date_between(start_date='-5y', end_date='-1y'),
                'lot': f'PN{random.randint(10000, 99999)}',
                'site': random.choice(['Left Deltoid', 'Right Deltoid']),
                'administrator': self.fake.name()
            })

        # Shingles (older patients)
        if random.random() > 0.5:
            shingrix_date1 = self.fake.date_between(start_date='-3y', end_date='-6m')
            vaccines.append({
                'vaccine': 'Shingrix (Herpes Zoster)',
                'dose': 'Dose 1',
                'date': shingrix_date1,
                'lot': f'SH{random.randint(10000, 99999)}',
                'site': random.choice(['Left Deltoid', 'Right Deltoid']),
                'administrator': self.fake.name()
            })
            if random.random() > 0.3:
                vaccines.append({
                    'vaccine': 'Shingrix (Herpes Zoster)',
                    'dose': 'Dose 2',
                    'date': self.fake.date_between(start_date=shingrix_date1, end_date='today'),
                    'lot': f'SH{random.randint(10000, 99999)}',
                    'site': random.choice(['Left Deltoid', 'Right Deltoid']),
                    'administrator': self.fake.name()
                })

        # Hepatitis B
        if random.random() > 0.6:
            vaccines.append({
                'vaccine': 'Hepatitis B',
                'dose': 'Series Complete',
                'date': self.fake.date_between(start_date='-10y', end_date='-2y'),
                'lot': f'HB{random.randint(10000, 99999)}',
                'site': random.choice(['Left Deltoid', 'Right Deltoid']),
                'administrator': self.fake.name()
            })

        return {
            'record_date': datetime.now(),
            'vaccines': sorted(vaccines, key=lambda x: x['date'], reverse=True)
        }


class ProviderGenerator:
    """Generates synthetic healthcare provider data"""

    def __init__(self, locale='en_US', seed=None):
        self.fake = Faker(locale)
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    def generate_provider(self):
        """Generate a complete provider record"""
        specialties = [
            'Internal Medicine',
            'Family Medicine',
            'Cardiology',
            'Endocrinology',
            'Nephrology',
            'Gastroenterology',
            'Pulmonology',
            'Neurology',
            'Psychiatry',
            'Orthopedics'
        ]

        provider = {
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'title': random.choice(['MD', 'DO', 'NP', 'PA']),
            'specialty': random.choice(specialties),
            'npi': self._generate_npi(),
            'phone': self.fake.phone_number(),
            'fax': self.fake.phone_number(),
            'email': self.fake.email(),
        }

        return provider

    def _generate_npi(self):
        """Generate National Provider Identifier (10 digits)"""
        return str(random.randint(1000000000, 9999999999))


class FacilityGenerator:
    """Generates synthetic healthcare facility data"""

    def __init__(self, locale='en_US', seed=None):
        self.fake = Faker(locale)
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    def generate_facility(self):
        """Generate a complete facility record"""
        facility_types = [
            'Medical Center',
            'Hospital',
            'Clinic',
            'Health System',
            'Regional Hospital',
            'Community Hospital'
        ]

        city = self.fake.city()
        facility = {
            'name': f"{city} {random.choice(facility_types)}",
            'address': {
                'street': self.fake.street_address(),
                'city': city,
                'state': self.fake.state_abbr(),
                'zip': self.fake.zipcode()
            },
            'phone': self.fake.phone_number(),
            'fax': self.fake.phone_number(),
        }

        return facility
