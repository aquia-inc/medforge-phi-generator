"""
PDF Form Field Populator

Populates fillable PDF forms with synthetic data using Faker.
Works with customer-provided CMS template forms.
"""
from PyPDF2 import PdfReader
from fillpdf import fillpdfs
from faker import Faker
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os


class PDFFormPopulator:
    """Populates fillable PDF forms with synthetic data."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize with optional random seed."""
        self.fake = Faker('en_US')
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    def populate_form(self, template_path: str, output_path: str, field_data: Dict[str, Any]) -> str:
        """
        Populate a PDF form with synthetic data.

        Args:
            template_path: Path to blank PDF template
            output_path: Path to save populated PDF
            field_data: Dictionary mapping field names to values

        Returns:
            Path to created file
        """
        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Use fillpdf to populate the form
        try:
            fillpdfs.write_fillable_pdf(
                template_path,
                output_path,
                field_data,
                flatten=False  # Keep as fillable form
            )
        except Exception as e:
            print(f"Warning: fillpdf error: {e}")
            # Fallback: just copy the template
            import shutil
            shutil.copy(template_path, output_path)

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

            # Part 3: CMS Administrative Fields (some populated)
            'Vendor Type': random.choice(['Individual', 'Business', 'Government', 'Non-Profit']),
            'CMS Employee': random.choice(['Yes', 'No']),
            'SES Employee': random.choice(['Yes', 'No']),
            'Federal Vendor': random.choice(['Yes', 'No']),
            '1099': random.choice(['Yes', 'No']),  # 1099 reporting
            'Trading Partner': random.choice(['Yes', 'No']),

            # Payment Terms
            'Supplier Payment Terms': random.choice(['Net 30', 'Net 60', 'Immediate']),

            # Signature
            'txtSignature': contact_name,
        }

        return form_data

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
            'Employee Name': employee_name,
            'Position': random.choice(['Program Analyst', 'IT Specialist', 'Budget Analyst', 'Administrative Officer']),
            'Office': random.choice(['Office of the Director', 'IT Department', 'Finance Division', 'HR Department']),
            'Supervisor': self.fake.name(),
            'Accommodation Requested': random.choice(accommodations),
            'Medical Documentation Attached': '/Yes',
            'Request Date': datetime.now().strftime('%m/%d/%Y'),
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
                'template': 'EFT Authorization Form-blank-CUI-Finance-negative.pdf',
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
        template_path = os.path.join(self.template_dir, template_info['template'])

        # Create clean filename
        clean_name = template_info['clean_name']
        filename = f"{clean_name}_{index:04d}.pdf"
        # output_subdir is now the full path, not relative
        output_path = os.path.join(output_subdir, filename)

        if populate:
            # Generate synthetic data
            field_data = template_info['generator']()
            return self.populator.populate_form(template_path, output_path, field_data)
        else:
            # Copy blank template
            import shutil
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy(template_path, output_path)
            return output_path

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
        'test_output',
        1,
        populate=True
    )
    print(f"Created: {output_file}")

    # Test blank version
    print("\nTesting blank form...")
    blank_file = manager.generate_from_template(
        'Medical Inquiry  Form',
        'test_output',
        2,
        populate=False
    )
    print(f"Created: {blank_file}")
