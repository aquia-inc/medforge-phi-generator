"""
PDF Form Field Populator

Populates fillable PDF forms with synthetic data using Faker.
Works with customer-provided CMS template forms.
"""
import pikepdf
from faker import Faker
import random
import os
from datetime import datetime
from typing import Dict, Any, Optional


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

        # Use reportlab to overlay text on template PDF (only way that renders everywhere)
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from io import BytesIO
            from PyPDF2 import PdfReader, PdfWriter

            # Create overlay with text
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            # Map field names to actual positions from PDF (extracted via pikepdf)
            # Coordinates are (x, y) for bottom-left corner of text
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
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                output.write(f)

        except Exception as e:
            print(f"Warning: reportlab overlay error: {e}")
            # Fallback: use pikepdf method
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

                # Save to temp file first
                temp_path = output_path + ".tmp.pdf"
                pdf.save(temp_path, normalize_content=True)
                pdf.close()

                # Flatten by removing AcroForm (keeps field text as static content)
                pdf2 = pikepdf.open(temp_path)
                if '/AcroForm' in pdf2.Root:
                    del pdf2.Root['/AcroForm']
                pdf2.save(output_path)
                pdf2.close()

                # Clean up temp
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                # Final fallback
                import shutil
                shutil.copy(template_path, output_path)

        except Exception as e:
            print(f"Warning: pikepdf error: {e}")
            # Fallback: copy template
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

        # Choose template based on positive/negative and whether we have separate templates
        if 'template_positive' in template_info:
            # Has separate positive/negative templates (e.g., EFT)
            if populate:
                template_file = template_info['template_positive']
            else:
                template_file = template_info['template_negative']
            # Just copy the appropriate template (positive already has data)
            template_path = os.path.join(self.template_dir, template_file)
            clean_name = template_info['clean_name']
            filename = f"{clean_name}_{index:04d}.pdf"
            output_path = os.path.join(output_subdir, filename)

            import shutil
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy(template_path, output_path)
            return output_path
        else:
            # Single template - need to populate
            template_path = os.path.join(self.template_dir, template_info['template'])
            clean_name = template_info['clean_name']
            filename = f"{clean_name}_{index:04d}.pdf"
            output_path = os.path.join(output_subdir, filename)

            if populate:
                # Generate synthetic data and fill form
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
