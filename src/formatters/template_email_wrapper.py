"""
Template email wrapper.

Wraps customer template files (DOCX, PDF, XLSX) in realistic
CMS emails as attachments, with varying levels of body detail
for Purview classifier training.
"""
import os
import random
from typing import Dict, Any, Optional, Tuple
from faker import Faker

from formatters.base_email_formatter import BaseEmailFormatter


class TemplateEmailWrapper(BaseEmailFormatter):
    """Wraps customer template files in emails as attachments."""

    SUBTYPE_MAP = {
        '.pdf': 'pdf',
        '.docx': 'vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pptx': 'vnd.openxmlformats-officedocument.presentationml.presentation',
        '.zip': 'zip',
    }

    MINIMAL_PHRASES = [
        'See attached.',
        'FYI.',
        'Per our earlier discussion.',
        'For your review.',
        'Please see the attached document.',
        'Attached for your records.',
        'As discussed.',
        'Please review at your convenience.',
    ]

    MINIMAL_SUBJECTS = [
        'FYI - {clean_name}',
        '{clean_name}',
        'Attached: {clean_name}',
        'FYI',
        '{clean_name} - For Your Records',
    ]

    CMS_TITLES = [
        'Contracting Officer', 'Program Manager', 'COR',
        'Branch Chief', 'Division Director', 'Team Lead',
        'ISSO', 'Budget Analyst', 'IT Specialist',
        'FOIA Officer', 'Security Engineer', 'Policy Analyst',
    ]

    CMS_OFFICES = ['OIT', 'OAGM', 'CMCS', 'CCIIO', 'CM', 'OFM', 'OA']

    # Category-specific medium-tier body templates.
    # Each template can reference keys from the faker data dict.
    MEDIUM_TEMPLATES = {
        'procurement': [
            "Hi team,\n\nAttached is the {clean_name} for your review. Please provide any comments or edits by end of week.\n\nThanks,\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
            "Good afternoon,\n\nPlease find the attached {clean_name}. This document is ready for routing and signature.\n\nRegards,\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
            "All,\n\nThe {clean_name} has been updated per the latest guidance. Attached for your review and concurrence.\n\nBest,\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
            "Hi,\n\nAttaching the {clean_name} as discussed in yesterday's meeting. Let me know if you have questions.\n\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
        ],
        'legal': [
            "Good morning,\n\nAttached is the {clean_name} for processing. Please review and route through the appropriate channels.\n\nThank you,\n{sender_name}\n{sender_title}\nFreedom of Information Group, CMS",
            "Hi,\n\nPlease find the attached {clean_name}. This response is ready for final review before mailing.\n\nRegards,\n{sender_name}\n{sender_title}\nFreedom of Information Group, CMS",
            "Team,\n\nThe {clean_name} is attached for your records. Please file accordingly.\n\nThanks,\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
        ],
        'financial': [
            "Hi team,\n\nAttached is the {clean_name} for the current fiscal year. Please review the funding details and confirm accuracy.\n\nThanks,\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
            "Good afternoon,\n\nPlease find the {clean_name} attached. This has been updated with the latest cost figures. Let me know if adjustments are needed.\n\nRegards,\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
            "All,\n\nThe {clean_name} is ready for submission. Attached for your review before we route to leadership.\n\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
        ],
        'critical_infrastructure': [
            "Hi team,\n\nAttached is the updated {clean_name}. Please review and confirm all information is current before the assessment deadline.\n\nThanks,\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
            "Good morning,\n\nPlease find the {clean_name} attached for your review. This document is due for annual renewal.\n\nRegards,\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
            "Team,\n\nThe {clean_name} has been completed and is attached. Please file with the system security package.\n\n{sender_name}\n{sender_title}\n{sender_office}, CMS",
        ],
    }

    MEDIUM_SUBJECTS = [
        '{clean_name} - For Review',
        '{clean_name} - Action Required',
        'Updated {clean_name}',
        '{clean_name} - Please Review',
        'RE: {clean_name}',
    ]

    def __init__(self, output_dir: str = 'output', seed: int = None):
        super().__init__(output_dir)
        self.fake = Faker('en_US')
        if seed:
            Faker.seed(seed)

    def _get_sender(self) -> Tuple[str, str, str, str]:
        """Generate a realistic CMS sender. Returns (name, email, title, office)."""
        name = self.fake.name()
        first = name.split()[0].lower()
        last = name.split()[-1].lower()
        email = f"{first}.{last}@cms.hhs.gov"
        title = random.choice(self.CMS_TITLES)
        office = random.choice(self.CMS_OFFICES)
        return name, email, title, office

    def _get_recipient(self) -> Tuple[str, str]:
        """Generate a realistic CMS recipient. Returns (name, email)."""
        name = self.fake.name()
        first = name.split()[0].lower()
        last = name.split()[-1].lower()
        email = f"{first}.{last}@cms.hhs.gov"
        return name, email

    def _minimal_body(self, clean_name: str) -> Tuple[str, str]:
        """Generate a minimal (stub) email subject and body."""
        subject = random.choice(self.MINIMAL_SUBJECTS).format(clean_name=clean_name)
        body = random.choice(self.MINIMAL_PHRASES)
        return subject, body

    def _medium_body(self, clean_name: str, category: str,
                     sender_name: str, sender_title: str,
                     sender_office: str) -> Tuple[str, str]:
        """Generate a medium-detail email subject and body from category templates."""
        templates = self.MEDIUM_TEMPLATES.get(category, self.MEDIUM_TEMPLATES['procurement'])
        template = random.choice(templates)
        body = template.format(
            clean_name=clean_name,
            sender_name=sender_name,
            sender_title=sender_title,
            sender_office=sender_office,
        )
        subject = random.choice(self.MEDIUM_SUBJECTS).format(clean_name=clean_name)
        return subject, body

    def wrap(self, template_path: str, template_key: str,
             clean_name: str, category: str,
             subject: str, body: str,
             output_dir: str, index: int) -> str:
        """Wrap a template file in an email as an attachment.

        Args:
            template_path: Path to the generated template file on disk
            template_key: Template identifier (e.g. 'AcquisitionPlan')
            clean_name: Human-readable template name
            category: CUI category (e.g. 'procurement')
            subject: Email subject line
            body: Email body text
            output_dir: Directory to save the .eml file
            index: Document index for filename

        Returns:
            Path to the saved .eml file
        """
        # Read the template file
        ext = os.path.splitext(template_path)[1].lower()
        subtype = self.SUBTYPE_MAP.get(ext, 'octet-stream')
        att_filename = os.path.basename(template_path)

        with open(template_path, 'rb') as f:
            att_data = f.read()

        # Build sender/recipient
        sender_name, sender_email, _, _ = self._get_sender()
        _, recipient_email = self._get_recipient()

        from_addr = f"{sender_name} <{sender_email}>"
        to_addr = recipient_email

        # Build and save the email
        eml_filename = f"{clean_name}_{index:04d}.eml"
        self.output_dir = output_dir

        return self._build_and_save_email(
            subject=subject,
            from_addr=from_addr,
            to_addr=to_addr,
            plain_body=body,
            attachments=[(att_data, att_filename, subtype)],
            filename=eml_filename,
            message_id_domain='cms.hhs.gov',
        )
