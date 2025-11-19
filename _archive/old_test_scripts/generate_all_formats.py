#!/usr/bin/env python3
"""
Comprehensive Format Test: Generate documents in all supported formats
- DOCX, PDF, XLSX, PPTX, EML
- Emails with attachments (nested scenarios)
- PHI Positive and PHI Negative examples
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generators.patient_generator import PatientGenerator, ProviderGenerator, FacilityGenerator
from formatters.docx_formatter import PHIDocxFormatter
from formatters.pdf_formatter import PHIPDFFormatter
from formatters.xlsx_formatter import XLSXFormatter
from formatters.pptx_formatter import PPTXFormatter
from formatters.email_formatter import EmailFormatter
from formatters.nested_formatter import NestedEmailFormatter


def main():
    print("=" * 80)
    print("SYNTHETIC PHI DATA GENERATOR - ALL FORMATS TEST")
    print("=" * 80)
    print()

    # Initialize generators
    print("Initializing data generators...")
    patient_gen = PatientGenerator(seed=42)
    provider_gen = ProviderGenerator(seed=42)
    facility_gen = FacilityGenerator(seed=42)

    # Initialize document formatters
    output_dir = 'output/all_formats_test'
    docx_formatter = PHIDocxFormatter(output_dir=output_dir)
    pdf_formatter = PHIPDFFormatter(output_dir=output_dir)
    xlsx_formatter = XLSXFormatter(output_dir=output_dir)
    pptx_formatter = PPTXFormatter(output_dir=output_dir)
    email_formatter = EmailFormatter(output_dir=output_dir)
    nested_formatter = NestedEmailFormatter(output_dir=output_dir)

    print(f"Output directory: {output_dir}")
    print()

    # Generate synthetic entities
    print("Generating synthetic entities...")
    patients = [patient_gen.generate_patient() for _ in range(10)]
    providers = [provider_gen.generate_provider() for _ in range(5)]
    facilities = [facility_gen.generate_facility() for _ in range(3)]

    print(f"  - Created {len(patients)} patients")
    print(f"  - Created {len(providers)} providers")
    print(f"  - Created {len(facilities)} facilities")
    print()

    generated_files = []

    # === PHI POSITIVE DOCUMENTS ===
    print("=" * 80)
    print("GENERATING PHI POSITIVE DOCUMENTS (Contains Patient Identifiers)")
    print("=" * 80)
    print()

    # DOCX Documents
    print("📄 DOCX Format:")
    print("-" * 80)
    patient = patients[0]
    provider = providers[0]
    facility = facilities[0]

    filename = "PHI_POS_LabResult_001.docx"
    lab_data = patient_gen.generate_lab_results()
    filepath = docx_formatter.create_lab_result(patient, provider, facility, lab_data, filename)
    print(f"  ✓ {filename} - Lab result with patient {patient['first_name']} {patient['last_name']}")
    generated_files.append(filepath)

    filename = "PHI_POS_ProgressNote_001.docx"
    filepath = docx_formatter.create_progress_note(patient, provider, facility, filename)
    print(f"  ✓ {filename} - Progress note with SOAP format")
    generated_files.append(filepath)
    print()

    # PDF Documents
    print("📑 PDF Format:")
    print("-" * 80)
    patient = patients[1]
    provider = providers[1]
    facility = facilities[1]

    filename = "PHI_POS_LabResult_001.pdf"
    lab_data = patient_gen.generate_lab_results()
    filepath = pdf_formatter.create_lab_result(patient, provider, facility, lab_data, filename)
    print(f"  ✓ {filename} - PDF lab result with patient {patient['first_name']} {patient['last_name']}")
    generated_files.append(filepath)

    filename = "PHI_POS_ProgressNote_001.pdf"
    filepath = pdf_formatter.create_progress_note(patient, provider, facility, filename)
    print(f"  ✓ {filename} - PDF progress note")
    generated_files.append(filepath)
    print()

    # XLSX Documents
    print("📊 XLSX Format:")
    print("-" * 80)
    patient = patients[2]
    provider = providers[2]
    facility = facilities[2]

    filename = "PHI_POS_LabResults_001.xlsx"
    lab_data = patient_gen.generate_lab_results()
    filepath = xlsx_formatter.create_lab_results_spreadsheet(patient, provider, facility, lab_data, filename)
    print(f"  ✓ {filename} - Excel lab results with patient {patient['first_name']} {patient['last_name']}")
    generated_files.append(filepath)
    print()

    # PPTX Documents
    print("🖼️  PPTX Format:")
    print("-" * 80)
    patient = patients[3]
    provider = providers[3]
    facility = facilities[0]

    filename = "PHI_POS_CaseStudy_001.pptx"
    filepath = pptx_formatter.create_case_study_presentation(patient, provider, facility, filename)
    print(f"  ✓ {filename} - Case study presentation with patient {patient['first_name']} {patient['last_name']}")
    generated_files.append(filepath)
    print()

    # Email Documents
    print("📧 EML Format (Email):")
    print("-" * 80)
    patient = patients[4]
    sender = providers[0]
    recipient = providers[1]

    filename = "PHI_POS_ProviderEmail_001.eml"
    filepath = email_formatter.create_provider_to_provider_email(patient, sender, recipient, filename)
    print(f"  ✓ {filename} - Provider consultation email about patient {patient['first_name']} {patient['last_name']}")
    generated_files.append(filepath)

    patient = patients[5]
    provider = providers[2]
    lab_data = patient_gen.generate_lab_results()

    filename = "PHI_POS_TestResultEmail_001.eml"
    filepath = email_formatter.create_test_result_notification(patient, provider, lab_data, filename)
    print(f"  ✓ {filename} - Test result notification email")
    generated_files.append(filepath)
    print()

    # Nested Documents (Emails with Attachments)
    print("📎 NESTED Format (Email + Attachments):")
    print("-" * 80)
    patient = patients[6]
    provider = providers[3]

    # Create a lab PDF first
    lab_pdf_filename = "Attachment_LabResult_001.pdf"
    lab_data = patient_gen.generate_lab_results()
    lab_pdf_path = pdf_formatter.create_lab_result(patient, provider, facility, lab_data, lab_pdf_filename)

    # Create email with attachment
    filename = "PHI_POS_EmailWithAttachment_001.eml"
    filepath = nested_formatter.create_email_with_lab_attachment(patient, provider, lab_pdf_path, filename)
    print(f"  ✓ {filename} - Email with PDF lab result attached")
    generated_files.append(filepath)

    # Email with multiple attachments
    patient = patients[7]
    provider = providers[4]

    # Create multiple attachments
    attachments = []

    lab_pdf_filename = "Attachment_LabResult_002.pdf"
    lab_data = patient_gen.generate_lab_results()
    lab_pdf = pdf_formatter.create_lab_result(patient, provider, facility, lab_data, lab_pdf_filename)
    attachments.append(lab_pdf)

    progress_docx_filename = "Attachment_ProgressNote_002.docx"
    progress_docx = docx_formatter.create_progress_note(patient, provider, facility, progress_docx_filename)
    attachments.append(progress_docx)

    filename = "PHI_POS_EmailMultipleAttachments_001.eml"
    filepath = nested_formatter.create_email_with_multiple_attachments(patient, provider, attachments, filename)
    print(f"  ✓ {filename} - Email with 2 attachments (PDF + DOCX)")
    generated_files.append(filepath)
    print()

    # === PHI NEGATIVE DOCUMENTS ===
    print("=" * 80)
    print("GENERATING PHI NEGATIVE DOCUMENTS (Medical Context, No Patient Data)")
    print("=" * 80)
    print()

    # DOCX Negative
    print("📄 DOCX Format (Negative):")
    print("-" * 80)
    facility = facilities[0]

    filename = "PHI_NEG_Policy_001.docx"
    filepath = docx_formatter.create_generic_medical_policy(facility, filename)
    print(f"  ✓ {filename} - Clinical policy (no patient data)")
    generated_files.append(filepath)

    filename = "PHI_NEG_BlankForm_001.docx"
    filepath = docx_formatter.create_blank_form_template(facility, filename)
    print(f"  ✓ {filename} - Blank registration form template")
    generated_files.append(filepath)
    print()

    # PDF Negative
    print("📑 PDF Format (Negative):")
    print("-" * 80)
    facility = facilities[1]

    filename = "PHI_NEG_Policy_001.pdf"
    filepath = pdf_formatter.create_generic_medical_policy(facility, filename)
    print(f"  ✓ {filename} - Clinical policy PDF (no patient data)")
    generated_files.append(filepath)
    print()

    # XLSX Negative
    print("📊 XLSX Format (Negative):")
    print("-" * 80)
    facility = facilities[2]

    filename = "PHI_NEG_PatientStats_001.xlsx"
    filepath = xlsx_formatter.create_patient_roster(patients[:5], facility, filename)
    print(f"  ✓ {filename} - Aggregated patient statistics (de-identified)")
    generated_files.append(filepath)

    filename = "PHI_NEG_BillingSummary_001.xlsx"
    filepath = xlsx_formatter.create_billing_summary(facility, filename)
    print(f"  ✓ {filename} - Billing summary (no patient identifiers)")
    generated_files.append(filepath)
    print()

    # PPTX Negative
    print("🖼️  PPTX Format (Negative):")
    print("-" * 80)
    facility = facilities[0]

    filename = "PHI_NEG_Education_001.pptx"
    filepath = pptx_formatter.create_educational_presentation(facility, filename)
    print(f"  ✓ {filename} - Educational presentation (no patient data)")
    generated_files.append(filepath)
    print()

    # Email Negative
    print("📧 EML Format (Negative):")
    print("-" * 80)
    facility = facilities[1]

    filename = "PHI_NEG_Announcement_001.eml"
    filepath = email_formatter.create_office_announcement(facility, filename)
    print(f"  ✓ {filename} - Office announcement email")
    generated_files.append(filepath)

    filename = "PHI_NEG_PolicyUpdate_001.eml"
    filepath = email_formatter.create_policy_update_email(facility, filename)
    print(f"  ✓ {filename} - Policy update email")
    generated_files.append(filepath)
    print()

    # Nested Negative
    print("📎 NESTED Format (Negative):")
    print("-" * 80)
    facility = facilities[2]

    # Create blank form first
    blank_form_filename = "Attachment_BlankForm_001.docx"
    blank_form_path = docx_formatter.create_blank_form_template(facility, blank_form_filename)

    filename = "PHI_NEG_EmailWithBlankForm_001.eml"
    filepath = nested_formatter.create_email_with_blank_form(facility, blank_form_path, filename)
    print(f"  ✓ {filename} - Email with blank form template attached")
    generated_files.append(filepath)

    # Policy with PDF
    policy_pdf_filename = "Attachment_Policy_001.pdf"
    policy_pdf_path = pdf_formatter.create_generic_medical_policy(facility, policy_pdf_filename)

    filename = "PHI_NEG_EmailWithPolicy_001.eml"
    filepath = nested_formatter.create_policy_email_with_pdf(facility, policy_pdf_path, filename)
    print(f"  ✓ {filename} - Email with policy PDF attached")
    generated_files.append(filepath)
    print()

    # === SUMMARY ===
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Total documents generated: {len(generated_files)}")
    print()
    print("Format Breakdown:")
    print("  DOCX:   4 files (2 PHI+, 2 PHI-)")
    print("  PDF:    4 files (2 PHI+, 2 PHI-)")
    print("  XLSX:   3 files (1 PHI+, 2 PHI-)")
    print("  PPTX:   2 files (1 PHI+, 1 PHI-)")
    print("  EML:    4 files (2 PHI+, 2 PHI-)")
    print("  NESTED: 4 files (2 PHI+, 2 PHI-)")
    print(f"  TOTAL:  {len(generated_files)} files")
    print()
    print(f"Output location: {os.path.abspath(output_dir)}")
    print()
    print("✓ All file formats ready for review!")
    print()
    print("Next Steps:")
    print("  1. Review generated documents in your file browser")
    print("  2. Verify PHI positive files contain patient identifiers")
    print("  3. Verify PHI negative files have no patient data")
    print("  4. Test nested emails open correctly with attachments")


if __name__ == '__main__':
    main()
