"""
PDF Form Field Populator

Populates fillable PDF forms with synthetic data using Faker.
Works with customer-provided CMS template forms.
"""
import logging
import pikepdf
from faker import Faker
import random
import os
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PDFFormPopulator:
    """Populates fillable PDF forms with synthetic data."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize with optional random seed."""
        self.fake = Faker('en_US')
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    def populate_form(self, template_path: str, output_path: str, field_data: Dict[str, Any],
                      field_positions: Optional[Dict[str, tuple]] = None) -> str:
        """
        Populate a PDF form with synthetic data.

        Args:
            template_path: Path to blank PDF template
            output_path: Path to save populated PDF
            field_data: Dictionary mapping field names to values
            field_positions: Optional dict mapping field names to (x, y) coordinates.
                           If None, uses default Reasonable Accommodation positions.

        Returns:
            Path to created file
        """
        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Use reportlab to overlay text on template PDF (only way that renders everywhere)
        primary_error = None
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from io import BytesIO
            from PyPDF2 import PdfReader, PdfWriter

            # Create overlay with text
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            # Use provided positions or default Reasonable Accommodation form positions
            if field_positions is None:
                field_positions = {
                    'Name': (145, 620),
                    'Component': (145, 596),
                    'Telephone number': (180, 574),
                    'Location': (200, 548),
                    'Grade': (150, 525),
                    'Date of Birth': (147, 501),
                    'Manager': (130, 476),
                    'Discription': (88, 380),  # Large text area
                }

            # Draw text on PDF
            can.setFont("Helvetica", 10)
            for field_name, value in field_data.items():
                if field_name in field_positions and value and value not in [True, False]:
                    x, y = field_positions[field_name]
                    can.drawString(x, y, str(value)[:80])

            can.save()
            packet.seek(0)

            # Overlay on template
            overlay = PdfReader(packet)
            template = PdfReader(template_path)
            output = PdfWriter()

            # Merge overlay with template
            page = template.pages[0]
            page.merge_page(overlay.pages[0])
            output.add_page(page)

            # Add remaining pages if any
            for i in range(1, len(template.pages)):
                output.add_page(template.pages[i])

            # Write
            with open(output_path, 'wb') as f:
                output.write(f)

        except ImportError as e:
            logger.warning("reportlab/PyPDF2 not installed, using pikepdf fallback: %s", e)
            primary_error = e
        except Exception as e:
            logger.warning("reportlab overlay failed for %s: %s", template_path, e)
            primary_error = e

        if primary_error is None:
            return output_path

        # Fallback: use pikepdf to set form field values.
        # NOTE: pikepdf form field values are NOT extractable by SharePoint/Purview
        # text indexers. This fallback produces viewer-visible but non-indexable text.
        try:
            pdf = pikepdf.open(template_path)

            if '/AcroForm' in pdf.Root and '/Fields' in pdf.Root.AcroForm:
                for field in pdf.Root.AcroForm.Fields:
                    field_name = str(field.T) if '/T' in field else None

                    if field_name and field_name in field_data:
                        value = field_data[field_name]

                        if value is True:
                            field['/V'] = pikepdf.Name('/On')
                        elif value is False:
                            field['/V'] = pikepdf.Name('/Off')
                        else:
                            field['/V'] = str(value) if value else ''

                        if '/AP' in field:
                            del field['/AP']

                pdf.Root.AcroForm['/NeedAppearances'] = True

            pdf.save(output_path)
            pdf.close()
            logger.warning(
                "Used pikepdf fallback for %s -- form field data may not be "
                "extractable by Purview/SharePoint text indexers", output_path
            )

        except Exception as e2:
            logger.error(
                "Both reportlab and pikepdf failed for %s: %s / %s",
                template_path, primary_error, e2
            )
            raise RuntimeError(
                f"Cannot populate PDF form {template_path}: "
                f"reportlab error: {primary_error}, pikepdf error: {e2}"
            ) from e2

        return output_path

    def generate_medical_inquiry_data(self) -> Dict[str, Any]:
        """Generate data for Medical Inquiry Form (PHI)."""

        # Generate employee/patient info
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        employee_name = f"{first_name} {last_name}"

        # Medical impairment options
        impairments = [
            "Severe latex allergy with contact dermatitis and respiratory symptoms",
            "Chronic lower back pain with limited mobility and sitting tolerance",
            "Type 1 Diabetes requiring insulin management and dietary modifications",
            "Severe asthma requiring inhaler use and environmental controls",
            "Rheumatoid arthritis affecting hand function and fine motor tasks",
            "Hearing loss requiring hearing aids and communication accommodations",
            "Visual impairment requiring screen reader and magnification software",
            "Chronic migraine disorder triggered by fluorescent lighting and stress",
        ]

        impairment = random.choice(impairments)

        # Duration options
        durations = ["permanent", "6 months", "1 year", "2 years", "indefinite"]
        duration = random.choice(durations)

        # Suggestions for accommodations
        accommodation_suggestions = [
            "Modified work schedule, ergonomic workstation, alternative lighting",
            "Flexible break schedule, accessible workspace location",
            "Remote work option 2-3 days per week, modified hours",
            "Assistive technology, adjusted performance standards",
            "Environmental modifications, alternative duty assignments",
        ]

        # Provider info
        provider_name = f"Dr. {self.fake.last_name()}, MD"

        # Major life activities - randomly select 2-4
        activities = {
            'Caring For Self': False,
            'Walking': False,
            'Hearing': False,
            'Lifting': False,
            'Interacting With Others': False,
            'Standing': False,
            'Seeing': False,
            'Sleeping': False,
            'Performing Manual Tasks': False,
            'Reaching': False,
            'Speaking': False,
            'Concentrating': False,
            'Breathing': False,
            'Thinking': False,
            'Learning': False,
            'Reproduction': False,
            'Working': False,
            'Toileting': False,
            'Sitting': False,
        }

        # Force 2-4 activities to be selected
        activities_list = list(activities.keys())
        for _ in range(random.randint(2, 4)):
            activities[random.choice(activities_list)] = True

        form_data = {
            'Employee Name Click here to enter text': employee_name,
            'Does the employee have a physical or mental impairment': 'Yes',
            'What is the impairmentdiagnosis Click here to enter text': impairment,
            'What is the expected duration of the impairment x months x years or permanent Click here to enter text': duration,
            'Does the impairment affect a major life activity': 'Yes_2',
            'Please describe how the employees limitations interfere with their ability to perform the job functions Click here to enter text':
                f"The employee's {impairment.split()[0].lower()} condition significantly impacts their ability to perform essential job functions without accommodation.",
            'Do you have any suggestions regarding possible accommodations to improve job performance  If so what are they Click here to enter text':
                random.choice(accommodation_suggestions),
            'If you have any additional comments please include them below Click here to enter text':
                "Employee is motivated and capable of performing job duties with reasonable accommodations in place.",
            'Print Name': provider_name,
            'Date': datetime.now().strftime('%m/%d/%Y'),
        }

        # Add activity checkboxes
        form_data.update(activities)

        return form_data

    def generate_eft_authorization_data(self) -> Dict[str, Any]:
        """Generate data for EFT Authorization Form (CUI-Finance)."""

        company_name = self.fake.company()
        contact_name = self.fake.name()

        # Generate routing number (9 digits, must be valid checksum)
        routing_number = f"{random.randint(100000000, 999999999)}"

        # Generate account number (8-12 digits)
        account_number = f"{random.randint(10000000, 999999999999)}"

        # Generate TIN/EIN (9 digits)
        tin = f"{random.randint(100000000, 999999999)}"

        # Generate UEI (12 character alphanumeric) - some vendors have this
        uei = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789', k=12)) if random.random() < 0.3 else ''

        # Generate CAGE code (5 character alphanumeric) - procurement vendors
        cage = ''.join(random.choices('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ', k=5)) if random.random() < 0.2 else ''

        form_data = {
            # Part 1: Account Holder Information
            'txtPayee': company_name,
            'txtDBA': '' if random.random() < 0.7 else self.fake.company_suffix(),
            'txtAHStreet': self.fake.street_address(),
            'txtAHCity': self.fake.city(),
            'txtAHState': self.fake.state_abbr(),
            'txtAHZip': self.fake.zipcode(),
            'txtTIN': tin,
            'txtTINType': random.choice(['SSN Individual', 'EIN Organization']),
            'txtUEI': uei,
            'txtCAGE': cage,
            'txtContactName': contact_name,
            'txtContactTelephone': self.fake.phone_number(),

            # Part 2: Financial Institution Information
            'txtBankName': random.choice([
                'Bank of America', 'Wells Fargo', 'Chase Bank', 'Citibank',
                'US Bank', 'PNC Bank', 'Capital One', 'TD Bank',
                'Truist Bank', 'Fifth Third Bank', 'Citizens Bank'
            ]),
            'txtRoutingNum': routing_number,
            'txtDepositNum': account_number,
            'txtTypeofAccount': random.choice(['Checking Account', 'Savings Account']),

            # Part 3: CMS Administrative Fields (use exact dropdown values from PDF)
            'Vendor Type': random.choice(['Customer', 'Supplier', 'Both - Cus. & Sup.']),
            'CMS Employee': random.choice(['Yes', 'No']),
            'SES Employee': random.choice(['Yes', 'No']),
            'Federal Vendor': random.choice(['Yes', 'No']),
            '1099': random.choice(['Yes', 'No']),
            'Trading Partner': random.choice(['Yes', 'No']),

            # Signature
            'txtSignature': contact_name,
        }

        return form_data

    # --- Critical Infrastructure generators ---

    def generate_kmp_data(self) -> Dict[str, Any]:
        """Generate data for Key Management Plan (CUI-Critical Infrastructure)."""
        SYSTEM_NAMES = [
            'CloudVault', 'SecureEdge', 'DataShield', 'NetGuard', 'CipherNet',
            'TrustCore', 'SafeLink', 'VaultStream', 'InfoSentry', 'CryptoGrid',
        ]
        system = random.choice(SYSTEM_NAMES)
        system_lower = system.lower().replace(' ', '-')
        return {
            'Mock System': system,
            'Mock-system': f"{system_lower}",
            'MockSystem': system.replace(' ', ''),
            'Mock system': system,
        }

    def generate_rules_of_behavior_data(self) -> Dict[str, Any]:
        """Generate data for Rules of Behavior (CUI-Critical Infrastructure).

        The negative template has [MAC NAME] placeholders; positive is pre-filled.
        """
        MAC_NAMES = [
            'CCSQ MAC', 'FISS MAC', 'HIGLAS MAC', 'MCS MAC', 'VMS MAC',
            'BCRC MAC', 'EDPS MAC', 'HETS MAC', 'MFFS MAC', 'SPS MAC',
        ]
        mac = random.choice(MAC_NAMES)
        return {
            '[MAC NAME]': mac,
            'MAC NAME': mac,
        }

    def generate_incident_response_data(self) -> Dict[str, Any]:
        """Generate data for Incident Response Report (CUI-Critical Infrastructure).

        Fills tables with synthetic incident data: contacts, incident details, timeline.
        """
        reporter_first = self.fake.first_name()
        reporter_last = self.fake.last_name()
        reporter_email = f"{reporter_first}.{reporter_last}@cms.hhs.gov".lower()
        mgr_first = self.fake.first_name()
        mgr_last = self.fake.last_name()
        mgr_email = f"{mgr_first}.{mgr_last}@cms.hhs.gov".lower()
        fisma = random.choice([
            'CMS Cloud Services', 'Medicare Fee-for-Service', 'Healthcare.gov',
            'Marketplace Platform', 'Quality Payment Program', 'HCFAC System',
        ])
        CMS_OFFICES = ['OIT', 'CCIIO', 'CM', 'CMCS', 'OFM']
        incident_date = self.fake.date_between(start_date='-60d', end_date='today')
        phone1 = self.fake.numerify('443-555-####')
        phone2 = self.fake.numerify('443-555-####')
        phone3 = self.fake.numerify('443-555-####')

        actions = [
            'Isolated affected systems and blocked malicious IP addresses',
            'Reviewed system logs and identified unauthorized access attempts',
            'Disabled compromised user accounts and reset credentials',
            'Deployed updated endpoint protection signatures',
            'Notified CISO and initiated forensic analysis',
        ]

        return {
            '_table_data': [
                # Table 0: Contact info (rows 2 and 4 have data)
                {
                    'table_index': 0,
                    'start_row': 2,
                    'rows': [
                        [reporter_first, reporter_last, 'Contractor', 'Contractor',
                         reporter_email, reporter_email],
                    ],
                },
                {
                    'table_index': 0,
                    'start_row': 4,
                    'rows': [
                        [phone1, phone2, phone3,
                         random.choice(CMS_OFFICES), random.choice(CMS_OFFICES),
                         f"E{random.randint(100, 999)}"],
                    ],
                },
                # Table 1: Impact counts
                {
                    'table_index': 1,
                    'start_row': 1,
                    'rows': [
                        [None, random.choice(['Yes', 'No'])],
                        [None, str(random.randint(1, 500))],
                        [None, str(random.randint(0, 100))],
                    ],
                },
                # Table 2: Timeline
                {
                    'table_index': 2,
                    'start_row': 1,
                    'rows': [
                        [None, incident_date.strftime('%b %d, %Y')],
                        [random.choice(actions), random.choice(actions)],
                        [None, incident_date.strftime('%b %d, %Y')],
                        [random.choice(actions), random.choice(actions)],
                        [None, incident_date.strftime('%b %d, %Y')],
                        ['Containment actions initiated per incident response plan.',
                         'Containment actions initiated per incident response plan.'],
                        [None, incident_date.strftime('%b %d, %Y')],
                        ['Recovery procedures in progress; monitoring for recurrence.',
                         'Recovery procedures in progress; monitoring for recurrence.'],
                    ],
                },
                # Table 3: System info
                {
                    'table_index': 3,
                    'start_row': 1,
                    'rows': [
                        [None, fisma, fisma, fisma, fisma, fisma, fisma],
                    ],
                },
                {
                    'table_index': 3,
                    'start_row': 4,
                    'rows': [
                        [None, mgr_first, mgr_last, 'Manager',
                         mgr_email, phone2, 'Y'],
                        [None, reporter_first, reporter_last, 'Analyst',
                         reporter_email, phone1, 'Y'],
                    ],
                },
            ],
        }

    # --- Financial generators ---

    def generate_afr_additional_info_data(self) -> Dict[str, Any]:
        """Generate data for Additional Info AFR (CUI-Financial)."""
        SECURITY_TOOLS = [
            'CrowdStrike Falcon', 'Palo Alto Cortex', 'Splunk Enterprise Security',
            'Tenable.io', 'Qualys VMDR', 'Carbon Black Cloud', 'SentinelOne Singularity',
        ]
        VENDORS = ['Accenture Federal', 'Deloitte', 'Booz Allen Hamilton',
                   'GDIT', 'Leidos', 'CGI Federal', 'Perspecta']
        tool = random.choice(SECURITY_TOOLS)
        vendor = random.choice(VENDORS)
        old_vendors = random.sample(['Symantec', 'McAfee', 'Trend Micro', 'FireEye', 'Forcepoint'], 2)
        return {
            'Mock Security Tool': tool,
            'Mock Security Tool from PRIORITY VENDOR': f"{tool} from {vendor}",
            'PRIORITY VENDOR': vendor,
            'Special Computers': random.choice(['CMS workstations', 'HHS endpoints', 'agency laptops',
                                                  'cloud instances', 'server infrastructure']),
            'OTHERVENDOR': random.choice(VENDORS),
            'OldVendor': old_vendors[0],
            'OldProduct': f"{old_vendors[1]} Endpoint Protection",
        }

    def generate_dibo_afr_data(self) -> Dict[str, Any]:
        """Generate data for DIBO AFR (CUI-Financial)."""
        CLOUD_PRODUCTS = [
            'CloudSecure', 'GovCloud Pro', 'FedConnect', 'DataVault Enterprise',
            'SecureHost', 'CipherStack', 'NetShield Pro', 'InfoGuard Cloud',
        ]
        product = random.choice(CLOUD_PRODUCTS)
        contract_num = f"HHSM-500-{random.randint(2030, 2036)}-{random.randint(10000, 99999)}I"
        task_order = self._contract_number()
        base_budget = random.randint(300000, 800000)
        base_cost = random.randint(1000000, 3000000)
        return {
            f"HHSM-500-2034-00016I_75FCMC34R0002 BestCloud (BestCloud)":
                f"{contract_num}_{task_order} {product} ({product})",
            'BestCloud': product,
            f"$428,293": self.format_currency(base_budget),
            f"$1,868,293": self.format_currency(base_cost),
            f"$1,440,000": self.format_currency(base_cost - base_budget),
            f"$1,954,129": self.format_currency(base_cost * 1.046),
            f"$1,525,836": self.format_currency(base_cost * 1.046 - base_budget),
            f"$2,044,024": self.format_currency(base_cost * 1.094),
            f"$1,615,731": self.format_currency(base_cost * 1.094 - base_budget),
        }

    def generate_supplemental_afr_data(self) -> Dict[str, Any]:
        """Generate data for Supplemental AFR (CUI-Financial)."""
        PRODUCTS = [
            'Zero Trust Gateway', 'Cloud Access Broker', 'Privileged Access Manager',
            'Threat Intelligence Platform', 'Container Security Suite',
            'API Gateway Manager', 'Identity Governance Platform',
        ]
        product = random.choice(PRODUCTS)
        return {
            'SuperSecure Support': f"{product} Support",
            'Internal Products and Service Now': f"{product} and ServiceNow",
            'Internal Products': product,
            'SSS solution': f"{self.fake.company()} solution",
            'SecurityKeys': random.choice(['YubiKeys', 'PIV cards', 'FIDO2 tokens', 'smart cards']),
        }

    def _contract_number(self) -> str:
        return f"75FCMC{random.randint(20, 25)}F{random.randint(1000, 9999)}"

    def _task_order_number(self) -> str:
        return f"75FCMC{random.randint(20, 25)}T{random.randint(10000, 99999)}"

    def generate_currency_amount(self, min_amt: int = 1000, max_amt: int = 10000000) -> float:
        return round(random.uniform(min_amt, max_amt), 2)

    def format_currency(self, amount: float) -> str:
        return f"${amount:,.2f}"

    def generate_rfc_memo_data(self) -> Dict[str, Any]:
        """Generate data for RFC Memo (CUI-Procurement).

        Fills 4 underline blanks: modification checkmarks and signature block.
        """
        mod_type = random.choice(['Administrative', 'No-Cost Extension', 'Option Exercise',
                                   'Incremental Funding', 'Change Order'])
        return {
            'XX/XX/XXXX': datetime.now().strftime('%m/%d/%Y'),
            '75FCMCXXXXXXXX / (if applicable) 75FCMCXXXXXXXX':
                f"{self._contract_number()} / {self._task_order_number()}",
            'TBD': f"APP-{random.randint(2024, 2026)}-{random.randint(100, 999)}",
            '_underline_fills': [
                f"__X__ {mod_type}" if mod_type in ['Administrative', 'No-Cost Extension', 'Option Exercise'] else f"_____ {mod_type}",
                f"__X__ {mod_type}" if mod_type in ['Incremental Funding', 'Change Order'] else f"_____ {mod_type}",
                '',  # Negotiated Change line
                self.fake.name(),  # Signature
            ],
        }

    def generate_agx_rfc_memo_data(self) -> Dict[str, Any]:
        """Generate data for AGX RFC Memo (CUI-Procurement).

        Same structure as RFC Memo with slightly different contract format.
        """
        mod_type = random.choice(['Administrative', 'No-Cost Extension', 'Option Exercise',
                                   'Incremental Funding', 'Change Order'])
        return {
            'XX/XX/XXXX': datetime.now().strftime('%m/%d/%Y'),
            '75FCMC 23F0113 / (if applicable) 75FCMCXXXXXXXX':
                f"{self._contract_number()} / {self._task_order_number()}",
            'TBD': f"APP-{random.randint(2024, 2026)}-{random.randint(100, 999)}",
            '_underline_fills': [
                f"__X__ {mod_type}" if mod_type in ['Administrative', 'No-Cost Extension', 'Option Exercise'] else f"_____ {mod_type}",
                f"__X__ {mod_type}" if mod_type in ['Incremental Funding', 'Change Order'] else f"_____ {mod_type}",
                '',
                self.fake.name(),
            ],
        }

    def generate_ja_limited_source_data(self) -> Dict[str, Any]:
        """Generate data for JA Limited Source Justification (CUI-Procurement).

        Fills 9 underline blanks (signature/approval lines).
        """
        names = [self.fake.name() for _ in range(5)]
        dates = [self.fake.date_between(start_date='-90d', end_date='today').strftime('%m/%d/%Y')
                 for _ in range(5)]
        return {
            '_underline_fills': [
                names[0],  # COR signature
                dates[0],
                names[1],  # Program Manager
                dates[1],
                names[2],  # Contracting Officer
                dates[2],
                names[3],  # Competition Advocate
                dates[3],
                f"{names[4]}, Head of Contracting Activity",
            ],
        }

    def generate_jofoc_data(self) -> Dict[str, Any]:
        """Generate data for JOFOC (CUI-Procurement).

        Fills 4 underline blanks and 1 table (option year cost estimates).
        """
        base_cost = self.generate_currency_amount(500000, 5000000)
        return {
            '_underline_fills': [
                random.choice(['Unique Source', 'Unusual and Compelling Urgency',
                               'Statutory Authority', 'National Security']),
                self.fake.name(),  # COR
                self.fake.name(),  # CO
                self.fake.name(),  # Competition Advocate
            ],
            '_table_data': [
                {
                    'table_index': 0,
                    'start_row': 1,
                    'rows': [[
                        self.format_currency(base_cost),
                        self.format_currency(base_cost * 1.03),
                        self.format_currency(base_cost * 1.06),
                        self.format_currency(base_cost * 1.09),
                        self.format_currency(base_cost * 1.12),
                    ]],
                }
            ],
        }

    def generate_oagm_source_selection_data(self) -> Dict[str, Any]:
        """Generate data for OAGM Source Selection Determination (CUI-Procurement).

        Fills header table, offeror evaluation table, and signature line.
        """
        offerors = [self.fake.company() for _ in range(random.randint(3, 5))]
        ratings = ['Outstanding', 'Good', 'Acceptable', 'Marginal']

        eval_rows = []
        for offeror in offerors:
            orig_score = random.randint(70, 98)
            fpr_score = orig_score + random.randint(-3, 5)
            orig_cost = self.generate_currency_amount(1000000, 50000000)
            fpr_cost = orig_cost * random.uniform(0.95, 1.05)
            eval_rows.append([
                offeror,
                f"{orig_score} - {random.choice(ratings)}",
                f"{min(fpr_score, 100)} - {random.choice(ratings[:2])}",
                self.format_currency(orig_cost),
                self.format_currency(fpr_cost),
            ])

        return {
            '_underline_fills': [
                f"{self.fake.name()}    {datetime.now().strftime('%m/%d/%Y')}",
            ],
            '_table_data': [
                {
                    'table_index': 0,
                    'start_row': 0,
                    'rows': [
                        [None, datetime.now().strftime('%B %d, %Y')],
                        [None, self.fake.name()],
                        [None, 'Source Selection Determination'],
                    ],
                },
                {
                    'table_index': 1,
                    'start_row': 1,
                    'rows': eval_rows,
                },
            ],
        }

    def generate_acquisition_plan_data(self) -> Dict[str, Any]:
        """Generate data for CMS Streamlined Acquisition Plan (CUI-Procurement).

        Fills Table 0 (basic info header) and underline blanks.
        """
        CMS_COMPONENTS = ['OAGM', 'OIT', 'CMCS', 'CCIIO', 'CM', 'OFM']
        project_titles = [
            'Enterprise Cloud Hosting Services',
            'Medicare Beneficiary Data Analytics',
            'Cybersecurity Operations Center Support',
            'Healthcare.gov Platform Maintenance',
            'Quality Payment Program IT Support',
            'Marketplace IT Infrastructure',
        ]
        return {
            '_underline_fills': [
                random.choice(['Mission Critical', 'Business Essential', 'Business Support']),
                self.format_currency(self.generate_currency_amount(1000000, 50000000)),
                f"LCID-{random.randint(2024, 2026)}-{random.randint(100, 999)}",
            ],
            '_table_data': [
                {
                    'table_index': 0,
                    'start_row': 0,
                    'rows': [
                        [None, ''],  # Row 0 header
                        [None, random.choice(CMS_COMPONENTS)],
                        [None, random.choice(project_titles)],
                        [None, self.fake.name()],
                        [None, self.fake.phone_number()],
                        [None, f"{self.fake.first_name().lower()}.{self.fake.last_name().lower()}@cms.hhs.gov"],
                        [None, self.format_currency(self.generate_currency_amount(5000000, 200000000))],
                        [None, self.fake.date_between(start_date='today', end_date='+1y').strftime('%m/%d/%Y')],
                        [None, f"AS-{random.randint(2024, 2026)}-{random.randint(100, 999)}"],
                    ],
                },
            ],
        }

    def generate_market_research_data(self) -> Dict[str, Any]:
        """Generate data for TAB D Market Research Report (CUI-Procurement).

        Fills 4 tables: acquisition team, vendor assessments, business size
        counts, and vendor capability list.
        """
        CMS_OFFICES = ['OAGM', 'OIT', 'CMCS', 'CCIIO', 'CM', 'OFM', 'OA']
        ROLES = [
            'Requirements development and technical evaluation',
            'Acquisition planning and contract execution',
            'Contract administration and oversight',
            'Technical oversight and acceptance',
            'Small business coordination and outreach',
            'Subject matter expertise',
        ]
        CAPABILITIES = [
            'Demonstrated capability in cloud migration and hosting for federal agencies',
            'Strong past performance on similar HHS/CMS contracts',
            'Certified FedRAMP High cloud service provider',
            'Experienced in Agile development with DevSecOps practices',
            'Holds relevant CMMI Level 3 or higher certification',
            'Proven 508 compliance and accessibility testing capabilities',
            'Extensive experience with Medicare/Medicaid IT systems',
            'ISO 27001 certified information security management',
        ]
        BIZ_SIZES = ['Small Business', 'Small Business', 'Large Business',
                     'Small Business', 'Large Business']

        # Table 0: Acquisition team (rows 1-6, col 0=name, 2=office, 3=phone, 4=email)
        team_rows = []
        for ri in range(6):
            name = self.fake.name()
            office = random.choice(CMS_OFFICES)
            phone = self.fake.phone_number()
            email = f"{name.split()[0].lower()}.{name.split()[-1].lower()}@cms.hhs.gov"
            role = ROLES[ri] if ri < len(ROLES) else random.choice(ROLES)
            # Only fill cols 0, 2, 3, 4, 5 — col 1 (title) is pre-filled
            team_rows.append([name, None, office, phone, email, role])

        # Table 1: Vendor assessments (3 rows)
        vendor_rows = []
        for _ in range(3):
            vendor_rows.append([
                self.fake.company(),
                f"{self.fake.city()}, {self.fake.state_abbr()}",
                self.fake.name(),
                random.choice(CAPABILITIES),
            ])

        # Table 2: Business size counts (rows 1-10, col 1 = count)
        size_rows = []
        for _ in range(10):
            count = random.choice([0, 0, 1, 2, 3, 5, 8])
            size_rows.append([None, str(count)])

        # Table 3: Vendor capability list (5 rows)
        cap_rows = []
        for _ in range(5):
            cap_rows.append([
                self.fake.company(),
                random.choice(BIZ_SIZES),
                random.choice(CAPABILITIES),
            ])

        return {
            '_table_data': [
                {'table_index': 0, 'start_row': 1, 'rows': team_rows},
                {'table_index': 1, 'start_row': 1, 'rows': vendor_rows},
                {'table_index': 2, 'start_row': 1, 'rows': size_rows},
                {'table_index': 3, 'start_row': 1, 'rows': cap_rows},
            ]
        }

    def generate_clin_template_data(self) -> Dict[str, Any]:
        """Generate data for CLIN Templates (CUI-Procurement).

        Fills all 3 contract line item tables (Fixed Price, Cost Reimbursement, T&M)
        with 2-4 synthetic CLINs each.
        """
        PSC_CODES = [
            'D302', 'D306', 'D307', 'D308', 'D310', 'D311', 'D314', 'D316', 'D317', 'D399',
            'R408', 'R413', 'R425', 'R497', 'R499', 'R707', 'R799',
        ]
        CLIN_DESCRIPTIONS = [
            'Cloud Infrastructure Hosting Services',
            'Cybersecurity Operations and Monitoring',
            'Application Development and Maintenance',
            'Enterprise Data Analytics Platform',
            'Help Desk and End User Support',
            'IT Program Management Support',
            'Network Operations Center Services',
            'Identity and Access Management Services',
            'System Integration and Testing',
            'Cloud Migration and Modernization',
            'Database Administration Services',
            'Quality Assurance and IV&V',
            'Disaster Recovery and COOP Services',
            'Section 508 Compliance Testing',
            'DevSecOps Pipeline Support',
        ]
        UNITS = ['Month', 'Each', 'Hour', 'Lot', 'Year']

        def _acct_class():
            return f"75-{random.randint(100,999)}0-0-1-{random.randint(300,399)}"

        def _make_ffp_rows(n):
            rows = []
            for i in range(n):
                clin = f"000{i+1}"
                desc = random.choice(CLIN_DESCRIPTIONS)
                unit = random.choice(UNITS)
                qty = random.randint(1, 24)
                price = round(random.uniform(5000, 150000), 2)
                total = round(price * qty, 2)
                rows.append([clin, desc, random.choice(PSC_CODES), _acct_class(),
                             unit, str(qty), f"${price:,.2f}", f"${total:,.2f}"])
            return rows

        def _make_cr_rows(n):
            rows = []
            for i in range(n):
                clin = f"000{i+1}"
                desc = random.choice(CLIN_DESCRIPTIONS)
                unit = random.choice(UNITS)
                qty = random.randint(1, 12)
                cost = round(random.uniform(50000, 500000), 2)
                fee = round(cost * random.uniform(0.05, 0.10), 2)
                total = round(cost + fee, 2)
                pop_start = self.fake.date_between(start_date='-1y', end_date='today')
                pop_end = self.fake.date_between(start_date='today', end_date='+2y')
                pop = f"{pop_start.strftime('%m/%d/%Y')} - {pop_end.strftime('%m/%d/%Y')}"
                rows.append([clin, desc, random.choice(PSC_CODES), _acct_class(),
                             unit, str(qty), f"${cost:,.2f}", f"${fee:,.2f}",
                             f"${total:,.2f}", pop])
            return rows

        def _make_tm_rows(n):
            rows = []
            for i in range(n):
                clin = f"000{i+1}"
                desc = random.choice(CLIN_DESCRIPTIONS)
                unit = random.choice(['Hour', 'Month'])
                qty = random.randint(100, 5000) if unit == 'Hour' else random.randint(6, 24)
                cost = round(random.uniform(75000, 750000), 2)
                pop_start = self.fake.date_between(start_date='-1y', end_date='today')
                pop_end = self.fake.date_between(start_date='today', end_date='+2y')
                pop = f"{pop_start.strftime('%m/%d/%Y')} - {pop_end.strftime('%m/%d/%Y')}"
                rows.append([clin, desc, random.choice(PSC_CODES), _acct_class(),
                             unit, str(qty), f"${cost:,.2f}", pop])
            return rows

        num_clins = random.randint(2, 4)
        return {
            '_table_data': [
                {'table_index': 0, 'start_row': 3, 'rows': _make_ffp_rows(num_clins)},
                {'table_index': 1, 'start_row': 3, 'rows': _make_cr_rows(num_clins)},
                {'table_index': 2, 'start_row': 3, 'rows': _make_tm_rows(num_clins)},
            ]
        }

    def generate_reasonable_accommodation_data(self) -> Dict[str, Any]:
        """Generate data for Reasonable Accommodation Request (CUI)."""

        employee_name = self.fake.name()

        accommodations = [
            "Modified work schedule to accommodate medical appointments",
            "Ergonomic keyboard and mouse for repetitive strain injury",
            "Screen reader software for visual impairment",
            "Reserved parking space near building entrance",
            "Standing desk for back condition",
            "Noise-canceling headphones for concentration",
            "Remote work option for chronic condition management",
        ]

        form_data = {
            'Name': employee_name,  # Actual field name in PDF
            'Date of Birth': self.fake.date_of_birth(minimum_age=25, maximum_age=65).strftime('%m/%d/%Y'),
            'Grade': random.choice(['GS-9', 'GS-11', 'GS-12', 'GS-13', 'GS-14', 'GS-15']),
            'Component': random.choice(['CMS', 'OIG', 'ACF', 'ASPE', 'OCR']),
            'Location': self.fake.city() + ', ' + self.fake.state_abbr(),
            'Telephone number': self.fake.phone_number(),
            'Manager': self.fake.name(),
            'Discription': random.choice(accommodations),  # Note: typo in actual PDF field name
        }

        return form_data


