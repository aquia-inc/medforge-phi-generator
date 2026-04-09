"""
ServiceNow ticket notification email generator.

Produces realistic CMS ServiceNow (CMSConnect) ticket notification emails
with randomized ticket numbers, request items, and assignment details.
Supports CUI-positive (internal system details) and CUI-negative (generic IT requests).
"""
import random
from typing import Optional

from faker import Faker

from formatters.base_email_formatter import BaseEmailFormatter


class ServiceNowEmailGenerator(BaseEmailFormatter):
    """Generates varied ServiceNow ticket notification emails."""

    # Ticket number prefixes and ranges
    REQ_PREFIX = 'REQ'
    RITM_PREFIX = 'RITM'
    INC_PREFIX = 'INC'
    CHG_PREFIX = 'CHG'

    # CUI-positive: internal CMS system requests (contain system names, internal details)
    CMS_REQUEST_ITEMS = [
        ('CMS VPN Access Request', 'Network access provisioning for CMS internal systems'),
        ('EIDM Account Modification', 'Enterprise Identity Management account role change'),
        ('HPMS Access Request', 'Health Plan Management System access for plan oversight'),
        ('CFACTS System Access', 'CyberFramework system access for security assessments'),
        ('MACPro Access Request', 'Medicaid and CHIP Program system access'),
        ('QPP Portal Access', 'Quality Payment Program portal access for reporting'),
        ('CMS 508 App Testing', 'Section 508 compliance testing for CMS application'),
        ('AWS GovCloud Provisioning', 'Cloud infrastructure provisioning in CMS AWS environment'),
        ('Confluence Space Creation', 'Internal wiki space creation for project documentation'),
        ('JIRA Project Setup', 'Issue tracking project setup for CMS development team'),
        ('PIV Card Replacement', 'Personal Identity Verification card replacement request'),
        ('Privileged Access Request', 'Elevated access request for system administration'),
        ('Firewall Rule Change', 'Network firewall modification for CMS internal traffic'),
        ('SSL Certificate Renewal', 'TLS certificate renewal for CMS internal service'),
        ('Database Access Request', 'Production database read access for reporting'),
        ('Service Account Creation', 'Automated service account for system integration'),
        ('Software Installation Request', 'Approved software deployment to CMS workstation'),
        ('Shared Mailbox Creation', 'Exchange shared mailbox for team communications'),
        ('Security Scan Request', 'Vulnerability scan for CMS application deployment'),
        ('Incident Report Submission', 'Security incident report for CISO review'),
    ]

    # CUI-negative: generic IT requests (no internal system names)
    GENERIC_REQUEST_ITEMS = [
        ('Password Reset', 'Standard password reset for user account'),
        ('New Employee Onboarding', 'Standard IT setup for new employee'),
        ('Monitor Request', 'Additional display monitor for workstation'),
        ('Keyboard/Mouse Replacement', 'Peripheral equipment replacement'),
        ('Conference Room AV Setup', 'Audio-visual equipment configuration'),
        ('Printer Access', 'Network printer access configuration'),
        ('Software License Request', 'Standard software license procurement'),
        ('Email Distribution List', 'Creation of email distribution group'),
        ('File Share Access', 'Network shared drive access request'),
        ('Laptop Refresh', 'Standard laptop refresh cycle replacement'),
    ]

    # Notification types
    NOTIFICATION_TYPES = [
        ('opened', 'has been opened', 'An agent will follow up with you shortly to provide further assistance if required.'),
        ('assigned', 'has been assigned', 'Your request has been assigned to a support agent who will begin working on it.'),
        ('updated', 'has been updated', 'Your request has been updated. Please review the latest notes for details.'),
        ('resolved', 'has been resolved', 'Your request has been resolved. If you have any concerns, please respond to this email within 5 business days.'),
        ('closed', 'has been closed', 'Your request has been closed. If you need additional assistance, please submit a new request through the CMSConnect portal.'),
        ('pending', 'is pending your approval', 'Action is required from you. Please log in to the CMSConnect portal to review and approve this request.'),
    ]

    CMS_SUPPORT_DESKS = [
        'End User Support Desk',
        'CMS IT Service Desk',
        'OIT Help Desk',
        'Enterprise Service Desk',
    ]

    def __init__(self, output_dir: str = 'output',
                 llm_generator=None, llm_percentage: float = 0.2):
        super().__init__(output_dir)
        self.fake = Faker('en_US')
        self.llm_generator = llm_generator
        self.llm_percentage = llm_percentage

    def _ticket_number(self, prefix: str) -> str:
        return f"{prefix}{random.randint(100000, 9999999):07d}"

    def create_servicenow_notification(self, filename: str,
                                        is_positive: bool = True) -> str:
        """Create a ServiceNow ticket notification email.

        Args:
            filename: Output filename
            is_positive: True for CUI-positive (CMS internal systems), False for generic

        Returns:
            Path to saved EML file
        """
        # Pick notification type
        notif_type, status_phrase, followup = random.choice(self.NOTIFICATION_TYPES)

        # Generate ticket numbers
        req_number = self._ticket_number(self.REQ_PREFIX)

        # Pick request item
        if is_positive:
            item_name, item_desc = random.choice(self.CMS_REQUEST_ITEMS)
        else:
            item_name, item_desc = random.choice(self.GENERIC_REQUEST_ITEMS)

        # Determine ticket type (REQ for requests, INC for incidents, CHG for changes)
        if 'Incident' in item_name or 'Security' in item_name:
            ticket_prefix = self.INC_PREFIX
        elif 'Firewall' in item_name or 'Change' in item_name:
            ticket_prefix = self.CHG_PREFIX
        else:
            ticket_prefix = self.RITM_PREFIX
        ritm_number = self._ticket_number(ticket_prefix)

        # Generate recipient
        first = self.fake.first_name()
        last = self.fake.last_name()
        recipient_email = f"{first.lower()}.{last.lower()}@cms.hhs.gov"

        # Build subject
        subject = f"Ticket #{req_number} {status_phrase}"

        # Build body
        desk = random.choice(self.CMS_SUPPORT_DESKS)
        ref_id = f"MSG{random.randint(10000000, 99999999)}"

        lines = [
            f"{first} {last},",
            "",
            f"Thank you for contacting the {desk}.",
            f"Your request {req_number} has generated the following item:",
            "",
            f"  {ritm_number}: {item_name}",
            "",
        ]

        # Add detail for some notification types
        if notif_type == 'assigned':
            agent = self.fake.name()
            lines.append(f"Assigned to: {agent}")
            lines.append(f"Priority: {random.choice(['Low', 'Medium', 'High', 'Critical'])}")
            lines.append("")
        elif notif_type == 'updated':
            lines.append(f"Latest update: {item_desc}")
            lines.append(f"Status: In Progress")
            lines.append("")
        elif notif_type == 'resolved':
            lines.append(f"Resolution: {item_desc} — completed successfully.")
            lines.append("")

        lines.append(followup)
        lines.append("")
        lines.append("If you should have any additional questions or concerns, please respond to this email.")
        lines.append("")
        lines.append("Thank you,")
        lines.append("")
        lines.append(desk)
        lines.append("")
        lines.append(f"Ref:{ref_id}")

        body = "\n".join(lines)

        return self._build_and_save_email(
            subject=subject,
            from_addr='CMSConnect <CMSITSM@cms.hhs.gov>',
            to_addr=f"<{recipient_email}>",
            plain_body=body,
            filename=filename,
            message_id_domain='cms.hhs.gov',
        )
