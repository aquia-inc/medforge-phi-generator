#!/usr/bin/env python3
"""
Batch Document Generator with 80/20 Template/LLM Mix
Generates multiple documents across all formats with statistics tracking
"""
import sys
import os
import random
from datetime import datetime
from collections import defaultdict

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generators.patient_generator import PatientGenerator, ProviderGenerator, FacilityGenerator
from formatters.docx_formatter_enhanced import EnhancedPHIDocxFormatter
from formatters.pdf_formatter import PHIPDFFormatter
from formatters.xlsx_formatter import XLSXFormatter
from formatters.pptx_formatter import PPTXFormatter
from formatters.email_formatter import EmailFormatter
from formatters.nested_formatter import NestedEmailFormatter
from generators.llm_generator import is_llm_available


class BatchGenerator:
    """Generate batches of synthetic PHI documents"""

    def __init__(self, output_dir='output/batch_generation', seed=None, llm_percentage=0.2):
        """
        Initialize batch generator

        Args:
            output_dir: Output directory
            seed: Random seed for reproducibility
            llm_percentage: Percentage of documents to use LLM (0.0-1.0)
        """
        self.output_dir = output_dir
        self.seed = seed
        self.llm_percentage = llm_percentage

        # Statistics
        self.stats = {
            'total_generated': 0,
            'llm_enhanced': 0,
            'template_based': 0,
            'by_format': defaultdict(int),
            'by_category': defaultdict(int),
            'phi_positive': 0,
            'phi_negative': 0,
        }

        # Initialize generators
        self.patient_gen = PatientGenerator(seed=seed)
        self.provider_gen = ProviderGenerator(seed=seed)
        self.facility_gen = FacilityGenerator(seed=seed)

        # Initialize formatters
        self.docx_formatter = EnhancedPHIDocxFormatter(
            output_dir=output_dir,
            llm_percentage=llm_percentage
        )
        self.pdf_formatter = PHIPDFFormatter(output_dir=output_dir)
        self.xlsx_formatter = XLSXFormatter(output_dir=output_dir)
        self.pptx_formatter = PPTXFormatter(output_dir=output_dir)
        self.email_formatter = EmailFormatter(output_dir=output_dir)
        self.nested_formatter = NestedEmailFormatter(output_dir=output_dir)

    def generate_phi_positive_batch(self, count=50):
        """
        Generate PHI positive documents

        Args:
            count: Number of documents to generate

        Returns:
            List of generated file paths
        """
        print(f"\nGenerating {count} PHI POSITIVE documents...")
        print("-" * 80)

        files = []
        patients = [self.patient_gen.generate_patient() for _ in range(count)]
        providers = [self.provider_gen.generate_provider() for _ in range(10)]
        facilities = [self.facility_gen.generate_facility() for _ in range(5)]

        for i in range(count):
            patient = patients[i]
            provider = random.choice(providers)
            facility = random.choice(facilities)

            # Randomly choose document type
            doc_type = random.choice(['progress_note', 'lab_result', 'email', 'case_study'])

            if doc_type == 'progress_note':
                filename = f"PHI_POS_ProgressNote_{i+1:04d}.docx"
                filepath, used_llm = self.docx_formatter.create_progress_note_enhanced(
                    patient, provider, facility, filename
                )
                self.stats['by_format']['docx'] += 1
                if used_llm:
                    self.stats['llm_enhanced'] += 1
                else:
                    self.stats['template_based'] += 1

            elif doc_type == 'lab_result':
                lab_data = self.patient_gen.generate_lab_results()
                # Alternate between PDF and DOCX
                if i % 2 == 0:
                    filename = f"PHI_POS_LabResult_{i+1:04d}.pdf"
                    filepath = self.pdf_formatter.create_lab_result(
                        patient, provider, facility, lab_data, filename
                    )
                    self.stats['by_format']['pdf'] += 1
                else:
                    filename = f"PHI_POS_LabResult_{i+1:04d}.docx"
                    filepath = self.docx_formatter.create_lab_result(
                        patient, provider, facility, lab_data, filename
                    )
                    self.stats['by_format']['docx'] += 1
                self.stats['template_based'] += 1

            elif doc_type == 'email':
                sender = random.choice(providers)
                recipient = random.choice([p for p in providers if p != sender])
                filename = f"PHI_POS_ProviderEmail_{i+1:04d}.eml"
                filepath = self.email_formatter.create_provider_to_provider_email(
                    patient, sender, recipient, filename
                )
                self.stats['by_format']['eml'] += 1
                self.stats['template_based'] += 1

            elif doc_type == 'case_study':
                filename = f"PHI_POS_CaseStudy_{i+1:04d}.pptx"
                filepath = self.pptx_formatter.create_case_study_presentation(
                    patient, provider, facility, filename
                )
                self.stats['by_format']['pptx'] += 1
                self.stats['template_based'] += 1

            files.append(filepath)
            self.stats['total_generated'] += 1
            self.stats['phi_positive'] += 1
            self.stats['by_category']['clinical'] += 1

            if (i + 1) % 10 == 0:
                print(f"  ✓ Generated {i+1}/{count} documents...")

        print(f"  ✓ Completed: {count} PHI positive documents")
        return files

    def generate_phi_negative_batch(self, count=20):
        """
        Generate PHI negative documents

        Args:
            count: Number of documents to generate

        Returns:
            List of generated file paths
        """
        print(f"\nGenerating {count} PHI NEGATIVE documents...")
        print("-" * 80)

        files = []
        facilities = [self.facility_gen.generate_facility() for _ in range(5)]

        for i in range(count):
            facility = random.choice(facilities)

            # Randomly choose document type
            doc_type = random.choice(['policy', 'announcement', 'education', 'blank_form'])

            if doc_type == 'policy':
                # Alternate between PDF and DOCX
                if i % 2 == 0:
                    filename = f"PHI_NEG_Policy_{i+1:04d}.pdf"
                    filepath = self.pdf_formatter.create_generic_medical_policy(facility, filename)
                    self.stats['by_format']['pdf'] += 1
                else:
                    from formatters.docx_formatter import PHIDocxFormatter
                    docx_fmt = PHIDocxFormatter(output_dir=self.output_dir)
                    filename = f"PHI_NEG_Policy_{i+1:04d}.docx"
                    filepath = docx_fmt.create_generic_medical_policy(facility, filename)
                    self.stats['by_format']['docx'] += 1

            elif doc_type == 'announcement':
                filename = f"PHI_NEG_Announcement_{i+1:04d}.eml"
                filepath = self.email_formatter.create_office_announcement(facility, filename)
                self.stats['by_format']['eml'] += 1

            elif doc_type == 'education':
                filename = f"PHI_NEG_Education_{i+1:04d}.pptx"
                filepath = self.pptx_formatter.create_educational_presentation(facility, filename)
                self.stats['by_format']['pptx'] += 1

            elif doc_type == 'blank_form':
                from formatters.docx_formatter import PHIDocxFormatter
                docx_fmt = PHIDocxFormatter(output_dir=self.output_dir)
                filename = f"PHI_NEG_BlankForm_{i+1:04d}.docx"
                filepath = docx_fmt.create_blank_form_template(facility, filename)
                self.stats['by_format']['docx'] += 1

            files.append(filepath)
            self.stats['total_generated'] += 1
            self.stats['phi_negative'] += 1
            self.stats['by_category']['administrative'] += 1
            self.stats['template_based'] += 1

            if (i + 1) % 10 == 0:
                print(f"  ✓ Generated {i+1}/{count} documents...")

        print(f"  ✓ Completed: {count} PHI negative documents")
        return files

    def print_statistics(self):
        """Print generation statistics"""
        print("\n" + "=" * 80)
        print("GENERATION STATISTICS")
        print("=" * 80)
        print(f"\nTotal Documents Generated: {self.stats['total_generated']}")
        print(f"  - PHI Positive: {self.stats['phi_positive']}")
        print(f"  - PHI Negative: {self.stats['phi_negative']}")
        print()

        print("Generation Method:")
        if self.stats['llm_enhanced'] > 0:
            llm_pct = (self.stats['llm_enhanced'] / self.stats['total_generated']) * 100
            print(f"  - LLM Enhanced: {self.stats['llm_enhanced']} ({llm_pct:.1f}%)")
        print(f"  - Template Based: {self.stats['template_based']}")
        print()

        print("By Format:")
        for fmt, count in sorted(self.stats['by_format'].items()):
            pct = (count / self.stats['total_generated']) * 100
            print(f"  - {fmt.upper()}: {count} ({pct:.1f}%)")
        print()

        print(f"Output Directory: {os.path.abspath(self.output_dir)}")
        print("=" * 80)


