"""
Base email formatter providing shared MIME construction logic.

All email formatters inherit from this class to avoid duplicating
MIME message building, header setup, and file save code.
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate
import os
import random
from typing import List, Optional, Tuple


class BaseEmailFormatter:
    """Shared MIME email construction base class.

    Encapsulates the pattern duplicated across EmailFormatter,
    NestedEmailFormatter, HTMLLabFormatter, SnykEmailGenerator,
    and CUIEmailFormatter.
    """

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _build_and_save_email(
        self,
        subject: str,
        from_addr: str,
        to_addr: str,
        plain_body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Tuple[bytes, str, str]]] = None,
        custom_headers: Optional[dict] = None,
        filename: Optional[str] = None,
        message_id_domain: str = 'healthsystem.org',
    ) -> str:
        """Build a MIME email and save as EML.

        Handles multipart/alternative (text + HTML) and multipart/mixed
        (with attachments). Sets standard headers, charset, and does
        binary write.

        Args:
            subject: Email subject line
            from_addr: Sender address (can include display name)
            to_addr: Recipient address (can include display name)
            plain_body: Plain text email body
            html_body: Optional HTML email body
            attachments: Optional list of (data, filename, subtype) tuples
            custom_headers: Optional dict of extra headers (e.g. X-Mailgun-Tag)
            filename: Output filename (required)
            message_id_domain: Domain for Message-ID header

        Returns:
            Absolute path to the saved EML file
        """
        has_attachments = attachments and len(attachments) > 0

        if has_attachments:
            # Mixed message: body + attachments
            msg = MIMEMultipart('mixed')

            if html_body:
                # Wrap text + HTML in an alternative sub-part
                alt_part = MIMEMultipart('alternative')
                alt_part.attach(MIMEText(plain_body, 'plain', 'utf-8'))
                alt_part.attach(MIMEText(html_body, 'html', 'utf-8'))
                msg.attach(alt_part)
            else:
                msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))

            for data, att_filename, subtype in attachments:
                attachment = MIMEApplication(data, _subtype=subtype)
                attachment.add_header(
                    'Content-Disposition', 'attachment',
                    filename=att_filename,
                )
                msg.attach(attachment)
        else:
            if html_body:
                # Alternative message: text + HTML
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            else:
                # Plain text only
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))

        # Standard headers
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = f"<{random.randint(100000, 999999999)}@{message_id_domain}>"

        # Custom headers
        if custom_headers:
            for key, value in custom_headers.items():
                msg[key] = value

        # Save as EML
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(msg.as_bytes())

        return filepath

    def _attach_file_from_path(self, msg: MIMEMultipart, filepath: str):
        """Attach a file from disk to an existing MIME message.

        Detects MIME type from file extension. Use this when you need
        to attach files from disk to an already-constructed message
        (e.g., NestedEmailFormatter's pre-existing attachment methods).
        """
        ext = os.path.splitext(filepath)[1].lower()

        subtype_map = {
            '.pdf': 'pdf',
            '.docx': 'vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pptx': 'vnd.openxmlformats-officedocument.presentationml.presentation',
            '.zip': 'zip',
        }

        subtype = subtype_map.get(ext, 'octet-stream')

        with open(filepath, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype=subtype)
            attachment.add_header(
                'Content-Disposition', 'attachment',
                filename=os.path.basename(filepath),
            )
            msg.attach(attachment)

    def _attach_binary(self, msg: MIMEMultipart, filename: str, data: bytes, subtype: str):
        """Attach in-memory binary data to an existing MIME message."""
        attachment = MIMEApplication(data, _subtype=subtype)
        attachment.add_header(
            'Content-Disposition', 'attachment',
            filename=filename,
        )
        msg.attach(attachment)
