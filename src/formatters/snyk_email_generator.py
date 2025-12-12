"""
Snyk Security Email Generator

Generates realistic Snyk vulnerability alert emails with varied findings.
Can be template-based or LLM-enhanced.
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import random
import os
from typing import Dict, Any, Optional


class SnykEmailGenerator:
    """Generates Snyk security alert emails with varied vulnerability findings."""

    # Real npm packages from 2025 supply chain attacks and common government use
    NPM_PACKAGES = [
        'chalk', 'debug', 'ansi-styles', 'strip-ansi',  # 2025 supply chain attack
        'lodash', 'axios', 'express', 'react', 'vue', 'moment', 'request',
        'webpack', 'jquery', 'body-parser', 'cookie-parser', 'cors',
        'dotenv', 'jsonwebtoken', 'bcrypt', 'mongoose', 'pg', 'mysql',
        'async', 'commander', 'yargs', 'inquirer', 'semver', 'glob',
    ]

    # Real Python packages with known 2025 CVEs
    PYTHON_PACKAGES = [
        'langflow',  # CVE-2025-3248 (RCE)
        'python-json-logger',  # CVE-2025-27607 (RCE)
        'pip',  # CVE-2025-8869 (Path Traversal)
        'pytorch', 'torch',  # CVE-2025-32434 (RCE)
        'django', 'flask', 'requests', 'numpy', 'pandas', 'pillow',
        'cryptography', 'pyyaml', 'sqlalchemy', 'celery', 'redis',
        'jinja2', 'werkzeug', 'boto3', 'paramiko', 'httpx',
    ]

    # Real Java packages with 2025 vulnerabilities
    JAVA_PACKAGES = [
        'lz4-java',  # CVE-2025-66566, CVE-2025-12183 (Info leak, DoS)
        'log4j-core', 'spring-core', 'spring-boot', 'jackson-databind',
        'commons-io', 'commons-lang', 'guava', 'httpclient', 'slf4j-api',
        'apache-tika-core', 'apache-tika-parsers',  # XXE vulnerabilities
        'netty', 'jersey', 'hibernate', 'struts2', 'gson',
    ]

    # Real CVE patterns from 2025 (we'll randomize the numbers but keep patterns realistic)
    REAL_CVE_TEMPLATES = [
        {'id': 'CVE-2025-3248', 'package': 'langflow', 'type': 'rce', 'cvss': 9.8},
        {'id': 'CVE-2025-27607', 'package': 'python-json-logger', 'type': 'rce', 'cvss': 9.3},
        {'id': 'CVE-2025-8869', 'package': 'pip', 'type': 'path_traversal', 'cvss': 6.5},
        {'id': 'CVE-2025-32434', 'package': 'pytorch', 'type': 'rce', 'cvss': 8.8},
        {'id': 'CVE-2025-66566', 'package': 'lz4-java', 'type': 'info_disclosure', 'cvss': 7.5},
        {'id': 'CVE-2025-12183', 'package': 'lz4-java', 'type': 'dos', 'cvss': 7.5},
        {'id': 'CVE-2025-55182', 'package': 'react-server-dom', 'type': 'rce', 'cvss': 9.1},
    ]

    # Vulnerability types with realistic patterns
    VULNERABILITY_TYPES = {
        'sql_injection': {
            'title': 'SQL Injection',
            'cwe': 'CWE-89',
            'severity_range': (7.0, 9.8),
            'description_template': 'Improper neutralization of special elements in SQL commands allows attackers to execute arbitrary SQL queries.',
            'impact': 'Unauthorized database access, data exfiltration, or data manipulation',
            'remediation': 'Upgrade to version {fix_version} or use parameterized queries',
        },
        'xss': {
            'title': 'Cross-site Scripting (XSS)',
            'cwe': 'CWE-79',
            'severity_range': (6.0, 8.5),
            'description_template': 'Improper neutralization of input allows injection of malicious scripts into web pages.',
            'impact': 'Session hijacking, credential theft, or malicious redirection',
            'remediation': 'Upgrade to version {fix_version} or sanitize user input',
        },
        'rce': {
            'title': 'Remote Code Execution',
            'cwe': 'CWE-94',
            'severity_range': (8.5, 10.0),
            'description_template': 'Unsafe deserialization or command injection allows remote code execution.',
            'impact': 'Complete system compromise, data breach, or denial of service',
            'remediation': 'Immediately upgrade to version {fix_version}',
        },
        'path_traversal': {
            'title': 'Path Traversal',
            'cwe': 'CWE-22',
            'severity_range': (5.5, 8.0),
            'description_template': 'Improper limitation of pathname allows access to files outside intended directory.',
            'impact': 'Unauthorized file access or information disclosure',
            'remediation': 'Upgrade to version {fix_version} or validate file paths',
        },
        'xxe': {
            'title': 'XML External Entity (XXE) Injection',
            'cwe': 'CWE-611',
            'severity_range': (6.5, 9.0),
            'description_template': 'XML parser processes external entity references, allowing file disclosure or SSRF.',
            'impact': 'Information disclosure, denial of service, or server-side request forgery',
            'remediation': 'Upgrade to version {fix_version} or disable external entity processing',
        },
        'prototype_pollution': {
            'title': 'Prototype Pollution',
            'cwe': 'CWE-1321',
            'severity_range': (6.0, 8.5),
            'description_template': 'Modification of Object.prototype allows injection of properties into all objects.',
            'impact': 'Property injection leading to denial of service or privilege escalation',
            'remediation': 'Upgrade to version {fix_version}',
        },
        'deserialization': {
            'title': 'Insecure Deserialization',
            'cwe': 'CWE-502',
            'severity_range': (7.5, 9.5),
            'description_template': 'Unsafe deserialization of untrusted data allows arbitrary code execution.',
            'impact': 'Remote code execution or denial of service',
            'remediation': 'Upgrade to version {fix_version} or avoid deserializing untrusted data',
        },
        'auth_bypass': {
            'title': 'Authentication Bypass',
            'cwe': 'CWE-287',
            'severity_range': (7.0, 9.0),
            'description_template': 'Improper authentication mechanism allows unauthorized access.',
            'impact': 'Unauthorized access to protected resources',
            'remediation': 'Upgrade to version {fix_version}',
        },
        'dos': {
            'title': 'Denial of Service (DoS)',
            'cwe': 'CWE-400',
            'severity_range': (5.0, 7.5),
            'description_template': 'Uncontrolled resource consumption allows denial of service attacks.',
            'impact': 'Service disruption or resource exhaustion',
            'remediation': 'Upgrade to version {fix_version} or implement rate limiting',
        },
        'info_disclosure': {
            'title': 'Information Disclosure',
            'cwe': 'CWE-200',
            'severity_range': (4.0, 7.0),
            'description_template': 'Sensitive information exposed through error messages or debug output.',
            'impact': 'Exposure of sensitive configuration or internal system details',
            'remediation': 'Upgrade to version {fix_version} or disable debug mode',
        },
    }

    # Government project names for CUI-positive emails
    GOV_PROJECTS = [
        'Medicare Provider Portal',
        'HIPAA Compliance Dashboard',
        'Claims Processing System',
        'Provider Enrollment API',
        'Beneficiary Data Platform',
        'Quality Reporting System',
        'Payment Processing Gateway',
        'Provider Directory Service',
        'Eligibility Verification API',
    ]

    # Generic/public project names for CUI-negative
    PUBLIC_PROJECTS = [
        'Website Frontend',
        'Public API Gateway',
        'Content Management System',
        'Documentation Portal',
        'Public Health Dashboard',
    ]

    def __init__(self, output_dir: str = 'output'):
        """Initialize Snyk email generator."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_vulnerability_finding(self, is_positive: bool = True) -> Dict[str, Any]:
        """
        Generate a single vulnerability finding with varied details.
        Uses mix of real 2025 CVEs and synthetic variations.

        Args:
            is_positive: If True, generate CUI-positive (internal project info)

        Returns:
            Dictionary with vulnerability details
        """
        # 30% chance to use a real CVE pattern, 70% generate synthetic
        use_real_cve = random.random() < 0.3

        if use_real_cve and self.REAL_CVE_TEMPLATES:
            # Use real CVE as basis but may randomize CVSS slightly
            template = random.choice(self.REAL_CVE_TEMPLATES)
            package = template['package']
            vuln_type = template['type']
            vuln_info = self.VULNERABILITY_TYPES[vuln_type]

            # Use real CVE ID or generate similar pattern
            if random.random() < 0.5:
                cve_id = template['id']
                cvss_score = template['cvss']
            else:
                # Generate CVE with same year but different number
                cve_year = int(template['id'].split('-')[1])
                cve_number = random.randint(1000, 99999)
                cve_id = f"CVE-{cve_year}-{cve_number}"
                # Randomize CVSS within +/- 1.0
                cvss_score = round(random.uniform(
                    max(template['cvss'] - 1.0, vuln_info['severity_range'][0]),
                    min(template['cvss'] + 1.0, vuln_info['severity_range'][1])
                ), 1)

            # Determine ecosystem from package
            if package in self.NPM_PACKAGES:
                ecosystem = 'npm'
                language = 'JavaScript'
            elif package in self.PYTHON_PACKAGES:
                ecosystem = 'pypi'
                language = 'Python'
            else:
                ecosystem = 'maven'
                language = 'Java'

        else:
            # Generate synthetic vulnerability
            vuln_type = random.choice(list(self.VULNERABILITY_TYPES.keys()))
            vuln_info = self.VULNERABILITY_TYPES[vuln_type]

            # Select package ecosystem and package
            ecosystem = random.choice(['npm', 'pypi', 'maven'])
            if ecosystem == 'npm':
                package = random.choice(self.NPM_PACKAGES)
                language = 'JavaScript'
            elif ecosystem == 'pypi':
                package = random.choice(self.PYTHON_PACKAGES)
                language = 'Python'
            else:
                package = random.choice(self.JAVA_PACKAGES)
                language = 'Java'

            # Generate CVE
            cve_year = random.choice([2024, 2025])
            cve_number = random.randint(1000, 99999)
            cve_id = f"CVE-{cve_year}-{cve_number}"

            # Calculate CVSS score within severity range (randomized)
            min_score, max_score = vuln_info['severity_range']
            cvss_score = round(random.uniform(min_score, max_score), 1)

        # Generate versions
        major = random.randint(1, 15)
        minor = random.randint(0, 20)
        patch = random.randint(0, 30)
        vulnerable_version = f"{major}.{minor}.{patch}"

        # Fix version (bump patch or minor)
        if random.random() < 0.7:
            fix_version = f"{major}.{minor}.{patch + 1}"
        else:
            fix_version = f"{major}.{minor + 1}.0"

        # Determine severity based on CVSS
        if cvss_score >= 9.0:
            severity = 'Critical'
        elif cvss_score >= 7.0:
            severity = 'High'
        elif cvss_score >= 4.0:
            severity = 'Medium'
        else:
            severity = 'Low'

        # Project/organization info
        if is_positive:
            # CUI-positive: internal government project
            organization = random.choice(['CMS', 'HHS', 'Department of Health and Human Services'])
            project_name = random.choice(self.GOV_PROJECTS)
            repo_path = f"github.com/cms-internal/{project_name.lower().replace(' ', '-')}"
        else:
            # CUI-negative: public/generic project
            organization = 'Public Repository'
            project_name = random.choice(self.PUBLIC_PROJECTS)
            repo_path = f"github.com/public/{project_name.lower().replace(' ', '-')}"

        return {
            'vulnerability_type': vuln_info['title'],
            'cwe': vuln_info['cwe'],
            'cve_id': cve_id,
            'cvss_score': cvss_score,
            'severity': severity,
            'package_name': package,
            'package_ecosystem': ecosystem,
            'language': language,
            'vulnerable_version': vulnerable_version,
            'fixed_version': fix_version,
            'description': vuln_info['description_template'],
            'impact': vuln_info['impact'],
            'remediation': vuln_info['remediation'].format(fix_version=fix_version),
            'organization': organization,
            'project_name': project_name,
            'repo_path': repo_path,
            'is_positive': is_positive,
        }

    def create_vulnerability_alert_email(self, recipient_email: str, findings: list,
                                        organization: str, filename: str) -> str:
        """
        Create a Snyk vulnerability alert email with multiple findings.

        Args:
            recipient_email: Recipient email address
            findings: List of vulnerability finding dictionaries
            organization: Organization name
            filename: Output filename

        Returns:
            Path to created email file
        """
        msg = MIMEMultipart('alternative')

        # Count by severity
        critical_count = sum(1 for f in findings if f['severity'] == 'Critical')
        high_count = sum(1 for f in findings if f['severity'] == 'High')
        medium_count = sum(1 for f in findings if f['severity'] == 'Medium')
        low_count = sum(1 for f in findings if f['severity'] == 'Low')

        # Email headers
        msg['Subject'] = f"[snyk] Vulnerability alert for the {organization} organization"
        msg['From'] = 'Snyk <support-noreply@snyk.io>'
        msg['To'] = recipient_email
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(10000000000, 99999999999)}@snyk.io>"
        msg['X-Mailgun-Tag'] = 'new-vulnerabilities'

        # Build plain text body
        plain_text = self._build_plain_text_vulnerability_alert(
            findings, organization, critical_count, high_count, medium_count, low_count
        )

        # Build HTML body
        html_text = self._build_html_vulnerability_alert(
            findings, organization, critical_count, high_count, medium_count, low_count
        )

        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_text, 'html'))

        # Save email
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def _build_plain_text_vulnerability_alert(self, findings, organization, crit, high, med, low):
        """Build plain text email body for vulnerability alert."""

        summary_counts = []
        if crit > 0:
            summary_counts.append(f"{crit} critical")
        if high > 0:
            summary_counts.append(f"{high} high")
        if med > 0:
            summary_counts.append(f"{med} medium")
        if low > 0:
            summary_counts.append(f"{low} low")

        summary = " • ".join(summary_counts) if summary_counts else "new issues"

        lines = [
            f"Snyk found {summary} severity vulnerabilities in {organization}",
            "",
            "="*70,
            "",
            "VULNERABILITY SUMMARY",
            "",
        ]

        for i, finding in enumerate(findings, 1):
            lines.extend([
                f"[{finding['severity'].upper()}] {finding['vulnerability_type']}",
                f"Package: {finding['package_name']} ({finding['package_ecosystem']})",
                f"Vulnerable Versions: {finding['vulnerable_version']} and below",
                f"Fixed in: {finding['fixed_version']}",
                f"CVE: {finding['cve_id']} | CVSS: {finding['cvss_score']} | {finding['cwe']}",
                "",
                f"Description:",
                finding['description'],
                "",
                f"Impact: {finding['impact']}",
                "",
                f"Remediation: {finding['remediation']}",
                "",
                "-"*70,
                "",
            ])

        lines.extend([
            "",
            "View full details and prioritize fixes at:",
            f"https://app.snyk.io/org/{organization.lower().replace(' ', '-')}/",
            "",
            "---",
            "Snyk Security",
            "https://snyk.io",
            "",
            "This is an automated security alert. To manage notification preferences,",
            "visit your Snyk account settings.",
        ])

        return '\n'.join(lines)

    def _build_html_vulnerability_alert(self, findings, organization, crit, high, med, low):
        """Build HTML email body for vulnerability alert."""

        # Build severity badge HTML
        badges = []
        if crit > 0:
            badges.append(f'<span style="background:#d32f2f;color:white;padding:4px 8px;border-radius:3px;font-weight:bold;">{crit} CRITICAL</span>')
        if high > 0:
            badges.append(f'<span style="background:#f57c00;color:white;padding:4px 8px;border-radius:3px;font-weight:bold;">{high} HIGH</span>')
        if med > 0:
            badges.append(f'<span style="background:#fbc02d;color:black;padding:4px 8px;border-radius:3px;font-weight:bold;">{med} MEDIUM</span>')
        if low > 0:
            badges.append(f'<span style="background:#7cb342;color:white;padding:4px 8px;border-radius:3px;font-weight:bold;">{low} LOW</span>')

        badges_html = ' '.join(badges)

        html_parts = [
            '<html><head></head><body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">',
            '<div style="max-width: 700px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px;">',

            # Header
            '<div style="background: #4a148c; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">',
            '<h1 style="margin: 0; font-size: 24px;">🔒 Snyk Security Alert</h1>',
            f'<p style="margin: 10px 0 0 0; opacity: 0.9;">New vulnerabilities found in {organization}</p>',
            '</div>',

            # Summary badges
            f'<div style="margin: 20px 0;">{badges_html}</div>',

            # Vulnerabilities
            '<div style="margin: 20px 0;">',
        ]

        for finding in findings:
            severity_color = {
                'Critical': '#d32f2f',
                'High': '#f57c00',
                'Medium': '#fbc02d',
                'Low': '#7cb342'
            }.get(finding['severity'], '#666')

            html_parts.extend([
                '<div style="border-left: 4px solid {color}; padding: 15px; margin: 15px 0; background: #fafafa;">'.format(color=severity_color),
                f'<h3 style="margin: 0 0 10px 0; color: {severity_color};">[{finding["severity"].upper()}] {finding["vulnerability_type"]}</h3>',
                f'<p style="margin: 5px 0;"><strong>Package:</strong> {finding["package_name"]} ({finding["package_ecosystem"]})</p>',
                f'<p style="margin: 5px 0;"><strong>Vulnerable:</strong> {finding["vulnerable_version"]} and below</p>',
                f'<p style="margin: 5px 0;"><strong>Fixed in:</strong> {finding["fixed_version"]}</p>',
                f'<p style="margin: 5px 0;"><strong>CVE:</strong> {finding["cve_id"]} | <strong>CVSS:</strong> {finding["cvss_score"]} | <strong>CWE:</strong> {finding["cwe"]}</p>',
                f'<p style="margin: 10px 0 5px 0;"><strong>Description:</strong></p>',
                f'<p style="margin: 0; color: #666;">{finding["description"]}</p>',
                f'<p style="margin: 10px 0 5px 0;"><strong>Remediation:</strong></p>',
                f'<p style="margin: 0; color: #666;">{finding["remediation"]}</p>',
                '</div>',
            ])

        html_parts.extend([
            '</div>',

            # CTA Button
            '<div style="text-align: center; margin: 30px 0;">',
            f'<a href="https://app.snyk.io/org/{organization.lower().replace(" ", "-")}/" ',
            'style="background: #4a148c; color: white; padding: 12px 30px; text-decoration: none; ',
            'border-radius: 5px; font-weight: bold; display: inline-block;">',
            'View All Vulnerabilities in Snyk',
            '</a>',
            '</div>',

            # Footer
            '<div style="border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px; color: #666; font-size: 12px;">',
            '<p>Snyk Security | <a href="https://snyk.io">https://snyk.io</a></p>',
            '<p>This is an automated security alert. To manage notification preferences, visit your Snyk account settings.</p>',
            '</div>',

            '</div>',
            '</body></html>',
        ])

        return ''.join(html_parts)

    def create_snyk_vulnerability_alert(self, filename: str, is_positive: bool = True,
                                       finding_count: Optional[int] = None) -> str:
        """
        Create a Snyk vulnerability alert email (CUI-Critical Infrastructure).

        Args:
            filename: Output filename
            is_positive: True for CUI-positive (internal org), False for CUI-negative (public)
            finding_count: Number of vulnerabilities (defaults to 1-4 random)

        Returns:
            Path to created file
        """
        # Generate 1-4 findings per email
        if finding_count is None:
            finding_count = random.randint(1, 4)

        findings = [self.generate_vulnerability_finding(is_positive) for _ in range(finding_count)]

        # Use first finding's org info for email level
        organization = findings[0]['organization']

        # Recipient email
        if is_positive:
            recipient = f"security.team@cms.hhs.gov"
        else:
            recipient = f"dev@example.com"

        return self.create_vulnerability_alert_email(recipient, findings, organization, filename)

    def create_snyk_weekly_report(self, filename: str, is_positive: bool = True) -> str:
        """
        Create a Snyk weekly summary report email.

        Args:
            filename: Output filename
            is_positive: True for CUI-positive, False for CUI-negative

        Returns:
            Path to created file
        """
        msg = MIMEMultipart('alternative')

        # Select project
        if is_positive:
            organization = random.choice(['CMS', 'HHS'])
            project_name = random.choice(self.GOV_PROJECTS)
            recipient = 'security.team@cms.hhs.gov'
        else:
            organization = 'Public Repository'
            project_name = random.choice(self.PUBLIC_PROJECTS)
            recipient = 'dev@example.com'

        # Email headers
        msg['Subject'] = f"[snyk] {project_name}'s weekly report"
        msg['From'] = 'Snyk <support-noreply@snyk.io>'
        msg['To'] = recipient
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(10000000000, 99999999999)}@snyk.io>"

        # Weekly summary stats
        new_vulns = random.randint(0, 5)
        fixed_vulns = random.randint(0, 8)
        open_vulns = random.randint(5, 25)
        dependencies = random.randint(150, 500)

        plain_text = f"""
{project_name} - Weekly Security Summary

This week's activity:
• {new_vulns} new vulnerabilities detected
• {fixed_vulns} vulnerabilities fixed
• {open_vulns} total open issues

Dependency Health:
• {dependencies} total dependencies scanned
• {random.randint(1, 10)} dependencies need updates
• {random.randint(0, 3)} critical issues require immediate attention

Top Priority:
Fix critical severity issues in production dependencies.

View full report:
https://app.snyk.io/org/{organization.lower().replace(' ', '-')}/projects/

---
Snyk Security
https://snyk.io
"""

        html_text = f"""
<html>
<body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px;">
    <div style="background: #4a148c; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
        <h1 style="margin: 0;">{project_name}</h1>
        <p style="margin: 5px 0 0 0;">Weekly Security Report</p>
    </div>

    <h2>This Week's Activity</h2>
    <ul>
        <li>{new_vulns} new vulnerabilities detected</li>
        <li>{fixed_vulns} vulnerabilities fixed</li>
        <li>{open_vulns} total open issues</li>
    </ul>

    <h2>Dependency Health</h2>
    <ul>
        <li>{dependencies} total dependencies scanned</li>
        <li>{random.randint(1, 10)} dependencies need updates</li>
        <li>{random.randint(0, 3)} critical issues require immediate attention</li>
    </ul>

    <div style="text-align: center; margin: 30px 0;">
        <a href="https://app.snyk.io/org/{organization.lower().replace(' ', '-')}/projects/"
           style="background: #4a148c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
           View Full Report
        </a>
    </div>

    <div style="border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px; color: #666; font-size: 12px;">
        <p>Snyk Security | https://snyk.io</p>
    </div>
</div>
</body>
</html>
"""

        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_text, 'html'))

        # Save email
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath


