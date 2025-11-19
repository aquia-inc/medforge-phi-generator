"""
Email formatter for EML and MSG formats
Creates PHI-containing and PHI-negative emails
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os
import random


class EmailFormatter:
    """Creates EML email files with PHI content"""

    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_provider_to_provider_email(self, patient, sender_provider, recipient_provider, filename):
        """Create provider-to-provider email with PHI (EML format)"""

        msg = MIMEMultipart('alternative')

        # Email headers
        msg['Subject'] = f"Patient Consultation: {patient['last_name']}, {patient['first_name']}"
        msg['From'] = f"{sender_provider['first_name']} {sender_provider['last_name']} <{sender_provider['email']}>"
        msg['To'] = f"{recipient_provider['first_name']} {recipient_provider['last_name']} <{recipient_provider['email']}>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@healthsystem.org>"

        # Email body (plain text)
        plain_text = f"""
Dr. {recipient_provider['last_name']},

I am writing to consult with you regarding one of our mutual patients:

Patient Name: {patient['first_name']} {patient['last_name']}
Date of Birth: {patient['dob'].strftime('%m/%d/%Y')}
MRN: {patient['mrn']}
Phone: {patient['phone']}

Current Diagnoses:
{self._format_diagnoses_text(patient['diagnoses'])}

Current Medications:
{self._format_medications_text(patient['medications'])}

Allergies: {', '.join(patient['allergies'])}

I would appreciate your input on management of this patient's {patient['diagnoses'][0]['name']}.
Recent lab work shows some concerning trends that I believe warrant specialist evaluation.

Would you be able to see this patient within the next 2-3 weeks?

Please let me know your availability.

Best regards,

{sender_provider['first_name']} {sender_provider['last_name']}, {sender_provider['title']}
{sender_provider['specialty']}
NPI: {sender_provider['npi']}
Phone: {sender_provider['phone']}
Fax: {sender_provider['fax']}
"""

        # Email body (HTML)
        html_text = f"""
<html>
<head></head>
<body style="font-family: Arial, sans-serif;">
    <p>Dr. {recipient_provider['last_name']},</p>

    <p>I am writing to consult with you regarding one of our mutual patients:</p>

    <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
        <tr><td><strong>Patient Name:</strong></td><td>{patient['first_name']} {patient['last_name']}</td></tr>
        <tr><td><strong>Date of Birth:</strong></td><td>{patient['dob'].strftime('%m/%d/%Y')}</td></tr>
        <tr><td><strong>MRN:</strong></td><td>{patient['mrn']}</td></tr>
        <tr><td><strong>Phone:</strong></td><td>{patient['phone']}</td></tr>
    </table>

    <h3>Current Diagnoses:</h3>
    <ul>
        {self._format_diagnoses_html(patient['diagnoses'])}
    </ul>

    <h3>Current Medications:</h3>
    <ul>
        {self._format_medications_html(patient['medications'])}
    </ul>

    <p><strong>Allergies:</strong> {', '.join(patient['allergies'])}</p>

    <p>I would appreciate your input on management of this patient's {patient['diagnoses'][0]['name']}.
    Recent lab work shows some concerning trends that I believe warrant specialist evaluation.</p>

    <p>Would you be able to see this patient within the next 2-3 weeks?</p>

    <p>Please let me know your availability.</p>

    <p>Best regards,</p>

    <div style="border-top: 1px solid #ccc; margin-top: 20px; padding-top: 10px;">
        <strong>{sender_provider['first_name']} {sender_provider['last_name']}, {sender_provider['title']}</strong><br/>
        {sender_provider['specialty']}<br/>
        NPI: {sender_provider['npi']}<br/>
        Phone: {sender_provider['phone']}<br/>
        Fax: {sender_provider['fax']}
    </div>
</body>
</html>
"""

        # Attach parts
        part1 = MIMEText(plain_text, 'plain')
        part2 = MIMEText(html_text, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def create_test_result_notification(self, patient, provider, lab_data, filename):
        """Create test result notification email with PHI (EML format)"""

        msg = MIMEMultipart('alternative')

        # Email headers
        msg['Subject'] = f"Lab Results Available - {patient['last_name']}, {patient['first_name']}"
        msg['From'] = f"{provider['first_name']} {provider['last_name']} <{provider['email']}>"
        msg['To'] = f"{patient['first_name']} {patient['last_name']} <{patient['email']}>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@patientportal.org>"

        # Plain text body
        plain_text = f"""
Dear {patient['first_name']} {patient['last_name']},

Your recent lab results from {lab_data['test_date'].strftime('%m/%d/%Y')} are now available.

Patient Information:
Name: {patient['first_name']} {patient['last_name']}
Date of Birth: {patient['dob'].strftime('%m/%d/%Y')}
MRN: {patient['mrn']}

Test Results:
{self._format_lab_results_text(lab_data['results'])}

