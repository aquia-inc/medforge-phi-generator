"""
Unit tests for CUI document formatters.

Tests that each CUI formatter produces valid, openable output files.
Distinct from test_cui_generators.py which tests the data generation layer.
"""
import email
import os

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation


class TestCUIDocxFormatter:
    """Tests for CUI DOCX document generation."""

    def test_creates_valid_docx(self, tmp_output_dir, sample_cui_data):
        """create_cui_document produces an openable DOCX file."""
        from formatters.cui_formatter import CUIDocxFormatter

        fmt = CUIDocxFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['legal']
        filepath = fmt.create_cui_document(doc_data, "test_legal.docx")

        assert os.path.exists(filepath)
        assert filepath.endswith('.docx')
        doc = Document(filepath)
        assert len(doc.paragraphs) > 0

    def test_with_component_config(self, tmp_output_dir, sample_cui_data):
        """create_cui_document applies component configuration styling."""
        from formatters.cui_formatter import CUIDocxFormatter
        from templates.components import ComponentMixer

        mixer = ComponentMixer(seed=42)
        config = mixer.get_random_configuration()

        fmt = CUIDocxFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['financial']
        filepath = fmt.create_cui_document(doc_data, "test_styled.docx", component_config=config)

        assert os.path.exists(filepath)
        doc = Document(filepath)
        assert len(doc.paragraphs) > 0

    def test_contains_category_content(self, tmp_output_dir, sample_cui_data):
        """Generated DOCX for a category contains relevant text."""
        from formatters.cui_formatter import CUIDocxFormatter

        fmt = CUIDocxFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['tax']
        filepath = fmt.create_cui_document(doc_data, "test_tax.docx")

        doc = Document(filepath)
        full_text = '\n'.join(p.text for p in doc.paragraphs)
        # Tax documents should contain at least the title or some tax-related content
        assert len(full_text) > 50


class TestCUIPdfFormatter:
    """Tests for CUI PDF document generation."""

    def test_creates_valid_pdf(self, tmp_output_dir, sample_cui_data):
        """create_cui_pdf produces a valid PDF file."""
        from formatters.cui_formatter import CUIPdfFormatter

        fmt = CUIPdfFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['procurement']
        filepath = fmt.create_cui_pdf(doc_data, "test_procurement.pdf")

        assert os.path.exists(filepath)
        assert filepath.endswith('.pdf')
        # Verify it starts with PDF magic bytes
        with open(filepath, 'rb') as f:
            header = f.read(5)
        assert header == b'%PDF-'

    def test_with_component_config(self, tmp_output_dir, sample_cui_data):
        """create_cui_pdf applies component configuration (font mapping)."""
        from formatters.cui_formatter import CUIPdfFormatter
        from templates.components import ComponentMixer

        mixer = ComponentMixer(seed=42)
        config = mixer.get_random_configuration()

        fmt = CUIPdfFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['legal']
        filepath = fmt.create_cui_pdf(doc_data, "test_styled.pdf", component_config=config)

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            header = f.read(5)
        assert header == b'%PDF-'


class TestCUIXlsxFormatter:
    """Tests for CUI XLSX spreadsheet generation."""

    def test_creates_valid_xlsx(self, tmp_output_dir, sample_cui_data):
        """create_cui_xlsx produces an openable XLSX file."""
        from formatters.cui_formatter import CUIXlsxFormatter

        fmt = CUIXlsxFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['financial']
        filepath = fmt.create_cui_xlsx(doc_data, "test_financial.xlsx")

        assert os.path.exists(filepath)
        assert filepath.endswith('.xlsx')
        wb = load_workbook(filepath)
        assert len(wb.sheetnames) >= 1
        wb.close()


class TestCUIEmailFormatter:
    """Tests for CUI plain-text email generation."""

    def test_creates_valid_eml(self, tmp_output_dir, sample_cui_data):
        """create_cui_email produces a parseable EML file."""
        from formatters.cui_formatter import CUIEmailFormatter

        fmt = CUIEmailFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['critical_infrastructure']
        filepath = fmt.create_cui_email(doc_data, "test_ci.eml")

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert msg['Subject'] is not None
        assert msg['From'] is not None


