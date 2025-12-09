"""
Critical Infrastructure CUI generator.

Generates synthetic CUI documents for:
- Emergency Management (COOP plans, ERG assignments)
- Systems Vulnerability (FISMA reports, vulnerability alerts)
- Physical Security (facility assessments, access control)
"""
from typing import Any, Dict, List, Optional
import random
from datetime import datetime, timedelta

from .base import BaseCUIGenerator
from .factory import CUIGeneratorFactory


@CUIGeneratorFactory.register('critical_infrastructure')
class CriticalInfrastructureCUIGenerator(BaseCUIGenerator):
    """Generator for Critical Infrastructure CUI documents."""

    CATEGORY = 'critical_infrastructure'
    SUBCATEGORIES = ['emergency_management', 'systems_vulnerability', 'physical_security']
    CUI_MARKINGS = [
        'CUI - EMERGENCY MANAGEMENT',
        'CUI//SP-CRITINFRA',
        'CUI//SP-EMGT',
        'CUI//SP-PHYSEC',
    ]
    AUTHORITIES = [
        'Presidential Policy Directive 40 (PPD-40)',
        'Federal Continuity Directive 1 (FCD-1)',
        'NIST SP 800-53',
    ]

    # Emergency Management data
    ESSENTIAL_FUNCTIONS = [
        'National Essential Functions (NEFs)',
        'Mission Essential Functions (MEFs)',
        'Primary Mission Essential Functions (PMEFs)',
        'Administrative Support Functions',
        'Emergency Response Coordination',
        'Public Safety Operations',
    ]

    EMERGENCY_SCENARIOS = [
        'Pandemic outbreak',
        'Natural disaster',
        'Cyber attack',
        'Terrorist incident',
        'Infrastructure failure',
        'Chemical/biological threat',
        'Nuclear emergency',
    ]

    LOCATION_TYPES = [
        'Primary Operating Facility',
        'Alternate Operating Facility',
        'Devolution Site',
        'Emergency Relocation Site',
        'Mobile Command Center',
        'Telework Location',
    ]

    # Vulnerability data
    VULNERABILITY_TYPES = [
        'Remote Code Execution',
        'Privilege Escalation',
        'Information Disclosure',
        'Denial of Service',
        'SQL Injection',
        'Cross-Site Scripting',
        'Authentication Bypass',
        'Buffer Overflow',
    ]

    SEVERITY_LEVELS = ['Critical', 'High', 'Medium', 'Low']

    AFFECTED_SYSTEMS = [
        'Web Application Server',
        'Database Server',
        'Authentication Service',
        'API Gateway',
        'Network Infrastructure',
        'Cloud Services',
        'Container Platform',
        'Legacy System',
    ]

    def __init__(self, locale: str = 'en_US', seed: Optional[int] = None):
        super().__init__(locale, seed)

    def get_document_types(self) -> List[Dict[str, Any]]:
        """Get available document types for critical infrastructure."""
        return self._document_types.get(self.CATEGORY, {})

    def generate_positive(self) -> Dict[str, Any]:
        """Generate a CUI-positive critical infrastructure document."""
        subcategory = random.choice(self.SUBCATEGORIES)
        doc_type = random.choice(['coop_plan', 'vulnerability_alert', 'fisma_report', 'facility_assessment'])

        if doc_type == 'coop_plan':
            return self._generate_coop_plan(subcategory)
        elif doc_type == 'vulnerability_alert':
            return self._generate_vulnerability_alert(subcategory)
        elif doc_type == 'fisma_report':
            return self._generate_fisma_report(subcategory)
        else:
            return self._generate_facility_assessment(subcategory)

    def generate_negative(self) -> Dict[str, Any]:
        """Generate a CUI-negative critical infrastructure document."""
        doc_type = random.choice(['servicenow_ticket', 'public_guidance', 'blank_template'])

        if doc_type == 'servicenow_ticket':
            return self._generate_servicenow_ticket()
        elif doc_type == 'public_guidance':
            return self._generate_public_guidance()
        else:
            return self._generate_blank_template()

    def _generate_coop_plan(self, subcategory: str) -> Dict[str, Any]:
        """Generate a Continuity of Operations Plan."""
        org = self.get_agency()
        sub_org = random.choice([
            'Office of the Chief Information Officer',
            'Office of Emergency Management',
            'Bureau of Administration',
            'Division of Operations',
        ])

        essential_funcs = random.sample(self.ESSENTIAL_FUNCTIONS, k=random.randint(3, 5))
        scenario = random.choice(self.EMERGENCY_SCENARIOS)

        doc = self._build_base_document('coop_plan', subcategory, is_positive=True)
        doc.update({
            'title': f'Continuity of Operations Plan (COOP)',
            'organization': org,
            'sub_organization': sub_org,
            'plan_version': f"{random.randint(1, 5)}.{random.randint(0, 9)}",
            'effective_date': self.generate_date_in_range(-365, 0).strftime('%B %d, %Y'),
            'executive_summary': (
                f"This COOP addresses continuity requirements for {org} during catastrophic emergencies "
                f"that may disrupt normal operations. Plan ensures sustainment of essential functions "
                f"in accordance with {self.get_authority(subcategory)}."
            ),
            'essential_functions': [
                {'function': func, 'priority': i + 1}
                for i, func in enumerate(essential_funcs)
            ],
            'alternate_locations': {
                'primary': random.choice(self.LOCATION_TYPES),
                'secondary': random.choice(self.LOCATION_TYPES),
                'devolution_distance': f"{random.randint(50, 200)} miles from primary facility",
            },
            'activation_triggers': [
                f"{scenario} affecting primary operations",
                f"Loss of {random.randint(25, 75)}% of essential personnel",
                "Facility damage preventing normal operations",
            ],
            'erg_details': {
                'leader_title': random.choice(['Deputy Administrator', 'Assistant Secretary', 'Regional Director']),
                'leader_name': self.fake.name(),
                'size': random.randint(15, 50),
                'deployment_hours': random.randint(2, 12),
            },
            'confidentiality_notice': self.get_confidentiality_notice(),
        })
        return doc

    def _generate_vulnerability_alert(self, subcategory: str) -> Dict[str, Any]:
        """Generate a security vulnerability alert (Snyk-style)."""
        severity = random.choice(self.SEVERITY_LEVELS)
        vuln_type = random.choice(self.VULNERABILITY_TYPES)
        affected_system = random.choice(self.AFFECTED_SYSTEMS)
        cvss_score = round(random.uniform(4.0, 10.0), 1) if severity in ['Critical', 'High'] else round(random.uniform(1.0, 6.0), 1)

        doc = self._build_base_document('vulnerability_alert', 'systems_vulnerability', is_positive=True)
        doc.update({
            'title': f'Security Vulnerability Alert - {severity}',
            'organization': self.get_agency(),
            'alert_id': f"VULN-{self.fake.uuid4()[:8].upper()}",
            'severity': severity,
            'cvss_score': cvss_score,
            'vulnerability_type': vuln_type,
            'cve_id': f"CVE-{random.randint(2020, 2025)}-{random.randint(10000, 99999)}",
            'affected_system': affected_system,
            'affected_versions': f"{random.randint(1, 5)}.{random.randint(0, 9)}.x through {random.randint(6, 10)}.{random.randint(0, 9)}.x",
            'description': (
                f"A {severity.lower()} severity {vuln_type.lower()} vulnerability has been identified "
                f"in {affected_system}. This vulnerability could allow an attacker to "
                f"{self._get_vulnerability_impact(vuln_type)}."
            ),
            'remediation': {
                'action': 'Upgrade to patched version',
                'target_version': f"{random.randint(11, 15)}.{random.randint(0, 9)}.{random.randint(0, 5)}",
                'deadline': (datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%B %d, %Y'),
            },
            'discovered_by': random.choice(['Snyk Security', 'Internal Scan', 'Vendor Advisory', 'CISA Alert']),
            'reported_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
            'confidentiality_notice': (
                "This vulnerability information is CUI and should not be shared "
                "outside of authorized security personnel."
            ),
        })
        return doc

    def _generate_fisma_report(self, subcategory: str) -> Dict[str, Any]:
        """Generate a FISMA compliance report."""
        org = self.get_agency()
        system_name = f"{self.fake.word().title()} {random.choice(['Information System', 'Platform', 'Application'])}"

        doc = self._build_base_document('fisma_report', 'systems_vulnerability', is_positive=True)
        doc.update({
            'title': 'FISMA Compliance Assessment Report',
            'organization': org,
            'system_name': system_name,
            'system_id': f"SYS-{self.fake.uuid4()[:8].upper()}",
            'impact_level': random.choice(['Low', 'Moderate', 'High']),
            'assessment_date': self.generate_date_in_range(-90, 0).strftime('%B %d, %Y'),
            'assessor': {
                'name': self.fake.name(),
                'organization': random.choice(['Internal Audit', 'OIG', 'Third-Party Assessor']),
            },
            'findings_summary': {
                'total_controls': random.randint(150, 300),
                'controls_tested': random.randint(100, 250),
                'compliant': random.randint(80, 200),
                'non_compliant': random.randint(5, 30),
                'not_applicable': random.randint(10, 50),
            },
            'risk_rating': random.choice(['Low', 'Moderate', 'High', 'Very High']),
            'authorization_status': random.choice(['Authorized', 'Conditionally Authorized', 'Denied']),
            'authorization_date': self.generate_date_in_range(-180, 0).strftime('%B %d, %Y'),
            'authorization_expiration': (datetime.now() + timedelta(days=random.randint(180, 365))).strftime('%B %d, %Y'),
            'authorizing_official': {
                'name': self.fake.name(),
                'title': self.get_agency_title('executive'),
            },
            'poam_items': random.randint(3, 15),
        })
        return doc

    def _generate_facility_assessment(self, subcategory: str) -> Dict[str, Any]:
        """Generate a facility security assessment."""
        org = self.get_agency()
        facility_type = random.choice(['Headquarters', 'Regional Office', 'Data Center', 'Field Office'])

        doc = self._build_base_document('facility_assessment', 'physical_security', is_positive=True)
        doc.update({
            'title': 'Facility Security Assessment Report',
            'organization': org,
            'facility_name': f"{org} - {facility_type}",
            'facility_address': f"{self.fake.street_address()}, {self.fake.city()}, {self.fake.state_abbr()} {self.fake.zipcode()}",
            'assessment_date': self.generate_date_in_range(-60, 0).strftime('%B %d, %Y'),
            'assessor': {
                'name': self.fake.name(),
                'organization': 'Federal Protective Service',
            },
            'facility_security_level': random.choice(['I', 'II', 'III', 'IV', 'V']),
            'occupancy': random.randint(50, 500),
            'security_measures': {
                'access_control': random.choice(['PIV/CAC Required', 'Badge Access', 'Visitor Management']),
                'surveillance': random.choice(['24/7 CCTV', 'Limited Coverage', 'None']),
                'guard_force': random.choice(['Armed Guards', 'Unarmed Guards', 'None']),
                'intrusion_detection': random.choice(['Full Coverage', 'Partial', 'None']),
            },
            'vulnerabilities_identified': random.randint(3, 12),
            'risk_rating': random.choice(['Low', 'Moderate', 'High']),
            'recommendations': [
                'Upgrade access control system',
                'Enhance perimeter security',
                'Improve lighting in parking areas',
            ][:random.randint(1, 3)],
        })
        return doc

    def _generate_servicenow_ticket(self) -> Dict[str, Any]:
        """Generate a generic ServiceNow IT ticket (negative example)."""
        doc = self._build_base_document('servicenow_ticket', 'general', is_positive=False)
        doc.update({
            'title': 'IT Service Request',
            'ticket_number': f"REQ{random.randint(1000000, 9999999)}",
            'requester': self.fake.name(),
            'department': random.choice(['Human Resources', 'Finance', 'Operations', 'IT']),
            'request_type': random.choice([
                'Password Reset',
                'Software Installation',
                'Hardware Request',
                'VPN Access',
                'Email Issue',
            ]),
            'priority': random.choice(['Low', 'Medium', 'High']),
            'status': random.choice(['Open', 'In Progress', 'Pending', 'Resolved']),
            'description': (
                f"User requesting assistance with {random.choice(['account access', 'software update', 'hardware replacement'])}. "
                f"This is a routine IT service request."
            ),
            'assigned_to': self.fake.name(),
            'created_date': self.generate_date_in_range(-30, 0).strftime('%B %d, %Y'),
        })
        return doc

    def _generate_public_guidance(self) -> Dict[str, Any]:
        """Generate public emergency preparedness guidance (negative example)."""
        doc = self._build_base_document('public_guidance', 'emergency_management', is_positive=False)
        doc.update({
            'title': 'Emergency Preparedness Guide',
            'organization': 'Federal Emergency Management Agency',
            'publication_date': self.generate_date_in_range(-365, 0).strftime('%B %d, %Y'),
            'audience': 'General Public',
            'topics': [
                'Emergency Kit Essentials',
                'Family Communication Plan',
                'Shelter-in-Place Procedures',
                'Evacuation Routes',
            ],
            'content_summary': (
                "This public guide provides general information about emergency preparedness "
                "for households and communities. No sensitive operational information is included."
            ),
            'distribution': 'Unlimited Public Distribution',        })
        return doc

    def _generate_blank_template(self) -> Dict[str, Any]:
        """Generate a blank template form (negative example)."""
        template_type = random.choice(['COOP Template', 'FISMA Template', 'Security Assessment Template'])
        doc = self._build_base_document('blank_template', 'general', is_positive=False)
        doc.update({
            'title': f'{template_type} (BLANK)',
            'organization': self.get_agency(),
            'template_version': f"{random.randint(1, 3)}.0",
            'last_updated': self.generate_date_in_range(-180, 0).strftime('%B %d, %Y'),
            'instructions': (
                f"This is a blank {template_type.lower()} for agency use. "
                "Fill in all required fields before submission. "
                "This template does not contain any sensitive information."
            ),
            'fields': [
                {'name': 'Organization Name', 'value': '[ENTER ORGANIZATION]'},
                {'name': 'Point of Contact', 'value': '[ENTER POC NAME]'},
                {'name': 'Date', 'value': '[ENTER DATE]'},
            ],        })
        return doc

    def _get_vulnerability_impact(self, vuln_type: str) -> str:
        """Get vulnerability impact description based on type."""
        impacts = {
            'Remote Code Execution': 'execute arbitrary code on the affected system',
            'Privilege Escalation': 'gain elevated privileges on the system',
            'Information Disclosure': 'access sensitive data without authorization',
            'Denial of Service': 'disrupt service availability',
            'SQL Injection': 'access or modify database contents',
            'Cross-Site Scripting': 'inject malicious scripts into web pages',
            'Authentication Bypass': 'bypass authentication controls',
            'Buffer Overflow': 'crash the system or execute arbitrary code',
        }
        return impacts.get(vuln_type, 'compromise system security')
