"""
CUI HTML email formatter.

Creates professional HTML-styled CUI emails with content-type routing:
vulnerability alerts get severity-colored tables, budget memos get
financial tables, legal memos get formal styling.
"""
import os
import random
from typing import Any, Dict

from formatters.base_email_formatter import BaseEmailFormatter


class CUIHTMLEmailFormatter(BaseEmailFormatter):
    """Creates CUI emails with professional HTML styling."""

    def create_cui_html_email(self, doc_data: Dict[str, Any], filename: str) -> str:
        """
        Create a CUI HTML-styled email.

        Routes content to appropriate HTML template based on document type.

        Args:
            doc_data: CUI document data dict
            filename: Output filename

        Returns:
            Path to created EML file
        """
        classification = doc_data.get('classification', '')
        has_cui = doc_data.get('has_cui', False)
        title = doc_data.get('title', 'Document')
        agency = doc_data.get('agency', 'Department of Health and Human Services')
        agency_domain = agency.lower().replace(' ', '').replace('of', '')[:10] + '.gov'

        subject = title
        from_addr = f"noreply@{agency_domain}"
        to_addr = f"recipient@{agency_domain}"

        # Build plain text
        plain_text = self._build_plain_text(doc_data)

        # Build HTML based on document type
        doc_type = doc_data.get('document_type', '')
        if doc_type == 'vulnerability_alert':
            html_body = self._build_vulnerability_html(doc_data, classification, has_cui)
        elif doc_type in ('budget_memo', 'eft_authorization', 'retirement_estimate',
                          'taxpayer_record', 'sam_registration'):
            html_body = self._build_financial_html(doc_data, classification, has_cui)
        elif doc_type in ('investigation_summary', 'criminal_history_check',
                          'admin_proceedings', 'collective_bargaining'):
            html_body = self._build_legal_html(doc_data, classification, has_cui)
        else:
            html_body = self._build_generic_html(doc_data, classification, has_cui)

        return self._build_and_save_email(
            subject=subject,
            from_addr=from_addr,
            to_addr=to_addr,
            plain_body=plain_text,
            html_body=html_body,
            filename=filename,
            message_id_domain=agency_domain,
        )

    def _build_plain_text(self, doc_data: Dict[str, Any]) -> str:
        """Build plain text fallback."""
        lines = []
        classification = doc_data.get('classification', '')
        if doc_data.get('has_cui', False) and classification:
            lines.append(classification)
            lines.append('')

        lines.append(doc_data.get('title', 'Document'))
        lines.append('=' * 50)
        lines.append('')

        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'generated_date', 'title',
                       'confidentiality_notice', 'document_date', 'agency', 'authority'}

        for key, value in doc_data.items():
            if key in skip_fields:
                continue
            if isinstance(value, (str, int, float)) and value:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")

        if doc_data.get('has_cui', False):
            notice = doc_data.get('confidentiality_notice', '')
            if notice:
                lines.append('')
                lines.append('-' * 50)
                lines.append(f'CONFIDENTIALITY NOTICE: {notice}')

        return '\n'.join(lines)

    def _wrap_html(self, content: str, classification: str, has_cui: bool,
                   doc_data: Dict[str, Any], accent_color: str = '#1a5276') -> str:
        """Wrap content in standard CUI HTML email template."""
        banner = ''
        if has_cui and classification:
            banner = f'''
            <tr>
                <td style="background-color: #8b0000; padding: 8px; text-align: center;">
                    <span style="color: #ffffff; font-weight: bold; font-size: 12px;">{classification}</span>
                </td>
            </tr>'''

        notice_html = ''
        if has_cui:
            notice = doc_data.get('confidentiality_notice', '')
            if notice:
                notice_html = f'''
                <tr>
                    <td style="padding: 15px 30px; background-color: #f8f8f8; border-top: 1px solid #ddd;">
                        <p style="font-size: 10px; color: #666; font-style: italic; margin: 0;">
                            <strong>CONFIDENTIALITY NOTICE:</strong> {notice}
                        </p>
                    </td>
                </tr>'''

        agency = doc_data.get('agency', '')
        date_str = doc_data.get('document_date', '')

        return f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background-color: #f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f4f4f4;">
        <tr>
            <td align="center" style="padding: 30px 0;">
                <table role="presentation" width="650" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                    {banner}
                    <tr>
                        <td style="background-color: {accent_color}; padding: 25px 30px; border-radius: {'0' if banner else '6px 6px'} 0 0;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 22px;">{doc_data.get('title', 'Document')}</h1>
                            <p style="color: #ffffff; margin: 8px 0 0 0; opacity: 0.9; font-size: 13px;">{agency} | {date_str}</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 25px 30px;">
                            {content}
                        </td>
                    </tr>
                    {notice_html}
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

    def _build_vulnerability_html(self, doc_data, classification, has_cui):
        """Build vulnerability alert HTML with severity-colored table."""
        severity = doc_data.get('severity', 'Unknown')
        severity_colors = {
            'Critical': '#d32f2f',
            'High': '#f57c00',
            'Medium': '#fbc02d',
            'Low': '#7cb342',
        }
        sev_color = severity_colors.get(severity, '#666')

        content = f'''
            <div style="margin-bottom: 20px;">
                <span style="background: {sev_color}; color: white; padding: 5px 12px; border-radius: 3px; font-weight: bold; font-size: 14px;">
                    {severity.upper()}
                </span>
            </div>
            <table width="100%" cellpadding="8" cellspacing="0" style="border: 1px solid #ddd; border-collapse: collapse; margin: 15px 0;">
                <tr style="background: #f5f5f5;">
                    <td style="border: 1px solid #ddd; font-weight: bold; width: 35%;">Alert ID</td>
                    <td style="border: 1px solid #ddd;">{doc_data.get('alert_id', '')}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; font-weight: bold;">CVSS Score</td>
                    <td style="border: 1px solid #ddd;">{doc_data.get('cvss_score', '')}</td>
                </tr>
                <tr style="background: #f5f5f5;">
                    <td style="border: 1px solid #ddd; font-weight: bold;">CVE</td>
                    <td style="border: 1px solid #ddd;">{doc_data.get('cve_id', '')}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; font-weight: bold;">Affected System</td>
                    <td style="border: 1px solid #ddd;">{doc_data.get('affected_system', '')}</td>
                </tr>
            </table>
            <h3 style="color: #333; margin: 20px 0 10px;">Description</h3>
            <p style="color: #555; line-height: 1.6;">{doc_data.get('description', '')}</p>
        '''

        rem = doc_data.get('remediation', {})
        if isinstance(rem, dict) and rem.get('action'):
            content += f'''
            <div style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin: 20px 0;">
                <h4 style="margin: 0 0 8px;">Remediation</h4>
                <p style="margin: 0;">Action: {rem['action']}</p>
                <p style="margin: 5px 0 0;">Target Version: {rem.get('target_version', 'N/A')}</p>
                <p style="margin: 5px 0 0;">Deadline: {rem.get('deadline', 'N/A')}</p>
            </div>'''

        return self._wrap_html(content, classification, has_cui, doc_data, accent_color='#4a148c')

    def _build_financial_html(self, doc_data, classification, has_cui):
        """Build financial document HTML with table layout."""
        rows = ''
        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'generated_date', 'title',
                       'confidentiality_notice', 'document_date', 'agency', 'authority'}
        i = 0
        for key, value in doc_data.items():
            if key in skip_fields:
                continue
            if isinstance(value, (str, int, float)) and value:
                bg = ' style="background: #f9f9f9;"' if i % 2 == 0 else ''
                rows += f'''
                <tr{bg}>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">{key.replace('_', ' ').title()}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{value}</td>
                </tr>'''
                i += 1

        content = f'''
            <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #ddd; border-collapse: collapse;">
                {rows}
            </table>
        '''
        return self._wrap_html(content, classification, has_cui, doc_data, accent_color='#0d47a1')

    def _build_legal_html(self, doc_data, classification, has_cui):
        """Build legal document HTML with formal styling."""
        rows = ''
        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'generated_date', 'title',
                       'confidentiality_notice', 'document_date', 'agency', 'authority'}
        for key, value in doc_data.items():
            if key in skip_fields:
                continue
            if isinstance(value, (str, int, float)) and value:
                rows += f'''
            <div style="margin-bottom: 12px;">
                <span style="font-weight: bold; color: #333;">{key.replace('_', ' ').title()}:</span>
                <span style="color: #555;">{value}</span>
            </div>'''

        content = f'''
            <div style="border: 1px solid #ddd; padding: 20px; background: #fafafa;">
                {rows}
            </div>
        '''
        return self._wrap_html(content, classification, has_cui, doc_data, accent_color='#37474f')

    def _build_generic_html(self, doc_data, classification, has_cui):
        """Build generic CUI HTML email."""
        rows = ''
        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'generated_date', 'title',
                       'confidentiality_notice', 'document_date', 'agency', 'authority'}
        i = 0
        for key, value in doc_data.items():
            if key in skip_fields:
                continue
            if isinstance(value, (str, int, float)) and value:
                bg = ' style="background: #f5f5f5;"' if i % 2 == 0 else ''
                rows += f'''
                <tr{bg}>
                    <td style="border: 1px solid #e0e0e0; padding: 8px; font-weight: bold; width: 35%;">{key.replace('_', ' ').title()}</td>
                    <td style="border: 1px solid #e0e0e0; padding: 8px;">{value}</td>
                </tr>'''
                i += 1

        content = f'''
            <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e0e0e0; border-collapse: collapse;">
                {rows}
            </table>
        '''
        return self._wrap_html(content, classification, has_cui, doc_data)