def main():
    print("=" * 80)
    print("SYNTHETIC PHI BATCH GENERATOR")
    print("=" * 80)
    print()

    # Configuration
    PHI_POSITIVE_COUNT = 50
    PHI_NEGATIVE_COUNT = 20
    LLM_PERCENTAGE = 0.2  # 20% LLM-enhanced
    SEED = 42

    print(f"Configuration:")
    print(f"  - PHI Positive: {PHI_POSITIVE_COUNT}")
    print(f"  - PHI Negative: {PHI_NEGATIVE_COUNT}")
    print(f"  - LLM Enhancement: {int(LLM_PERCENTAGE * 100)}%")
    print(f"  - Random Seed: {SEED}")
    print(f"  - LLM Available: {'Yes' if is_llm_available() else 'No (using templates)'}")
    print()

    # Initialize generator
    generator = BatchGenerator(
        output_dir='output/batch_generation',
        seed=SEED,
        llm_percentage=LLM_PERCENTAGE
    )

    start_time = datetime.now()

    # Generate PHI positive documents
    phi_pos_files = generator.generate_phi_positive_batch(PHI_POSITIVE_COUNT)

    # Generate PHI negative documents
    phi_neg_files = generator.generate_phi_negative_batch(PHI_NEGATIVE_COUNT)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Print statistics
    generator.print_statistics()
    print(f"\nGeneration Time: {duration:.2f} seconds")
    print(f"Average: {duration / (PHI_POSITIVE_COUNT + PHI_NEGATIVE_COUNT):.2f} seconds per document")
    print()
    print("✓ Batch generation complete!")


if __name__ == '__main__':
    main()
