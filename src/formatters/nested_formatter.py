"""
Nested document formatter for emails with attachments
Creates complex scenarios: emails containing PHI documents
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
from datetime import datetime
import os
import random


class NestedEmailFormatter:
    """Creates emails with document attachments (nested PHI scenarios)"""

    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_email_with_lab_attachment(self, patient, provider, lab_pdf_path, filename):
        """
        Create email with lab result PDF attached (PHI Positive)
        This tests Purview's ability to detect PHI in nested documents
        """
        msg = MIMEMultipart('mixed')

        # Email headers
        msg['Subject'] = f"Lab Results - {patient['first_name']} {patient['last_name']}"
        msg['From'] = f"{provider['first_name']} {provider['last_name']} <{provider['email']}>"
        msg['To'] = f"{patient['first_name']} {patient['last_name']} <{patient['email']}>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@healthsystem.org>"

        # Email body
        body_text = f"""
Dear {patient['first_name']} {patient['last_name']},

Please find attached your recent laboratory results from our office visit on {datetime.now().strftime('%m/%d/%Y')}.

Patient: {patient['first_name']} {patient['last_name']}
MRN: {patient['mrn']}
Date of Birth: {patient['dob'].strftime('%m/%d/%Y')}

The attached PDF contains your complete test results. Please review and contact our office if you have any questions.

Best regards,

{provider['first_name']} {provider['last_name']}, {provider['title']}
{provider['specialty']}
Phone: {provider['phone']}

---
CONFIDENTIAL: This email contains protected health information (PHI).
Unauthorized disclosure or forwarding is prohibited under HIPAA regulations.
"""

        body = MIMEText(body_text, 'plain')
        msg.attach(body)

        # Attach the PDF file
        if os.path.exists(lab_pdf_path):
            with open(lab_pdf_path, 'rb') as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                pdf_attachment.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=os.path.basename(lab_pdf_path)
                )
                msg.attach(pdf_attachment)

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def create_email_with_multiple_attachments(self, patient, provider, attachment_paths, filename):
        """
        Create email with multiple document attachments (PHI Positive)
        Tests detection of PHI across multiple nested files
        """
        msg = MIMEMultipart('mixed')

        # Email headers
        msg['Subject'] = f"Medical Records - {patient['last_name']}, {patient['first_name']}"
        msg['From'] = "Medical Records <records@healthsystem.org>"
        msg['To'] = f"{provider['first_name']} {provider['last_name']} <{provider['email']}>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@healthsystem.org>"

        # Email body
        body_text = f"""
Dr. {provider['last_name']},

As requested, please find attached medical records for:

Patient Name: {patient['first_name']} {patient['last_name']}
Date of Birth: {patient['dob'].strftime('%m/%d/%Y')}
MRN: {patient['mrn']}
Phone: {patient['phone']}
Address: {patient['address']['street']}, {patient['address']['city']}, {patient['address']['state']} {patient['address']['zip']}

Attached documents include:
{self._list_attachments(attachment_paths)}

Please confirm receipt of these records.

Medical Records Department
Phone: (555) 123-4567

---
CONFIDENTIAL MEDICAL RECORDS: This email and all attachments contain protected health information.
Handle in accordance with HIPAA privacy regulations.
"""

        body = MIMEText(body_text, 'plain')
        msg.attach(body)

        # Attach all files
        for attachment_path in attachment_paths:
            if os.path.exists(attachment_path):
                self._attach_file(msg, attachment_path)

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def create_referral_email_with_notes(self, patient, referring_provider, specialist_provider,
                                        progress_note_path, filename):
        """
        Create referral email with progress note attached (PHI Positive)
        Common real-world scenario: provider sends patient records to specialist
        """
        msg = MIMEMultipart('mixed')

        # Email headers
        msg['Subject'] = f"Patient Referral: {patient['last_name']}, {patient['first_name']}"
        msg['From'] = f"{referring_provider['first_name']} {referring_provider['last_name']} <{referring_provider['email']}>"
        msg['To'] = f"{specialist_provider['first_name']} {specialist_provider['last_name']} <{specialist_provider['email']}>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@healthsystem.org>"

        # Email body
        diagnoses_text = '\n'.join([f"- {d['name']} (ICD-10: {d['icd10']})" for d in patient['diagnoses']])
        meds_text = '\n'.join([f"- {med}" for med in patient['medications'][:5]])

        body_text = f"""
Dear Dr. {specialist_provider['last_name']},

I am referring the following patient to you for evaluation and management of {patient['diagnoses'][0]['name']}:

PATIENT INFORMATION:
Name: {patient['first_name']} {patient['last_name']}
DOB: {patient['dob'].strftime('%m/%d/%Y')} (Age: {patient['age']})
MRN: {patient['mrn']}
Contact: {patient['phone']} / {patient['email']}
Address: {patient['address']['street']}, {patient['address']['city']}, {patient['address']['state']} {patient['address']['zip']}

CURRENT DIAGNOSES:
{diagnoses_text}

