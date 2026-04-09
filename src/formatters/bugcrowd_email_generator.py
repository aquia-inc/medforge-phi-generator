"""
BugCrowd vulnerability disclosure email generator.

Produces realistic BugCrowd-style vulnerability notification emails
with randomized programs, vulnerability types, priorities, and reporters.
Supports CUI-positive (CMS-specific) and CUI-negative (generic) variants.
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional

from faker import Faker

from formatters.base_email_formatter import BaseEmailFormatter


class BugCrowdEmailGenerator(BaseEmailFormatter):
    """Generates varied BugCrowd vulnerability disclosure emails."""

    # CUI-positive: CMS-specific program engagements
    CMS_PROGRAMS = [
        ('CMS Bug Bounty Program 2025', 'cms-bb3'),
        ('CMS Vulnerability Disclosure Program', 'cms-vdp'),
        ('HHS Bug Bounty', 'hhs-bb'),
        ('Medicare.gov VDP', 'mgov-vdp'),
        ('Healthcare.gov Bug Bounty', 'hcgov-bb'),
        ('CMS Enterprise Security VDP', 'cms-es-vdp'),
    ]

    # CUI-negative: generic programs
    GENERIC_PROGRAMS = [
        ('Public Bug Bounty Program', 'pub-bb'),
        ('Open Source VDP', 'os-vdp'),
        ('Community Security Program', 'comm-sec'),
        ('Web Application Bug Bounty', 'webapp-bb'),
    ]

    # BugCrowd VRT (Vulnerability Rating Taxonomy)
    VRT_CATEGORIES = [
        ('Broken Authentication and Session Management', [
            'Second Factor Authentication (2FA) Bypass',
            'Session Fixation',
            'Weak Password Policy',
            'Credential Stuffing',
        ]),
        ('Server-Side Injection', [
            'SQL Injection',
            'OS Command Injection',
            'LDAP Injection',
            'Server-Side Template Injection',
        ]),
        ('Cross-Site Scripting (XSS)', [
            'Stored XSS',
            'Reflected XSS',
            'DOM-Based XSS',
        ]),
        ('Insecure Direct Object Reference (IDOR)', [
            'Read Access to Sensitive Data',
            'Write Access to Sensitive Data',
            'Account Takeover via IDOR',
        ]),
        ('Server-Side Request Forgery (SSRF)', [
            'Internal Network Access',
            'Cloud Metadata Exposure',
            'Port Scanning via SSRF',
        ]),
        ('Sensitive Data Exposure', [
            'Hardcoded Credentials',
            'Personal Access Token Leaked',
            'API Key Exposure',
            'PII Data Leak',
            'Internal Documentation Exposed',
        ]),
        ('Broken Access Control', [
            'Privilege Escalation',
            'Missing Function-Level Access Control',
            'Horizontal Privilege Escalation',
        ]),
        ('Security Misconfiguration', [
            'Verbose Error Messages',
            'Directory Listing Enabled',
            'Default Credentials',
            'Missing Security Headers',
        ]),
    ]

    PRIORITIES = ['P1', 'P2', 'P3', 'P4', 'P5']
    PRIORITY_WEIGHTS = [5, 20, 35, 30, 10]  # Weighted toward P2-P3

    STATUSES = ['New', 'Triaged', 'Unresolved', 'Resolved',
                'Informational', 'Not Applicable', 'Duplicate']

    CHANGE_FIELDS = ['Priority', 'Status', 'Assignee', 'VRT Category', 'Severity']

    # CMS-specific endpoints (CUI-positive)
    CMS_ENDPOINTS = [
        'https://portal.cms.gov/wps/portal/unauthenticated',
        'https://idm.cms.gov/auth/realms/cms',
        'https://qpp.cms.gov/api/submissions',
        'https://data.cms.gov/provider-data/api',
        'https://hpms.cms.gov/app/ng/home',
        'https://eua.cms.gov/eidm/authenticate',
        'https://marketplace.cms.gov/api/v1',
        'https://ztmf.cms.gov/dashboard',
        'https://cfacts.cms.gov/apps/ito',
    ]

    # Generic endpoints (CUI-negative)
    GENERIC_ENDPOINTS = [
        'https://app.example.com/api/v2/users',
        'https://portal.example.org/login',
        'https://api.example.com/graphql',
        'https://staging.example.com/admin',
        'https://cdn.example.com/assets',
    ]

    REPORTER_PREFIXES = [
        'security_researcher', 'bug_hunter', 'ethicalhacker',
        'vuln_finder', 'infosec_pro', 'pentest_', 'hackerone_',
        'crowdcontrol', 'whitehat', 'redsec',
    ]

    def __init__(self, output_dir: str = 'output',
                 llm_generator=None, llm_percentage: float = 0.2):
        super().__init__(output_dir)
        self.fake = Faker('en_US')
        self.llm_generator = llm_generator
        self.llm_percentage = llm_percentage

    def _random_reporter(self) -> str:
        prefix = random.choice(self.REPORTER_PREFIXES)
        return f"{prefix}{random.randint(10, 999)}"

    def _random_vulnerability(self):
        """Return (category, sub_type, full_title)."""
        category, sub_types = random.choice(self.VRT_CATEGORIES)
        sub_type = random.choice(sub_types)
        return category, sub_type, f"{category} > {sub_type}"

    def _random_priority(self) -> str:
        return random.choices(self.PRIORITIES, weights=self.PRIORITY_WEIGHTS, k=1)[0]

    def _generate_changes(self, priority: str) -> list:
        """Generate 1-3 field changes for the update notification."""
        changes = []
        # Always include the priority change
        old_priority = random.choice([p for p in self.PRIORITIES if p != priority]) if random.random() < 0.7 else 'none'
        changes.append(('Priority', old_priority, priority))

        if random.random() < 0.5:
            old_status = random.choice(self.STATUSES[:3])
            new_status = random.choice(self.STATUSES)
            if old_status != new_status:
                changes.append(('Status', old_status, new_status))

        if random.random() < 0.3:
            changes.append(('Assignee', 'Unassigned', self.fake.name()))

        return changes

    def _build_plain_body(self, reporter: str, vuln_title: str,
                          changes: list, program_name: str,
                          engagement_code: str, submission_id: str,
                          description: str = '') -> str:
        """Build plain text email body in BugCrowd format."""
        lines = []
        lines.append(f"{reporter} updated {vuln_title}.")
        lines.append('')
        lines.append('')
        lines.append('Changes')

        for field, old_val, new_val in changes:
            lines.append(f'{field}')
            lines.append(f'{old_val} to {new_val}')
            lines.append('')

        if description:
            lines.append('Description')
            lines.append(description)
            lines.append('')

        lines.append(f'Engagement: {program_name} [{engagement_code}]')
        lines.append(f'Submission ID: {submission_id}')
        lines.append(f'Submitted: {self.fake.date_time_between(start_date="-90d", end_date="now").strftime("%-d %b %Y %H:%M:%S UTC")}')
        lines.append('')
        lines.append(f'View Submission Details <https://tracker.bugcrowd.com/{engagement_code}/submissions/{submission_id}>')
        lines.append(f'Getting too much email? Check your notification settings. <https://tracker.bugcrowd.com/user/notification_settings>')
        lines.append('')
        lines.append('Copyright \u00a9 2014 \u2013 2025 Bugcrowd, Inc. All rights reserved.')
        lines.append('300 California Street, Suite 220, San Francisco, CA 94104')

        return '\n'.join(lines)

    def create_bugcrowd_alert(self, filename: str, is_positive: bool = True) -> str:
        """Create a BugCrowd vulnerability disclosure notification email.

        Args:
            filename: Output filename
            is_positive: True for CUI-positive (CMS-specific), False for generic

        Returns:
            Path to saved EML file
        """
        # Select program
        if is_positive:
            program_name, engagement_code = random.choice(self.CMS_PROGRAMS)
        else:
            program_name, engagement_code = random.choice(self.GENERIC_PROGRAMS)

        # Generate vulnerability
        vrt_category, vrt_subtype, vrt_full = self._random_vulnerability()
        priority = self._random_priority()
        status = random.choice(self.STATUSES[:4])  # Active statuses
        reporter = self._random_reporter()
        submission_id = str(uuid.uuid4())

        # Build a descriptive vulnerability title
        if is_positive:
            endpoint = random.choice(self.CMS_ENDPOINTS)
            system_name = endpoint.split('//')[1].split('/')[0].split('.')[0].upper()
            vuln_title = f"{vrt_subtype} in {system_name} {random.choice(['portal', 'API', 'authentication endpoint', 'admin panel', 'data feed'])}"
        else:
            endpoint = random.choice(self.GENERIC_ENDPOINTS)
            vuln_title = f"{vrt_subtype} in {random.choice(['web application', 'REST API', 'login page', 'user dashboard'])}"

        # Generate changes
        changes = self._generate_changes(priority)

        # Optional LLM enrichment for description
        description = ''
        llm_used = False
        if is_positive and self.llm_generator and random.random() < self.llm_percentage:
            try:
                result = self.llm_generator.generate_cui_security_report(
                    system_name=system_name if is_positive else 'Web Application',
                    vulnerability_type=vrt_subtype,
                    severity=priority,
                    agency='CMS' if is_positive else 'Organization',
                )
                if result and hasattr(result, 'technical_details'):
                    description = result.technical_details
                    llm_used = True
            except Exception:
                pass

        # Build email
        subject = f"[{engagement_code}] {vuln_title}"

        if is_positive:
            recipient_name = self.fake.name()
            first = recipient_name.split()[0].lower()
            last = recipient_name.split()[-1].lower()
            to_addr = f'"{recipient_name} (CMS/OIT)" <{first}.{last}@cms.hhs.gov>'
        else:
            to_addr = 'security@example.com'

        plain_body = self._build_plain_body(
            reporter=reporter,
            vuln_title=vuln_title,
            changes=changes,
            program_name=program_name,
            engagement_code=engagement_code,
            submission_id=submission_id,
            description=description,
        )

        custom_headers = {
            'Thread-Topic': subject,
            'X-MS-Exchange-Organization-RecordReviewCfmType': '0',
        }

        filepath = self._build_and_save_email(
            subject=subject,
            from_addr='The Bugcrowd Team <support@bugcrowd.com>',
            to_addr=to_addr,
            plain_body=plain_body,
            custom_headers=custom_headers,
            filename=filename,
            message_id_domain='email.amazonses.com',
        )

        return filepath
