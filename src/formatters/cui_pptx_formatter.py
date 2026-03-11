"""
CUI PPTX formatter.

Creates PowerPoint presentations with CUI markings and content,
mirroring the PHI PPTXFormatter capabilities for CUI format parity.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from datetime import datetime
import os
from typing import Any, Dict


class CUIPPTXFormatter:
    """Creates PowerPoint presentations with CUI content."""

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_cui_presentation(self, doc_data: Dict[str, Any], filename: str) -> str:
        """
        Create a PPTX presentation from CUI data.

        Slides: Title (classification banner + title), Metadata (agency, date,
        authority), Content (2-3 slides based on doc_data sections),
        Footer (distribution + classification).

        Args:
            doc_data: Dictionary containing CUI document data
            filename: Output filename

        Returns:
            Path to created file
        """
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        classification = doc_data.get('classification', '')
        has_cui = doc_data.get('has_cui', False)
        title_text = doc_data.get('title', 'Document')

        # Slide 1: Title slide with classification banner
        self._add_title_slide(prs, title_text, classification, has_cui, doc_data)

        # Slide 2: Metadata
        self._add_metadata_slide(prs, doc_data)

        # Slides 3+: Content slides
        self._add_content_slides(prs, doc_data)

        # Final slide: Distribution / classification footer
        if has_cui:
            self._add_footer_slide(prs, doc_data, classification)

        filepath = os.path.join(self.output_dir, filename)
        prs.save(filepath)
        return filepath

    def _add_title_slide(self, prs, title_text, classification, has_cui, doc_data):
        """Add title slide with optional classification banner."""
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        title = slide.shapes.title
        subtitle = slide.placeholders[1]

        title.text = title_text
        agency = doc_data.get('agency', '')
        date_str = doc_data.get('document_date', datetime.now().strftime('%B %Y'))
        subtitle.text = f"{agency}\n{date_str}"

        # Add classification banner at top if CUI positive
        if has_cui and classification:
            left = Inches(0)
            top = Inches(0)
            width = Inches(10)
            height = Inches(0.5)
            txBox = slide.shapes.add_textbox(left, top, width, height)
            tf = txBox.text_frame
            p = tf.paragraphs[0]
            p.text = classification
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = RGBColor(139, 0, 0)
            p.alignment = 1  # Center

    def _add_metadata_slide(self, prs, doc_data):
        """Add metadata slide with agency, date, authority."""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = "Document Information"

        left = Inches(1)
        top = Inches(2)
        width = Inches(8)
        height = Inches(4)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame

        fields = [
            ('Agency', doc_data.get('agency', '')),
            ('Date', doc_data.get('document_date', '')),
            ('Authority', doc_data.get('authority', '')),
            ('Category', doc_data.get('category', '').replace('_', ' ').title()),
            ('Document Type', doc_data.get('document_type', '').replace('_', ' ').title()),
        ]

        for label, value in fields:
            if value:
                p = tf.add_paragraph()
                run = p.add_run()
                run.text = f"{label}: "
                run.font.bold = True
                run.font.size = Pt(16)
                run2 = p.add_run()
                run2.text = str(value)
                run2.font.size = Pt(16)

    def _add_content_slides(self, prs, doc_data):
        """Add content slides based on document type."""
        doc_type = doc_data.get('document_type', '')

        if doc_type == 'vulnerability_alert':
            self._add_vulnerability_slides(prs, doc_data)
        elif doc_type in ('budget_memo', 'eft_authorization', 'retirement_estimate'):
            self._add_financial_slides(prs, doc_data)
        elif doc_type in ('investigation_summary', 'criminal_history_check'):
            self._add_law_enforcement_slides(prs, doc_data)
        else:
            self._add_generic_content_slides(prs, doc_data)

    def _add_vulnerability_slides(self, prs, doc_data):
        """Add vulnerability alert content slides."""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = "Vulnerability Details"

        left = Inches(1)
        top = Inches(2)
        width = Inches(8)
        height = Inches(4)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame

        fields = [
            ('Severity', doc_data.get('severity', '')),
            ('CVSS Score', doc_data.get('cvss_score', '')),
            ('CVE', doc_data.get('cve_id', '')),
            ('Affected System', doc_data.get('affected_system', '')),
        ]

        for label, value in fields:
            if value:
                p = tf.add_paragraph()
                run = p.add_run()
                run.text = f"{label}: {value}"
                run.font.size = Pt(16)

        # Description slide
        desc = doc_data.get('description', '')
        if desc:
            slide2 = prs.slides.add_slide(prs.slide_layouts[1])
            slide2.shapes.title.text = "Description & Remediation"
            txBox2 = slide2.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4))
            tf2 = txBox2.text_frame
            tf2.word_wrap = True
            p = tf2.add_paragraph()
            p.text = desc
            p.font.size = Pt(14)

            rem = doc_data.get('remediation', {})
            if isinstance(rem, dict) and rem.get('action'):
                p2 = tf2.add_paragraph()
                p2.text = f"\nRemediation: {rem['action']}"
                p2.font.size = Pt(14)
                p2.font.bold = True

    def _add_financial_slides(self, prs, doc_data):
        """Add financial document content slides."""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = doc_data.get('title', 'Financial Details')

        left = Inches(1)
        top = Inches(2)
        width = Inches(8)
        height = Inches(4)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True

        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'generated_date', 'title',
                       'confidentiality_notice', 'document_date', 'agency', 'authority'}

        for key, value in doc_data.items():
            if key in skip_fields:
                continue
            if isinstance(value, (str, int, float)) and value:
                p = tf.add_paragraph()
                run = p.add_run()
                run.text = f"{key.replace('_', ' ').title()}: {value}"
                run.font.size = Pt(14)

    def _add_law_enforcement_slides(self, prs, doc_data):
        """Add law enforcement content slides."""
        self._add_financial_slides(prs, doc_data)  # Same layout works

    def _add_generic_content_slides(self, prs, doc_data):
        """Add generic content slides for any document type."""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = "Details"

        left = Inches(1)
        top = Inches(2)
        width = Inches(8)
        height = Inches(4)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True

        skip_fields = {'document_id', 'document_type', 'category', 'subcategory',
                       'has_cui', 'classification', 'generated_date', 'title',
                       'confidentiality_notice', 'document_date', 'agency', 'authority'}

        for key, value in doc_data.items():
            if key in skip_fields:
                continue
            if isinstance(value, (str, int, float)) and value:
                p = tf.add_paragraph()
                run = p.add_run()
                run.text = f"{key.replace('_', ' ').title()}: {value}"
                run.font.size = Pt(14)

        # Add description on separate slide if long
        desc = doc_data.get('description', '')
        if desc and len(desc) > 200:
            slide2 = prs.slides.add_slide(prs.slide_layouts[1])
            slide2.shapes.title.text = "Additional Details"
            txBox2 = slide2.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4))
            tf2 = txBox2.text_frame
            tf2.word_wrap = True
            p = tf2.add_paragraph()
            p.text = desc
            p.font.size = Pt(14)

    def _add_footer_slide(self, prs, doc_data, classification):
        """Add distribution/classification footer slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank slide

        # Classification banner
        if classification:
            txBox = slide.shapes.add_textbox(Inches(0), Inches(0), Inches(10), Inches(0.5))
            tf = txBox.text_frame
            p = tf.paragraphs[0]
            p.text = classification
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = RGBColor(139, 0, 0)
            p.alignment = 1

        # Distribution notice
        notice = doc_data.get('confidentiality_notice', '')
        if notice:
            txBox2 = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4))
            tf2 = txBox2.text_frame
            tf2.word_wrap = True
            p2 = tf2.add_paragraph()
            p2.text = "DISTRIBUTION NOTICE"
            p2.font.size = Pt(18)
            p2.font.bold = True

            p3 = tf2.add_paragraph()
            p3.text = notice
            p3.font.size = Pt(12)
