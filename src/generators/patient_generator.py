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

    def generate_lab_results(self):
        """Generate lab test results"""
        return {
            'test_date': self.fake.date_between(start_date='-30d', end_date='today'),
            'results': [
                {
                    'test': 'Hemoglobin A1C',
                    'value': round(random.uniform(5.0, 9.0), 1),
                    'unit': '%',
                    'reference_range': '4.0-5.6',
                    'flag': 'H' if random.random() > 0.5 else ''
                },
                {
                    'test': 'Total Cholesterol',
                    'value': random.randint(150, 280),
                    'unit': 'mg/dL',
                    'reference_range': '<200',
                    'flag': 'H' if random.random() > 0.5 else ''
                },
                {
                    'test': 'LDL Cholesterol',
                    'value': random.randint(70, 190),
                    'unit': 'mg/dL',
                    'reference_range': '<100',
                    'flag': 'H' if random.random() > 0.6 else ''
                },
                {
                    'test': 'HDL Cholesterol',
                    'value': random.randint(35, 80),
                    'unit': 'mg/dL',
                    'reference_range': '>40',
                    'flag': 'L' if random.random() > 0.7 else ''
                },
                {
                    'test': 'Glucose',
                    'value': random.randint(70, 180),
                    'unit': 'mg/dL',
                    'reference_range': '70-100',
                    'flag': 'H' if random.random() > 0.5 else ''
                }
            ]
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