if __name__ == "__main__":
    # Test the generator
    generator = SnykEmailGenerator(output_dir='output/snyk_test')

    print("Testing Snyk Email Generator\n")
    print("="*70)

    # Test CUI-positive vulnerability alert (3 findings)
    print("\n1. Generating CUI-Positive vulnerability alert...")
    positive_file = generator.create_snyk_vulnerability_alert(
        'SnykAlert_Positive_001.eml',
        is_positive=True,
        finding_count=3
    )
    print(f"   ✓ Created: {positive_file}")

    # Test CUI-negative vulnerability alert (1 finding)
    print("\n2. Generating CUI-Negative vulnerability alert...")
    negative_file = generator.create_snyk_vulnerability_alert(
        'SnykAlert_Negative_001.eml',
        is_positive=False,
        finding_count=1
    )
    print(f"   ✓ Created: {negative_file}")

    # Test weekly report
    print("\n3. Generating weekly report...")
    weekly_file = generator.create_snyk_weekly_report(
        'SnykWeekly_001.eml',
        is_positive=True
    )
    print(f"   ✓ Created: {weekly_file}")

    print("\n" + "="*70)
    print("Snyk email generation complete!")
    print("\nVariety achieved through:")
    print("  • 10 different vulnerability types")
    print("  • 40+ real package names (npm, PyPI, Maven)")
    print("  • Randomized CVE IDs, CVSS scores, versions")
    print("  • 1-4 findings per email")
    print("  • CUI-positive: internal CMS projects")
    print("  • CUI-negative: public/generic projects")
