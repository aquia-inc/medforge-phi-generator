"""
Tax CUI generator.

Generates synthetic CUI documents for:
- Federal Taxpayer Information
- Written Determinations (Private Letter Rulings)
"""
from typing import Any, Dict, List, Optional
import random
from datetime import datetime, timedelta

from .base import BaseCUIGenerator
from .factory import CUIGeneratorFactory


@CUIGeneratorFactory.register('tax')
class TaxCUIGenerator(BaseCUIGenerator):
    """Generator for Tax CUI documents."""

    CATEGORY = 'tax'
    SUBCATEGORIES = ['federal_taxpayer', 'written_determinations']
    CUI_MARKINGS = [
        'CUI//SP-TAX',
        'CUI//SP-FTI',
        'FEDERAL TAX INFORMATION',
        'CONTROLLED UNCLASSIFIED INFORMATION - TAX',
    ]
    AUTHORITIES = [
        '26 USC 6103',
        '26 CFR 301.6103',
        'Internal Revenue Code Section 6103',
        'Tax Information Security Guidelines',
    ]

    # Tax form types
    FORM_TYPES = [
        ('1040', 'Individual Income Tax Return'),
        ('1120', 'Corporate Income Tax Return'),
        ('941', 'Employer\'s Quarterly Federal Tax Return'),
        ('1099', 'Information Return'),
        ('W-2', 'Wage and Tax Statement'),
        ('1065', 'Partnership Return'),
    ]

    FILING_STATUS = [
        'Single',
        'Married Filing Jointly',
        'Married Filing Separately',
        'Head of Household',
        'Qualifying Widow(er)',
    ]

    PENALTY_TYPES = [
        ('FTP', 'Failure to Pay'),
        ('FTF', 'Failure to File'),
        ('ACC', 'Accuracy-Related'),
        ('EFP', 'Estimated Tax'),
        ('TFRP', 'Trust Fund Recovery'),
    ]

    DETERMINATION_TYPES = [
        'Private Letter Ruling',
        'Technical Advice Memorandum',
        'Chief Counsel Advice',
        'Determination Letter',
        'Revenue Ruling Draft',
    ]

    def __init__(self, locale: str = 'en_US', seed: Optional[int] = None):
        super().__init__(locale, seed)

    def get_document_types(self) -> List[Dict[str, Any]]:
        """Get available document types for tax category."""
        return self._document_types.get(self.CATEGORY, {})

    def generate_positive(self) -> Dict[str, Any]:
        """Generate a CUI-positive tax document."""
        subcategory = random.choice(self.SUBCATEGORIES)

        if subcategory == 'federal_taxpayer':
            doc_type = random.choice(['taxpayer_record', 'audit_workpapers', 'collection_case'])
            generators = {
                'taxpayer_record': self._generate_taxpayer_record,
                'audit_workpapers': self._generate_audit_workpapers,
                'collection_case': self._generate_collection_case,
            }
            return generators[doc_type](subcategory)
        else:
            return self._generate_written_determination(subcategory)

    def generate_negative(self) -> Dict[str, Any]:
        """Generate a CUI-negative tax document."""
        doc_type = random.choice(['blank_tax_form', 'published_ruling', 'tax_guidance'])

        if doc_type == 'blank_tax_form':
            return self._generate_blank_tax_form()
        elif doc_type == 'published_ruling':
            return self._generate_published_ruling()
        else:
            return self._generate_tax_guidance()

    def _generate_taxpayer_record(self, subcategory: str) -> Dict[str, Any]:
        """Generate a taxpayer account record."""
        taxpayer_name = self.fake.name()
        form_type = random.choice(self.FORM_TYPES)

        doc = self._build_base_document('taxpayer_record', subcategory, is_positive=True)
        doc.update({
            'title': 'Taxpayer Account Record',
            'classification': 'FEDERAL TAX INFORMATION - CUI',
            'record_type': 'Individual Taxpayer Account Transcript',
            'taxpayer': {
                'name': taxpayer_name,
                'ssn_masked': f"XXX-XX-{random.randint(1000, 9999)}",
                'address': {
                    'street': self.fake.street_address(),
                    'city': self.fake.city(),
                    'state': self.fake.state_abbr(),
                    'zip': self.fake.zipcode(),
                },
                'filing_status': random.choice(self.FILING_STATUS),
            },
            'tax_period': f"{random.randint(2020, 2024)}",
            'form_type': form_type[0],
            'form_description': form_type[1],
            'account_summary': {
                'gross_income': self.format_currency(self.generate_currency_amount(30000, 500000)),
                'taxable_income': self.format_currency(self.generate_currency_amount(20000, 450000)),
                'tax_liability': self.format_currency(self.generate_currency_amount(5000, 150000)),
                'payments_credits': self.format_currency(self.generate_currency_amount(4000, 160000)),
                'balance_due': self.format_currency(self.generate_currency_amount(0, 20000)),
            },
            'transaction_history': [
                {
                    'date': self.generate_date_in_range(-365, 0).strftime('%m/%d/%Y'),
                    'transaction': random.choice([
                        'Return Filed',
                        'Payment Received',
                        'Refund Issued',
                        'Notice Issued',
                        'Penalty Assessed',
                    ]),
                    'amount': self.format_currency(random.randint(100, 50000)),
                }
                for _ in range(random.randint(3, 8))
            ],
            'disclosure_authorization': random.choice([True, False]),
            'record_date': self.generate_date_in_range(-7, 0).strftime('%B %d, %Y'),
            'confidentiality_notice': (
                "This document contains Federal Tax Information protected under 26 USC 6103. "
                "Unauthorized disclosure is a federal crime punishable by fine and imprisonment."
            ),
        })
        return doc

    def _generate_audit_workpapers(self, subcategory: str) -> Dict[str, Any]:
        """Generate tax audit workpapers."""
        taxpayer_name = self.fake.name()

        doc = self._build_base_document('audit_workpapers', subcategory, is_positive=True)
        doc.update({
            'title': 'Examination Workpapers',
            'classification': 'FEDERAL TAX INFORMATION - CUI',
            'case_number': f"EX-{random.randint(2020, 2025)}-{random.randint(100000, 999999)}",
            'taxpayer': {
                'name': taxpayer_name,
                'tin_masked': f"XXX-XX-{random.randint(1000, 9999)}",
            },
            'examination_type': random.choice([
                'Office Examination',
                'Field Examination',
                'Correspondence Examination',
            ]),
            'tax_years_examined': [str(year) for year in range(random.randint(2019, 2021), random.randint(2022, 2024))],
            'examiner': {
                'name': self.fake.name(),
                'badge_number': f"RA-{random.randint(10000, 99999)}",
                'group': f"Group {random.randint(1, 50)}",
            },
            'examination_period': {
                'start_date': self.generate_date_in_range(-180, -90).strftime('%B %d, %Y'),
                'closing_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            },
            'issues_examined': [
                {
                    'issue': random.choice([
                        'Business Expenses',
                        'Charitable Contributions',
                        'Investment Income',
                        'Self-Employment Income',
                        'Employee Business Expenses',
                    ]),
                    'proposed_adjustment': self.format_currency(self.generate_currency_amount(1000, 100000)),
                    'status': random.choice(['Agreed', 'Unagreed', 'Pending']),
                }
                for _ in range(random.randint(2, 5))
            ],
            'total_proposed_adjustment': self.format_currency(self.generate_currency_amount(5000, 500000)),
            'examination_result': random.choice([
                'No Change',
                'Agreed Adjustment',
                'Unagreed - Referred to Appeals',
                '30-Day Letter Issued',
            ]),
            'supervisor_approval': {
                'name': self.fake.name(),
                'title': 'Group Manager',
                'date': self.generate_date_in_range(-7, 0).strftime('%B %d, %Y'),
            },
        })
        return doc

    def _generate_collection_case(self, subcategory: str) -> Dict[str, Any]:
        """Generate a collection case file."""
        taxpayer_name = self.fake.name()
        balance = self.generate_currency_amount(5000, 500000)

        doc = self._build_base_document('collection_case', subcategory, is_positive=True)
        doc.update({
            'title': 'Collection Case File',
            'classification': 'FEDERAL TAX INFORMATION - CUI',
            'case_number': f"COL-{random.randint(2020, 2025)}-{random.randint(100000, 999999)}",
            'taxpayer': {
                'name': taxpayer_name,
                'tin_masked': f"XXX-XX-{random.randint(1000, 9999)}",
                'address': f"{self.fake.city()}, {self.fake.state_abbr()}",
            },
            'collection_status': random.choice([
                'Active Collection',
                'Currently Not Collectible',
                'Installment Agreement',
                'Offer in Compromise',
                'Taxpayer Delinquent Account',
            ]),
            'balance_due': {
                'tax': self.format_currency(balance * 0.7),
                'penalties': self.format_currency(balance * 0.2),
                'interest': self.format_currency(balance * 0.1),
                'total': self.format_currency(balance),
            },
            'tax_periods': [f"{random.randint(2018, 2023)}" for _ in range(random.randint(1, 4))],
            'collection_history': [
                {
                    'date': self.generate_date_in_range(-365, 0).strftime('%m/%d/%Y'),
                    'action': random.choice([
                        'Notice CP14 Sent',
                        'Notice CP501 Sent',
                        'Notice CP504 Sent',
                        'Federal Tax Lien Filed',
                        'Installment Agreement Proposed',
                        'Taxpayer Contact Attempted',
                    ]),
                }
                for _ in range(random.randint(3, 7))
            ],
            'assets_identified': {
                'real_property': random.choice([True, False]),
                'bank_accounts': random.choice([True, False]),
                'wages': random.choice([True, False]),
                'vehicles': random.choice([True, False]),
            },
            'assigned_officer': {
                'name': self.fake.name(),
                'title': 'Revenue Officer',
                'badge': f"RO-{random.randint(10000, 99999)}",
            },
            'next_action': random.choice([
                'Issue Final Notice of Intent to Levy',
                'Conduct Asset Investigation',
                'Process Installment Agreement',
                'Prepare Offer in Compromise',
            ]),
            'next_action_date': self.generate_date_in_range(7, 30).strftime('%B %d, %Y'),
        })
        return doc

    def _generate_written_determination(self, subcategory: str) -> Dict[str, Any]:
        """Generate a written determination (PLR, TAM, etc.)."""
        determination_type = random.choice(self.DETERMINATION_TYPES)
        taxpayer_name = self.fake.name()

        doc = self._build_base_document('written_determination', subcategory, is_positive=True)
        doc.update({
            'title': f'{determination_type} (DRAFT)',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - TAX',
            'document_status': 'DRAFT - PRE-RELEASE',
            'document_number': f"PLR-{random.randint(2024, 2025)}{random.randint(10000, 99999)}",
            'taxpayer_identifier': f"Taxpayer {random.randint(1, 999):03d}",
            'issue_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'issues': [
                f"Issue {i+1}: {random.choice(['Tax treatment of', 'Deductibility of', 'Character of', 'Timing of'])} "
                f"{random.choice(['transaction', 'payment', 'income', 'expense', 'distribution'])}"
                for i in range(random.randint(1, 3))
            ],
            'code_sections': [
                f"IRC Section {random.randint(1, 9999)}"
                for _ in range(random.randint(1, 4))
            ],
            'facts': (
                "The taxpayer has represented the following facts in connection with this ruling request: "
                "[Detailed fact pattern regarding the transaction and parties involved]"
            ),
            'law_and_analysis': (
                "Based on the applicable law and the facts presented, the Service has determined that "
                "[analysis of how the law applies to the taxpayer's situation]"
            ),
            'conclusion': random.choice([
                'The proposed transaction will be treated as described by the taxpayer.',
                'The proposed transaction will not qualify for the requested treatment.',
                'The Service will not rule on this issue at this time.',
            ]),
            'caveats': [
                'This ruling is based solely on the facts as represented.',
                'This ruling has no precedential value for other taxpayers.',
                'This ruling may be revoked if facts change.',
            ],
            'prepared_by': {
                'name': self.fake.name(),
                'title': 'Attorney Advisor',
                'office': 'Office of Chief Counsel',
            },
            'review_status': random.choice([
                'Pending Branch Chief Review',
                'Pending Associate Chief Counsel Review',
                'Pending Taxpayer Consent to Disclosure',
            ]),
            'confidentiality_notice': (
                "This draft ruling contains taxpayer-specific information protected under 26 USC 6103. "
                "Do not release until redacted version is published per 26 USC 6110."
            ),
        })
        return doc

    def _generate_blank_tax_form(self) -> Dict[str, Any]:
        """Generate blank tax forms (negative example)."""
        form_type = random.choice(self.FORM_TYPES)
        doc = self._build_base_document('blank_tax_form', 'general', is_positive=False)
        doc.update({
            'title': f'Form {form_type[0]} (BLANK)',
            'form_number': form_type[0],
            'form_title': form_type[1],
            'tax_year': str(random.randint(2023, 2024)),
            'revision_date': self.generate_date_in_range(-365, 0).strftime('%B %Y'),
            'omb_number': f"1545-{random.randint(1000, 9999)}",
            'instructions': (
                f"This is a blank Form {form_type[0]} for reference purposes. "
                "Complete all applicable fields before filing."
            ),
            'fields': [
                {'name': 'Taxpayer Name', 'value': '[ENTER NAME]'},
                {'name': 'SSN/EIN', 'value': '[ENTER TIN]'},
                {'name': 'Address', 'value': '[ENTER ADDRESS]'},
            ],
            'available_at': 'IRS.gov',
            'distribution': 'Unlimited Public Distribution',
        })
        return doc

    def _generate_published_ruling(self) -> Dict[str, Any]:
        """Generate a published revenue ruling (negative example)."""
        doc = self._build_base_document('published_ruling', 'written_determinations', is_positive=False)
        doc.update({
            'title': 'Revenue Ruling (Published)',
            'ruling_number': f"Rev. Rul. {random.randint(2020, 2024)}-{random.randint(1, 50)}",
            'publication_date': self.generate_date_in_range(-365, 0).strftime('%B %d, %Y'),
            'published_in': f"IRB {random.randint(2020, 2024)}-{random.randint(1, 52)}",
            'issue': random.choice([
                'Treatment of cryptocurrency transactions',
                'Deductibility of business meals',
                'Qualified business income deduction',
                'Foreign tax credit computation',
            ]),
            'holding': (
                "The Service has ruled on the tax treatment of [topic], "
                "establishing guidance for all similarly situated taxpayers."
            ),
            'code_sections': [
                f"IRC Section {random.randint(1, 9999)}"
                for _ in range(random.randint(1, 3))
            ],
            'status': 'Published and in effect',
            'supersedes': random.choice([None, f"Rev. Rul. {random.randint(2000, 2019)}-{random.randint(1, 50)}"]),
            'distribution': 'Unlimited Public Distribution',
        })
        return doc

    def _generate_tax_guidance(self) -> Dict[str, Any]:
        """Generate public tax guidance (negative example)."""
        doc = self._build_base_document('tax_guidance', 'general', is_positive=False)
        doc.update({
            'title': 'Tax Topic Guidance',
            'publisher': 'Internal Revenue Service',
            'topic_number': f"Topic No. {random.randint(100, 999)}",
            'topic': random.choice([
                'Filing Requirements',
                'Standard Deduction',
                'Retirement Savings Contributions Credit',
                'Home Office Deduction',
                'Estimated Tax Payments',
            ]),
            'last_updated': self.generate_date_in_range(-90, 0).strftime('%B %d, %Y'),
            'content': (
                "This publication provides general guidance on federal tax matters. "
                "Consult a tax professional for advice specific to your situation."
            ),
            'related_forms': [
                f"Form {random.choice(['1040', '1040-SR', 'Schedule C', 'Schedule A', 'W-4'])}"
                for _ in range(random.randint(1, 3))
            ],
            'available_at': 'IRS.gov',
            'distribution': 'Unlimited Public Distribution',
        })
        return doc
