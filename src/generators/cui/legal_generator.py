"""
Legal CUI generator.

Generates synthetic CUI documents for:
- Legal Privilege (attorney-client)
- Collective Bargaining
- Legislative Materials
- Administrative Proceedings
"""
from typing import Any, Dict, List, Optional
import random
from datetime import datetime, timedelta

from .base import BaseCUIGenerator
from .factory import CUIGeneratorFactory


@CUIGeneratorFactory.register('legal')
class LegalCUIGenerator(BaseCUIGenerator):
    """Generator for Legal CUI documents."""

    CATEGORY = 'legal'
    SUBCATEGORIES = ['privilege', 'collective_bargaining', 'legislative', 'administrative']
    CUI_MARKINGS = [
        'CUI//SP-PRVLG',
        'CUI//SP-CLBRG',
        'CUI - LEGAL',
        'ATTORNEY-CLIENT PRIVILEGED',
    ]
    AUTHORITIES = [
        'Federal Rules of Evidence 501',
        '5 USC Chapter 71',
        '5 USC 552(b)(5)',
        'Administrative Procedure Act',
    ]

    # Legal matter types
    LEGAL_MATTERS = [
        'Employment Dispute',
        'Contract Interpretation',
        'Regulatory Compliance',
        'FOIA Litigation',
        'Administrative Appeal',
        'Personnel Action',
        'Ethics Advisory',
        'Policy Implementation',
    ]

    # Bargaining units
    BARGAINING_UNITS = [
        'AFGE Local',
        'NTEU Chapter',
        'NFFE Local',
        'SEIU Local',
    ]

    # Legislative bodies
    LEGISLATIVE_BODIES = [
        'House Committee on Oversight',
        'Senate Committee on Finance',
        'House Committee on Appropriations',
        'Senate Committee on Homeland Security',
        'House Ways and Means Committee',
    ]

    def __init__(self, locale: str = 'en_US', seed: Optional[int] = None):
        super().__init__(locale, seed)

    def get_document_types(self) -> List[Dict[str, Any]]:
        """Get available document types for legal category."""
        return self._document_types.get(self.CATEGORY, {})

    def generate_positive(self) -> Dict[str, Any]:
        """Generate a CUI-positive legal document."""
        subcategory = random.choice(self.SUBCATEGORIES)

        generators = {
            'privilege': self._generate_attorney_memo,
            'collective_bargaining': self._generate_bargaining_proposal,
            'legislative': self._generate_congressional_testimony,
            'administrative': self._generate_hearing_record,
        }

        return generators[subcategory](subcategory)

    def generate_negative(self) -> Dict[str, Any]:
        """Generate a CUI-negative legal document."""
        doc_type = random.choice(['legal_faq', 'union_rights', 'public_testimony', 'appeal_guide'])

        generators = {
            'legal_faq': self._generate_legal_faq,
            'union_rights': self._generate_union_rights,
            'public_testimony': self._generate_public_testimony,
            'appeal_guide': self._generate_appeal_guide,
        }

        return generators[doc_type]()

    def _generate_attorney_memo(self, subcategory: str) -> Dict[str, Any]:
        """Generate an attorney-client privileged memorandum."""
        agency = self.get_agency()
        matter = random.choice(self.LEGAL_MATTERS)
        attorney = self.fake.name()
        client = self.fake.name()

        doc = self._build_base_document('attorney_memo', subcategory, is_positive=True)
        doc.update({
            'title': 'Attorney-Client Privileged Memorandum',
            'classification': 'ATTORNEY-CLIENT PRIVILEGED - CUI',
            'memo_number': f"OGC-{random.randint(2024, 2025)}-{random.randint(100, 999)}",
            'attorney': {
                'name': attorney,
                'title': random.choice(['Associate General Counsel', 'Attorney Advisor', 'Deputy General Counsel']),
                'organization': f'{agency} - Office of General Counsel',
            },
            'client': {
                'name': client,
                'title': self.get_agency_title('executive'),
                'organization': agency,
            },
            'date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'subject': f"Legal Analysis: {matter}",
            'privilege_assertion': [
                'Attorney-Client Privilege',
                'Attorney Work Product',
            ],
            'question_presented': (
                f"You have requested a legal analysis regarding {matter.lower()} "
                f"as it pertains to {agency}'s obligations under applicable law and regulation."
            ),
            'brief_answer': (
                f"Based on our analysis, {agency} {'should' if random.choice([True, False]) else 'may'} "
                f"proceed with the proposed course of action, subject to the conditions outlined below."
            ),
            'analysis': (
                "This memorandum provides confidential legal advice regarding the matter described above. "
                "The analysis is based on the facts provided and applicable legal authorities."
            ),
            'recommendation': random.choice([
                'Proceed with proposed action',
                'Modify approach as outlined',
                'Seek additional information',
                'Delay pending further analysis',
            ]),
            'confidentiality_notice': (
                "This memorandum is protected by attorney-client privilege and the work product doctrine. "
                "Do not disclose without authorization from the Office of General Counsel."
            ),
        })
        return doc

    def _generate_bargaining_proposal(self, subcategory: str) -> Dict[str, Any]:
        """Generate a collective bargaining proposal."""
        agency = self.get_agency()
        union = f"{random.choice(self.BARGAINING_UNITS)} {random.randint(100, 999)}"

        doc = self._build_base_document('bargaining_proposal', subcategory, is_positive=True)
        doc.update({
            'title': 'Collective Bargaining Proposal',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - COLLECTIVE BARGAINING',
            'proposal_number': f"CBP-{random.randint(2024, 2025)}-{random.randint(10, 99)}",
            'agency': agency,
            'union': union,
            'negotiation_status': random.choice(['Initial Proposal', 'Counter-Proposal', 'Final Offer']),
            'date_submitted': self.generate_date_in_range(-14, 0).strftime('%B %d, %Y'),
            'articles_under_negotiation': [
                {
                    'article': f"Article {random.randint(1, 30)}",
                    'subject': random.choice([
                        'Telework Policy',
                        'Performance Evaluation',
                        'Leave Policies',
                        'Grievance Procedures',
                        'Work Schedules',
                        'Training and Development',
                    ]),
                    'management_position': 'See attached language',
                }
                for _ in range(random.randint(3, 7))
            ],
            'ground_rules': {
                'negotiation_location': f"{self.fake.city()}, {self.fake.state_abbr()}",
                'session_dates': [
                    self.generate_date_in_range(-7, 7).strftime('%B %d, %Y')
                    for _ in range(3)
                ],
            },
            'management_team_lead': {
                'name': self.fake.name(),
                'title': 'Labor Relations Officer',
            },
            'union_team_lead': {
                'name': self.fake.name(),
                'title': 'Union President',
            },
            'confidentiality_notice': (
                "This proposal is confidential under 5 USC Chapter 71. "
                "Do not disclose outside of the negotiating teams."
            ),
        })
        return doc

    def _generate_congressional_testimony(self, subcategory: str) -> Dict[str, Any]:
        """Generate draft congressional testimony."""
        agency = self.get_agency()
        official = self.fake.name()
        committee = random.choice(self.LEGISLATIVE_BODIES)

        doc = self._build_base_document('congressional_testimony', subcategory, is_positive=True)
        doc.update({
            'title': 'Draft Congressional Testimony',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - LEGISLATIVE',
            'document_status': 'DRAFT - PRE-DECISIONAL',
            'witness': {
                'name': official,
                'title': self.get_agency_title('executive'),
                'agency': agency,
            },
            'committee': committee,
            'hearing_topic': random.choice([
                'Agency Budget Request',
                'Program Oversight',
                'Policy Implementation',
                'Regulatory Reform',
                'Audit Findings',
            ]),
            'scheduled_date': self.generate_date_in_range(7, 30).strftime('%B %d, %Y'),
            'prepared_statement_summary': (
                f"This testimony addresses {agency}'s {random.choice(['priorities', 'progress', 'challenges', 'achievements'])} "
                f"in the area of {random.choice(['program administration', 'service delivery', 'compliance', 'modernization'])}."
            ),
            'key_messages': [
                f"Key message {i+1} regarding agency priorities"
                for i in range(random.randint(3, 5))
            ],
            'questions_for_the_record': random.randint(0, 15),
            'clearance_status': random.choice(['Pending OMB Review', 'Agency Review', 'Final Clearance']),
            'prepared_by': {
                'name': self.fake.name(),
                'title': 'Congressional Affairs Specialist',
            },
            'confidentiality_notice': (
                "This draft testimony is pre-decisional and protected under 5 USC 552(b)(5). "
                "Do not release until after congressional testimony is delivered."
            ),
        })
        return doc

    def _generate_hearing_record(self, subcategory: str) -> Dict[str, Any]:
        """Generate an administrative hearing record."""
        agency = self.get_agency()
        appellant = self.fake.name()

        doc = self._build_base_document('hearing_record', subcategory, is_positive=True)
        doc.update({
            'title': 'Administrative Hearing Record',
            'classification': 'CONTROLLED UNCLASSIFIED INFORMATION - ADMINISTRATIVE PROCEEDINGS',
            'docket_number': f"{random.randint(2020, 2025)}-{random.randint(1000, 9999)}",
            'case_type': random.choice([
                'Adverse Personnel Action Appeal',
                'Retirement Benefits Dispute',
                'Performance Rating Appeal',
                'Discrimination Complaint',
                'Whistleblower Retaliation',
            ]),
            'appellant': {
                'name': appellant,
                'former_position': self.fake.job(),
                'former_agency': agency,
            },
            'respondent': {
                'agency': agency,
                'representative': self.fake.name(),
            },
            'administrative_judge': {
                'name': self.fake.name(),
                'title': 'Administrative Judge',
                'board': random.choice(['MSPB', 'EEOC', 'FLRA', 'OWCP']),
            },
            'hearing_date': self.generate_date_in_range(-60, -7).strftime('%B %d, %Y'),
            'hearing_location': f"{self.fake.city()}, {self.fake.state_abbr()}",
            'issues': [
                f"Issue {i+1}: {random.choice(['Procedural violation', 'Substantive violation', 'Penalty determination'])}"
                for i in range(random.randint(2, 5))
            ],
            'witnesses_called': random.randint(2, 8),
            'exhibits_admitted': random.randint(5, 25),
            'record_status': random.choice(['Open', 'Closed', 'Under Advisement']),
            'decision_due': self.generate_date_in_range(30, 90).strftime('%B %d, %Y'),
        })
        return doc

    def _generate_legal_faq(self) -> Dict[str, Any]:
        """Generate a public legal FAQ (negative example)."""
        doc = self._build_base_document('legal_faq', 'general', is_positive=False)
        doc.update({
            'title': 'Legal FAQ for Federal Employees',
            'publisher': 'Office of Personnel Management',
            'publication_date': self.generate_date_in_range(-180, 0).strftime('%B %d, %Y'),
            'topics': [
                'Hatch Act Overview',
                'Ethics Rules for Federal Employees',
                'FOIA Request Process',
                'Whistleblower Protections',
            ],
            'disclaimer': (
                "This FAQ provides general information only and does not constitute legal advice. "
                "Consult with your agency's Office of General Counsel for specific legal questions."
            ),
            'distribution': 'Unlimited Public Distribution',        })
        return doc

    def _generate_union_rights(self) -> Dict[str, Any]:
        """Generate employee union rights information (negative example)."""
        doc = self._build_base_document('union_rights', 'collective_bargaining', is_positive=False)
        doc.update({
            'title': 'Federal Employee Union Rights',
            'publisher': 'Federal Labor Relations Authority',
            'publication_date': self.generate_date_in_range(-365, 0).strftime('%B %d, %Y'),
            'content': (
                "This document outlines the statutory rights of federal employees to organize "
                "and participate in labor organizations under 5 USC Chapter 71."
            ),
            'topics': [
                'Right to Organize',
                'Collective Bargaining Process',
                'Unfair Labor Practice Complaints',
                'Representation Rights',
            ],
            'resources': [
                'FLRA Website',
                'Your Union Representative',
                'Agency Labor Relations Office',
            ],
            'distribution': 'Unlimited Public Distribution',        })
        return doc

    def _generate_public_testimony(self) -> Dict[str, Any]:
        """Generate published congressional testimony (negative example)."""
        agency = self.get_agency()
        doc = self._build_base_document('public_testimony', 'legislative', is_positive=False)
        doc.update({
            'title': 'Published Congressional Testimony',
            'witness': {
                'name': self.fake.name(),
                'title': self.get_agency_title('executive'),
                'agency': agency,
            },
            'committee': random.choice(self.LEGISLATIVE_BODIES),
            'hearing_date': self.generate_date_in_range(-90, -7).strftime('%B %d, %Y'),
            'publication_date': self.generate_date_in_range(-60, 0).strftime('%B %d, %Y'),
            'topic': 'Agency Oversight Hearing',
            'status': 'Published in Congressional Record',
            'transcript_available': True,
            'distribution': 'Unlimited Public Distribution',        })
        return doc

    def _generate_appeal_guide(self) -> Dict[str, Any]:
        """Generate an appeal process guide (negative example)."""
        doc = self._build_base_document('appeal_guide', 'administrative', is_positive=False)
        doc.update({
            'title': 'Guide to the Appeals Process',
            'publisher': 'Merit Systems Protection Board',
            'publication_date': self.generate_date_in_range(-365, 0).strftime('%B %Y'),
            'audience': 'Federal Employees and Applicants',
            'chapters': [
                'Understanding Your Appeal Rights',
                'Filing an Appeal',
                'The Hearing Process',
                'Post-Hearing Procedures',
                'Further Review Options',
            ],
            'forms_referenced': [
                'MSPB Form 185',
                'Standard Form 50',
            ],
            'contact': 'MSPB Regional Offices',
            'distribution': 'Unlimited Public Distribution',        })
        return doc