CURRENT MEDICATIONS:
{meds_text}

ALLERGIES: {', '.join(patient['allergies'])}

REASON FOR REFERRAL:
Patient requires specialist evaluation for management of {patient['diagnoses'][0]['name']}.
Recent symptoms and lab findings suggest need for advanced treatment planning.

Attached is my most recent progress note with additional clinical details.

Please contact me if you need any additional information.

Thank you for seeing this patient.

Best regards,

{referring_provider['first_name']} {referring_provider['last_name']}, {referring_provider['title']}
{referring_provider['specialty']}
NPI: {referring_provider['npi']}
Phone: {referring_provider['phone']}
Fax: {referring_provider['fax']}
"""

        body = MIMEText(body_text, 'plain')
        msg.attach(body)

        # Attach progress note
        if os.path.exists(progress_note_path):
            self._attach_file(msg, progress_note_path)

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def create_email_with_blank_form(self, facility, form_path, filename):
        """
        Create email with blank form template attached (PHI Negative)
        No patient data - just distributing forms
        """
        msg = MIMEMultipart('mixed')

        # Email headers
        msg['Subject'] = "Updated Patient Registration Forms"
        msg['From'] = f"Office Manager <manager@{facility['name'].lower().replace(' ', '')}.org>"
        msg['To'] = "Front Desk Staff <frontdesk@{facility['name'].lower().replace(' ', '')}.org>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@healthsystem.org>"

        # Email body
        body_text = f"""
Dear Front Desk Team,

Please find attached the updated patient registration forms effective January 1, 2025.

KEY UPDATES:
- Added emergency contact section
- Updated insurance information fields
- New HIPAA consent language
- Spanish language version included

Please print copies for the front desk and use these forms for all new patient registrations starting next month.

The old forms should be discarded after December 31, 2024.

If you have questions, please contact the Office Manager.

Thank you,

Office Management
{facility['name']}
{facility['address']['street']}
{facility['address']['city']}, {facility['address']['state']} {facility['address']['zip']}
Phone: {facility['phone']}
"""

        body = MIMEText(body_text, 'plain')
        msg.attach(body)

        # Attach blank form
        if os.path.exists(form_path):
            self._attach_file(msg, form_path)

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def create_policy_email_with_pdf(self, facility, policy_pdf_path, filename):
        """
        Create policy distribution email with PDF attached (PHI Negative)
        Administrative content, no patient data
        """
        msg = MIMEMultipart('mixed')

        # Email headers
        msg['Subject'] = "New Clinical Documentation Policy - Action Required"
        msg['From'] = f"Compliance Department <compliance@{facility['name'].lower().replace(' ', '')}.org>"
        msg['To'] = "All Clinical Staff <clinical@{facility['name'].lower().replace(' ', '')}.org>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@healthsystem.org>"

        # Email body
        body_text = f"""
Dear Clinical Team,

Please review the attached Clinical Documentation Policy (CPG-2024-001) which becomes effective immediately.

SUMMARY OF CHANGES:
- Enhanced medication reconciliation requirements
- Updated electronic signature procedures
- New patient education documentation standards
- ICD-11 transition timeline

ACTION REQUIRED:
1. Read the attached policy document
2. Complete acknowledgment form by December 15, 2024
3. Attend one mandatory training session (dates in policy)

TRAINING SESSIONS:
- Session 1: January 10, 2025 at 2:00 PM
- Session 2: January 12, 2025 at 9:00 AM

Register for training through the staff portal.

Questions should be directed to the Compliance Department at ext. 2500.

Thank you for your cooperation.

Compliance Department
{facility['name']}
Phone: {facility['phone']}
"""

        body = MIMEText(body_text, 'plain')
        msg.attach(body)

        # Attach policy PDF
        if os.path.exists(policy_pdf_path):
            self._attach_file(msg, policy_pdf_path)

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def _attach_file(self, msg, filepath):
        """Helper method to attach a file to an email message"""
        # Determine MIME type based on file extension
        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.pdf':
            subtype = 'pdf'
            maintype = 'application'
        elif ext == '.docx':
            subtype = 'vnd.openxmlformats-officedocument.wordprocessingml.document'
            maintype = 'application'
        elif ext == '.xlsx':
            subtype = 'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            maintype = 'application'
        elif ext == '.pptx':
            subtype = 'vnd.openxmlformats-officedocument.presentationml.presentation'
            maintype = 'application'
        else:
            subtype = 'octet-stream'
            maintype = 'application'

        with open(filepath, 'rb') as f:
            if maintype == 'application':
                attachment = MIMEApplication(f.read(), _subtype=subtype)
            else:
                attachment = MIMEBase(maintype, subtype)
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)

            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=os.path.basename(filepath)
            )
            msg.attach(attachment)

    def _list_attachments(self, attachment_paths):
        """Helper to create a bullet list of attachment filenames"""
        return '\n'.join([f"- {os.path.basename(path)}" for path in attachment_paths])
