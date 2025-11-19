#!/usr/bin/env python3
"""
Proof of Concept: Generate 10 sample PHI documents
- 5 PHI Positive (contains patient data)
- 5 PHI Negative (no patient data)
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generators.patient_generator import PatientGenerator, ProviderGenerator, FacilityGenerator
from formatters.docx_formatter import PHIDocxFormatter


def main():
    print("=" * 60)
    print("SYNTHETIC PHI DATA GENERATOR - PROOF OF CONCEPT")
    print("=" * 60)
    print()

    # Initialize generators
    print("Initializing data generators...")
    patient_gen = PatientGenerator(seed=42)
    provider_gen = ProviderGenerator(seed=42)
    facility_gen = FacilityGenerator(seed=42)

    # Initialize document formatter
    output_dir = 'output/poc_documents'
    formatter = PHIDocxFormatter(output_dir=output_dir)

    print(f"Output directory: {output_dir}")
    print()

    # Generate synthetic entities
    print("Generating synthetic entities...")
    patients = [patient_gen.generate_patient() for _ in range(5)]
    providers = [provider_gen.generate_provider() for _ in range(3)]
    facilities = [facility_gen.generate_facility() for _ in range(2)]

    print(f"  - Created {len(patients)} patients")
    print(f"  - Created {len(providers)} providers")
    print(f"  - Created {len(facilities)} facilities")
    print()

    # Generate PHI POSITIVE documents (contains patient data)
    print("Generating PHI POSITIVE documents (contains patient identifiers)...")
    print("-" * 60)

    generated_files = []

    # 3 Lab Results
    for i in range(3):
        patient = patients[i]
        provider = providers[i % len(providers)]
        facility = facilities[i % len(facilities)]
        lab_data = patient_gen.generate_lab_results()

        filename = f"PHI_POSITIVE_LabResult_{i+1:03d}.docx"
        filepath = formatter.create_lab_result(patient, provider, facility, lab_data, filename)

        print(f"  ✓ {filename}")
        print(f"    Patient: {patient['first_name']} {patient['last_name']}, MRN: {patient['mrn']}")
        generated_files.append(filepath)

    # 2 Progress Notes
    for i in range(2):
        patient = patients[i + 3]
        provider = providers[i % len(providers)]
        facility = facilities[i % len(facilities)]

        filename = f"PHI_POSITIVE_ProgressNote_{i+1:03d}.docx"
        filepath = formatter.create_progress_note(patient, provider, facility, filename)

        print(f"  ✓ {filename}")
        print(f"    Patient: {patient['first_name']} {patient['last_name']}, MRN: {patient['mrn']}")
        generated_files.append(filepath)

    print()

    # Generate PHI NEGATIVE documents (no patient data)
    print("Generating PHI NEGATIVE documents (medical context, no patient data)...")
    print("-" * 60)

    # 3 Clinical Policies
    for i in range(3):
        facility = facilities[i % len(facilities)]
        filename = f"PHI_NEGATIVE_ClinicalPolicy_{i+1:03d}.docx"
        filepath = formatter.create_generic_medical_policy(facility, filename)

        print(f"  ✓ {filename}")
        print(f"    Facility: {facility['name']}")
        generated_files.append(filepath)

    # 2 Blank Forms
    for i in range(2):
        facility = facilities[i % len(facilities)]
        filename = f"PHI_NEGATIVE_BlankForm_{i+1:03d}.docx"
        filepath = formatter.create_blank_form_template(facility, filename)

        print(f"  ✓ {filename}")
        print(f"    Facility: {facility['name']}")
        generated_files.append(filepath)

    print()
    print("=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"Total documents generated: {len(generated_files)}")
    print(f"  - PHI Positive: 5")
    print(f"  - PHI Negative: 5")
    print()
    print(f"Output location: {os.path.abspath(output_dir)}")
    print()
    print("✓ All documents ready for review!")


if __name__ == '__main__':
    main()
