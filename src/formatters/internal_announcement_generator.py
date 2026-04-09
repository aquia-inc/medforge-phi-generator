"""
Internal announcement email generator for CUI Proprietary.

Produces realistic CMS internal newsletter and announcement emails
("Things to Know", weekly digests, leadership messages) with internal-only
links (CUI-positive) or public links (CUI-negative).
"""
import random
from datetime import datetime, timedelta
from typing import Optional

from faker import Faker

from formatters.base_email_formatter import BaseEmailFormatter


class InternalAnnouncementGenerator(BaseEmailFormatter):
    """Generates CMS internal announcement and newsletter emails."""

    # --- Sender personas ---

    CMS_COMM_SENDERS = [
        ('CMS Office of Communications', 'communications@cms.hhs.gov'),
        ('CMS Weekly Digest', 'digest@cms.hhs.gov'),
        ('CMS Internal Communications', 'internal-comms@cms.hhs.gov'),
        ('OIT Communications', 'oit-comms@cms.hhs.gov'),
    ]

    CMS_LEADERSHIP_TITLES = [
        'Chief Information Officer',
        'Chief Information Security Officer',
        'Deputy Administrator',
        'Director, Office of Information Technology',
        'Director, Center for Medicare',
        'Chief Operating Officer',
        'Chief Financial Officer',
    ]

    # --- Topic templates (positive = internal, negative = public) ---

    TOPICS_POSITIVE = {
        'budget': [
            ('FY{fy} Budget Guidance Update',
             'The Office of Financial Management has released updated budget guidance for FY{fy}. All divisions must submit revised estimates by {deadline}. Contact your budget liaison for the updated templates.'),
            ('Spending Freeze Reminder — Q{q} Closeout',
             'As we approach the Q{q} closeout, please ensure all outstanding obligations are recorded in UFMS. No new commitments without OFM approval until further notice.'),
            ('AFR Submission Deadline Extended',
             'The deadline for Additional Funds Requests has been extended to {deadline}. Submit via the standard AFR template on SharePoint.'),
        ],
        'it_security': [
            ('Scheduled Maintenance: {system} — {date}',
             '{system} will be unavailable from 10:00 PM to 2:00 AM ET on {date} for scheduled maintenance. Save all work before the maintenance window.'),
            ('MFA Enrollment Required by {deadline}',
             'All CMS staff must complete multi-factor authentication enrollment by {deadline}. Instructions are available on the EUA portal. Contact the OIT Help Desk for assistance.'),
            ('VPN Configuration Change — Action Required',
             'OIT is updating the CMS VPN configuration effective {date}. You must download the updated Cisco AnyConnect profile from the OIT self-service portal before {deadline}.'),
        ],
        'personnel': [
            ('Leadership Change: {office}',
             '{name} has been appointed as the new {title} for {office}, effective {date}. Please join us in welcoming {name} to the team.'),
            ('Organizational Restructure — {office}',
             'Effective {date}, {office} will reorganize into three branches. Details and the updated org chart are available on the CMS intranet.'),
            ('Hiring Update: Open Positions in {office}',
             '{office} has {count} open positions for FY{fy}. Internal candidates are encouraged to apply through USA Staffing by {deadline}.'),
        ],
        'policy': [
            ('Updated Telework Policy Effective {date}',
             'The revised CMS telework policy takes effect {date}. Key changes include updated core hours and new documentation requirements. Review the full policy on SharePoint.'),
            ('Travel Authorization Reminder',
             'All domestic travel requires pre-approval through Concur at least 14 days in advance. International travel requires 30 days and CISO review. See the updated travel SOP on the intranet.'),
            ('Procurement Guidance: New Threshold for Micro-Purchases',
             'Effective immediately, the micro-purchase threshold has been updated to ${threshold}. All purchases above this amount require a purchase order. Refer to the OAGM procurement guide.'),
        ],
        'program': [
            ('Medicare Open Enrollment Data — Internal Only',
             'Preliminary Medicare Open Enrollment numbers are attached for internal review only. Do not share externally until the official press release on {date}.'),
            ('CMCS Data Sharing MOU — Action Items',
             'The data sharing MOU between CMCS and {partner} has been finalized. System owners must update their data flow documentation by {deadline}.'),
            ('Quality Payment Program Update',
             'QPP reporting for performance year {fy} closes on {deadline}. The MIPS data validation team has identified {count} providers requiring outreach.'),
        ],
        'training': [
            ('Mandatory: Annual Security Awareness Training Due {deadline}',
             'All CMS employees and contractors must complete the FY{fy} Security Awareness Training in the CMS LMS by {deadline}. Non-compliance will be reported to supervisors.'),
            ('New Course Available: {course}',
             'A new training course "{course}" is now available in the CMS Learning Management System. This course is recommended for all {office} staff.'),
            ('Compliance Training Reminder',
             'Your annual Records Management training is overdue. Please complete it in the LMS by {deadline} to avoid escalation to your supervisor.'),
        ],
    }

    TOPICS_NEGATIVE = {
        'budget': [
            ('CMS FY{fy} Budget Request Published',
             'The CMS FY{fy} budget request has been published and is available for public review. Visit CMS.gov for the full document.'),
        ],
        'it_security': [
            ('CMS IT Modernization Progress Report',
             'CMS has published its annual IT modernization progress report. The report highlights investments in cloud services and cybersecurity improvements.'),
        ],
        'personnel': [
            ('CMS Career Opportunities',
             'CMS is hiring across multiple divisions. View current openings and apply through USAJobs.gov.'),
        ],
        'policy': [
            ('CMS Final Rule Published in Federal Register',
             'CMS has published a final rule updating Medicare payment policies. The rule is effective 60 days from publication. Public comments are no longer being accepted.'),
        ],
        'program': [
            ('Medicare Open Enrollment: What Beneficiaries Need to Know',
             'Medicare Open Enrollment runs from October 15 to December 7. Beneficiaries can compare plans and make changes at Medicare.gov.'),
        ],
        'training': [
            ('Free CMS Webinar: Health Equity in Medicare',
             'CMS is hosting a free public webinar on health equity initiatives. Register at CMS.gov/events.'),
        ],
    }

    # --- Link pools ---

    INTERNAL_LINK_TEMPLATES = [
        'https://share.cms.gov/center/{office}/SitePages/{page}.aspx',
        'https://jira.cms.gov/browse/{office}-{ticket}',
        'https://confluence.cms.gov/display/{office}/{page}',
        'https://cms.sharepoint.com/sites/{office}/Shared%20Documents/{doc}',
        'https://cmsintranet.cms.gov/announcements/{slug}',
        'https://eua.cms.gov/eidm/authenticate?target={path}',
        'https://cfacts.cms.gov/apps/ito/{page}',
        'https://hpms.cms.gov/app/ng/{page}',
        'https://lms.cms.gov/course/{course_id}',
    ]

    PUBLIC_LINK_TEMPLATES = [
        'https://www.cms.gov/newsroom/press-releases/{slug}',
        'https://www.hhs.gov/about/news/{year}/{month}/{slug}',
        'https://www.federalregister.gov/documents/{year}/{month}/{day}/{doc_id}',
        'https://sam.gov/content/{page}',
        'https://www.usajobs.gov/job/{job_id}',
        'https://www.medicare.gov/{page}',
        'https://data.cms.gov/provider-data/{dataset}',
    ]

    CMS_OFFICES = ['OIT', 'OAGM', 'CMCS', 'CCIIO', 'CM', 'OFM', 'OA', 'OC', 'OL']

    COURSES = [
        'Zero Trust Architecture Fundamentals',
        'CMS Records Management',
        'Incident Response Procedures',
        'Section 508 Compliance',
        'FISMA Continuous Monitoring',
        'Agile Development at CMS',
        'Cloud Security Best Practices',
    ]

    def __init__(self, output_dir: str = 'output',
                 llm_generator=None, llm_percentage: float = 0.2):
        super().__init__(output_dir)
        self.fake = Faker('en_US')
        self.llm_generator = llm_generator
        self.llm_percentage = llm_percentage

    def _fill_template(self, template: str) -> str:
        """Fill placeholder tokens in a topic template string."""
        fy = random.randint(25, 27)
        office = random.choice(self.CMS_OFFICES)
        deadline = self.fake.date_between(start_date='+7d', end_date='+90d').strftime('%B %-d, %Y')
        date = self.fake.date_between(start_date='+1d', end_date='+60d').strftime('%B %-d, %Y')
        return template.format(
            fy=fy, q=random.randint(1, 4), deadline=deadline, date=date,
            system=random.choice(['EIDM', 'HPMS', 'CFACTS', 'QPP Portal', 'MACPro', 'UFMS']),
            office=office, name=self.fake.name(),
            title=random.choice(self.CMS_LEADERSHIP_TITLES),
            partner=random.choice(['SSA', 'IRS', 'OIG', 'GAO', 'OMB']),
            count=random.randint(3, 25), threshold=random.choice(['10,000', '25,000', '50,000']),
            course=random.choice(self.COURSES),
        )

    def _generate_link(self, is_positive: bool) -> str:
        """Generate a single realistic link."""
        if is_positive:
            template = random.choice(self.INTERNAL_LINK_TEMPLATES)
            return template.format(
                office=random.choice(self.CMS_OFFICES),
                page=self.fake.slug(),
                ticket=random.randint(1000, 9999),
                doc=self.fake.file_name(extension='pdf'),
                slug=self.fake.slug(),
                path=self.fake.uri_path(),
                course_id=f"CMS-{random.randint(100, 999)}",
            )
        else:
            template = random.choice(self.PUBLIC_LINK_TEMPLATES)
            return template.format(
                slug=self.fake.slug(),
                year=random.randint(2024, 2026),
                month=f"{random.randint(1,12):02d}",
                day=f"{random.randint(1,28):02d}",
                doc_id=f"{random.randint(2024,2026)}-{random.randint(10000,99999)}",
                page=self.fake.slug(),
                job_id=f"{random.randint(700000000, 799999999)}",
                dataset=self.fake.slug(),
            )

    def _generate_items(self, count: int, is_positive: bool) -> list:
        """Generate a list of announcement items."""
        topics = self.TOPICS_POSITIVE if is_positive else self.TOPICS_NEGATIVE
        categories = list(topics.keys())
        items = []
        for _ in range(count):
            cat = random.choice(categories)
            headline_template, summary_template = random.choice(topics[cat])
            headline = self._fill_template(headline_template)
            summary = self._fill_template(summary_template)
            links = [self._generate_link(is_positive) for _ in range(random.randint(1, 2))]
            items.append({'headline': headline, 'summary': summary, 'links': links})
        return items

    def _build_digest_body(self, items: list, week_date: str) -> str:
        """Build a weekly digest email body."""
        lines = [f"CMS Things to Know — Week of {week_date}", "=" * 50, ""]
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item['headline']}")
            lines.append(f"   {item['summary']}")
            for link in item['links']:
                lines.append(f"   More info: {link}")
            lines.append("")
        lines.append("---")
        lines.append("CMS Office of Communications | 7500 Security Blvd, Baltimore, MD 21244")
        lines.append("To unsubscribe from this digest, update your preferences in the CMS intranet portal.")
        return "\n".join(lines)

    def _build_single_body(self, item: dict, sender_name: str, sender_title: str) -> str:
        """Build a single-announcement email body."""
        lines = [
            f"Dear CMS Staff,",
            "",
            item['summary'],
            "",
        ]
        for link in item['links']:
            lines.append(f"Details: {link}")
        lines.append("")
        lines.append(f"Thank you,")
        lines.append(f"{sender_name}")
        lines.append(f"{sender_title}")
        lines.append("Centers for Medicare & Medicaid Services")
        return "\n".join(lines)

    def _build_leadership_body(self, items: list, leader_name: str,
                                leader_title: str) -> str:
        """Build a leadership message email body."""
        lines = [
            f"Team,",
            "",
            f"I wanted to share a few important updates with you this week.",
            "",
        ]
        for item in items:
            lines.append(f"**{item['headline']}**")
            lines.append(f"{item['summary']}")
            for link in item['links']:
                lines.append(f"  {link}")
            lines.append("")
        lines.append("Please don't hesitate to reach out to your division lead if you have questions.")
        lines.append("")
        lines.append(f"Best regards,")
        lines.append(f"{leader_name}")
        lines.append(f"{leader_title}")
        lines.append("Centers for Medicare & Medicaid Services")
        return "\n".join(lines)

    def create_announcement_email(self, filename: str, is_positive: bool = True) -> str:
        """Create an internal announcement email.

        Args:
            filename: Output filename
            is_positive: True for CUI-positive (internal links), False for public

        Returns:
            Path to saved EML file
        """
        # Pick variant
        roll = random.random()
        if roll < 0.5:
            variant = 'digest'
        elif roll < 0.8:
            variant = 'single'
        else:
            variant = 'leadership'

        week_date = self.fake.date_between(
            start_date='-30d', end_date='+7d').strftime('%B %-d, %Y')

        if variant == 'digest':
            items = self._generate_items(random.randint(3, 6), is_positive)
            subject = f"CMS Things to Know — Week of {week_date}"
            body = self._build_digest_body(items, week_date)
            sender_name, sender_email = random.choice(self.CMS_COMM_SENDERS)
            from_addr = f"{sender_name} <{sender_email}>"
        elif variant == 'single':
            items = self._generate_items(1, is_positive)
            sender_name = self.fake.name()
            sender_title = random.choice(self.CMS_LEADERSHIP_TITLES)
            subject = f"Important: {items[0]['headline']}"
            body = self._build_single_body(items[0], sender_name, sender_title)
            first = sender_name.split()[0].lower()
            last = sender_name.split()[-1].lower()
            from_addr = f"{sender_name} <{first}.{last}@cms.hhs.gov>"
        else:  # leadership
            items = self._generate_items(random.randint(2, 4), is_positive)
            leader_name = self.fake.name()
            leader_title = random.choice(self.CMS_LEADERSHIP_TITLES)
            subject = f"Message from the {leader_title}: Weekly Update"
            body = self._build_leadership_body(items, leader_name, leader_title)
            first = leader_name.split()[0].lower()
            last = leader_name.split()[-1].lower()
            from_addr = f"{leader_name} <{first}.{last}@cms.hhs.gov>"

        # Recipient
        if is_positive:
            to_addr = random.choice([
                'cms-all-staff@cms.hhs.gov',
                f"{random.choice(self.CMS_OFFICES).lower()}-staff@cms.hhs.gov",
                'cms-it-staff@cms.hhs.gov',
            ])
        else:
            to_addr = random.choice([
                'public-updates@cms.gov',
                'cms-news@cms.gov',
                'subscribers@cms.gov',
            ])

        return self._build_and_save_email(
            subject=subject,
            from_addr=from_addr,
            to_addr=to_addr,
            plain_body=body,
            filename=filename,
            message_id_domain='cms.hhs.gov',
        )