class CustomerTemplateManager:
    """Manages customer-provided template forms."""

    def __init__(self, template_dir: str = 'temp', output_dir: str = 'output'):
        """
        Initialize template manager.

        Args:
            template_dir: Directory containing customer template files
            output_dir: Base output directory
        """
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.populator = PDFFormPopulator()

        # Map templates to data generators
        self.template_mappings = {
            'Medical Inquiry  Form': {
                'template': 'Medical Inquiry  Form_508-blank-PHI-negative.pdf',
                'generator': self.populator.generate_medical_inquiry_data,
                'category': 'PHI',
                'clean_name': 'MedicalInquiryForm'
            },
            'EFT Authorization Form': {
                'template_positive': 'EFT Authorization Form-blank-CUI-Finance-positive.pdf',  # Elizabeth's perfect filled example
                'template_negative': 'EFT Authorization Form-blank-CUI-Finance-negative.pdf',  # Blank for negatives
                'generator': self.populator.generate_eft_authorization_data,
                'category': 'CUI-Finance',
                'clean_name': 'EFTAuthorizationForm'
            },
            'ReasonableAccommodationRequest': {
                'template': 'ReasonableAccommodationRequest-blank-CUI-negative.pdf',
                'generator': self.populator.generate_reasonable_accommodation_data,
                'category': 'CUI',
                'clean_name': 'ReasonableAccommodationRequest'
            },
            # Procurement: IGCE XLSX (positive-only, copy mode — openpyxl can't parse drawings)
            'IGCE': {
                'template_positive': 'IaaS Mainframe MFA IGCE OY1-CUI-Procurement and Acquisition-positive.xlsx',
                'category': 'CUI-Procurement',
                'clean_name': 'IGCE',
                'positive_only': True,
            },
            'CLINTemplates': {
                'template': 'CLIN Templates-CUI-Procurement-positive.docx',
                'generator': self.populator.generate_clin_template_data,
                'category': 'CUI-Procurement',
                'clean_name': 'CLINTemplates',
                'positive_only': True,
            },
            'MarketResearch': {
                'template': 'TAB D Market Research-CUI-Procurement-positive.docx',
                'generator': self.populator.generate_market_research_data,
                'category': 'CUI-Procurement',
                'clean_name': 'MarketResearch',
                'positive_only': True,
            },
            'RFCMemo': {
                'template': 'RFC Memo-CUI-Procurement-positive.docx',
                'generator': self.populator.generate_rfc_memo_data,
                'category': 'CUI-Procurement',
                'clean_name': 'RFCMemo',
                'positive_only': True,
            },
            'AGXRFCMemo': {
                'template': 'AGX RFC Memo-CUI-Procurement-positive.docx',
                'generator': self.populator.generate_agx_rfc_memo_data,
                'category': 'CUI-Procurement',
                'clean_name': 'AGXRFCMemo',
                'positive_only': True,
            },
            'JALimitedSource': {
                'template': 'JA LimitedSource-CUI-Procurement-positive.docx',
                'generator': self.populator.generate_ja_limited_source_data,
                'category': 'CUI-Procurement',
                'clean_name': 'JALimitedSource',
                'positive_only': True,
            },
            'JOFOC': {
                'template': 'JOFOC-CUI-Procurement-positive.docx',
                'generator': self.populator.generate_jofoc_data,
                'category': 'CUI-Procurement',
                'clean_name': 'JOFOC',
                'positive_only': True,
            },
            'OAGMSourceSelection': {
                'template': 'OAGM SourceSelection-CUI-Procurement-positive.docx',
                'generator': self.populator.generate_oagm_source_selection_data,
                'category': 'CUI-Procurement',
                'clean_name': 'OAGMSourceSelection',
                'positive_only': True,
            },
            'AcquisitionPlan': {
                'template': 'CMS AcquisitionPlan-CUI-Procurement-positive.docx',
                'generator': self.populator.generate_acquisition_plan_data,
                'category': 'CUI-Procurement',
                'clean_name': 'AcquisitionPlan',
                'positive_only': True,
            },
            # Critical Infrastructure: fillable DOCX pairs
            'KMP': {
                'template': 'KMP-MockSystem-CUI-Critical Infrastructure-Positive.docx',
                'template_negative': 'KMPTemplate-CUI-Critical Infrastructure-negative.docx',
                'generator': self.populator.generate_kmp_data,
                'category': 'CUI-CritInfra',
                'clean_name': 'KMP',
            },
            'RulesOfBehavior': {
                'template': '2025 PQCRA Rules of Behavior - MAC NAME-CUI-Critical Infrastructure-positive.docx',
                'template_negative': '2025 PQCRA Rules of Behavior - MAC NAME-CUI-Critical Infrastructure-negative.docx',
                'generator': self.populator.generate_rules_of_behavior_data,
                'category': 'CUI-CritInfra',
                'clean_name': 'RulesOfBehavior',
            },
            'IncidentResponse': {
                'template': 'rmh-chapter-08-incident-response-incident-report-template-CUI-Critical Infrastructure-positive.docx',
                'template_negative': 'rmh-chapter-08-incident-response-incident-report-template-CUI-Critical Infrastructure-negative.docx',
                'generator': self.populator.generate_incident_response_data,
                'category': 'CUI-CritInfra',
                'clean_name': 'IncidentResponse',
            },
            # Financial: fillable DOCX pairs
            'AFRAdditionalInfo': {
                'template': 'Additional Information OIT FO-Mock AFR-CUI-Budget-positive.docx',
                'template_negative': 'Additional Information OIT FO form-CUI-Budget-negative.docx',
                'generator': self.populator.generate_afr_additional_info_data,
                'category': 'CUI-Financial',
                'clean_name': 'AFRAdditionalInfo',
            },
            'DIBOAFR': {
                'template': 'DIBO AFR -AMI-CUI-Budget-Positive.docx',
                'template_negative': 'DIBO AFR Guidance-template-CUI-Budget-Negative.docx',
                'generator': self.populator.generate_dibo_afr_data,
                'category': 'CUI-Financial',
                'clean_name': 'DIBOAFR',
            },
            'SupplementalAFR': {
                'template': 'Supplemental AFR Information-MockProject-CUI-Budget-Positive.docx',
                'template_negative': 'Supplemental AFR Information-template-CUI-Budget-negative.docx',
                'generator': self.populator.generate_supplemental_afr_data,
                'category': 'CUI-Financial',
                'clean_name': 'SupplementalAFR',
            },
        }

    def generate_from_template(self, template_key: str, output_subdir: str,
                               index: int, populate: bool = True) -> str:
        """
        Generate a document from customer template.

        Args:
            template_key: Key from template_mappings
            output_subdir: Full path to output directory (not relative)
            index: Document index for filename
            populate: If True, populate with data. If False, use blank template.

        Returns:
            Path to generated file
        """
        template_info = self.template_mappings[template_key]

        # Skip positive-only templates when generating negatives
        if not populate and template_info.get('positive_only'):
            return None

        # Choose template based on positive/negative and whether we have separate templates
        if 'template_positive' in template_info:
            # Has separate positive/negative templates (e.g., EFT)
            if populate:
                template_file = template_info['template_positive']
            elif 'template_negative' in template_info:
                template_file = template_info['template_negative']
            else:
                return None  # No negative template available
            # Just copy the appropriate template (positive already has data)
            template_path = os.path.join(self.template_dir, template_file)
            clean_name = template_info['clean_name']
            ext = os.path.splitext(template_file)[1]  # Detect extension from template
            filename = f"{clean_name}_{index:04d}{ext}"
            output_path = os.path.join(output_subdir, filename)

            import shutil
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy(template_path, output_path)
            return output_path
        else:
            # Single template - need to populate
            template_path = os.path.join(self.template_dir, template_info['template'])
            clean_name = template_info['clean_name']
            ext = os.path.splitext(template_info['template'])[1]  # Detect extension from template
            filename = f"{clean_name}_{index:04d}{ext}"
            output_path = os.path.join(output_subdir, filename)

            if populate:
                # Generate synthetic data and fill form
                field_data = template_info['generator']()
                if ext.lower() == '.pdf':
                    return self.populator.populate_form(
                        template_path, output_path, field_data,
                        field_positions=template_info.get('field_positions'))
                elif ext.lower() == '.docx':
                    return self.populate_docx_template(template_path, output_path, field_data)
                else:
                    # For other formats, copy and let caller handle
                    import shutil
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    shutil.copy(template_path, output_path)
                    return output_path
            else:
                # Copy blank/negative template
                import shutil
                # Use separate negative template if available
                if 'template_negative' in template_info:
                    neg_path = os.path.join(self.template_dir, template_info['template_negative'])
                    ext = os.path.splitext(template_info['template_negative'])[1]
                    filename = f"{clean_name}_{index:04d}{ext}"
                    output_path = os.path.join(output_subdir, filename)
                    template_path = neg_path
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copy(template_path, output_path)
                return output_path

    def populate_docx_template(self, template_path: str, output_path: str,
                                replacements: Dict[str, str]) -> str:
        """
        Populate a DOCX template with synthetic values.

        Supports three fill mechanisms (all optional, can be combined):
        1. Text placeholder substitution: {'PlaceholderText': 'replacement'}
        2. Underline blank fills: {'_underline_fills': ['val1', 'val2', ...]}
           Replaces ___ blanks in document order
        3. Table data fills: {'_table_data': [{'table_index': 0, 'start_row': 3,
           'rows': [['a','b'], ['c','d']]}]}
           Writes values into table cells by position

        Args:
            template_path: Path to DOCX template
            output_path: Path to save populated DOCX
            replacements: Dict with text replacements and optional _table_data/_underline_fills

        Returns:
            Path to created file
        """
        from docx import Document
        import re

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = Document(template_path)

        # Extract special keys before text substitution
        table_data = replacements.pop('_table_data', None)
        underline_fills = replacements.pop('_underline_fills', None)
        underline_iter = iter(underline_fills) if underline_fills else None

        def replace_in_runs(paragraph):
            """Replace placeholder text in paragraph runs, preserving formatting."""
            full_text = paragraph.text
            changed = False

            # Standard placeholder substitution
            for placeholder, value in replacements.items():
                if placeholder in full_text:
                    full_text = full_text.replace(placeholder, str(value))
                    changed = True

            # Underline blank substitution: replace each ___ with next value
            if underline_iter and re.search(r'_{3,}', full_text):
                def replace_blank(match):
                    try:
                        return next(underline_iter)
                    except StopIteration:
                        return match.group(0)
                full_text = re.sub(r'_{3,}', replace_blank, full_text)
                changed = True

            if changed and paragraph.runs:
                paragraph.runs[0].text = full_text
                for run in paragraph.runs[1:]:
                    run.text = ""

        for paragraph in doc.paragraphs:
            replace_in_runs(paragraph)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        replace_in_runs(paragraph)

        # Also check headers and footers
        for section in doc.sections:
            for header in [section.header, section.first_page_header, section.even_page_header]:
                if header and header.is_linked_to_previous is False:
                    for paragraph in header.paragraphs:
                        replace_in_runs(paragraph)
            for footer in [section.footer, section.first_page_footer, section.even_page_footer]:
                if footer and footer.is_linked_to_previous is False:
                    for paragraph in footer.paragraphs:
                        replace_in_runs(paragraph)

        # Table data fill: write values into empty cells by position
        if table_data:
            self._populate_docx_tables(doc, table_data)

        doc.save(output_path)
        return output_path

    def _populate_docx_tables(self, doc, table_data: list):
        """
        Fill table rows with synthetic data.

        Args:
            doc: python-docx Document (mutated in place)
            table_data: list of dicts:
                {
                    'table_index': int,   # which table in the doc
                    'start_row': int,     # first data row to fill
                    'rows': [             # data rows
                        ['val1', 'val2', ...],
                    ]
                }
        """
        for entry in table_data:
            table_idx = entry['table_index']
            start_row = entry['start_row']
            rows = entry['rows']

            if table_idx >= len(doc.tables):
                continue

            table = doc.tables[table_idx]
            for row_offset, row_values in enumerate(rows):
                row_idx = start_row + row_offset
                if row_idx >= len(table.rows):
                    break
                row = table.rows[row_idx]
                for col_idx, value in enumerate(row_values):
                    if col_idx >= len(row.cells) or value is None:
                        continue  # None = skip, preserve existing cell content
                    cell = row.cells[col_idx]
                    if cell.paragraphs:
                        cell.paragraphs[0].text = str(value)
                    else:
                        cell.text = str(value)

    def list_available_templates(self):
        """List all available customer templates."""
        print("\nAvailable Customer Templates:")
        print("="*70)
        for key, info in self.template_mappings.items():
            print(f"\n{key}")
            print(f"  Template: {info['template']}")
            print(f"  Category: {info['category']}")
            print(f"  Output Name: {info['clean_name']}")
        print("\n" + "="*70)


if __name__ == "__main__":
    # Test the populator
    manager = CustomerTemplateManager()
    manager.list_available_templates()

    # Test generating a populated Medical Inquiry Form
    print("\nTesting Medical Inquiry Form population...")
    output_file = manager.generate_from_template(
        'Medical Inquiry  Form',
        'temp',
        1,
        populate=True
    )
    print(f"Created: {output_file}")

    # Test blank version
    print("\nTesting blank form...")
    blank_file = manager.generate_from_template(
        'Medical Inquiry  Form',
        'temp',
        2,
        populate=False
    )
    print(f"Created: {blank_file}")
