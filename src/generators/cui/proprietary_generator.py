"""
Proprietary Business Information CUI generator.

Generates synthetic CUI documents for:
- Entity Registration Information
- General Proprietary Business Information
"""
from typing import Any, Dict, List, Optional
import random
from datetime import datetime, timedelta

from .base import BaseCUIGenerator
from .factory import CUIGeneratorFactory


@CUIGeneratorFactory.register('proprietary')
class ProprietaryCUIGenerator(BaseCUIGenerator):
    """Generator for Proprietary Business Information CUI documents."""

    CATEGORY = 'proprietary'
    SUBCATEGORIES = ['entity_registration', 'general']
    CUI_MARKINGS = [
        'CUI//SP-PROPIN',
        'CUI//SP-BSNCONF',
        'PROPRIETARY INFORMATION',
        'BUSINESS CONFIDENTIAL',
    ]
    AUTHORITIES = [
        '18 USC 1905',
        'Trade Secrets Act',
        '5 USC 552(b)(4)',
        'Defend Trade Secrets Act of 2016',
    ]

    # Business types
    BUSINESS_TYPES = [
        'Small Business',
        'Woman-Owned Small Business',
        'Service-Disabled Veteran-Owned',
        '8(a) Small Business',
        'HUBZone Small Business',
        'Large Business',
        'Small Disadvantaged Business',
    ]

    NAICS_CODES = [
        ('541511', 'Custom Computer Programming Services'),
        ('541512', 'Computer Systems Design Services'),
        ('541519', 'Other Computer Related Services'),
        ('541611', 'Administrative Management Consulting'),
        ('541614', 'Process, Physical Distribution, and Logistics Consulting'),
        ('541620', 'Environmental Consulting Services'),
        ('541690', 'Other Scientific and Technical Consulting'),
        ('561110', 'Office Administrative Services'),
        ('561210', 'Facilities Support Services'),
        ('541330', 'Engineering Services'),
    ]

    def __init__(self, locale: str = 'en_US', seed: Optional[int] = None):
        super().__init__(locale, seed)

    def get_document_types(self) -> List[Dict[str, Any]]:
        """Get available document types for proprietary category."""
        return self._document_types.get(self.CATEGORY, {})

    def generate_positive(self) -> Dict[str, Any]:
        """Generate a CUI-positive proprietary business document."""
        subcategory = random.choice(self.SUBCATEGORIES)

        if subcategory == 'entity_registration':
            return self._generate_sam_registration(subcategory)
        else:
            doc_type = random.choice(['trade_secret', 'contractor_info', 'financial_data'])
            generators = {
                'trade_secret': self._generate_trade_secret_disclosure,
                'contractor_info': self._generate_contractor_info,
                'financial_data': self._generate_financial_data,
            }
            return generators[doc_type](subcategory)

    def generate_negative(self) -> Dict[str, Any]:
        """Generate a CUI-negative proprietary document."""
        doc_type = random.choice(['sam_guide', 'public_business_info', 'company_profile'])

        if doc_type == 'sam_guide':
            return self._generate_sam_guide()
        elif doc_type == 'public_business_info':
            return self._generate_public_business_info()
        else:
            return self._generate_public_company_profile()

    def _generate_sam_registration(self, subcategory: str) -> Dict[str, Any]:
        """Generate SAM entity registration data."""
        company = self.fake.company()
        naics = random.choice(self.NAICS_CODES)

        doc = self._build_base_document('sam_registration', subcategory, is_positive=True)
        doc.update({
            'title': 'SAM Entity Registration Record',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - PROPRIETARY',
            'registration_status': 'Active',
            'entity': {
                'legal_business_name': company,
                'dba': f"{company} Solutions" if random.choice([True, False]) else None,
                'uei': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=12)),
                'cage_code': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5)),
                'duns': f"{random.randint(100000000, 999999999)}",
                'ein': f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}",
            },
            'physical_address': {
                'street': self.fake.street_address(),
                'city': self.fake.city(),
                'state': self.fake.state_abbr(),
                'zip': self.fake.zipcode(),
                'country': 'USA',
            },
            'mailing_address': {
                'street': self.fake.street_address(),
                'city': self.fake.city(),
                'state': self.fake.state_abbr(),
                'zip': self.fake.zipcode(),
            },
            'business_information': {
                'business_type': random.choice(self.BUSINESS_TYPES),
                'entity_type': random.choice(['Corporation', 'LLC', 'Sole Proprietor', 'Partnership']),
                'business_start_date': self.generate_date_in_range(-7300, -365).strftime('%m/%d/%Y'),
                'fiscal_year_end': random.choice(['December 31', 'September 30', 'June 30']),
                'employees': random.randint(5, 1000),
            },
            'naics_codes': [
                {'code': naics[0], 'description': naics[1], 'primary': True},
            ] + [
                {'code': n[0], 'description': n[1], 'primary': False}
                for n in random.sample(self.NAICS_CODES, k=random.randint(1, 3))
                if n[0] != naics[0]
            ],
            'financial_information': {
                'annual_revenue': self.format_currency(self.generate_currency_amount(100000, 50000000)),
                'average_revenue_3yr': self.format_currency(self.generate_currency_amount(80000, 45000000)),
                'bank_account_on_file': True,
            },
            'points_of_contact': {
                'government_business': {
                    'name': self.fake.name(),
                    'title': 'Government Contracts Manager',
                    'phone': self.fake.phone_number(),
                    'email': f"contracts@{company.lower().replace(' ', '')}.com",
                },
                'electronic_business': {
                    'name': self.fake.name(),
                    'title': 'IT Administrator',
                    'email': f"sam@{company.lower().replace(' ', '')}.com",
                },
            },
            'registration_dates': {
                'activation_date': self.generate_date_in_range(-365, -30).strftime('%m/%d/%Y'),
                'expiration_date': self.generate_date_in_range(30, 365).strftime('%m/%d/%Y'),
            },
            'exclusions': 'None',
            'confidentiality_notice': (
                "This entity registration data contains proprietary business information. "
                "Access limited to authorized government personnel."
            ),
        })
        return doc

    def _generate_trade_secret_disclosure(self, subcategory: str) -> Dict[str, Any]:
        """Generate a trade secret disclosure document."""
        company = self.fake.company()

        doc = self._build_base_document('trade_secret', subcategory, is_positive=True)
        doc.update({
            'title': 'Trade Secret and Proprietary Information Disclosure',
            'classification': 'PROPRIETARY INFORMATION - CUI',
            'disclosure_number': f"TS-{random.randint(2024, 2025)}-{random.randint(1000, 9999)}",
            'disclosing_party': {
                'company': company,
                'contact': self.fake.name(),
                'title': 'Chief Technology Officer',
            },
            'receiving_party': {
                'agency': self.get_agency(),
                'purpose': random.choice([
                    'Contract Performance',
                    'Technical Evaluation',
                    'Regulatory Review',
                    'Grant Application',
                ]),
            },
            'disclosure_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'trade_secret_description': {
                'type': random.choice([
                    'Software Algorithm',
                    'Manufacturing Process',
                    'Technical Specifications',
                    'Customer List',
                    'Pricing Methodology',
                ]),
                'summary': (
                    f"Proprietary information regarding {company}'s "
                    f"{random.choice(['core technology', 'business methods', 'technical approach', 'cost structure'])}."
                ),
            },
            'protective_measures': [
                'Access limited to need-to-know government personnel',
                'Information stored in secure systems',
                'Physical documents maintained in locked storage',
                'No copies without written authorization',
            ],
            'duration_of_protection': f"{random.randint(3, 10)} years from disclosure date",
            'legal_basis': '18 USC 1905 (Trade Secrets Act)',
            'non_disclosure_acknowledgment': {
                'signed_by': self.fake.name(),
                'title': 'Contracting Officer',
                'date': self.generate_date_in_range(-14, 0).strftime('%B %d, %Y'),
            },
        })
        return doc

    def _generate_contractor_info(self, subcategory: str) -> Dict[str, Any]:
        """Generate contractor proprietary information."""
        company = self.fake.company()

        doc = self._build_base_document('contractor_info', subcategory, is_positive=True)
        doc.update({
            'title': 'Contractor Proprietary Information',
            'classification': 'CUI - BUSINESS CONFIDENTIAL',
            'contract_number': f"GS-{random.randint(10, 99)}F-{random.randint(1000, 9999)}W",
            'contractor': {
                'name': company,
                'cage_code': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5)),
            },
            'information_type': random.choice([
                'Labor Rate Structure',
                'Cost and Pricing Data',
                'Technical Approach',
                'Subcontractor Information',
                'Key Personnel Information',
            ]),
            'labor_categories': [
                {
                    'category': random.choice(['Program Manager', 'Senior Analyst', 'Developer', 'Engineer']),
                    'rate': self.format_currency(random.randint(100, 300)),
                    'rate_type': 'Hourly',
                }
                for _ in range(random.randint(3, 6))
            ],
            'indirect_rates': {
                'fringe': f"{random.randint(25, 40)}%",
                'overhead': f"{random.randint(50, 120)}%",
                'g_and_a': f"{random.randint(5, 15)}%",
            },
            'profit_margin': f"{random.randint(5, 15)}%",
            'subcontractors': [
                {
                    'name': self.fake.company(),
                    'percentage_of_work': f"{random.randint(5, 30)}%",
                }
                for _ in range(random.randint(0, 3))
            ],
            'confidentiality_notice': (
                "This document contains contractor proprietary cost and pricing data. "
                "Disclosure is prohibited under 5 USC 552(b)(4)."
            ),
        })
        return doc

    def _generate_financial_data(self, subcategory: str) -> Dict[str, Any]:
        """Generate proprietary financial data."""
        company = self.fake.company()
        annual_revenue = self.generate_currency_amount(1000000, 100000000)

        doc = self._build_base_document('financial_data', subcategory, is_positive=True)
        doc.update({
            'title': 'Proprietary Financial Data Submission',
            'classification': 'CUI - PROPRIETARY',
            'company': company,
            'fiscal_year': f"FY {random.randint(2022, 2024)}",
            'submission_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'financial_summary': {
                'total_revenue': self.format_currency(annual_revenue),
                'government_revenue': self.format_currency(annual_revenue * random.uniform(0.3, 0.9)),
                'commercial_revenue': self.format_currency(annual_revenue * random.uniform(0.1, 0.7)),
                'net_income': self.format_currency(annual_revenue * random.uniform(0.03, 0.15)),
            },
            'key_metrics': {
                'current_ratio': round(random.uniform(1.2, 3.0), 2),
                'debt_to_equity': round(random.uniform(0.1, 1.5), 2),
                'days_cash_on_hand': random.randint(30, 180),
            },
            'purpose': random.choice([
                'Contractor Responsibility Determination',
                'Small Business Size Verification',
                'Financial Capability Assessment',
            ]),
            'certified_by': {
                'name': self.fake.name(),
                'title': 'Chief Financial Officer',
                'date': self.generate_date_in_range(-7, 0).strftime('%B %d, %Y'),
            },
            'confidentiality_notice': (
                "This financial data is proprietary and confidential. "
                "Use is limited to the stated purpose."
            ),
        })
        return doc

    def _generate_sam_guide(self) -> Dict[str, Any]:
        """Generate SAM registration guide (negative example)."""
        doc = self._build_base_document('sam_guide', 'entity_registration', is_positive=False)
        doc.update({
            'title': 'SAM.gov Registration Guide',
            'publisher': 'General Services Administration',
            'publication_date': self.generate_date_in_range(-180, 0).strftime('%B %d, %Y'),
            'chapters': [
                'Creating a SAM Account',
                'Entity Registration Process',
                'Required Information',
                'Maintaining Your Registration',
                'Troubleshooting Common Issues',
            ],
            'requirements': [
                'DUNS Number (transitioning to UEI)',
                'TIN/EIN',
                'Banking Information',
                'NAICS Codes',
            ],
            'help_resources': [
                'SAM.gov Help Desk',
                'Federal Service Desk',
                'Online Tutorials',
            ],
            'distribution': 'Unlimited Public Distribution',
            'note': 'PUBLIC INFORMATION - Not CUI',
        })
        return doc

    def _generate_public_business_info(self) -> Dict[str, Any]:
        """Generate publicly available business information (negative example)."""
        company = self.fake.company()
        doc = self._build_base_document('public_business_info', 'general', is_positive=False)
        doc.update({
            'title': 'Public Business Profile',
            'company': company,
            'source': 'SAM.gov Public Search',
            'public_data': {
                'legal_name': company,
                'dba': None,
                'physical_address': {
                    'city': self.fake.city(),
                    'state': self.fake.state_abbr(),
                },
                'entity_status': 'Active',
                'registration_expiration': self.generate_date_in_range(30, 365).strftime('%m/%d/%Y'),
            },
            'note': (
                "This information is publicly available through SAM.gov and does not "
                "include proprietary business information."
            ),
            'distribution': 'Unlimited Public Distribution',
        })
        return doc

    def _generate_public_company_profile(self) -> Dict[str, Any]:
        """Generate a public company profile (negative example)."""
        company = self.fake.company()
        doc = self._build_base_document('company_profile', 'general', is_positive=False)
        doc.update({
            'title': 'Company Capability Statement',
            'company': company,
            'tagline': self.fake.catch_phrase(),
            'about': (
                f"{company} is a leading provider of professional services to the federal government. "
                f"We specialize in IT modernization, cybersecurity, and program management."
            ),
            'core_capabilities': [
                'IT Modernization',
                'Cybersecurity Services',
                'Program Management',
                'Data Analytics',
            ],
            'certifications': random.sample(self.BUSINESS_TYPES[:5], k=random.randint(1, 3)),
            'past_performance_references': 'Available upon request',
            'contact': {
                'email': f"info@{company.lower().replace(' ', '')}.com",
                'website': f"www.{company.lower().replace(' ', '')}.com",
            },
            'distribution': 'Marketing material - Unlimited distribution',
            'note': 'PUBLIC MARKETING MATERIAL - Not CUI',
        })
        return doc
