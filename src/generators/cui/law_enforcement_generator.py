"""
Law Enforcement CUI generator.

Generates synthetic CUI documents for:
- Criminal History Records Information
- Investigation files and reports
"""
from typing import Any, Dict, List, Optional
import random
from datetime import datetime, timedelta

from .base import BaseCUIGenerator
from .factory import CUIGeneratorFactory


@CUIGeneratorFactory.register('law_enforcement')
class LawEnforcementCUIGenerator(BaseCUIGenerator):
    """Generator for Law Enforcement CUI documents."""

    CATEGORY = 'law_enforcement'
    SUBCATEGORIES = ['criminal_history', 'investigation', 'general']
    CUI_MARKINGS = [
        'CUI//LES',
        'CUI//SP-CRIM',
        'CUI//SP-INVST',
        'LAW ENFORCEMENT SENSITIVE',
    ]
    AUTHORITIES = [
        '28 USC 534',
        '5 USC 552(b)(7)',
        'Privacy Act of 1974',
        'Inspector General Act of 1978',
    ]

    # Criminal history data
    OFFENSE_TYPES = [
        'Fraud',
        'Embezzlement',
        'Tax Evasion',
        'False Statements',
        'Conspiracy',
        'Wire Fraud',
        'Money Laundering',
        'Bribery',
    ]

    INVESTIGATION_STATUS = [
        'Open',
        'Active',
        'Pending Review',
        'Closed',
        'Referred for Prosecution',
        'Administratively Closed',
    ]

    INVESTIGATING_AGENCIES = [
        'Federal Bureau of Investigation',
        'Securities and Exchange Commission',
        'Department of Health and Human Services OIG',
        'Department of Justice',
        'Internal Revenue Service Criminal Investigation',
        'Office of Inspector General',
    ]

    def __init__(self, locale: str = 'en_US', seed: Optional[int] = None):
        super().__init__(locale, seed)

    def get_document_types(self) -> List[Dict[str, Any]]:
        """Get available document types for law enforcement category."""
        return self._document_types.get(self.CATEGORY, {})

    def generate_positive(self) -> Dict[str, Any]:
        """Generate a CUI-positive law enforcement document."""
        subcategory = random.choice(self.SUBCATEGORIES[:2])  # Exclude 'general'

        if subcategory == 'criminal_history':
            return self._generate_criminal_history(subcategory)
        else:
            doc_type = random.choice(['investigation_report', 'interview_summary', 'evidence_log'])
            if doc_type == 'investigation_report':
                return self._generate_investigation_report(subcategory)
            elif doc_type == 'interview_summary':
                return self._generate_interview_summary(subcategory)
            else:
                return self._generate_evidence_log(subcategory)

    def generate_negative(self) -> Dict[str, Any]:
        """Generate a CUI-negative law enforcement document."""
        doc_type = random.choice(['crime_prevention', 'fraud_awareness', 'public_safety'])

        if doc_type == 'crime_prevention':
            return self._generate_crime_prevention()
        elif doc_type == 'fraud_awareness':
            return self._generate_fraud_awareness()
        else:
            return self._generate_public_safety_bulletin()

    def _generate_criminal_history(self, subcategory: str) -> Dict[str, Any]:
        """Generate a criminal history record."""
        subject_name = self.fake.name()
        dob = self.fake.date_of_birth(minimum_age=25, maximum_age=70)

        doc = self._build_base_document('criminal_history', subcategory, is_positive=True)
        doc.update({
            'title': 'Criminal History Record Information',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - CRIMINAL HISTORY',
            'record_id': f"CHR-{self.fake.uuid4()[:10].upper()}",
            'subject': {
                'name': subject_name,
                'aliases': [self.fake.name() for _ in range(random.randint(0, 2))],
                'dob': dob.strftime('%m/%d/%Y'),
                'ssn_last4': f"XXX-XX-{random.randint(1000, 9999)}",
                'fbi_number': f"{random.randint(100000, 999999)}AA{random.randint(1, 9)}",
                'state_id': f"ST{random.randint(1000000, 9999999)}",
            },
            'physical_description': {
                'sex': random.choice(['Male', 'Female']),
                'race': random.choice(['W', 'B', 'H', 'A', 'O']),
                'height': f"{random.randint(5, 6)}'{random.randint(0, 11)}\"",
                'weight': f"{random.randint(120, 250)} lbs",
                'hair': random.choice(['BLK', 'BRN', 'BLN', 'RED', 'GRY']),
                'eyes': random.choice(['BRN', 'BLU', 'GRN', 'HAZ']),
            },
            'criminal_entries': [
                {
                    'arrest_date': self.generate_date_in_range(-3650, -365).strftime('%m/%d/%Y'),
                    'agency': random.choice(self.INVESTIGATING_AGENCIES),
                    'charge': random.choice(self.OFFENSE_TYPES),
                    'disposition': random.choice(['Convicted', 'Acquitted', 'Dismissed', 'Pending']),
                    'sentence': random.choice(['Probation', 'Fine', 'Incarceration', 'N/A']),
                }
                for _ in range(random.randint(1, 4))
            ],
            'record_source': 'Interstate Identification Index (III)',
            'purpose': random.choice([
                'Employment Background Check',
                'Security Clearance Investigation',
                'Law Enforcement Inquiry',
            ]),
            'requesting_agency': random.choice(self.INVESTIGATING_AGENCIES),
            'request_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'confidentiality_notice': (
                "Criminal History Record Information is CUI under 28 USC 534. "
                "Unauthorized disclosure is prohibited and may result in criminal penalties."
            ),
        })
        return doc

    def _generate_investigation_report(self, subcategory: str) -> Dict[str, Any]:
        """Generate an investigation report."""
        subject_name = self.fake.name()
        agency = random.choice(self.INVESTIGATING_AGENCIES)

        doc = self._build_base_document('investigation_report', subcategory, is_positive=True)
        doc.update({
            'title': 'Investigation Report',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - INVESTIGATION',
            'case_number': f"{random.randint(2020, 2025)}-INV-{random.randint(100000, 999999)}",
            'investigating_agency': agency,
            'case_agent': {
                'name': self.fake.name(),
                'badge_number': f"{random.randint(1000, 9999)}",
                'title': random.choice(['Special Agent', 'Criminal Investigator', 'Supervisory Agent']),
            },
            'subject': {
                'name': subject_name,
                'status': random.choice(['Target', 'Subject', 'Witness', 'Person of Interest']),
                'employer': self.fake.company(),
            },
            'investigation_type': random.choice(self.OFFENSE_TYPES) + ' Investigation',
            'investigation_status': random.choice(self.INVESTIGATION_STATUS),
            'date_opened': self.generate_date_in_range(-365, -30).strftime('%B %d, %Y'),
            'summary': (
                f"This investigation was initiated based on allegations of {random.choice(self.OFFENSE_TYPES).lower()} "
                f"involving {subject_name} during the period of "
                f"{self.generate_date_in_range(-730, -365).strftime('%B %Y')} to "
                f"{self.generate_date_in_range(-365, -30).strftime('%B %Y')}."
            ),
            'allegations': [
                f"Allegation {i+1}: {random.choice(self.OFFENSE_TYPES)}"
                for i in range(random.randint(1, 4))
            ],
            'evidence_collected': random.randint(5, 25),
            'interviews_conducted': random.randint(3, 15),
            'estimated_loss': self.format_currency(self.generate_currency_amount(10000, 5000000)),
            'next_steps': random.choice([
                'Continue investigation',
                'Prepare referral for prosecution',
                'Schedule grand jury presentation',
                'Close investigation administratively',
            ]),
            'supervisor_approval': {
                'name': self.fake.name(),
                'title': 'Supervisory Special Agent',
                'date': self.generate_date_in_range(-7, 0).strftime('%B %d, %Y'),
            },
        })
        return doc

    def _generate_interview_summary(self, subcategory: str) -> Dict[str, Any]:
        """Generate an investigative interview summary."""
        interviewee = self.fake.name()

        doc = self._build_base_document('interview_summary', subcategory, is_positive=True)
        doc.update({
            'title': 'Investigative Interview Summary',
            'classification': 'LAW ENFORCEMENT SENSITIVE',
            'case_number': f"{random.randint(2020, 2025)}-INV-{random.randint(100000, 999999)}",
            'interview_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'interview_location': f"{self.fake.street_address()}, {self.fake.city()}, {self.fake.state_abbr()}",
            'interviewee': {
                'name': interviewee,
                'status': random.choice(['Witness', 'Subject', 'Cooperating Individual']),
                'employer': self.fake.company(),
                'title': self.fake.job(),
            },
            'interviewing_agents': [
                {'name': self.fake.name(), 'title': 'Special Agent'}
                for _ in range(random.randint(1, 2))
            ],
            'counsel_present': random.choice([True, False]),
            'recorded': random.choice([True, False]),
            'duration': f"{random.randint(1, 4)} hours",
            'summary': (
                f"On {self.generate_date_in_range(-30, 0).strftime('%B %d, %Y')}, agents interviewed "
                f"{interviewee} regarding their knowledge of activities related to the subject matter "
                f"of this investigation. The interviewee provided information concerning "
                f"{random.choice(['financial transactions', 'organizational structure', 'personnel matters', 'business operations'])}."
            ),
            'key_points': [
                f"Point {i+1}: Information regarding {random.choice(['transactions', 'meetings', 'communications', 'documents'])}"
                for i in range(random.randint(3, 6))
            ],
            'documents_provided': random.randint(0, 10),
            'follow_up_required': random.choice([True, False]),
            'prepared_by': {
                'name': self.fake.name(),
                'title': 'Special Agent',
                'date': self.generate_date_in_range(-7, 0).strftime('%B %d, %Y'),
            },
        })
        return doc

    def _generate_evidence_log(self, subcategory: str) -> Dict[str, Any]:
        """Generate an evidence collection log."""
        doc = self._build_base_document('evidence_log', subcategory, is_positive=True)
        doc.update({
            'title': 'Evidence Collection Log',
            'classification': 'LAW ENFORCEMENT SENSITIVE',
            'case_number': f"{random.randint(2020, 2025)}-INV-{random.randint(100000, 999999)}",
            'collection_date': self.generate_date_in_range(-60, 0).strftime('%B %d, %Y'),
            'collection_location': f"{self.fake.street_address()}, {self.fake.city()}, {self.fake.state_abbr()}",
            'collecting_agent': {
                'name': self.fake.name(),
                'badge_number': f"{random.randint(1000, 9999)}",
            },
            'evidence_items': [
                {
                    'item_number': f"EV-{random.randint(1000, 9999)}",
                    'description': random.choice([
                        'Financial documents',
                        'Electronic storage device',
                        'Email correspondence',
                        'Bank statements',
                        'Contracts and agreements',
                        'Photographs',
                    ]),
                    'quantity': random.randint(1, 50),
                    'chain_of_custody': 'Maintained',
                }
                for _ in range(random.randint(3, 8))
            ],
            'storage_location': f"Evidence Vault {random.randint(1, 10)}",
            'witness_to_collection': self.fake.name(),
        })
        return doc

    def _generate_crime_prevention(self) -> Dict[str, Any]:
        """Generate crime prevention resources (negative example)."""
        doc = self._build_base_document('crime_prevention', 'general', is_positive=False)
        doc.update({
            'title': 'Crime Prevention Resources',
            'publisher': 'Federal Bureau of Investigation',
            'publication_date': self.generate_date_in_range(-180, 0).strftime('%B %d, %Y'),
            'audience': 'General Public',
            'topics': [
                'Identity Theft Prevention',
                'Online Safety Tips',
                'Reporting Suspicious Activity',
                'Scam Awareness',
            ],
            'resources': [
                'IC3.gov - Internet Crime Complaint Center',
                'FBI Tips Portal',
                'Local Field Office Contact Information',
            ],
            'distribution': 'Unlimited Public Distribution',        })
        return doc

    def _generate_fraud_awareness(self) -> Dict[str, Any]:
        """Generate fraud awareness bulletin (negative example)."""
        doc = self._build_base_document('fraud_awareness', 'general', is_positive=False)
        doc.update({
            'title': 'Fraud Awareness Bulletin',
            'publisher': random.choice(['FBI', 'FTC', 'SEC', 'OIG']),
            'bulletin_number': f"FAB-{random.randint(2024, 2025)}-{random.randint(1, 50)}",
            'publication_date': self.generate_date_in_range(-90, 0).strftime('%B %d, %Y'),
            'alert_type': random.choice([
                'Healthcare Fraud Alert',
                'Investment Scam Warning',
                'Phishing Campaign Alert',
                'Identity Theft Trends',
            ]),
            'description': (
                "This bulletin provides general awareness information about current fraud trends. "
                "No law enforcement sensitive information is included."
            ),
            'red_flags': [
                'Unsolicited contacts requesting personal information',
                'Pressure to act immediately',
                'Requests for unusual payment methods',
                'Offers that seem too good to be true',
            ],
            'reporting_instructions': 'Report suspected fraud to local authorities',
            'distribution': 'Unlimited Public Distribution',        })
        return doc

    def _generate_public_safety_bulletin(self) -> Dict[str, Any]:
        """Generate a public safety bulletin (negative example)."""
        doc = self._build_base_document('public_safety', 'general', is_positive=False)
        doc.update({
            'title': 'Public Safety Bulletin',
            'publisher': 'Department of Homeland Security',
            'publication_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'topic': random.choice([
                'Severe Weather Preparedness',
                'Community Emergency Response',
                'Cybersecurity Best Practices',
                'Holiday Safety Tips',
            ]),
            'content': (
                "This public bulletin provides general safety information for community awareness. "
                "No sensitive law enforcement information is included."
            ),
            'tips': [
                'Develop a family communication plan',
                'Maintain emergency supplies',
                'Stay informed through official channels',
                'Know your evacuation routes',
            ],
            'distribution': 'Unlimited Public Distribution',        })
        return doc
