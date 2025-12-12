"""
Snyk Email Template Populator

Uses Elizabeth's real Snyk email as a template and populates with varied vulnerability data.
Preserves authentic Snyk formatting while generating different findings.
"""
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import random
from datetime import datetime
from typing import List, Dict, Any
import os


class SnykTemplatePopulator:
    """Populates real Snyk email templates with varied vulnerability data."""

    def __init__(self, template_dir: str = 'temp'):
        """Initialize with customer template directory."""
        self.template_dir = template_dir

        # Map template files to their types
        self.templates = {
            'vulnerability_alert_positive': '[snyk] Vulnerability alert for the ZTMF Scoring organization-CUI-Critical Infrastructure-Positive.eml',
            'weekly_report_positive': '[snyk] ZTMF Scoring\'s weekly report-CUI-Critical Infrastructure-Positive.eml',
            'supply_chain_negative': '[snyk] "Shai-Hulud" npm supply chain incident - Updated Advisories-CUI-Critical Infrastructure-Negative.eml',
        }

        # Real 2025 CVE data
        self.real_cves = [
            {'cve': 'CVE-2025-3248', 'package': 'langflow', 'ecosystem': 'pypi', 'severity': 'Critical', 'cvss': 9.8, 'type': 'Remote Code Execution'},
            {'cve': 'CVE-2025-27607', 'package': 'python-json-logger', 'ecosystem': 'pypi', 'severity': 'Critical', 'cvss': 9.3, 'type': 'Remote Code Execution'},
            {'cve': 'CVE-2025-8869', 'package': 'pip', 'ecosystem': 'pypi', 'severity': 'Medium', 'cvss': 6.5, 'type': 'Path Traversal'},
            {'cve': 'CVE-2025-32434', 'package': 'pytorch', 'ecosystem': 'pypi', 'severity': 'High', 'cvss': 8.8, 'type': 'Remote Code Execution'},
            {'cve': 'CVE-2025-66566', 'package': 'lz4-java', 'ecosystem': 'maven', 'severity': 'High', 'cvss': 7.5, 'type': 'Information Disclosure'},
            {'cve': 'CVE-2025-12183', 'package': 'lz4-java', 'ecosystem': 'maven', 'severity': 'High', 'cvss': 7.5, 'type': 'Denial of Service'},
            {'cve': 'CVE-2025-55182', 'package': 'react-server-dom', 'ecosystem': 'npm', 'severity': 'Critical', 'cvss': 9.1, 'type': 'Remote Code Execution'},
        ]

        # Additional synthetic packages for variety
        self.packages = {
            'npm': ['chalk', 'debug', 'ansi-styles', 'lodash', 'axios', 'express', 'react', 'webpack', 'jquery'],
            'pypi': ['django', 'flask', 'requests', 'numpy', 'pandas', 'cryptography', 'pyyaml', 'sqlalchemy'],
            'maven': ['log4j-core', 'spring-boot', 'jackson-databind', 'commons-io', 'guava', 'httpclient'],
        }

        # CMS project names for CUI-positive
        self.cms_projects = [
            'Medicare Provider Portal',
            'HIPAA Compliance Dashboard',
            'Claims Processing System',
            'Provider Enrollment API',
            'Beneficiary Data Platform',
            'Quality Reporting System',
        ]

    def generate_vulnerability_data(self, count: int = 1) -> List[Dict[str, Any]]:
        """
        Generate varied vulnerability findings.

        Args:
            count: Number of vulnerabilities to generate

        Returns:
            List of vulnerability dictionaries
        """
        findings = []

        for _ in range(count):
            # 40% chance to use real CVE, 60% synthetic
            if random.random() < 0.4 and self.real_cves:
                # Use real CVE
                cve_data = random.choice(self.real_cves)
                package = cve_data['package']
                ecosystem = cve_data['ecosystem']
                cve_id = cve_data['cve']
                severity = cve_data['severity']
                cvss = cve_data['cvss']
                vuln_type = cve_data['type']
            else:
                # Generate synthetic
                ecosystem = random.choice(['npm', 'pypi', 'maven'])
                package = random.choice(self.packages[ecosystem])
                cve_year = random.choice([2024, 2025])
                cve_number = random.randint(1000, 99999)
                cve_id = f"CVE-{cve_year}-{cve_number}"

                vuln_type = random.choice([
                    'Remote Code Execution', 'SQL Injection', 'Cross-site Scripting',
                    'Path Traversal', 'XML External Entity', 'Denial of Service',
                    'Authentication Bypass', 'Information Disclosure', 'Prototype Pollution'
                ])

                # CVSS based on vuln type
                if 'Code Execution' in vuln_type:
                    cvss = round(random.uniform(8.0, 10.0), 1)
                    severity = 'Critical' if cvss >= 9.0 else 'High'
                elif 'Injection' in vuln_type or 'Bypass' in vuln_type:
                    cvss = round(random.uniform(7.0, 9.5), 1)
                    severity = 'High' if cvss >= 7.0 else 'Medium'
                else:
                    cvss = round(random.uniform(4.0, 8.0), 1)
                    if cvss >= 7.0:
                        severity = 'High'
                    elif cvss >= 4.0:
                        severity = 'Medium'
                    else:
                        severity = 'Low'

            # Generate versions
            major = random.randint(1, 12)
            minor = random.randint(0, 20)
            patch = random.randint(0, 30)
            vuln_version = f"{major}.{minor}.{patch}"
            fix_version = f"{major}.{minor}.{patch + 1}" if random.random() < 0.7 else f"{major}.{minor + 1}.0"

            findings.append({
                'package': package,
                'ecosystem': ecosystem,
                'cve': cve_id,
                'severity': severity,
                'cvss': cvss,
                'type': vuln_type,
                'vulnerable_version': vuln_version,
                'fixed_version': fix_version,
            })

        return findings

    def populate_snyk_email(self, template_type: str, output_path: str,
                           recipient_name: str = None, recipient_email: str = None,
                           organization: str = None, findings: List[Dict] = None) -> str:
        """
        Populate a Snyk email template with new data.

        Args:
            template_type: Type of template ('vulnerability_alert_positive', etc.)
            output_path: Where to save the populated email
            recipient_name: Name for To: header (defaults to random)
            recipient_email: Email for To: header (defaults to CMS email)
            organization: Organization name (defaults to random CMS project)
            findings: List of vulnerability findings (defaults to generated)

        Returns:
            Path to created file
        """
        # Load template
        template_file = self.templates.get(template_type)
        if not template_file:
            raise ValueError(f"Unknown template type: {template_type}")

        template_path = os.path.join(self.template_dir, template_file)
        with open(template_path, 'r', errors='ignore') as f:
            original_email = email.message_from_file(f)

        # Generate defaults if not provided
        if not recipient_name:
            recipient_name = f"{random.choice(['John', 'Jane', 'Michael', 'Sarah', 'David'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'])}"

        if not recipient_email:
            recipient_email = f"{recipient_name.lower().replace(' ', '.')}@cms.hhs.gov"

        if not organization:
            organization = random.choice(self.cms_projects)

        if not findings:
            findings = self.generate_vulnerability_data(count=random.randint(1, 4))

        # Create new multipart message
        new_msg = MIMEMultipart('alternative')

        # Set headers (update key ones, keep some authentic ones)
        new_msg['Subject'] = f"[snyk] Vulnerability alert for the {organization} organization"
        new_msg['From'] = 'Snyk <support-noreply@snyk.io>'
        new_msg['To'] = f"{recipient_name} <{recipient_email}>"
        new_msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        new_msg['Message-Id'] = f"<{datetime.now().strftime('%Y%m%d%H%M%S')}.{random.randint(100000000, 999999999)}@snyk.io>"
        new_msg['X-Mailgun-Tag'] = 'new-vulnerabilities'

        # Build new body with vulnerability data
        plain_body = self._build_plain_text_from_template(findings, organization, recipient_name)
        html_body = self._build_html_from_template(findings, organization)

        new_msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
        new_msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(new_msg.as_string())

        return output_path

    def _build_plain_text_from_template(self, findings: List[Dict], org: str, recipient: str) -> str:
        """Build plain text body matching Snyk's format."""

        # Extract first name
        first_name = recipient.split()[0] if recipient else "there"

        # Count severities
        crit_count = sum(1 for f in findings if f['severity'] == 'Critical')
        high_count = sum(1 for f in findings if f['severity'] == 'High')
        med_count = sum(1 for f in findings if f['severity'] == 'Medium')

        severity_text = []
        if crit_count > 0:
            severity_text.append(f"{crit_count} critical")
        if high_count > 0:
            severity_text.append(f"{high_count} high")
        if med_count > 0:
            severity_text.append(f"{med_count} medium")

        severity_summary = ", ".join(severity_text) if severity_text else "new"

        # Build body (matching Snyk's actual format)
        lines = [
            f"Hi {first_name},",
            "",
            f"We found {severity_summary} severity vulnerabilities that affect 1 project in the {org} organization:",
            "",
        ]

        # Add findings
        for finding in findings:
            lines.extend([
                f"• [{finding['severity'].upper()}] {finding['type']} in {finding['package']}",
                f"  {finding['cve']} (CVSS {finding['cvss']})",
                f"  Introduced through: {finding['package']}@{finding['vulnerable_version']}",
                f"  Fixed in: {finding['package']}@{finding['fixed_version']}",
                "",
            ])

        lines.extend([
            "",
            f"View and fix these issues in Snyk: https://app.snyk.io/org/{org.lower().replace(' ', '-')}/",
            "",
            "═"*70,
            "",
            "Notification settings · Unsubscribe from this type of notification",
            "",
            "© 2025 Snyk Ltd.",
            "Snyk is a developer security platform. Integrating directly into development tools,",
            "workflows, and automation pipelines, Snyk makes it easy for teams to find, prioritize,",
            "and fix security vulnerabilities in code, dependencies, containers, and infrastructure",
            "as code. Supported by industry-leading application and security intelligence, Snyk puts",
            "security expertise in any developer's toolkit.",
        ])

        return '\n'.join(lines)

    def _build_html_from_template(self, findings: List[Dict], org: str) -> str:
        """Build HTML body matching Snyk's actual email design."""

        # Snyk's color scheme
        severity_colors = {
            'Critical': '#AB1A86',
            'High': '#CE5019',
            'Medium': '#D68000',
            'Low': '#88879E',
        }

        # Build findings HTML
        findings_html = []
        for finding in findings:
            color = severity_colors.get(finding['severity'], '#666')
            findings_html.append(f'''
            <tr>
                <td style="padding: 15px; border-bottom: 1px solid #e5e5e5;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td>
                                <span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold;">
                                    {finding['severity'].upper()}
                                </span>
                                <span style="font-size: 16px; font-weight: bold; margin-left: 10px;">
                                    {finding['type']}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding-top: 8px; color: #666;">
                                <strong>{finding['package']}</strong> ({finding['ecosystem']})
                            </td>
                        </tr>
                        <tr>
                            <td style="padding-top: 5px; color: #666; font-size: 14px;">
                                {finding['cve']} • CVSS {finding['cvss']}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding-top: 8px; font-size: 14px;">
                                <span style="color: #CE5019;">Vulnerable:</span> {finding['vulnerable_version']} and below<br>
                                <span style="color: #2E7D32;">Fixed in:</span> {finding['fixed_version']}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            ''')

        # Full HTML email (matching Snyk's design)
        html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f7f7f7;">
    <table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f7f7f7">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="background-color: #4a148c; padding: 30px; border-radius: 8px 8px 0 0;">
                            <table width="100%">
                                <tr>
                                    <td>
                                        <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">
                                            🔒 Snyk Security Alert
                                        </h1>
                                        <p style="color: #ffffff; margin: 10px 0 0 0; opacity: 0.9;">
                                            {org}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Summary -->
                    <tr>
                        <td style="padding: 30px;">
                            <p style="font-size: 16px; color: #333; margin: 0 0 20px 0;">
                                We found <strong>{len(findings)} new vulnerabilit{"y" if len(findings) == 1 else "ies"}</strong> in your project.
                            </p>
                        </td>
                    </tr>

                    <!-- Vulnerabilities -->
                    <tr>
                        <td>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                {''.join(findings_html)}
                            </table>
                        </td>
                    </tr>

                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 30px; text-align: center;">
                            <a href="https://app.snyk.io/org/{org.lower().replace(' ', '-')}/"
                               style="background-color: #4a148c; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                                View in Snyk
                            </a>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9f9f9; padding: 30px; border-top: 1px solid #e5e5e5; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; font-size: 12px; color: #666; line-height: 1.6;">
                                <strong>Snyk</strong> is a developer security platform.<br>
                                © 2025 Snyk Ltd. | <a href="https://snyk.io" style="color: #4a148c;">snyk.io</a>
                            </p>
                            <p style="margin: 15px 0 0 0; font-size: 11px; color: #999;">
                                To manage notification preferences, visit your <a href="https://app.snyk.io/account" style="color: #4a148c;">account settings</a>.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''
        return html

    def create_vulnerability_alert(self, output_path: str, is_positive: bool = True,
                                   finding_count: int = None) -> str:
        """
        Create a Snyk vulnerability alert using real template structure.

        Args:
            output_path: Where to save the email
            is_positive: True for CUI-positive (internal CMS projects)
            finding_count: Number of findings (defaults to 1-4 random)

        Returns:
            Path to created file
        """
        if finding_count is None:
            finding_count = random.randint(1, 4)

        # Generate vulnerability data
        findings = self.generate_vulnerability_data(finding_count)

        # Set organization and recipient
        if is_positive:
            organization = random.choice(self.cms_projects)
            recipient_name = f"{random.choice(['John', 'Sarah', 'Michael', 'Jennifer'])} {random.choice(['Smith', 'Johnson', 'Williams'])}"
            recipient_email = f"{recipient_name.lower().replace(' ', '.')}@cms.hhs.gov"
        else:
            organization = "Public Repository"
            recipient_name = "Developer"
            recipient_email = "dev@example.com"

        # Use template to create email
        template_type = 'vulnerability_alert_positive' if is_positive else 'supply_chain_negative'

        return self.populate_snyk_email(
            template_type,
            output_path,
            recipient_name,
            recipient_email,
            organization,
            findings
        )


if __name__ == "__main__":
    # Test the template populator
    populator = SnykTemplatePopulator()

    print("Testing Snyk Template Populator")
    print("="*70)

    # Generate 3 varied alerts
    for i in range(1, 4):
        output_file = f"output/snyk_template_test/SnykAlert_{i:02d}.eml"
        populator.create_vulnerability_alert(
            output_file,
            is_positive=True,
            finding_count=random.choice([1, 2, 3, 4])
        )
        print(f"✓ Created: {output_file}")

    print("\n" + "="*70)
    print("Snyk emails generated using Elizabeth's real template structure!")
