"""
Unit and functional tests for email formatters.

Covers BaseEmailFormatter MIME construction, NestedEmailFormatter
attachment handling, and CUI nested email generation.
"""
import email
import os



class TestBaseEmailFormatter:
    """Tests for shared MIME construction in BaseEmailFormatter."""

    def test_build_and_save_plain_email(self, tmp_output_dir):
        """_build_and_save_email creates a valid plain-text EML file."""
        from formatters.base_email_formatter import BaseEmailFormatter

        fmt = BaseEmailFormatter(output_dir=tmp_output_dir)
        filepath = fmt._build_and_save_email(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            plain_body="Hello, this is a test.",
            filename="test_plain.eml",
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert msg['Subject'] == "Test Subject"
        assert msg['From'] == "sender@example.com"
        assert msg['To'] == "recipient@example.com"
        assert msg.get_content_type() in ('text/plain', 'multipart/mixed', 'multipart/alternative')

    def test_build_and_save_html_email(self, tmp_output_dir):
        """_build_and_save_email with HTML body creates multipart/alternative."""
        from formatters.base_email_formatter import BaseEmailFormatter

        fmt = BaseEmailFormatter(output_dir=tmp_output_dir)
        filepath = fmt._build_and_save_email(
            subject="HTML Test",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            plain_body="Plain fallback",
            html_body="<html><body><p>HTML content</p></body></html>",
            filename="test_html.eml",
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        # Should have both plain and HTML parts
        parts = list(msg.walk())
        content_types = [p.get_content_type() for p in parts]
        assert 'text/plain' in content_types
        assert 'text/html' in content_types

    def test_build_and_save_email_with_attachment(self, tmp_output_dir):
        """_build_and_save_email with attachment creates multipart/mixed."""
        from formatters.base_email_formatter import BaseEmailFormatter

        fmt = BaseEmailFormatter(output_dir=tmp_output_dir)
        test_data = b"fake PDF content"
        filepath = fmt._build_and_save_email(
            subject="With Attachment",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            plain_body="See attached.",
            attachments=[(test_data, "report.pdf", "pdf")],
            filename="test_attach.eml",
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        # Walk parts to find attachment
        attachments = [
            p for p in msg.walk()
            if p.get_content_disposition() == 'attachment'
        ]
        assert len(attachments) == 1
        assert 'report.pdf' in attachments[0].get_filename()

    def test_attach_binary(self, tmp_output_dir):
        """_attach_binary adds binary data as MIME attachment."""
        from email.mime.multipart import MIMEMultipart
        from formatters.base_email_formatter import BaseEmailFormatter

        fmt = BaseEmailFormatter(output_dir=tmp_output_dir)
        msg = MIMEMultipart()
        fmt._attach_binary(msg, "data.xlsx", b"spreadsheet bytes", "xlsx")

        parts = list(msg.walk())
        attachments = [p for p in parts if p.get_content_disposition() == 'attachment']
        assert len(attachments) == 1


class TestNestedEmailFormatter:
    """Tests for PHI nested email attachment handling."""

    def test_attach_file_pdf(self, tmp_output_dir):
        """_attach_file handles PDF MIME type correctly."""
        from email.mime.multipart import MIMEMultipart
        from formatters.nested_formatter import NestedEmailFormatter

        fmt = NestedEmailFormatter(output_dir=tmp_output_dir)

        # Create a dummy PDF file
        pdf_path = os.path.join(tmp_output_dir, "test.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(b"%PDF-1.4 fake content")

        msg = MIMEMultipart()
        fmt._attach_file(msg, pdf_path)

        parts = list(msg.walk())
        assert len(parts) > 1  # multipart + at least one attachment

    def test_attach_file_docx(self, tmp_output_dir):
        """_attach_file handles DOCX MIME type correctly."""
        from email.mime.multipart import MIMEMultipart
        from formatters.nested_formatter import NestedEmailFormatter

        fmt = NestedEmailFormatter(output_dir=tmp_output_dir)

        # Create a dummy DOCX file (ZIP-based format)
        docx_path = os.path.join(tmp_output_dir, "test.docx")
        with open(docx_path, 'wb') as f:
            f.write(b"PK\x03\x04 fake docx")

        msg = MIMEMultipart()
        fmt._attach_file(msg, docx_path)

        parts = list(msg.walk())
        assert len(parts) > 1

    def test_nested_email_roundtrip(self, tmp_output_dir, sample_phi_patient,
                                     sample_phi_provider, sample_phi_facility):
        """Generate a nested email, parse it, verify structure."""
        from formatters.nested_formatter import NestedEmailFormatter
        from formatters.pdf_formatter import PHIPDFFormatter
        from generators.patient_generator import PatientGenerator

        # First generate a lab PDF to attach
        pdf_fmt = PHIPDFFormatter(output_dir=tmp_output_dir)
        pg = PatientGenerator(seed=42)
        lab_data = pg.generate_lab_results()
        lab_pdf = pdf_fmt.create_lab_result(
            sample_phi_patient, sample_phi_provider, sample_phi_facility,
            lab_data, "lab_for_attach.pdf"
        )

        # Create nested email
        fmt = NestedEmailFormatter(output_dir=tmp_output_dir)
        eml_path = fmt.create_email_with_lab_attachment(
            sample_phi_patient, sample_phi_provider, lab_pdf, "nested_test.eml"
        )

        assert os.path.exists(eml_path)
        with open(eml_path, 'rb') as f:
            msg = email.message_from_bytes(f.read())

        # Verify it's multipart with attachment
        assert msg.is_multipart()
        attachments = [
            p for p in msg.walk()
            if p.get_content_disposition() == 'attachment'
        ]
        assert len(attachments) >= 1


class TestCUINestedEmailFormatter:
    """Tests for CUI nested email generation."""

    def test_cui_nested_email_creates_valid_eml(self, tmp_output_dir, sample_cui_data):
        """CUI nested email produces a parseable EML file."""
        from formatters.cui_nested_formatter import CUINestedEmailFormatter

        fmt = CUINestedEmailFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['legal']
        doc_data['classification'] = 'CUI//SP-LEGAL'
        doc_data['has_cui'] = True

        filepath = fmt.create_cui_email_with_attachment(
            doc_data, "cui_nested_test.eml", is_positive=True
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert msg.is_multipart()

    def test_cui_nested_email_roundtrip(self, tmp_output_dir, sample_cui_data):
        """CUI nested email roundtrip — verify attachment count and types."""
        from formatters.cui_nested_formatter import CUINestedEmailFormatter

        fmt = CUINestedEmailFormatter(output_dir=tmp_output_dir)
        doc_data = sample_cui_data['procurement']
        doc_data['classification'] = 'CUI//SP-PROCURE'
        doc_data['has_cui'] = True

        filepath = fmt.create_cui_email_with_attachment(
            doc_data, "cui_roundtrip.eml", is_positive=True
        )

        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())

        attachments = [
            p for p in msg.walk()
            if p.get_content_disposition() == 'attachment'
        ]
        # Should have at least one attachment (PDF, DOCX, or ZIP)
        assert len(attachments) >= 1
        filenames = [a.get_filename() for a in attachments]
        assert any(
            fn.endswith(('.pdf', '.docx', '.zip'))
            for fn in filenames if fn
        )
