"""
Professional HTML Lab Result Formatter
Creates realistic lab result emails and documents with modern styling
"""
import os
import random
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class HTMLLabFormatter:
    """Creates professional HTML lab result documents and emails"""

    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Lab company branding options
        self.lab_companies = [
            {
                'name': 'Quest Diagnostics',
                'portal': 'MyQuest',
                'url': 'https://myquest.questdiagnostics.com',
                'color': '#00529B',
                'phone': '1-866-697-8378'
            },
            {
                'name': 'LabCorp',
                'portal': 'Labcorp Patient Portal',
                'url': 'https://patient.labcorp.com',
                'color': '#003366',
                'phone': '1-800-845-6167'
            },
            {
                'name': 'BioReference Laboratories',
                'portal': 'BioReference Patient Portal',
                'url': 'https://patient.bioreference.com',
                'color': '#1B4F72',
                'phone': '1-800-229-5227'
            },
            {
                'name': 'ARUP Laboratories',
                'portal': 'ARUP Connect',
                'url': 'https://connect.aruplab.com',
                'color': '#2E7D32',
                'phone': '1-800-522-2787'
            }
        ]

    def _get_lab_company(self):
        """Get random lab company branding"""
        return random.choice(self.lab_companies)

    def create_lab_result_email_phi_positive(self, patient, provider, facility, lab_data, filename):
        """
        Create professional HTML lab result email with full PHI
        This is what Purview SHOULD detect
        """
        lab = self._get_lab_company()
        msg = MIMEMultipart('alternative')

        msg['Subject'] = f"Your {lab_data.get('panel_name', 'Lab')} Results Are Ready - {lab['name']}"
        msg['From'] = f"{lab['name']} <noreply@{lab['name'].lower().replace(' ', '')}.com>"
        msg['To'] = f"{patient['first_name']} {patient['last_name']} <{patient['email']}>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        msg['Message-ID'] = f"<{random.randint(100000000, 999999999)}@{lab['name'].lower().replace(' ', '')}.com>"

        # Build results table
        results_html = self._build_results_table(lab_data['results'], lab['color'])

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background-color: #f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f4f4f4;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: {lab['color']}; padding: 30px; border-radius: 8px 8px 0 0;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px;">{lab['name']}</h1>
                            <p style="color: #ffffff; margin: 10px 0 0 0; opacity: 0.9;">Laboratory Results Notification</p>
                        </td>
                    </tr>

                    <!-- Patient Info Banner -->
                    <tr>
                        <td style="background-color: #e8f4f8; padding: 20px 30px; border-bottom: 1px solid #d0e8ef;">
                            <table width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td>
                                        <p style="margin: 0; color: #333; font-size: 14px;"><strong>Patient:</strong> {patient['first_name']} {patient['last_name']}</p>
                                        <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">DOB: {patient['dob'].strftime('%m/%d/%Y')} | MRN: {patient['mrn']}</p>
                                    </td>
                                    <td align="right">
                                        <p style="margin: 0; color: #333; font-size: 14px;"><strong>Collection Date:</strong></p>
                                        <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">{lab_data['test_date'].strftime('%m/%d/%Y')}</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 30px;">
                            <p style="color: #333; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                                Dear {patient['first_name']},
                            </p>
                            <p style="color: #333; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                                Your <strong>{lab_data.get('panel_name', 'laboratory')}</strong> results from your recent visit are now available. Please review the results below.
                            </p>

                            <!-- Results Section -->
                            <div style="background-color: #fafafa; border: 1px solid #e0e0e0; border-radius: 6px; padding: 20px; margin: 20px 0;">
                                <h2 style="color: {lab['color']}; font-size: 18px; margin: 0 0 15px 0; border-bottom: 2px solid {lab['color']}; padding-bottom: 10px;">
                                    {lab_data.get('panel_name', 'Test Results')}
                                </h2>
                                {results_html}
                            </div>

                            <!-- Ordering Provider -->
                            <div style="background-color: #f5f5f5; border-left: 4px solid {lab['color']}; padding: 15px; margin: 20px 0;">
                                <p style="margin: 0; color: #333; font-size: 14px;"><strong>Ordering Provider:</strong></p>
                                <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">
                                    {provider['first_name']} {provider['last_name']}, {provider['title']}<br>
                                    {provider['specialty']}<br>
                                    NPI: {provider['npi']}<br>
                                    Phone: {provider['phone']}
                                </p>
                            </div>

                            <p style="color: #666; font-size: 14px; line-height: 1.6; margin: 20px 0;">
                                <strong>Important:</strong> These results should be reviewed with your healthcare provider.
                                If you have questions about your results, please contact your provider's office.
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{lab['url']}/results" style="background-color: {lab['color']}; color: #ffffff; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                                            View Full Results in {lab['portal']}
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f8f8; padding: 25px 30px; border-top: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;">
                            <p style="color: #666; font-size: 12px; margin: 0; line-height: 1.5;">
                                <strong>{lab['name']}</strong><br>
                                Customer Service: {lab['phone']}<br>
                                {lab['url']}
                            </p>
                            <p style="color: #999; font-size: 11px; margin: 15px 0 0 0; line-height: 1.5;">
                                This message contains Protected Health Information (PHI) and is intended only for the individual named above.
                                If you received this in error, please delete it immediately and notify the sender.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        plain_text = f"""
{lab['name']} - Laboratory Results

Patient: {patient['first_name']} {patient['last_name']}
DOB: {patient['dob'].strftime('%m/%d/%Y')}
MRN: {patient['mrn']}
Collection Date: {lab_data['test_date'].strftime('%m/%d/%Y')}

{lab_data.get('panel_name', 'Test Results')}:
{self._build_results_plain(lab_data['results'])}

Ordering Provider: {provider['first_name']} {provider['last_name']}, {provider['title']}
NPI: {provider['npi']}

View full results at: {lab['url']}

---
CONFIDENTIALITY NOTICE: This email contains Protected Health Information (PHI).
"""

        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def create_lab_notification_phi_negative(self, facility, filename):
        """
        Create lab result NOTIFICATION email - PHI Negative
        Has link to portal but NO actual patient data
        This is what Purview should NOT flag
        """
        lab = self._get_lab_company()
        msg = MIMEMultipart('alternative')

        msg['Subject'] = f"New Lab Results Available - {lab['name']}"
        msg['From'] = f"{lab['name']} <noreply@{lab['name'].lower().replace(' ', '')}.com>"
        msg['To'] = f"Patient <patient@example.com>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        msg['Message-ID'] = f"<{random.randint(100000000, 999999999)}@{lab['name'].lower().replace(' ', '')}.com>"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background-color: #f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f4f4f4;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: {lab['color']}; padding: 30px; border-radius: 8px 8px 0 0;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px;">{lab['name']}</h1>
                            <p style="color: #ffffff; margin: 10px 0 0 0; opacity: 0.9;">Results Notification</p>
                        </td>
                    </tr>

                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="color: #333; font-size: 20px; margin: 0 0 20px 0;">Your Lab Results Are Ready</h2>

                            <p style="color: #333; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                                New laboratory results have been posted to your {lab['portal']} account.
                            </p>

                            <p style="color: #333; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                                To view your results, please log in to your secure patient portal using the button below.
                            </p>

                            <!-- Info Box -->
                            <div style="background-color: #e8f4f8; border-radius: 6px; padding: 20px; margin: 20px 0;">
                                <p style="color: #333; font-size: 14px; margin: 0;">
                                    <strong>Why am I receiving this?</strong><br>
                                    You opted in to receive email notifications when new lab results are available.
                                    For your privacy and security, we do not include specific test results in this email.
                                </p>
                            </div>

                            <!-- CTA Button -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{lab['url']}/login" style="background-color: {lab['color']}; color: #ffffff; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                                            View Results in {lab['portal']}
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="color: #666; font-size: 14px; line-height: 1.6; margin: 20px 0;">
                                If you have questions about your results, please contact your healthcare provider.
                            </p>

                            <!-- Security Notice -->
                            <div style="background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 15px; margin: 20px 0;">
                                <p style="color: #856404; font-size: 13px; margin: 0;">
                                    <strong>⚠️ Security Reminder:</strong> {lab['name']} will never ask for your password,
                                    Social Security number, or financial information via email.
                                </p>
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f8f8; padding: 25px 30px; border-top: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;">
                            <p style="color: #666; font-size: 12px; margin: 0; line-height: 1.5;">
                                <strong>{lab['name']}</strong><br>
                                Customer Service: {lab['phone']}<br>
                                {lab['url']}
                            </p>
                            <p style="color: #999; font-size: 11px; margin: 15px 0 0 0; line-height: 1.5;">
                                This is an automated notification. Please do not reply to this email.<br>
                                To manage your notification preferences, visit your account settings.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        plain_text = f"""
{lab['name']} - Results Notification

Your Lab Results Are Ready

New laboratory results have been posted to your {lab['portal']} account.

To view your results, please log in to your secure patient portal:
{lab['url']}/login

For your privacy and security, we do not include specific test results in this email.

If you have questions about your results, please contact your healthcare provider.

---
{lab['name']}
Customer Service: {lab['phone']}
{lab['url']}

This is an automated notification. Please do not reply to this email.
"""

        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def create_immunization_record_email(self, patient, provider, facility, imm_data, filename):
        """
        Create professional immunization record email with full PHI
        """
        msg = MIMEMultipart('alternative')

        msg['Subject'] = f"Your Immunization Record - {facility['name']}"
        msg['From'] = f"{facility['name']} <records@{facility['name'].lower().replace(' ', '')}.org>"
        msg['To'] = f"{patient['first_name']} {patient['last_name']} <{patient['email']}>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        msg['Message-ID'] = f"<{random.randint(100000000, 999999999)}@healthsystem.org>"

        # Build vaccine table
        vaccine_rows = ""
        for vax in imm_data['vaccines']:
            vaccine_rows += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{vax['vaccine']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{vax['dose']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{vax['date'].strftime('%m/%d/%Y')}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{vax['lot']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{vax['site']}</td>
                </tr>
            """

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellspacing="0" cellpadding="0" style="max-width: 800px; margin: 0 auto; background-color: #ffffff; border: 1px solid #ddd;">
        <!-- Header -->
        <tr>
            <td style="background-color: #2E7D32; padding: 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 22px;">{facility['name']}</h1>
                <p style="color: #ffffff; margin: 5px 0 0 0; font-size: 14px;">Official Immunization Record</p>
            </td>
        </tr>

        <!-- Patient Info -->
        <tr>
            <td style="padding: 20px; background-color: #f0f7f0; border-bottom: 2px solid #2E7D32;">
                <table width="100%" cellspacing="0">
                    <tr>
                        <td width="50%">
                            <p style="margin: 0; font-size: 14px;"><strong>Patient Name:</strong> {patient['first_name']} {patient['last_name']}</p>
                            <p style="margin: 5px 0 0 0; font-size: 14px;"><strong>Date of Birth:</strong> {patient['dob'].strftime('%m/%d/%Y')}</p>
                        </td>
                        <td width="50%">
                            <p style="margin: 0; font-size: 14px;"><strong>MRN:</strong> {patient['mrn']}</p>
                            <p style="margin: 5px 0 0 0; font-size: 14px;"><strong>Record Date:</strong> {datetime.now().strftime('%m/%d/%Y')}</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>

        <!-- Vaccine Table -->
        <tr>
            <td style="padding: 20px;">
                <h2 style="color: #2E7D32; font-size: 18px; margin: 0 0 15px 0;">Vaccination History</h2>
                <table width="100%" cellspacing="0" cellpadding="0" style="border: 1px solid #ddd; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #2E7D32; color: #ffffff;">
                            <th style="padding: 12px; text-align: left; font-size: 13px;">Vaccine</th>
                            <th style="padding: 12px; text-align: left; font-size: 13px;">Dose</th>
                            <th style="padding: 12px; text-align: left; font-size: 13px;">Date</th>
                            <th style="padding: 12px; text-align: left; font-size: 13px;">Lot #</th>
                            <th style="padding: 12px; text-align: left; font-size: 13px;">Site</th>
                        </tr>
                    </thead>
                    <tbody>
                        {vaccine_rows}
                    </tbody>
                </table>
            </td>
        </tr>

        <!-- Provider Info -->
        <tr>
            <td style="padding: 20px; background-color: #f8f8f8;">
                <p style="margin: 0; font-size: 13px; color: #666;">
                    <strong>Primary Care Provider:</strong> {provider['first_name']} {provider['last_name']}, {provider['title']}<br>
                    {facility['name']} | {facility['phone']}
                </p>
            </td>
        </tr>

        <!-- Footer -->
        <tr>
            <td style="padding: 15px; background-color: #333; color: #ffffff; font-size: 11px; text-align: center;">
                This document contains Protected Health Information (PHI). {facility['name']} | {facility['address']['city']}, {facility['address']['state']}
            </td>
        </tr>
    </table>
</body>
</html>
"""

        plain_text = f"""
{facility['name']} - Official Immunization Record

Patient: {patient['first_name']} {patient['last_name']}
DOB: {patient['dob'].strftime('%m/%d/%Y')}
MRN: {patient['mrn']}

Vaccination History:
"""
        for vax in imm_data['vaccines']:
            plain_text += f"- {vax['vaccine']} ({vax['dose']}) - {vax['date'].strftime('%m/%d/%Y')} - Lot: {vax['lot']}\n"

        plain_text += f"""
Primary Care Provider: {provider['first_name']} {provider['last_name']}, {provider['title']}
{facility['name']} | {facility['phone']}

---
This document contains Protected Health Information (PHI).
"""

        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())

        return filepath

    def _build_results_table(self, results, color):
        """Build HTML table for lab results"""
        rows = ""
        for r in results:
            flag_style = ""
            flag_text = ""
            if r.get('flag'):
                if r['flag'] in ['H', 'A']:
                    flag_style = "color: #c0392b; font-weight: bold;"
                    flag_text = f" <span style='{flag_style}'>↑ {r['flag']}</span>"
                elif r['flag'] == 'L':
                    flag_style = "color: #2980b9; font-weight: bold;"
                    flag_text = f" <span style='{flag_style}'>↓ {r['flag']}</span>"

            value_display = f"{r['value']} {r.get('unit', '')}"

            rows += f"""
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #eee; font-size: 14px;">{r['test']}</td>
                <td style="padding: 10px 0; border-bottom: 1px solid #eee; font-size: 14px; font-weight: 500;">{value_display}{flag_text}</td>
                <td style="padding: 10px 0; border-bottom: 1px solid #eee; font-size: 13px; color: #666;">{r['reference_range']}</td>
            </tr>
            """

        return f"""
        <table width="100%" cellspacing="0" cellpadding="0">
            <thead>
                <tr style="border-bottom: 2px solid {color};">
                    <th style="text-align: left; padding: 10px 0; font-size: 13px; color: #666;">Test</th>
                    <th style="text-align: left; padding: 10px 0; font-size: 13px; color: #666;">Result</th>
                    <th style="text-align: left; padding: 10px 0; font-size: 13px; color: #666;">Reference Range</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _build_results_plain(self, results):
        """Build plain text results list"""
        lines = []
        for r in results:
            flag = f" ({r['flag']})" if r.get('flag') else ""
            lines.append(f"  {r['test']}: {r['value']} {r.get('unit', '')} [Ref: {r['reference_range']}]{flag}")
        return '\n'.join(lines)