class TestCUIPPTXFormatter:
    """Tests for CUI PowerPoint generation."""

    def test_creates_valid_pptx(self, tmp_output_dir, sample_cui_data):
        """create_cui_presentation produces an openable PPTX file."""
        from formatters.cui_pptx_formatter import CUIPPTXFormatter

        fmt = CUIPPTXFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['procurement']
        filepath = fmt.create_cui_presentation(doc_data, "test_procurement.pptx")

        assert os.path.exists(filepath)
        assert filepath.endswith('.pptx')
        prs = Presentation(filepath)
        assert len(prs.slides) >= 1

    def test_with_component_config(self, tmp_output_dir, sample_cui_data):
        """create_cui_presentation applies component configuration."""
        from formatters.cui_pptx_formatter import CUIPPTXFormatter
        from templates.components import ComponentMixer

        mixer = ComponentMixer(seed=42)
        config = mixer.get_random_configuration()

        fmt = CUIPPTXFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['legal']
        filepath = fmt.create_cui_presentation(doc_data, "test_styled.pptx", component_config=config)

        assert os.path.exists(filepath)
        prs = Presentation(filepath)
        assert len(prs.slides) >= 1


class TestCUIHTMLEmailFormatter:
    """Tests for CUI HTML-styled email generation."""

    def test_creates_valid_html_eml(self, tmp_output_dir, sample_cui_data):
        """create_cui_html_email produces a parseable EML with HTML part."""
        from formatters.cui_html_email_formatter import CUIHTMLEmailFormatter

        fmt = CUIHTMLEmailFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['financial']
        filepath = fmt.create_cui_html_email(doc_data, "test_html.eml")

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())

        # Should have HTML content
        parts = list(msg.walk())
        content_types = [p.get_content_type() for p in parts]
        assert 'text/html' in content_types


class TestSnykEmailGenerator:
    """Tests for Snyk vulnerability alert email generation."""

    def test_creates_valid_snyk_eml(self, tmp_output_dir):
        """create_snyk_vulnerability_alert produces a valid EML."""
        from formatters.snyk_email_generator import SnykEmailGenerator

        gen = SnykEmailGenerator(output_dir=tmp_output_dir)
        filepath = gen.create_snyk_vulnerability_alert(
            "test_snyk.eml", is_positive=True
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert msg['Subject'] is not None

    def test_negative_snyk_eml(self, tmp_output_dir):
        """Negative Snyk alert generates without CUI content."""
        from formatters.snyk_email_generator import SnykEmailGenerator

        gen = SnykEmailGenerator(output_dir=tmp_output_dir)
        filepath = gen.create_snyk_vulnerability_alert(
            "test_snyk_neg.eml", is_positive=False
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert msg['Subject'] is not None


class TestNegativeDocumentStructure:
    """Tests for CUI negative document structure."""

    def test_negative_docx_has_structure(self, tmp_output_dir):
        """Negative DOCX documents have expected structure."""
        from formatters.cui_formatter import CUIDocxFormatter
        from generators.cui import CUIGeneratorFactory

        gen = CUIGeneratorFactory.get_generator('legal', seed=42)
        neg_data = gen.generate_negative()

        fmt = CUIDocxFormatter(output_dir=tmp_output_dir)
        filepath = fmt.create_cui_document(neg_data, "test_neg.docx")

        assert os.path.exists(filepath)
        doc = Document(filepath)
        assert len(doc.paragraphs) > 0

    def test_classification_header_present(self, tmp_output_dir, sample_cui_data):
        """When has_cui=True and classification provided, it appears in DOCX."""
        from formatters.cui_formatter import CUIDocxFormatter

        fmt = CUIDocxFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['tax']
        doc_data['has_cui'] = True
        doc_data['classification'] = 'CUI//SP-TAX'

        filepath = fmt.create_cui_document(doc_data, "test_classified.docx")
        doc = Document(filepath)
        full_text = '\n'.join(p.text for p in doc.paragraphs)
        assert 'CUI' in full_text