Please contact our office at {provider['phone']} if you have any questions about these results.

If any results are flagged as abnormal, we will follow up with you directly to discuss next steps.

Thank you,

{provider['first_name']} {provider['last_name']}, {provider['title']}
{provider['specialty']}
Phone: {provider['phone']}

---
CONFIDENTIALITY NOTICE: This email and any attachments contain confidential patient health information.
If you received this in error, please delete it immediately and notify the sender.
"""

        # HTML body
        html_text = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <p>Dear {patient['first_name']} {patient['last_name']},</p>

    <p>Your recent lab results from {lab_data['test_date'].strftime('%m/%d/%Y')} are now available.</p>

    <h3>Patient Information:</h3>
    <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
        <tr><td><strong>Name:</strong></td><td>{patient['first_name']} {patient['last_name']}</td></tr>
        <tr><td><strong>Date of Birth:</strong></td><td>{patient['dob'].strftime('%m/%d/%Y')}</td></tr>
        <tr><td><strong>MRN:</strong></td><td>{patient['mrn']}</td></tr>
    </table>

    <h3>Test Results:</h3>
    <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
        <tr style="background-color: #f0f0f0;">
            <th>Test</th><th>Result</th><th>Unit</th><th>Reference Range</th><th>Flag</th>
        </tr>
        {self._format_lab_results_html(lab_data['results'])}
    </table>

    <p>Please contact our office at {provider['phone']} if you have any questions about these results.</p>

    <p>If any results are flagged as abnormal, we will follow up with you directly to discuss next steps.</p>

    <p>Thank you,</p>

    <div style="border-top: 1px solid #ccc; margin-top: 20px; padding-top: 10px;">
        <strong>{provider['first_name']} {provider['last_name']}, {provider['title']}</strong><br/>
        {provider['specialty']}<br/>
        Phone: {provider['phone']}
    </div>

    <hr style="border: 0; border-top: 1px solid #ccc; margin-top: 20px;"/>
    <p style="font-size: 9px; color: #666;">
        <strong>CONFIDENTIALITY NOTICE:</strong> This email and any attachments contain confidential patient health information.
        If you received this in error, please delete it immediately and notify the sender.
    </p>
</body>
</html>
"""

        # Attach parts
        part1 = MIMEText(plain_text, 'plain')
        part2 = MIMEText(html_text, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def create_office_announcement(self, facility, filename):
        """Create office announcement email (PHI Negative - No Patient Data)"""

        msg = MIMEMultipart('alternative')

        # Email headers
        msg['Subject'] = "Office Closure Notice - Holiday Schedule"
        msg['From'] = f"Office Administrator <admin@{facility['name'].lower().replace(' ', '')}.org>"
        msg['To'] = "All Staff <staff@{facility['name'].lower().replace(' ', '')}.org>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@healthsystem.org>"

        # Plain text body
        plain_text = f"""
Dear Staff,

This is to inform you of our upcoming holiday schedule for {facility['name']}.

OFFICE CLOSURES:
- December 24-25, 2024: Christmas Holiday
- January 1, 2025: New Year's Day
- January 15, 2025: Martin Luther King Jr. Day

During these closures, emergency services will be available through our on-call system.
Please refer patients to the emergency contact number: {facility['phone']}

REGULAR HOURS RESUME:
Normal business hours will resume on the next business day following each holiday.

Thank you for your attention to this matter.

{facility['name']}
{facility['address']['street']}
{facility['address']['city']}, {facility['address']['state']} {facility['address']['zip']}
Phone: {facility['phone']}
"""

        # HTML body
        html_text = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #2c3e50;">Holiday Office Hours</h2>

    <p>Dear Staff,</p>

    <p>This is to inform you of our upcoming holiday schedule for <strong>{facility['name']}</strong>.</p>

    <h3>OFFICE CLOSURES:</h3>
    <ul>
        <li>December 24-25, 2024: Christmas Holiday</li>
        <li>January 1, 2025: New Year's Day</li>
        <li>January 15, 2025: Martin Luther King Jr. Day</li>
    </ul>

    <p>During these closures, emergency services will be available through our on-call system.
    Please refer patients to the emergency contact number: <strong>{facility['phone']}</strong></p>

    <h3>REGULAR HOURS RESUME:</h3>
    <p>Normal business hours will resume on the next business day following each holiday.</p>

    <p>Thank you for your attention to this matter.</p>

    <div style="border-top: 2px solid #3498db; margin-top: 20px; padding-top: 10px;">
        <strong>{facility['name']}</strong><br/>
        {facility['address']['street']}<br/>
        {facility['address']['city']}, {facility['address']['state']} {facility['address']['zip']}<br/>
        Phone: {facility['phone']}
    </div>
</body>
</html>
"""

        # Attach parts
        part1 = MIMEText(plain_text, 'plain')
        part2 = MIMEText(html_text, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def create_policy_update_email(self, facility, filename):
        """Create policy update email (PHI Negative - No Patient Data)"""

        msg = MIMEMultipart('alternative')

        # Email headers
        msg['Subject'] = "Updated Clinical Documentation Policy"
        msg['From'] = f"Compliance Department <compliance@{facility['name'].lower().replace(' ', '')}.org>"
        msg['To'] = "Clinical Staff <clinical@{facility['name'].lower().replace(' ', '')}.org>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@healthsystem.org>"

        # Plain text body
        plain_text = f"""
Dear Clinical Team,

The Clinical Documentation Policy (CPG-2024-001) has been updated effective immediately.

KEY CHANGES:
1. All progress notes must now include medication reconciliation
2. Patient education documentation is now required for all visits
3. Diagnosis codes must be updated to ICD-11 by March 31, 2025
4. Electronic signature requirements have been clarified

TRAINING:
Mandatory training sessions will be held:
- January 10, 2025 at 2:00 PM
- January 12, 2025 at 9:00 AM

Please attend one session to review the updated requirements.

The full policy document is available on the intranet under Clinical Policies.

If you have questions, please contact the Compliance Department.

Best regards,

Compliance Department
{facility['name']}
Phone: {facility['phone']}
"""

        # HTML body
        html_text = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #e74c3c;">IMPORTANT: Policy Update</h2>

    <p>Dear Clinical Team,</p>

    <p>The <strong>Clinical Documentation Policy (CPG-2024-001)</strong> has been updated effective immediately.</p>

    <h3 style="color: #2c3e50;">KEY CHANGES:</h3>
    <ol>
        <li>All progress notes must now include medication reconciliation</li>
        <li>Patient education documentation is now required for all visits</li>
        <li>Diagnosis codes must be updated to ICD-11 by March 31, 2025</li>
        <li>Electronic signature requirements have been clarified</li>
    </ol>

    <h3 style="color: #2c3e50;">TRAINING:</h3>
    <p>Mandatory training sessions will be held:</p>
    <ul>
        <li>January 10, 2025 at 2:00 PM</li>
        <li>January 12, 2025 at 9:00 AM</li>
    </ul>

    <p>Please attend one session to review the updated requirements.</p>

    <p>The full policy document is available on the intranet under <strong>Clinical Policies</strong>.</p>

    <p>If you have questions, please contact the Compliance Department.</p>

    <p>Best regards,</p>

    <div style="border-top: 1px solid #ccc; margin-top: 20px; padding-top: 10px;">
        <strong>Compliance Department</strong><br/>
        {facility['name']}<br/>
        Phone: {facility['phone']}
    </div>
</body>
</html>
"""

        # Attach parts
        part1 = MIMEText(plain_text, 'plain')
        part2 = MIMEText(html_text, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    # Helper methods for formatting
    def _format_diagnoses_text(self, diagnoses):
        return '\n'.join([f"- {d['name']} (ICD-10: {d['icd10']})" for d in diagnoses])

    def _format_diagnoses_html(self, diagnoses):
        return '\n'.join([f"<li>{d['name']} (ICD-10: {d['icd10']})</li>" for d in diagnoses])

    def _format_medications_text(self, medications):
        return '\n'.join([f"- {med}" for med in medications])

    def _format_medications_html(self, medications):
        return '\n'.join([f"<li>{med}</li>" for med in medications])

    def _format_lab_results_text(self, results):
        lines = []
        for result in results:
            flag = f" [{result.get('flag', '')}]" if result.get('flag') else ""
            lines.append(
                f"{result['test']}: {result['value']} {result['unit']} "
                f"(Reference: {result['reference_range']}){flag}"
            )
        return '\n'.join(lines)

    def _format_lab_results_html(self, results):
        rows = []
        for result in results:
            flag_color = "color: red; font-weight: bold;" if result.get('flag') else ""
            rows.append(
                f"<tr>"
                f"<td>{result['test']}</td>"
                f"<td>{result['value']}</td>"
                f"<td>{result['unit']}</td>"
                f"<td>{result['reference_range']}</td>"
                f"<td style='{flag_color}'>{result.get('flag', '')}</td>"
                f"</tr>"
            )
        return '\n'.join(rows)


class MSGFormatter:
    """Creates MSG (Outlook) email files"""

    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_from_eml(self, eml_path, msg_filename):
        """
        Convert EML to MSG format
        Note: MSG format is proprietary and complex. For now, we save as EML
        and note that proper MSG creation would require Outlook COM automation
        or specialized libraries that work better on Windows.

        For cross-platform compatibility, we'll primarily use EML format.
        """
        # For MVP, we'll note this limitation and focus on EML
        # Production version could use olefile or msg-extractor on Windows
        # or convert via email to create MSG-like structure

        print("Note: MSG format requires Windows/Outlook COM automation.")
        print(f"Using EML format for cross-platform compatibility: {eml_path}")

        return eml_path
