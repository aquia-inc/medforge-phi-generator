"""
Financial CUI generator.

Generates synthetic CUI documents for:
- Budget (Presidential memos, agency justifications)
- Bank Secrecy (SARs, CTRs)
- EFT (Electronic Funds Transfer)
- Retirement (FERS/CSRS)
- Comptroller General
"""
from typing import Any, Dict, List, Optional
import random
from datetime import datetime, timedelta

from .base import BaseCUIGenerator
from .factory import CUIGeneratorFactory


@CUIGeneratorFactory.register('financial')
class FinancialCUIGenerator(BaseCUIGenerator):
    """Generator for Financial CUI documents."""

    CATEGORY = 'financial'
    SUBCATEGORIES = ['budget', 'bank_secrecy', 'eft', 'retirement', 'comptroller_general']
    CUI_MARKINGS = [
        'CUI//SP-BUDG',
        'CUI//SP-BNKSCR',
        'CUI//SP-FINC',
        'CUI - BUDGET',
    ]
    AUTHORITIES = [
        '31 USC 1105',
        'OMB Circular A-11',
        '31 USC 5311',
        'Bank Secrecy Act',
    ]

    # Budget-related data
    BUDGET_PROGRAMS = [
        'Healthcare Initiatives',
        'Information Technology Modernization',
        'Research and Development',
        'Infrastructure Improvement',
        'Personnel Services',
        'Grant Programs',
        'Regulatory Compliance',
        'Cybersecurity Enhancement',
    ]

    BUDGET_CATEGORIES = [
        'Personnel Compensation',
        'Personnel Benefits',
        'Travel',
        'Transportation',
        'Rent and Communications',
        'Printing and Reproduction',
        'Contractual Services',
        'Supplies and Materials',
        'Equipment',
    ]

    # Bank Secrecy data
    SUSPICIOUS_ACTIVITIES = [
        'Structuring transactions to avoid reporting',
        'Unusual wire transfer patterns',
        'Large cash transactions inconsistent with business type',
        'Rapid movement of funds through multiple accounts',
        'Transactions with high-risk jurisdictions',
    ]

    # Retirement systems
    RETIREMENT_SYSTEMS = ['FERS', 'CSRS', 'FERS-FRAE', 'FERS-RAE']

    def __init__(self, locale: str = 'en_US', seed: Optional[int] = None):
        super().__init__(locale, seed)

    def get_document_types(self) -> List[Dict[str, Any]]:
        """Get available document types for financial category."""
        return self._document_types.get(self.CATEGORY, {})

    def generate_positive(self) -> Dict[str, Any]:
        """Generate a CUI-positive financial document."""
        subcategory = random.choice(self.SUBCATEGORIES)

        generators = {
            'budget': self._generate_budget_memo,
            'bank_secrecy': self._generate_sar,
            'eft': self._generate_eft_authorization,
            'retirement': self._generate_retirement_estimate,
            'comptroller_general': self._generate_comptroller_report,
        }

        return generators[subcategory](subcategory)

    def generate_negative(self) -> Dict[str, Any]:
        """Generate a CUI-negative financial document."""
        doc_type = random.choice(['public_budget', 'aml_training', 'blank_eft_form', 'retirement_guide'])

        if doc_type == 'public_budget':
            return self._generate_public_budget_summary()
        elif doc_type == 'aml_training':
            return self._generate_aml_training()
        elif doc_type == 'blank_eft_form':
            return self._generate_blank_eft_form()
        else:
            return self._generate_retirement_guide()

    def _generate_budget_memo(self, subcategory: str) -> Dict[str, Any]:
        """Generate a Presidential Budget Decision Memorandum."""
        agency = self.get_agency()
        program = random.choice(self.BUDGET_PROGRAMS)
        fiscal_year = self.generate_fiscal_year()
        amount = self.generate_currency_amount(100000000, 5000000000)

        doc = self._build_base_document('budget_memo', subcategory, is_positive=True)
        doc.update({
            'title': 'Presidential Budget Decision Memorandum',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - BUDGET',
            'to': agency,
            'from': 'Office of Management and Budget',
            'subject': f'FY {fiscal_year} Budget Decision - {program}',
            'fiscal_year': fiscal_year,
            'program': program,
            'decision': (
                f"The President has decided to allocate {self.format_currency(amount)} "
                f"for {program} within {agency} for fiscal year {fiscal_year}."
            ),
            'key_decision_points': [
                f"Funding level represents {'increase' if random.choice([True, False]) else 'decrease'} from FY {fiscal_year - 1}",
                f"Implementation timeline: Q{random.randint(1, 4)} FY {fiscal_year}",
                f"Congressional justification required by {self.fake.date_this_year().strftime('%B %d, %Y')}",
            ],
            'amount': amount,
            'amount_formatted': self.format_currency(amount),
            'confidentiality_notice': self.get_confidentiality_notice('budget'),
            'distribution': 'Executive Branch Only - Pre-decisional Information',
        })
        return doc

    def _generate_sar(self, subcategory: str) -> Dict[str, Any]:
        """Generate a Suspicious Activity Report."""
        filing_institution = f"{self.fake.company()} Bank"
        subject_name = self.fake.name()
        amount = self.generate_currency_amount(10000, 1000000)

        doc = self._build_base_document('sar', 'bank_secrecy', is_positive=True)
        doc.update({
            'title': 'Suspicious Activity Report (SAR)',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - BANK SECRECY',
            'sar_number': f"SAR-{self.fake.uuid4()[:12].upper()}",
            'filing_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'filing_institution': {
                'name': filing_institution,
                'rssd_id': f"{random.randint(100000, 999999)}",
                'address': f"{self.fake.street_address()}, {self.fake.city()}, {self.fake.state_abbr()}",
            },
            'subject': {
                'name': subject_name,
                'dob': self.fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%m/%d/%Y'),
                'ssn_last4': f"XXX-XX-{random.randint(1000, 9999)}",
                'address': f"{self.fake.street_address()}, {self.fake.city()}, {self.fake.state_abbr()}",
                'account_numbers': [f"XXXX-XXXX-{random.randint(1000, 9999)}" for _ in range(random.randint(1, 3))],
            },
            'suspicious_activity': {
                'type': random.choice(self.SUSPICIOUS_ACTIVITIES),
                'amount': amount,
                'amount_formatted': self.format_currency(amount),
                'date_range': {
                    'start': self.generate_date_in_range(-180, -30).strftime('%m/%d/%Y'),
                    'end': self.generate_date_in_range(-30, 0).strftime('%m/%d/%Y'),
                },
                'narrative': (
                    f"On multiple occasions, the subject {subject_name} engaged in transactions "
                    f"that appear designed to evade Currency Transaction Report requirements. "
                    f"Total suspicious activity amount: {self.format_currency(amount)}."
                ),
            },
            'fincen_filing_name': self.fake.name(),
            'confidentiality_notice': (
                "This SAR is confidential under 31 USC 5318(g)(2). "
                "Unauthorized disclosure is prohibited."
            ),
        })
        return doc

    def _generate_eft_authorization(self, subcategory: str) -> Dict[str, Any]:
        """Generate an EFT Authorization Form."""
        agency = self.get_agency()
        payee_name = self.fake.name()

        doc = self._build_base_document('eft_authorization', 'eft', is_positive=True)
        doc.update({
            'title': 'Electronic Funds Transfer Authorization',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - EFT',
            'authorization_number': f"EFT-{random.randint(100000, 999999)}",
            'agency': agency,
            'payee': {
                'name': payee_name,
                'address': f"{self.fake.street_address()}, {self.fake.city()}, {self.fake.state_abbr()} {self.fake.zipcode()}",
                'tin_last4': f"XXX-XX-{random.randint(1000, 9999)}",
            },
            'financial_institution': {
                'name': f"{self.fake.company()} Bank",
                'routing_number': f"{random.randint(100000000, 999999999)}",
                'account_number': f"XXXXXX{random.randint(1000, 9999)}",
                'account_type': random.choice(['Checking', 'Savings']),
            },
            'payment_details': {
                'amount': self.generate_currency_amount(1000, 100000),
                'frequency': random.choice(['One-time', 'Monthly', 'Bi-weekly']),
                'effective_date': self.generate_date_in_range(0, 30).strftime('%B %d, %Y'),
            },
            'authorization_signature': payee_name,
            'authorization_date': self.generate_date_in_range(-7, 0).strftime('%B %d, %Y'),
            'confidentiality_notice': (
                "This document contains financial account information protected under "
                "31 CFR 210. Do not disclose to unauthorized parties."
            ),
        })
        return doc

    def _generate_retirement_estimate(self, subcategory: str) -> Dict[str, Any]:
        """Generate a FERS/CSRS Retirement Estimate."""
        employee_name = self.fake.name()
        retirement_system = random.choice(self.RETIREMENT_SYSTEMS)
        years_of_service = random.randint(20, 40)
        high_3_salary = self.generate_currency_amount(80000, 180000)

        # Calculate approximate annuity
        if retirement_system.startswith('FERS'):
            annuity_factor = 0.01 if years_of_service < 20 else 0.011
        else:
            annuity_factor = 0.015 if years_of_service < 5 else 0.0175

        monthly_annuity = (high_3_salary * years_of_service * annuity_factor) / 12

        doc = self._build_base_document('retirement_estimate', 'retirement', is_positive=True)
        doc.update({
            'title': f'{retirement_system} Retirement Estimate',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - RETIREMENT',
            'estimate_number': f"RET-{random.randint(100000, 999999)}",
            'employee': {
                'name': employee_name,
                'employee_id': f"EMP{random.randint(100000, 999999)}",
                'agency': self.get_agency(),
                'grade': f"GS-{random.randint(12, 15)}, Step {random.randint(1, 10)}",
            },
            'service_computation': {
                'retirement_system': retirement_system,
                'years_of_service': years_of_service,
                'months_of_service': random.randint(0, 11),
                'sick_leave_credit_months': random.randint(0, 24),
            },
            'salary_information': {
                'current_salary': self.format_currency(high_3_salary),
                'high_3_average': self.format_currency(high_3_salary * 0.95),
            },
            'estimated_benefits': {
                'gross_monthly_annuity': self.format_currency(monthly_annuity),
                'fers_supplement': self.format_currency(random.randint(500, 1500)) if retirement_system.startswith('FERS') else 'N/A',
                'tsp_balance': self.format_currency(self.generate_currency_amount(200000, 1500000)),
            },
            'projected_retirement_date': self.generate_date_in_range(365, 730).strftime('%B %d, %Y'),
            'computed_by': self.fake.name(),
            'computation_date': self.generate_date_in_range(-7, 0).strftime('%B %d, %Y'),
            'disclaimer': (
                "This is an estimate only and is not a guarantee of benefits. "
                "Final annuity computation will be made at time of retirement."
            ),
        })
        return doc

    def _generate_comptroller_report(self, subcategory: str) -> Dict[str, Any]:
        """Generate a Comptroller General report."""
        agency = self.get_agency()
        report_topics = [
            'Financial Management Practices',
            'Program Efficiency Review',
            'Compliance Assessment',
            'Internal Controls Evaluation',
            'Cost Savings Opportunities',
        ]

        doc = self._build_base_document('comptroller_report', 'comptroller_general', is_positive=True)
        doc.update({
            'title': 'Government Accountability Office Report (DRAFT)',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - COMPTROLLER GENERAL',
            'report_number': f"GAO-{self.generate_fiscal_year()}-{random.randint(100, 999)}",
            'agency_reviewed': agency,
            'topic': random.choice(report_topics),
            'report_status': 'DRAFT - Pre-decisional',
            'findings': [
                {
                    'finding_number': i + 1,
                    'description': f"Finding related to {random.choice(['internal controls', 'financial reporting', 'compliance', 'efficiency'])}",
                    'significance': random.choice(['High', 'Medium', 'Low']),
                }
                for i in range(random.randint(3, 7))
            ],
            'recommendations': random.randint(2, 8),
            'estimated_savings': self.format_currency(self.generate_currency_amount(1000000, 100000000)),
            'review_period': {
                'start': f"FY {self.generate_fiscal_year() - 2}",
                'end': f"FY {self.generate_fiscal_year() - 1}",
            },
            'gao_team_lead': self.fake.name(),
            'confidentiality_notice': (
                "This draft report is protected under 31 USC 716. "
                "Do not release until final report is published."
            ),
        })
        return doc

    def _generate_public_budget_summary(self) -> Dict[str, Any]:
        """Generate a public budget summary (negative example)."""
        doc = self._build_base_document('public_budget_summary', 'budget', is_positive=False)
        doc.update({
            'title': 'Budget of the United States Government - Summary',
            'publication': 'Office of Management and Budget',
            'fiscal_year': self.generate_fiscal_year(),
            'publication_date': self.generate_date_in_range(-60, 0).strftime('%B %d, %Y'),
            'overview': (
                "This document provides a summary of the President's Budget request "
                "as transmitted to Congress. All information is publicly available."
            ),
            'highlights': [
                'Total discretionary budget request',
                'Mandatory spending projections',
                'Revenue estimates',
                'Deficit/surplus projections',
            ],
            'distribution': 'Unlimited Public Distribution',        })
        return doc

    def _generate_aml_training(self) -> Dict[str, Any]:
        """Generate AML training materials (negative example)."""
        doc = self._build_base_document('aml_training', 'bank_secrecy', is_positive=False)
        doc.update({
            'title': 'Anti-Money Laundering Training Program',
            'organization': 'Financial Crimes Enforcement Network',
            'course_id': f"AML-{random.randint(100, 999)}",
            'target_audience': 'Financial Institution Personnel',
            'modules': [
                'BSA/AML Regulatory Overview',
                'Customer Due Diligence',
                'Suspicious Activity Recognition',
                'SAR Filing Procedures',
                'Recordkeeping Requirements',
            ],
            'duration': f"{random.randint(2, 8)} hours",
            'certification': 'Certificate of Completion provided',
            'distribution': 'Unlimited distribution for training purposes',        })
        return doc

    def _generate_blank_eft_form(self) -> Dict[str, Any]:
        """Generate a blank EFT form (negative example)."""
        doc = self._build_base_document('blank_eft_form', 'eft', is_positive=False)
        doc.update({
            'title': 'SF 1199A - Direct Deposit Sign-Up Form (BLANK)',
            'form_number': 'SF 1199A',
            'revision_date': 'Rev. 10/2023',
            'agency': '[AGENCY NAME]',
            'instructions': (
                "Use this form to start, change, or cancel Direct Deposit/Electronic Funds Transfer. "
                "Complete all fields and submit to your payroll office."
            ),
            'fields': [
                {'name': 'Payee/Joint Payee Name', 'value': '[ENTER NAME]'},
                {'name': 'Address', 'value': '[ENTER ADDRESS]'},
                {'name': 'Financial Institution Name', 'value': '[ENTER BANK NAME]'},
                {'name': 'Routing Number', 'value': '[ENTER 9-DIGIT ROUTING NUMBER]'},
                {'name': 'Account Number', 'value': '[ENTER ACCOUNT NUMBER]'},
            ],
            'paperwork_reduction_notice': 'OMB No. 1510-0007',        })
        return doc

    def _generate_retirement_guide(self) -> Dict[str, Any]:
        """Generate a general retirement planning guide (negative example)."""
        doc = self._build_base_document('retirement_guide', 'retirement', is_positive=False)
        doc.update({
            'title': 'FERS Retirement Planning Guide',
            'publisher': 'Office of Personnel Management',
            'publication_date': self.generate_date_in_range(-365, 0).strftime('%B %Y'),
            'audience': 'Federal Employees',
            'chapters': [
                'Understanding FERS',
                'Eligibility Requirements',
                'Annuity Computation Basics',
                'FERS Supplement',
                'Thrift Savings Plan',
                'Health and Life Insurance in Retirement',
            ],
            'resources': [
                'OPM Retirement Services Online',
                'Benefits Officer Contact Information',
                'TSP.gov',
            ],
            'distribution': 'Available to all federal employees',        })
        return doc
