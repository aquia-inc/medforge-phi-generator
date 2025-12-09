"""
Procurement CUI generator.

Generates synthetic CUI documents for:
- Source Selection (evaluation reports, IGCEs)
- Small Business Research and Technology (SBIR/STTR)
"""
from typing import Any, Dict, List, Optional
import random
from datetime import datetime, timedelta

from .base import BaseCUIGenerator
from .factory import CUIGeneratorFactory


@CUIGeneratorFactory.register('procurement')
class ProcurementCUIGenerator(BaseCUIGenerator):
    """Generator for Procurement and Acquisition CUI documents."""

    CATEGORY = 'procurement'
    SUBCATEGORIES = ['source_selection', 'small_business']
    CUI_MARKINGS = [
        'SOURCE SELECTION INFORMATION - PROTECTED UNDER FAR 2.101',
        'CUI//SP-SRSEL',
        'CUI//SP-PROCMNT',
        'SOURCE SELECTION SENSITIVE',
    ]
    AUTHORITIES = [
        '48 CFR 2.101',
        '48 CFR 3.104',
        '41 USC 2102(a)',
        'FAR Part 15',
    ]

    # Procurement data
    EVALUATION_FACTORS = [
        'Technical Approach',
        'Management Approach',
        'Past Performance',
        'Price/Cost',
        'Small Business Participation',
        'Key Personnel',
        'Quality Control',
        'Schedule',
    ]

    ADJECTIVAL_RATINGS = [
        'Outstanding',
        'Good',
        'Acceptable',
        'Marginal',
        'Unacceptable',
    ]

    CONTRACT_TYPES = [
        'Firm Fixed Price (FFP)',
        'Cost Plus Fixed Fee (CPFF)',
        'Time and Materials (T&M)',
        'Labor Hour (LH)',
        'Indefinite Delivery/Indefinite Quantity (IDIQ)',
    ]

    NAICS_CODES = [
        ('541511', 'Custom Computer Programming Services'),
        ('541512', 'Computer Systems Design Services'),
        ('541519', 'Other Computer Related Services'),
        ('541611', 'Administrative Management Consulting'),
        ('541990', 'All Other Professional Services'),
        ('561110', 'Office Administrative Services'),
    ]

    def __init__(self, locale: str = 'en_US', seed: Optional[int] = None):
        super().__init__(locale, seed)

    def get_document_types(self) -> List[Dict[str, Any]]:
        """Get available document types for procurement category."""
        return self._document_types.get(self.CATEGORY, {})

    def generate_positive(self) -> Dict[str, Any]:
        """Generate a CUI-positive procurement document."""
        subcategory = random.choice(self.SUBCATEGORIES)

        if subcategory == 'source_selection':
            doc_type = random.choice(['source_selection_plan', 'evaluation_report', 'igce', 'award_recommendation'])
            generators = {
                'source_selection_plan': self._generate_source_selection_plan,
                'evaluation_report': self._generate_evaluation_report,
                'igce': self._generate_igce,
                'award_recommendation': self._generate_award_recommendation,
            }
            return generators[doc_type](subcategory)
        else:
            return self._generate_sbir_evaluation(subcategory)

    def generate_negative(self) -> Dict[str, Any]:
        """Generate a CUI-negative procurement document."""
        doc_type = random.choice(['procurement_guide', 'sbir_overview', 'vendor_outreach'])

        if doc_type == 'procurement_guide':
            return self._generate_procurement_guide()
        elif doc_type == 'sbir_overview':
            return self._generate_sbir_overview()
        else:
            return self._generate_vendor_outreach()

    def _generate_source_selection_plan(self, subcategory: str) -> Dict[str, Any]:
        """Generate a source selection plan."""
        agency = self.get_agency()
        program = f"{self.fake.catch_phrase()} Program"

        doc = self._build_base_document('source_selection_plan', subcategory, is_positive=True)
        doc.update({
            'title': 'Source Selection Plan',
            'classification': 'SOURCE SELECTION INFORMATION - PROTECTED UNDER FAR 2.101',
            'solicitation_number': f"{random.randint(10, 99)}S{random.randint(100, 999)}D{random.randint(1000, 9999)}",
            'agency': agency,
            'program': program,
            'estimated_value': self.format_currency(self.generate_currency_amount(1000000, 500000000)),
            'contract_type': random.choice(self.CONTRACT_TYPES),
            'naics': random.choice(self.NAICS_CODES),
            'source_selection_authority': {
                'name': self.fake.name(),
                'title': 'Contracting Officer',
            },
            'evaluation_team': {
                'chairperson': self.fake.name(),
                'members': random.randint(3, 7),
            },
            'evaluation_factors': [
                {
                    'factor': factor,
                    'weight': random.randint(10, 30),
                    'description': f'Evaluation of {factor.lower()} capabilities',
                }
                for factor in random.sample(self.EVALUATION_FACTORS, k=random.randint(4, 6))
            ],
            'acquisition_strategy': random.choice([
                'Full and Open Competition',
                'Small Business Set-Aside',
                '8(a) Competition',
                'HUBZone Set-Aside',
            ]),
            'proposal_due_date': self.generate_date_in_range(30, 90).strftime('%B %d, %Y'),
            'anticipated_award_date': self.generate_date_in_range(120, 180).strftime('%B %d, %Y'),
            'confidentiality_notice': (
                "This Source Selection Plan contains source selection information protected "
                "under FAR 2.101 and 41 USC 2102. Unauthorized disclosure is prohibited."
            ),
        })
        return doc

    def _generate_evaluation_report(self, subcategory: str) -> Dict[str, Any]:
        """Generate a technical evaluation report."""
        offeror = f"{self.fake.company()}"

        doc = self._build_base_document('evaluation_report', subcategory, is_positive=True)
        doc.update({
            'title': 'Technical Evaluation Report',
            'classification': 'SOURCE SELECTION SENSITIVE - CUI',
            'solicitation_number': f"{random.randint(10, 99)}S{random.randint(100, 999)}D{random.randint(1000, 9999)}",
            'offeror': offeror,
            'offeror_cage_code': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5)),
            'evaluation_date': self.generate_date_in_range(-14, 0).strftime('%B %d, %Y'),
            'evaluator': {
                'name': self.fake.name(),
                'title': 'Technical Evaluation Panel Member',
            },
            'factor_evaluations': [
                {
                    'factor': factor,
                    'rating': random.choice(self.ADJECTIVAL_RATINGS),
                    'score': random.randint(60, 100),
                    'strengths': random.randint(2, 5),
                    'weaknesses': random.randint(0, 3),
                    'deficiencies': random.randint(0, 2),
                }
                for factor in random.sample(self.EVALUATION_FACTORS, k=random.randint(4, 6))
            ],
            'overall_rating': random.choice(self.ADJECTIVAL_RATINGS[:3]),
            'overall_score': random.randint(70, 95),
            'narrative_summary': (
                f"The proposal submitted by {offeror} demonstrates "
                f"{'strong' if random.choice([True, False]) else 'adequate'} capabilities "
                f"in the areas evaluated. See detailed ratings above."
            ),
            'recommendation': random.choice([
                'Recommend for competitive range',
                'Recommend for award consideration',
                'Further clarification needed',
                'Does not meet minimum requirements',
            ]),
            'confidentiality_notice': (
                "This evaluation contains proprietary information and source selection data. "
                "Do not disclose to offerors or unauthorized parties."
            ),
        })
        return doc

    def _generate_igce(self, subcategory: str) -> Dict[str, Any]:
        """Generate an Independent Government Cost Estimate."""
        agency = self.get_agency()
        total = self.generate_currency_amount(500000, 50000000)

        doc = self._build_base_document('igce', subcategory, is_positive=True)
        doc.update({
            'title': 'Independent Government Cost Estimate (IGCE)',
            'classification': 'SOURCE SELECTION INFORMATION - CUI',
            'solicitation_number': f"{random.randint(10, 99)}S{random.randint(100, 999)}D{random.randint(1000, 9999)}",
            'agency': agency,
            'prepared_by': {
                'name': self.fake.name(),
                'title': 'Cost Analyst',
            },
            'preparation_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'period_of_performance': {
                'base_period': '12 months',
                'option_periods': f"{random.randint(1, 4)} x 12 months",
            },
            'cost_elements': [
                {
                    'element': 'Labor (Direct)',
                    'base_year': self.format_currency(total * 0.5),
                    'options': self.format_currency(total * 0.4),
                },
                {
                    'element': 'Labor (Indirect)',
                    'base_year': self.format_currency(total * 0.15),
                    'options': self.format_currency(total * 0.12),
                },
                {
                    'element': 'ODCs/Materials',
                    'base_year': self.format_currency(total * 0.1),
                    'options': self.format_currency(total * 0.08),
                },
                {
                    'element': 'Travel',
                    'base_year': self.format_currency(total * 0.05),
                    'options': self.format_currency(total * 0.04),
                },
                {
                    'element': 'Fee/Profit',
                    'base_year': self.format_currency(total * 0.08),
                    'options': self.format_currency(total * 0.06),
                },
            ],
            'total_estimated_cost': self.format_currency(total),
            'methodology': random.choice([
                'Comparison with similar contracts',
                'Bottom-up engineering estimate',
                'Parametric cost model',
                'Expert judgment with historical data',
            ]),
            'assumptions': [
                'Labor rates based on current GSA schedule',
                'Inflation factor of 2.5% per year applied',
                'Standard overhead rates assumed',
            ],
            'confidence_level': random.choice(['High', 'Medium', 'Low']),
            'confidentiality_notice': (
                "This IGCE is source selection sensitive. Do not disclose to potential offerors."
            ),
        })
        return doc

    def _generate_award_recommendation(self, subcategory: str) -> Dict[str, Any]:
        """Generate an award recommendation memorandum."""
        agency = self.get_agency()
        recommended_offeror = self.fake.company()

        doc = self._build_base_document('award_recommendation', subcategory, is_positive=True)
        doc.update({
            'title': 'Award Recommendation Memorandum',
            'classification': 'SOURCE SELECTION INFORMATION - CUI',
            'solicitation_number': f"{random.randint(10, 99)}S{random.randint(100, 999)}D{random.randint(1000, 9999)}",
            'agency': agency,
            'to': {
                'name': self.fake.name(),
                'title': 'Source Selection Authority',
            },
            'from': {
                'name': self.fake.name(),
                'title': 'Contracting Officer',
            },
            'date': self.generate_date_in_range(-7, 0).strftime('%B %d, %Y'),
            'subject': 'Recommendation for Contract Award',
            'offerors_evaluated': random.randint(3, 8),
            'competitive_range': random.randint(2, 4),
            'recommended_offeror': {
                'name': recommended_offeror,
                'cage_code': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5)),
                'proposed_price': self.format_currency(self.generate_currency_amount(1000000, 50000000)),
                'overall_rating': random.choice(self.ADJECTIVAL_RATINGS[:2]),
            },
            'evaluation_summary': (
                f"{recommended_offeror} submitted the proposal representing the best value to the Government, "
                f"considering technical capability, past performance, and price."
            ),
            'price_reasonableness': 'Fair and reasonable based on IGCE comparison and competition',
            'small_business_determination': random.choice([
                'Full and open competition - not applicable',
                'Small business set-aside requirements met',
                'Subcontracting plan meets SBA requirements',
            ]),
            'recommendation': f"Award contract to {recommended_offeror}",
            'signature_block': {
                'name': self.fake.name(),
                'title': 'Contracting Officer',
                'date': self.generate_date_in_range(-3, 0).strftime('%B %d, %Y'),
            },
        })
        return doc

    def _generate_sbir_evaluation(self, subcategory: str) -> Dict[str, Any]:
        """Generate an SBIR/STTR proposal evaluation."""
        program = random.choice(['SBIR', 'STTR'])
        company = self.fake.company()

        doc = self._build_base_document('sbir_evaluation', subcategory, is_positive=True)
        doc.update({
            'title': f'{program} Proposal Evaluation',
            'classification': 'CUI - PROCUREMENT',
            'topic_number': f"{program}-{random.randint(2024, 2025)}-{random.randint(100, 999)}",
            'proposal_number': f"P{random.randint(10000, 99999)}",
            'company': {
                'name': company,
                'cage_code': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5)),
                'location': f"{self.fake.city()}, {self.fake.state_abbr()}",
            },
            'phase': random.choice(['Phase I', 'Phase II', 'Phase III']),
            'evaluation_criteria': [
                {
                    'criterion': 'Scientific/Technical Merit',
                    'score': random.randint(70, 100),
                    'max_score': 100,
                },
                {
                    'criterion': 'Commercial Potential',
                    'score': random.randint(60, 100),
                    'max_score': 100,
                },
                {
                    'criterion': 'Team Qualifications',
                    'score': random.randint(70, 100),
                    'max_score': 100,
                },
            ],
            'total_score': random.randint(210, 290),
            'max_total_score': 300,
            'requested_funding': self.format_currency(random.randint(150000, 1500000)),
            'recommendation': random.choice(['Recommend for Award', 'Not Recommended', 'Further Review Required']),
            'evaluator': self.fake.name(),
            'evaluation_date': self.generate_date_in_range(-14, 0).strftime('%B %d, %Y'),
        })
        return doc

    def _generate_procurement_guide(self) -> Dict[str, Any]:
        """Generate public procurement guidelines (negative example)."""
        doc = self._build_base_document('procurement_guide', 'general', is_positive=False)
        doc.update({
            'title': 'Federal Procurement Guide for Industry',
            'publisher': 'General Services Administration',
            'publication_date': self.generate_date_in_range(-365, 0).strftime('%B %d, %Y'),
            'chapters': [
                'Understanding Federal Procurement',
                'SAM Registration Requirements',
                'Responding to Solicitations',
                'Contract Types Overview',
                'Small Business Programs',
            ],
            'resources': [
                'SAM.gov',
                'GSA Schedules',
                'FPDS.gov',
                'USASpending.gov',
            ],
            'distribution': 'Unlimited Public Distribution',
            'note': 'PUBLIC INFORMATION - Not CUI',
        })
        return doc

    def _generate_sbir_overview(self) -> Dict[str, Any]:
        """Generate SBIR program overview (negative example)."""
        doc = self._build_base_document('sbir_overview', 'small_business', is_positive=False)
        doc.update({
            'title': 'SBIR/STTR Program Overview',
            'publisher': 'Small Business Administration',
            'publication_date': self.generate_date_in_range(-180, 0).strftime('%B %d, %Y'),
            'content': (
                "The Small Business Innovation Research (SBIR) and Small Business Technology Transfer (STTR) "
                "programs provide funding opportunities for small businesses to conduct R&D with commercial potential."
            ),
            'participating_agencies': [
                'Department of Defense',
                'Department of Health and Human Services',
                'NASA',
                'Department of Energy',
                'NSF',
            ],
            'phases': [
                {'phase': 'Phase I', 'description': 'Feasibility study', 'typical_award': '$50,000 - $275,000'},
                {'phase': 'Phase II', 'description': 'R&D and prototype', 'typical_award': '$500,000 - $1,500,000'},
                {'phase': 'Phase III', 'description': 'Commercialization', 'typical_award': 'Non-SBIR funding'},
            ],
            'eligibility': 'US-based small businesses with fewer than 500 employees',
            'distribution': 'Unlimited Public Distribution',
            'note': 'PUBLIC INFORMATION - Not CUI',
        })
        return doc

    def _generate_vendor_outreach(self) -> Dict[str, Any]:
        """Generate vendor outreach materials (negative example)."""
        agency = self.get_agency()
        doc = self._build_base_document('vendor_outreach', 'general', is_positive=False)
        doc.update({
            'title': 'Industry Day Announcement',
            'agency': agency,
            'event_date': self.generate_date_in_range(14, 60).strftime('%B %d, %Y'),
            'event_type': 'Virtual Industry Day',
            'topic': f"{agency} Upcoming Acquisition Opportunities",
            'registration': 'Open to all interested vendors',
            'agenda': [
                'Agency Mission Overview',
                'Upcoming Contract Opportunities',
                'Small Business Goals',
                'Q&A Session',
            ],
            'contact': {
                'name': self.fake.name(),
                'email': f"industry.day@{agency.lower().replace(' ', '')}.gov",
            },
            'distribution': 'Unlimited Public Distribution',
            'note': 'PUBLIC ANNOUNCEMENT - Not CUI',
        })
        return doc
