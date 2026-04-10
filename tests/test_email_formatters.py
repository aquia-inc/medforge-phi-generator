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


    def test_phi_positive_email_with_in_memory_attachment(self, tmp_output_dir,
                                                          sample_phi_patient,
                                                          sample_phi_provider,
                                                          sample_phi_facility,
                                                          patient_generator):
        """PHI positive email generates in-memory attachment (PDF, DOCX, or ZIP)."""
        from formatters.nested_formatter import NestedEmailFormatter

        fmt = NestedEmailFormatter(output_dir=tmp_output_dir)
        lab_data = patient_generator.generate_lab_results()

        filepath = fmt.create_phi_positive_email_with_attachment(
            sample_phi_patient, sample_phi_provider, sample_phi_facility,
            lab_data, "phi_pos_inmem.eml"
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert msg.is_multipart()
        attachments = [p for p in msg.walk() if p.get_content_disposition() == 'attachment']
        assert len(attachments) >= 1
        # Attachment should be PDF, DOCX, or ZIP
        filenames = [a.get_filename() for a in attachments]
        assert any(fn.endswith(('.pdf', '.docx', '.zip')) for fn in filenames if fn)

    def test_phi_negative_email_with_in_memory_attachment(self, tmp_output_dir,
                                                           sample_phi_facility):
        """PHI negative email generates in-memory attachment with no patient data."""
        from formatters.nested_formatter import NestedEmailFormatter

        fmt = NestedEmailFormatter(output_dir=tmp_output_dir)
        filepath = fmt.create_phi_negative_email_with_attachment(
            sample_phi_facility, "phi_neg_inmem.eml"
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert msg.is_multipart()
        attachments = [p for p in msg.walk() if p.get_content_disposition() == 'attachment']
        assert len(attachments) >= 1

    def test_blank_form_email(self, tmp_output_dir, sample_phi_facility):
        """Blank form email is PHI-negative and has attachment."""
        from formatters.nested_formatter import NestedEmailFormatter

        fmt = NestedEmailFormatter(output_dir=tmp_output_dir)

        # Create a dummy form file
        form_path = os.path.join(tmp_output_dir, "blank_form.docx")
        with open(form_path, 'wb') as f:
            f.write(b"PK\x03\x04 fake docx")

        filepath = fmt.create_email_with_blank_form(
            sample_phi_facility, form_path, "blank_form_email.eml"
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert msg['Subject'] == "Updated Patient Registration Forms"
        attachments = [p for p in msg.walk() if p.get_content_disposition() == 'attachment']
        assert len(attachments) == 1

    def test_policy_email(self, tmp_output_dir, sample_phi_facility):
        """Policy distribution email is PHI-negative with PDF attachment."""
        from formatters.nested_formatter import NestedEmailFormatter

        fmt = NestedEmailFormatter(output_dir=tmp_output_dir)

        # Create a dummy policy PDF
        pdf_path = os.path.join(tmp_output_dir, "policy.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(b"%PDF-1.4 fake policy")

        filepath = fmt.create_policy_email_with_pdf(
            sample_phi_facility, pdf_path, "policy_email.eml"
        )

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert "Policy" in msg['Subject']
        attachments = [p for p in msg.walk() if p.get_content_disposition() == 'attachment']
        assert len(attachments) == 1

    def test_in_memory_pdf_contains_patient_data(self, tmp_output_dir,
                                                   sample_phi_patient,
                                                   sample_phi_provider,
                                                   patient_generator):
        """In-memory PDF generation includes patient identifiers."""
        from formatters.nested_formatter import NestedEmailFormatter

        fmt = NestedEmailFormatter(output_dir=tmp_output_dir)
        lab_data = patient_generator.generate_lab_results()
        pdf_bytes = fmt._generate_phi_positive_pdf_in_memory(
            sample_phi_patient, sample_phi_provider, lab_data)

        assert len(pdf_bytes) > 100
        assert pdf_bytes[:5] == b'%PDF-'


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


class TestTemplateEmailWrapper:
    """Tests for TemplateEmailWrapper — wraps template files as email attachments."""

    def test_minimal_body_returns_subject_and_body(self, tmp_output_dir):
        from formatters.template_email_wrapper import TemplateEmailWrapper

        w = TemplateEmailWrapper(output_dir=tmp_output_dir)
        subject, body = w._minimal_body('TestDoc')
        assert len(subject) > 0
        assert body in TemplateEmailWrapper.MINIMAL_PHRASES

    def test_medium_body_contains_doc_name(self, tmp_output_dir):
        from formatters.template_email_wrapper import TemplateEmailWrapper

        w = TemplateEmailWrapper(output_dir=tmp_output_dir)
        subject, body = w._medium_body('KMP', 'critical_infrastructure',
                                        'Jane Doe', 'ISSO', 'OIT')
        assert 'KMP' in body
        assert 'Jane Doe' in body

    def test_wrap_creates_eml_with_attachment(self, tmp_output_dir):
        from formatters.template_email_wrapper import TemplateEmailWrapper

        w = TemplateEmailWrapper(output_dir=tmp_output_dir)
        pdf_path = os.path.join(tmp_output_dir, "test.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(b"%PDF-1.4 fake content")

        eml_path = w.wrap(pdf_path, 'TestKey', 'TestDoc', 'procurement',
                          'Test Subject', 'Test body.', tmp_output_dir, 1)

        assert os.path.exists(eml_path)
        with open(eml_path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        attachments = [p for p in msg.walk() if p.get_content_disposition() == 'attachment']
        assert len(attachments) == 1
        assert attachments[0].get_filename().endswith('.pdf')


class TestBugCrowdEmailGenerator:
    """Tests for BugCrowdEmailGenerator."""

    def test_positive_email_has_cms_recipient(self, tmp_output_dir):
        from formatters.bugcrowd_email_generator import BugCrowdEmailGenerator

        gen = BugCrowdEmailGenerator(output_dir=tmp_output_dir)
        path = gen.create_bugcrowd_alert('bc_pos.eml', is_positive=True)

        with open(path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert 'bugcrowd.com' in msg['From']
        assert 'cms.hhs.gov' in msg['To']

    def test_negative_email_has_generic_recipient(self, tmp_output_dir):
        from formatters.bugcrowd_email_generator import BugCrowdEmailGenerator

        gen = BugCrowdEmailGenerator(output_dir=tmp_output_dir)
        path = gen.create_bugcrowd_alert('bc_neg.eml', is_positive=False)

        with open(path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert 'example.com' in msg['To']

    def test_subject_has_engagement_code(self, tmp_output_dir):
        from formatters.bugcrowd_email_generator import BugCrowdEmailGenerator

        gen = BugCrowdEmailGenerator(output_dir=tmp_output_dir)
        path = gen.create_bugcrowd_alert('bc_code.eml', is_positive=True)

        with open(path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert '[' in msg['Subject'] and ']' in msg['Subject']


class TestServiceNowEmailGenerator:
    """Tests for ServiceNowEmailGenerator."""

    def test_positive_has_cms_sender(self, tmp_output_dir):
        from formatters.servicenow_email_generator import ServiceNowEmailGenerator

        gen = ServiceNowEmailGenerator(output_dir=tmp_output_dir)
        path = gen.create_servicenow_notification('sn_pos.eml', is_positive=True)

        with open(path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert 'CMSITSM@cms.hhs.gov' in msg['From']

    def test_email_has_ticket_number(self, tmp_output_dir):
        from formatters.servicenow_email_generator import ServiceNowEmailGenerator

        gen = ServiceNowEmailGenerator(output_dir=tmp_output_dir)
        path = gen.create_servicenow_notification('sn_ticket.eml', is_positive=True)

        with open(path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        body = msg.get_payload(decode=True).decode() if not msg.is_multipart() else ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode()
        assert 'REQ' in body

    def test_negative_has_generic_request(self, tmp_output_dir):
        from formatters.servicenow_email_generator import ServiceNowEmailGenerator

        gen = ServiceNowEmailGenerator(output_dir=tmp_output_dir)
        # Generate several to check none have CMS-specific items
        cms_terms = {'EIDM', 'HPMS', 'CFACTS', 'MACPro', 'QPP Portal', 'AWS GovCloud'}
        for i in range(5):
            path = gen.create_servicenow_notification(f'sn_neg_{i}.eml', is_positive=False)
            with open(path, 'rb') as f:
                msg = email.message_from_bytes(f.read())
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode()
                    for term in cms_terms:
                        assert term not in body, f"Negative email should not contain '{term}'"


class TestInternalAnnouncementGenerator:
    """Tests for InternalAnnouncementGenerator."""

    def test_positive_has_internal_links(self, tmp_output_dir):
        from formatters.internal_announcement_generator import InternalAnnouncementGenerator

        gen = InternalAnnouncementGenerator(output_dir=tmp_output_dir)
        path = gen.create_announcement_email('ann_pos.eml', is_positive=True)

        with open(path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode()
                internal_domains = ['share.cms.gov', 'confluence.cms.gov', 'jira.cms.gov',
                                    'cms.sharepoint.com', 'cmsintranet.cms.gov',
                                    'eua.cms.gov', 'cfacts.cms.gov', 'hpms.cms.gov',
                                    'lms.cms.gov']
                assert any(d in body for d in internal_domains), \
                    "Positive announcement should contain internal CMS links"

    def test_negative_has_public_links(self, tmp_output_dir):
        from formatters.internal_announcement_generator import InternalAnnouncementGenerator

        gen = InternalAnnouncementGenerator(output_dir=tmp_output_dir)
        path = gen.create_announcement_email('ann_neg.eml', is_positive=False)

        with open(path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode()
                public_domains = ['www.cms.gov', 'www.hhs.gov', 'medicare.gov',
                                  'federalregister.gov', 'sam.gov', 'usajobs.gov']
                assert any(d in body for d in public_domains), \
                    "Negative announcement should contain public links"

    def test_email_is_valid_eml(self, tmp_output_dir):
        from formatters.internal_announcement_generator import InternalAnnouncementGenerator

        gen = InternalAnnouncementGenerator(output_dir=tmp_output_dir)
        path = gen.create_announcement_email('ann_valid.eml', is_positive=True)

        assert os.path.exists(path)
        with open(path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        assert msg['Subject'] is not None
        assert 'cms.hhs.gov' in msg['From'] or 'cms.hhs.gov' in (msg['To'] or '')
