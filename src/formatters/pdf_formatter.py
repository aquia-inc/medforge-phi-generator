"""
PDF document formatter for PHI documents using ReportLab
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os


class PHIPDFFormatter:
    """Creates PDF documents with PHI content"""

    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))

        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            spaceAfter=6
        ))

    def create_lab_result(self, patient, provider, facility, lab_data, filename):
        """Generate a lab result PDF (PHI Positive)"""
        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        # Container for flowable objects
        story = []

        # Facility header
        facility_name = Paragraph(facility['name'].upper(), self.styles['CustomTitle'])
        story.append(facility_name)

        facility_addr = Paragraph(
            f"{facility['address']['street']}<br/>"
            f"{facility['address']['city']}, {facility['address']['state']} {facility['address']['zip']}<br/>"
            f"Phone: {facility['phone']} | Fax: {facility['fax']}",
            self.styles['Normal']
        )
        facility_addr.alignment = TA_CENTER
        story.append(facility_addr)
        story.append(Spacer(1, 0.3 * inch))

        # Document title
        title = Paragraph('LABORATORY RESULTS', self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # Patient Information Table
        story.append(Paragraph('PATIENT INFORMATION', self.styles['SectionHeader']))

        patient_data = [
            ['Patient Name:', f"{patient['last_name']}, {patient['first_name']}"],
            ['Date of Birth:', patient['dob'].strftime('%m/%d/%Y')],
            ['Age:', str(patient['age'])],
            ['MRN:', patient['mrn']],
            ['Address:', f"{patient['address']['street']}, {patient['address']['city']}, {patient['address']['state']} {patient['address']['zip']}"],
            ['Phone:', patient['phone']]
        ]

        patient_table = Table(patient_data, colWidths=[2 * inch, 4 * inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 0.2 * inch))

        # Test Information
        story.append(Paragraph('TEST INFORMATION', self.styles['SectionHeader']))

        test_data = [
            ['Collection Date:', lab_data['test_date'].strftime('%m/%d/%Y')],
            ['Report Date:', datetime.now().strftime('%m/%d/%Y')],
            ['Ordering Provider:', f"{provider['first_name']} {provider['last_name']}, {provider['title']}"]
        ]

        test_table = Table(test_data, colWidths=[2 * inch, 4 * inch])
        test_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(test_table)
        story.append(Spacer(1, 0.2 * inch))

        # Lab Results Table
        story.append(Paragraph('LABORATORY RESULTS', self.styles['SectionHeader']))

        results_header = [['Test Name', 'Result', 'Unit', 'Reference Range', 'Flag']]
        results_data = results_header + [
            [
                result['test'],
                str(result['value']),
                result['unit'],
                result['reference_range'],
                result.get('flag', '')
            ]
            for result in lab_data['results']
        ]

        results_table = Table(results_data, colWidths=[2.2 * inch, 1 * inch, 0.8 * inch, 1.5 * inch, 0.5 * inch])

        # Build style list dynamically for flagged values
        table_style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]

        # Highlight abnormal results
        for i, result in enumerate(lab_data['results'], 1):
            if result.get('flag'):
                table_style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffe6e6')))
                table_style_commands.append(('TEXTCOLOR', (4, i), (4, i), colors.red))

        results_table.setStyle(TableStyle(table_style_commands))
        story.append(results_table)
        story.append(Spacer(1, 0.3 * inch))

        # Footer
        footer_text = Paragraph(
            '<hr width="100%"/>'
            'This report contains confidential patient health information. '
            'Distribution or copying is prohibited without authorization.<br/>'
            f'Medical Director: {provider["first_name"]} {provider["last_name"]}, {provider["title"]}<br/>'
            f'NPI: {provider["npi"]}',
            self.styles['Footer']
        )
        story.append(footer_text)

        # Build PDF
        doc.build(story)
        return filepath

    def create_progress_note(self, patient, provider, facility, filename):
        """Generate a clinical progress note PDF (PHI Positive)"""
        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        story = []

        # Header
        facility_name = Paragraph(facility['name'].upper(), self.styles['CustomTitle'])
        story.append(facility_name)
        story.append(Spacer(1, 0.2 * inch))

        # Document title
        title = Paragraph('PROGRESS NOTE / SOAP NOTE', self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # Patient header
        patient_header = Paragraph(
            f"<b>Patient:</b> {patient['last_name']}, {patient['first_name']} | "
            f"<b>DOB:</b> {patient['dob'].strftime('%m/%d/%Y')} | "
            f"<b>MRN:</b> {patient['mrn']}<br/>"
            f"<b>Date of Visit:</b> {datetime.now().strftime('%m/%d/%Y')}<br/>"
            f"<b>Provider:</b> {provider['first_name']} {provider['last_name']}, {provider['title']} - {provider['specialty']}",
            self.styles['Normal']
        )
        story.append(patient_header)
        story.append(Spacer(1, 0.2 * inch))

        # Vital Signs
        story.append(Paragraph('VITAL SIGNS', self.styles['SectionHeader']))
        vitals = patient['vital_signs']
        vitals_text = Paragraph(
            f"BP: {vitals['blood_pressure']} mmHg | "
            f"HR: {vitals['heart_rate']} bpm | "
            f"Temp: {vitals['temperature']}°F | "
            f"RR: {vitals['respiratory_rate']} | "
            f"O2 Sat: {vitals['oxygen_saturation']}%<br/>"
            f"Weight: {vitals['weight']} lbs | "
            f"Height: {vitals['height']} inches",
            self.styles['Normal']
        )
        story.append(vitals_text)
        story.append(Spacer(1, 0.15 * inch))

        # SOAP Format
        # Subjective
        story.append(Paragraph('SUBJECTIVE:', self.styles['SectionHeader']))
        subjective = Paragraph(
            f"Patient presents for follow-up visit. Reports feeling generally well. "
            f"Current medications include: {', '.join(patient['medications'][:3])}. "
            f"Known allergies: {', '.join(patient['allergies'])}.",
            self.styles['Normal']
        )
        story.append(subjective)
        story.append(Spacer(1, 0.1 * inch))

        # Objective
        story.append(Paragraph('OBJECTIVE:', self.styles['SectionHeader']))
        objective = Paragraph(
            "Physical exam reveals patient in no acute distress. "
            "Vital signs as noted above. "
            "Review of systems within normal limits for age.",
            self.styles['Normal']
        )
        story.append(objective)
        story.append(Spacer(1, 0.1 * inch))

        # Assessment
        story.append(Paragraph('ASSESSMENT:', self.styles['SectionHeader']))
        for diagnosis in patient['diagnoses']:
            diag_text = Paragraph(
                f"• {diagnosis['name']} (ICD-10: {diagnosis['icd10']})",
                self.styles['Normal']
            )
            story.append(diag_text)
        story.append(Spacer(1, 0.1 * inch))

        # Plan
        story.append(Paragraph('PLAN:', self.styles['SectionHeader']))
        plan = Paragraph(
            "1. Continue current medications as prescribed<br/>"
            "2. Follow-up lab work in 3 months<br/>"
            "3. Return to clinic in 6 months or sooner if symptoms worsen<br/>"
            "4. Patient education provided regarding disease management",
            self.styles['Normal']
        )
        story.append(plan)
        story.append(Spacer(1, 0.3 * inch))

        # Signature
        sig = Paragraph(
            '<hr width="100%"/>'
            f"Electronically signed by: {provider['first_name']} {provider['last_name']}, {provider['title']}<br/>"
            f"Date: {datetime.now().strftime('%m/%d/%Y %H:%M')}<br/>"
            f"NPI: {provider['npi']}",
            self.styles['Footer']
        )
        story.append(sig)

        # Build PDF
        doc.build(story)
        return filepath

    def create_generic_medical_policy(self, facility, filename):
        """Generate a generic medical policy PDF (PHI Negative - No Patient Data)"""
        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        story = []

        # Header
        facility_name = Paragraph(facility['name'].upper(), self.styles['CustomTitle'])
        story.append(facility_name)
        story.append(Spacer(1, 0.2 * inch))

        # Title
        title = Paragraph('CLINICAL PRACTICE POLICY', self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        # Policy metadata
        meta_data = [
            ['Policy Number:', 'CPG-2024-001'],
            ['Effective Date:', '01/01/2024'],
            ['Review Date:', '01/01/2025'],
            ['Department:', 'Clinical Operations']
        ]

        meta_table = Table(meta_data, colWidths=[2 * inch, 4 * inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.2 * inch))

        # Purpose
        story.append(Paragraph('PURPOSE:', self.styles['SectionHeader']))
        purpose = Paragraph(
            'This policy establishes guidelines for clinical documentation standards '
            'to ensure quality patient care and regulatory compliance.',
            self.styles['Normal']
        )
        story.append(purpose)
        story.append(Spacer(1, 0.15 * inch))

        # Scope
        story.append(Paragraph('SCOPE:', self.styles['SectionHeader']))
        scope = Paragraph(
            'This policy applies to all clinical staff, including physicians, nurses, '
            'and allied health professionals providing patient care services.',
            self.styles['Normal']
        )
        story.append(scope)
        story.append(Spacer(1, 0.15 * inch))

        # Policy
        story.append(Paragraph('POLICY:', self.styles['SectionHeader']))
        policy = Paragraph(
            '1. All clinical encounters must be documented within 24 hours<br/>'
            '2. Documentation must include patient assessment, diagnosis, and treatment plan<br/>'
            '3. All entries must be signed and dated by the responsible provider<br/>'
            '4. Abbreviations must conform to the approved abbreviation list<br/>'
            '5. Late entries must be clearly identified as such',
            self.styles['Normal']
        )
        story.append(policy)
        story.append(Spacer(1, 0.15 * inch))

        # Procedure
        story.append(Paragraph('PROCEDURE:', self.styles['SectionHeader']))
        procedure = Paragraph(
            '<b>A. Documentation Requirements</b><br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;- Chief complaint<br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;- History of present illness<br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;- Review of systems<br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;- Physical examination findings<br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;- Assessment and diagnosis<br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;- Treatment plan<br/><br/>'
            '<b>B. Quality Assurance</b><br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;- Random chart audits conducted quarterly<br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;- Feedback provided to clinical staff<br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;- Corrective action plans for deficiencies',
            self.styles['Normal']
        )
        story.append(procedure)
        story.append(Spacer(1, 0.3 * inch))

        # Footer
        footer = Paragraph(
            '<hr width="100%"/>'
            f'{facility["name"]}<br/>'
            f'{facility["address"]["street"]}, {facility["address"]["city"]}, {facility["address"]["state"]}<br/>'
            f'Policy Review Committee<br/>'
            f'Approved: {datetime.now().strftime("%m/%d/%Y")}',
            self.styles['Footer']
        )
        story.append(footer)

        # Build PDF
        doc.build(story)
        return filepath
