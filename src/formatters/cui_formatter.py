"""
CUI document formatter.

Creates CUI documents in various formats (DOCX, PDF, EML, XLSX)
with proper classification headers, footers, and markings.
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime
import os
import random
from typing import Any, Dict, Optional


class CUIDocxFormatter:
    """Creates DOCX documents with CUI markings and content."""

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_cui_document(self, doc_data: Dict[str, Any], filename: str) -> str:
        """
        Create a DOCX document from CUI data.

        Args:
            doc_data: Dictionary containing CUI document data
            filename: Output filename

        Returns:
            Path to created file
        """
        doc = Document()

        # Add classification header if CUI positive
        if doc_data.get('has_cui', False):
            self._add_classification_header(doc, doc_data)

        # Add document title
        self._add_title(doc, doc_data)

        # Add metadata section
        self._add_metadata_section(doc, doc_data)

        # Add main content based on document type
        self._add_content(doc, doc_data)

        # Add confidentiality notice if CUI positive
        if doc_data.get('has_cui', False):
            self._add_confidentiality_notice(doc, doc_data)

        # Add classification footer
        if doc_data.get('has_cui', False):
            self._add_classification_footer(doc, doc_data)

        # Save document
        filepath = os.path.join(self.output_dir, filename)
        doc.save(filepath)
        return filepath

    def _add_classification_header(self, doc: Document, doc_data: Dict[str, Any]):
        """Add classification banner at top of document."""
        header = doc.add_paragraph()
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = header.add_run(doc_data.get('classification', 'CONTROLLED UNCLASSIFIED INFORMATION'))
        run.bold = True
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(139, 0, 0)  # Dark red
        doc.add_paragraph()

    def _add_title(self, doc: Document, doc_data: Dict[str, Any]):
        """Add document title."""
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.add_run(doc_data.get('title', 'Document'))
        run.bold = True
        run.font.size = Pt(14)
        doc.add_paragraph()

    def _add_metadata_section(self, doc: Document, doc_data: Dict[str, Any]):
        """Add document metadata section."""
        # Create metadata table
        metadata_items = []

        if 'agency' in doc_data:
            metadata_items.append(('Organization:', doc_data['agency']))
        if 'document_date' in doc_data:
            metadata_items.append(('Date:', doc_data['document_date']))
        if 'document_id' in doc_data:
            metadata_items.append(('Document ID:', doc_data['document_id']))
        if doc_data.get('authority'):
            metadata_items.append(('Authority:', doc_data['authority']))

        if metadata_items:
            table = doc.add_table(rows=len(metadata_items), cols=2)
            for i, (label, value) in enumerate(metadata_items):
                table.rows[i].cells[0].text = label
                table.rows[i].cells[1].text = str(value)
                table.rows[i].cells[0].paragraphs[0].runs[0].bold = True
            doc.add_paragraph()

    def _add_content(self, doc: Document, doc_data: Dict[str, Any]):
        """Add main document content based on document type."""
        doc_type = doc_data.get('document_type', '')

        # Handle different document types
        if doc_type == 'coop_plan':
            self._add_coop_plan_content(doc, doc_data)
        elif doc_type == 'vulnerability_alert':
            self._add_vulnerability_content(doc, doc_data)
        elif doc_type == 'budget_memo':
            self._add_budget_memo_content(doc, doc_data)
        elif doc_type == 'attorney_memo':
            self._add_attorney_memo_content(doc, doc_data)
        elif doc_type in ['source_selection_plan', 'evaluation_report', 'igce']:
            self._add_procurement_content(doc, doc_data)
        elif doc_type == 'taxpayer_record':
            self._add_tax_record_content(doc, doc_data)
        else:
            # Generic content handler
            self._add_generic_content(doc, doc_data)

    def _add_coop_plan_content(self, doc: Document, doc_data: Dict[str, Any]):
        """Add COOP plan specific content."""
        # Executive Summary
        doc.add_paragraph('EXECUTIVE SUMMARY', style='Heading 2')
        doc.add_paragraph(doc_data.get('executive_summary', ''))

        # Essential Functions
        if 'essential_functions' in doc_data:
            doc.add_paragraph('ESSENTIAL FUNCTIONS PRIORITIZATION', style='Heading 2')
            for func in doc_data['essential_functions']:
                doc.add_paragraph(f"• Priority {func['priority']}: {func['function']}")

        # Alternate Locations
        if 'alternate_locations' in doc_data:
            doc.add_paragraph('ALTERNATE LOCATIONS', style='Heading 2')
            locs = doc_data['alternate_locations']
            doc.add_paragraph(f"Primary: {locs.get('primary', 'N/A')}")
            doc.add_paragraph(f"Secondary: {locs.get('secondary', 'N/A')}")
            doc.add_paragraph(f"Devolution: {locs.get('devolution_distance', 'N/A')}")

        # Activation Triggers
        if 'activation_triggers' in doc_data:
            doc.add_paragraph('ACTIVATION TRIGGERS', style='Heading 2')
            for trigger in doc_data['activation_triggers']:
                doc.add_paragraph(f"• {trigger}")

        # ERG Details
        if 'erg_details' in doc_data:
            doc.add_paragraph('EMERGENCY RELOCATION GROUP', style='Heading 2')
            erg = doc_data['erg_details']
            doc.add_paragraph(f"ERG Leader: {erg.get('leader_name', '')} ({erg.get('leader_title', '')})")
            doc.add_paragraph(f"ERG Size: {erg.get('size', '')} personnel")
            doc.add_paragraph(f"Deployment Time: Within {erg.get('deployment_hours', '')} hours")

    def _add_vulnerability_content(self, doc: Document, doc_data: Dict[str, Any]):
        """Add vulnerability alert content."""
        # Alert details
        doc.add_paragraph('ALERT DETAILS', style='Heading 2')
        doc.add_paragraph(f"Alert ID: {doc_data.get('alert_id', '')}")
        doc.add_paragraph(f"Severity: {doc_data.get('severity', '')}")
        doc.add_paragraph(f"CVSS Score: {doc_data.get('cvss_score', '')}")
        doc.add_paragraph(f"CVE: {doc_data.get('cve_id', '')}")

        # Affected System
        doc.add_paragraph('AFFECTED SYSTEM', style='Heading 2')
        doc.add_paragraph(f"System: {doc_data.get('affected_system', '')}")
        doc.add_paragraph(f"Versions: {doc_data.get('affected_versions', '')}")

        # Description
        doc.add_paragraph('DESCRIPTION', style='Heading 2')
        doc.add_paragraph(doc_data.get('description', ''))

        # Remediation
        if 'remediation' in doc_data:
            doc.add_paragraph('REMEDIATION', style='Heading 2')
            rem = doc_data['remediation']
            doc.add_paragraph(f"Action: {rem.get('action', '')}")
            doc.add_paragraph(f"Target Version: {rem.get('target_version', '')}")
            doc.add_paragraph(f"Deadline: {rem.get('deadline', '')}")

    def _add_budget_memo_content(self, doc: Document, doc_data: Dict[str, Any]):
        """Add budget memo content."""
        # TO/FROM section
        doc.add_paragraph(f"TO: {doc_data.get('to', '')}")
        doc.add_paragraph(f"FROM: {doc_data.get('from', '')}")
        doc.add_paragraph(f"SUBJECT: {doc_data.get('subject', '')}")
        doc.add_paragraph()

        # Decision
        doc.add_paragraph('PRESIDENTIAL DECISION:', style='Heading 2')
        doc.add_paragraph(doc_data.get('decision', ''))

        # Key Decision Points
        if 'key_decision_points' in doc_data:
            doc.add_paragraph('KEY DECISION POINTS:', style='Heading 2')
            for point in doc_data['key_decision_points']:
                doc.add_paragraph(f"• {point}")

    def _add_attorney_memo_content(self, doc: Document, doc_data: Dict[str, Any]):
        """Add attorney memorandum content."""
        # Privilege assertion
        if 'privilege_assertion' in doc_data:
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(' | '.join(doc_data['privilege_assertion']))
            run.italic = True

        # Attorney/Client info
        attorney = doc_data.get('attorney', {})
        client = doc_data.get('client', {})
        doc.add_paragraph(f"TO: {client.get('name', '')} - {client.get('title', '')}")
        doc.add_paragraph(f"FROM: {attorney.get('name', '')} - {attorney.get('title', '')}")
        doc.add_paragraph(f"RE: {doc_data.get('subject', '')}")
        doc.add_paragraph()

        # Question Presented
        doc.add_paragraph('QUESTION PRESENTED:', style='Heading 2')
        doc.add_paragraph(doc_data.get('question_presented', ''))

        # Brief Answer
        doc.add_paragraph('BRIEF ANSWER:', style='Heading 2')
        doc.add_paragraph(doc_data.get('brief_answer', ''))

        # Analysis
        doc.add_paragraph('ANALYSIS:', style='Heading 2')
        doc.add_paragraph(doc_data.get('analysis', ''))

        # Recommendation
        doc.add_paragraph('RECOMMENDATION:', style='Heading 2')
        doc.add_paragraph(doc_data.get('recommendation', ''))

    def _add_procurement_content(self, doc: Document, doc_data: Dict[str, Any]):
        """Add procurement document content."""
        doc.add_paragraph(f"Solicitation Number: {doc_data.get('solicitation_number', '')}")

        if doc_data.get('document_type') == 'source_selection_plan':
            doc.add_paragraph(f"Program: {doc_data.get('program', '')}")
            doc.add_paragraph(f"Estimated Value: {doc_data.get('estimated_value', '')}")
            doc.add_paragraph(f"Contract Type: {doc_data.get('contract_type', '')}")

            if 'evaluation_factors' in doc_data:
                doc.add_paragraph('EVALUATION FACTORS:', style='Heading 2')
                for factor in doc_data['evaluation_factors']:
                    doc.add_paragraph(f"• {factor['factor']}: Weight {factor['weight']}%")

        elif doc_data.get('document_type') == 'evaluation_report':
            doc.add_paragraph(f"Offeror: {doc_data.get('offeror', '')}")
            doc.add_paragraph(f"Overall Rating: {doc_data.get('overall_rating', '')}")

    def _add_tax_record_content(self, doc: Document, doc_data: Dict[str, Any]):
        """Add tax record content."""
        taxpayer = doc_data.get('taxpayer', {})
        doc.add_paragraph(f"Taxpayer: {taxpayer.get('name', '')}")
        doc.add_paragraph(f"SSN: {taxpayer.get('ssn_masked', '')}")
        doc.add_paragraph(f"Tax Period: {doc_data.get('tax_period', '')}")

        if 'account_summary' in doc_data:
            doc.add_paragraph('ACCOUNT SUMMARY:', style='Heading 2')
            summary = doc_data['account_summary']
            for key, value in summary.items():
                doc.add_paragraph(f"{key.replace('_', ' ').title()}: {value}")

    def _add_generic_content(self, doc: Document, doc_data: Dict[str, Any]):
        """Add generic document content."""
        # Add any remaining text-based fields
        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'authority', 'distribution',
                       'generated_date', 'document_date', 'agency', 'title',
                       'confidentiality_notice'}

        for key, value in doc_data.items():
            if key in skip_fields:
                continue

            # Handle different value types
            if isinstance(value, str):
                doc.add_paragraph(f"{key.replace('_', ' ').title()}: {value}")
            elif isinstance(value, list):
                doc.add_paragraph(f"{key.replace('_', ' ').title()}:", style='Heading 2')
                for item in value:
                    if isinstance(item, dict):
                        doc.add_paragraph(f"• {item}")
                    else:
                        doc.add_paragraph(f"• {item}")
            elif isinstance(value, dict):
                doc.add_paragraph(f"{key.replace('_', ' ').title()}:", style='Heading 2')
                for k, v in value.items():
                    doc.add_paragraph(f"  {k}: {v}")

    def _add_confidentiality_notice(self, doc: Document, doc_data: Dict[str, Any]):
        """Add confidentiality notice at bottom of document."""
        # Only add if notice is present and not empty
        notice_text = doc_data.get('confidentiality_notice', '')
        if not notice_text:
            return  # Skip if no notice

        doc.add_paragraph()
        notice = doc.add_paragraph()
        notice.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = notice.add_run('CONFIDENTIALITY NOTICE:')
        run.bold = True
        run.font.size = Pt(10)

        notice_para = doc.add_paragraph()
        notice_para.add_run(notice_text)
        notice_para.runs[0].font.size = Pt(9)
        notice_para.runs[0].italic = True

    def _add_classification_footer(self, doc: Document, doc_data: Dict[str, Any]):
        """Add classification footer."""
        doc.add_paragraph()
        footer = doc.add_paragraph()
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = footer.add_run(doc_data.get('classification', 'CUI'))
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(139, 0, 0)

        # Distribution statement
        if doc_data.get('distribution'):
            dist = doc.add_paragraph()
            dist.alignment = WD_ALIGN_PARAGRAPH.CENTER
            dist_run = dist.add_run(doc_data['distribution'])
            dist_run.font.size = Pt(9)
            dist_run.italic = True

    def _get_default_notice(self) -> str:
        return ("This document contains Controlled Unclassified Information (CUI) that requires "
                "safeguarding or dissemination controls pursuant to applicable laws, regulations, "
                "and Government-wide policies.")


class CUIEmailFormatter:
    """Creates EML email files with CUI content."""

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_cui_email(self, doc_data: Dict[str, Any], filename: str) -> str:
        """
        Create an EML email from CUI data.

        Args:
            doc_data: Dictionary containing CUI document data
            filename: Output filename

        Returns:
            Path to created file
        """
        msg = MIMEMultipart('alternative')

        # Build subject without classification marking (for realistic training data)
        subject = doc_data.get('title', 'Document')

        # Generate sender/recipient
        agency = doc_data.get('agency', 'Department of Health and Human Services')
        agency_domain = agency.lower().replace(' ', '').replace('of', '')[:10] + '.gov'

        msg['Subject'] = subject
        msg['From'] = f"noreply@{agency_domain}"
        msg['To'] = f"recipient@{agency_domain}"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S -0500')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}@{agency_domain}>"

        # Build email body
        plain_text = self._build_plain_text(doc_data)
        html_text = self._build_html(doc_data)

        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_text, 'html'))

        # Save email
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(msg.as_string())
        return filepath

    def _build_plain_text(self, doc_data: Dict[str, Any]) -> str:
        """Build plain text email body."""
        lines = []

        if doc_data.get('has_cui', False):
            lines.append(doc_data.get('classification', 'CONTROLLED UNCLASSIFIED INFORMATION'))
            lines.append('')

        lines.append(doc_data.get('title', 'Document'))
        lines.append('=' * 50)
        lines.append('')

        # Add document content based on type
        doc_type = doc_data.get('document_type', '')

        if doc_type == 'vulnerability_alert':
            lines.extend(self._format_vulnerability_alert_text(doc_data))
        elif doc_type == 'servicenow_ticket':
            lines.extend(self._format_servicenow_text(doc_data))
        else:
            lines.extend(self._format_generic_text(doc_data))

        if doc_data.get('has_cui', False):
            lines.append('')
            lines.append('-' * 50)
            lines.append('CONFIDENTIALITY NOTICE:')
            lines.append(doc_data.get('confidentiality_notice', ''))

        return '\n'.join(lines)

    def _format_vulnerability_alert_text(self, doc_data: Dict[str, Any]) -> list:
        """Format vulnerability alert for plain text."""
        lines = [
            f"Alert ID: {doc_data.get('alert_id', '')}",
            f"Severity: {doc_data.get('severity', '')}",
            f"CVSS Score: {doc_data.get('cvss_score', '')}",
            f"CVE: {doc_data.get('cve_id', '')}",
            '',
            f"Affected System: {doc_data.get('affected_system', '')}",
            f"Affected Versions: {doc_data.get('affected_versions', '')}",
            '',
            'Description:',
            doc_data.get('description', ''),
            '',
        ]
        if 'remediation' in doc_data:
            rem = doc_data['remediation']
            lines.extend([
                'Remediation:',
                f"  Action: {rem.get('action', '')}",
                f"  Target Version: {rem.get('target_version', '')}",
                f"  Deadline: {rem.get('deadline', '')}",
            ])
        return lines

    def _format_servicenow_text(self, doc_data: Dict[str, Any]) -> list:
        """Format ServiceNow ticket for plain text."""
        return [
            f"Ticket Number: {doc_data.get('ticket_number', '')}",
            f"Requester: {doc_data.get('requester', '')}",
            f"Department: {doc_data.get('department', '')}",
            f"Request Type: {doc_data.get('request_type', '')}",
            f"Priority: {doc_data.get('priority', '')}",
            f"Status: {doc_data.get('status', '')}",
            '',
            'Description:',
            doc_data.get('description', ''),
            '',
            f"Assigned To: {doc_data.get('assigned_to', '')}",
            f"Created: {doc_data.get('created_date', '')}",
        ]

    def _format_generic_text(self, doc_data: Dict[str, Any]) -> list:
        """Format generic document for plain text."""
        lines = []
        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'generated_date', 'title',
                       'confidentiality_notice'}

        for key, value in doc_data.items():
            if key in skip_fields:
                continue
            if isinstance(value, (str, int, float)):
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
        return lines

    def _build_html(self, doc_data: Dict[str, Any]) -> str:
        """Build HTML email body."""
        html_parts = ['<html><head></head><body style="font-family: Arial, sans-serif;">']

        if doc_data.get('has_cui', False):
            html_parts.append(
                f'<p style="color: darkred; font-weight: bold; text-align: center;">'
                f'{doc_data.get("classification", "CONTROLLED UNCLASSIFIED INFORMATION")}</p>'
            )

        html_parts.append(f'<h2>{doc_data.get("title", "Document")}</h2>')
        html_parts.append(f'<p><strong>Date:</strong> {doc_data.get("document_date", "")}</p>')
        html_parts.append(f'<p><strong>Organization:</strong> {doc_data.get("agency", "")}</p>')

        # Add content based on document type
        doc_type = doc_data.get('document_type', '')
        if doc_type == 'vulnerability_alert':
            html_parts.append(self._format_vulnerability_alert_html(doc_data))
        else:
            html_parts.append(self._format_generic_html(doc_data))

        if doc_data.get('has_cui', False):
            html_parts.append('<hr>')
            html_parts.append('<p style="font-size: 10px; font-style: italic;">')
            html_parts.append(f'<strong>CONFIDENTIALITY NOTICE:</strong><br>')
            html_parts.append(doc_data.get('confidentiality_notice', ''))
            html_parts.append('</p>')

        html_parts.append('</body></html>')
        return ''.join(html_parts)

    def _format_vulnerability_alert_html(self, doc_data: Dict[str, Any]) -> str:
        """Format vulnerability alert for HTML."""
        severity = doc_data.get('severity', 'Unknown')
        severity_color = {'Critical': 'red', 'High': 'orange', 'Medium': 'yellow', 'Low': 'green'}.get(severity, 'gray')

        return f'''
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr><td><strong>Alert ID:</strong></td><td>{doc_data.get('alert_id', '')}</td></tr>
            <tr><td><strong>Severity:</strong></td><td style="background-color: {severity_color};">{severity}</td></tr>
            <tr><td><strong>CVSS Score:</strong></td><td>{doc_data.get('cvss_score', '')}</td></tr>
            <tr><td><strong>CVE:</strong></td><td>{doc_data.get('cve_id', '')}</td></tr>
            <tr><td><strong>Affected System:</strong></td><td>{doc_data.get('affected_system', '')}</td></tr>
        </table>
        <h3>Description</h3>
        <p>{doc_data.get('description', '')}</p>
        '''

    def _format_generic_html(self, doc_data: Dict[str, Any]) -> str:
        """Format generic document for HTML."""
        html = '<table border="1" cellpadding="5" style="border-collapse: collapse;">'
        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'generated_date', 'title',
                       'confidentiality_notice', 'document_date', 'agency'}

        for key, value in doc_data.items():
            if key in skip_fields:
                continue
            if isinstance(value, (str, int, float)):
                html += f'<tr><td><strong>{key.replace("_", " ").title()}:</strong></td><td>{value}</td></tr>'

        html += '</table>'
        return html


class CUIPdfFormatter:
    """Creates PDF documents with CUI markings."""

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_cui_pdf(self, doc_data: Dict[str, Any], filename: str) -> str:
        """
        Create a PDF document from CUI data.

        Args:
            doc_data: Dictionary containing CUI document data
            filename: Output filename

        Returns:
            Path to created file
        """
        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)

        styles = getSampleStyleSheet()
        story = []

        # Classification header
        if doc_data.get('has_cui', False):
            cui_style = ParagraphStyle(
                'CUIHeader',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.darkred,
                alignment=1,  # Center
                spaceAfter=20,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph(
                doc_data.get('classification', 'CONTROLLED UNCLASSIFIED INFORMATION'),
                cui_style
            ))

        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            alignment=1,
            spaceAfter=20
        )
        story.append(Paragraph(doc_data.get('title', 'Document'), title_style))

        # Metadata
        story.append(Paragraph(f"<b>Organization:</b> {doc_data.get('agency', '')}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {doc_data.get('document_date', '')}", styles['Normal']))
        if doc_data.get('authority'):
            story.append(Paragraph(f"<b>Authority:</b> {doc_data.get('authority', '')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # Content
        self._add_pdf_content(story, doc_data, styles)

        # Confidentiality notice
        if doc_data.get('has_cui', False):
            notice_text = doc_data.get('confidentiality_notice', '')
            if notice_text:  # Only add if present
                story.append(Spacer(1, 30))
                notice_style = ParagraphStyle(
                    'Notice',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=colors.gray,
                    spaceAfter=10
                )
                story.append(Paragraph('<b>CONFIDENTIALITY NOTICE:</b>', notice_style))
                story.append(Paragraph(notice_text, notice_style))

        doc.build(story)
        return filepath

    def _add_pdf_content(self, story: list, doc_data: Dict[str, Any], styles):
        """Add content to PDF story."""
        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'authority', 'distribution',
                       'generated_date', 'document_date', 'agency', 'title',
                       'confidentiality_notice'}

        for key, value in doc_data.items():
            if key in skip_fields:
                continue

            if isinstance(value, str):
                story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", styles['Normal']))
            elif isinstance(value, (int, float)):
                story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", styles['Normal']))
            elif isinstance(value, list):
                story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b>", styles['Normal']))
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            story.append(Paragraph(f"  • {k}: {v}", styles['Normal']))
                    else:
                        story.append(Paragraph(f"  • {item}", styles['Normal']))
            elif isinstance(value, dict):
                story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b>", styles['Normal']))
                for k, v in value.items():
                    story.append(Paragraph(f"  {k.replace('_', ' ').title()}: {v}", styles['Normal']))

            story.append(Spacer(1, 6))


class CUIXlsxFormatter:
    """Creates XLSX spreadsheets with CUI markings."""

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_cui_xlsx(self, doc_data: Dict[str, Any], filename: str) -> str:
        """
        Create an XLSX spreadsheet from CUI data.

        Args:
            doc_data: Dictionary containing CUI document data
            filename: Output filename

        Returns:
            Path to created file
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "CUI Document"

        row = 1

        # Classification header
        if doc_data.get('has_cui', False):
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
            cell = ws.cell(row=row, column=1, value=doc_data.get('classification', 'CUI'))
            cell.font = Font(bold=True, color='8B0000')
            cell.alignment = Alignment(horizontal='center')
            row += 2

        # Title
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
        cell = ws.cell(row=row, column=1, value=doc_data.get('title', 'Document'))
        cell.font = Font(bold=True, size=14)
        cell.alignment = Alignment(horizontal='center')
        row += 2

        # Metadata
        metadata = [
            ('Organization', doc_data.get('agency', '')),
            ('Date', doc_data.get('document_date', '')),
            ('Document ID', doc_data.get('document_id', '')),
        ]
        if doc_data.get('authority'):
            metadata.append(('Authority', doc_data.get('authority', '')))

        for label, value in metadata:
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)
            row += 1

        row += 1

        # Content
        row = self._add_xlsx_content(ws, row, doc_data)

        # Confidentiality notice
        if doc_data.get('has_cui', False):
            notice_text = doc_data.get('confidentiality_notice', '')
            if notice_text:  # Only add if present
                row += 2
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
                cell = ws.cell(row=row, column=1, value='CONFIDENTIALITY NOTICE:')
                cell.font = Font(bold=True, size=9)
                row += 1
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
                ws.cell(row=row, column=1, value=notice_text)

        # Adjust column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20

        filepath = os.path.join(self.output_dir, filename)
        wb.save(filepath)
        return filepath

    def _add_xlsx_content(self, ws, row: int, doc_data: Dict[str, Any]) -> int:
        """Add content to worksheet."""
        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'authority', 'distribution',
                       'generated_date', 'document_date', 'agency', 'title',
                       'confidentiality_notice'}

        for key, value in doc_data.items():
            if key in skip_fields:
                continue

            if isinstance(value, (str, int, float)):
                ws.cell(row=row, column=1, value=key.replace('_', ' ').title()).font = Font(bold=True)
                ws.cell(row=row, column=2, value=str(value))
                row += 1
            elif isinstance(value, list) and value:
                ws.cell(row=row, column=1, value=key.replace('_', ' ').title()).font = Font(bold=True)
                row += 1
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            ws.cell(row=row, column=2, value=k)
                            ws.cell(row=row, column=3, value=str(v))
                            row += 1
                    else:
                        ws.cell(row=row, column=2, value=str(item))
                        row += 1
            elif isinstance(value, dict):
                ws.cell(row=row, column=1, value=key.replace('_', ' ').title()).font = Font(bold=True)
                row += 1
                for k, v in value.items():
                    ws.cell(row=row, column=2, value=k.replace('_', ' ').title())
                    ws.cell(row=row, column=3, value=str(v))
                    row += 1

        return row
