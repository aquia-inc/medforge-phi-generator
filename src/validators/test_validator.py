#!/usr/bin/env python3
"""
Test script for PHI Validator

Demonstrates usage of the PHI validation system.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from validators.phi_validator import PHIValidator, validate_batch


def test_validator():
    """Test the PHI validator with sample files"""

    print("PHI Document Validator - Test Script")
    print("=" * 60)

    validator = PHIValidator()

    # Check what formats are supported
    print("\nSupported Formats:")
    for fmt in sorted(validator.supported_formats):
        print(f"  - {fmt}")

    # Example: Test with a directory of files
    # Adjust this path to your actual test files
    test_dir = Path(__file__).parent.parent.parent / "output"

    if not test_dir.exists():
        print(f"\nTest directory not found: {test_dir}")
        print("Please generate some test documents first.")
        return

    # Find all supported files in output directory
    all_files = []
    for fmt in validator.supported_formats:
        pattern = f"**/*{fmt}"
        files = list(test_dir.glob(pattern))
        all_files.extend(files)

    if not all_files:
        print(f"\nNo test files found in {test_dir}")
        print("Please generate some test documents first.")
        return

    print(f"\nFound {len(all_files)} test files")
    print("\nTesting validation on sample files...")
    print("-" * 60)

    # Test first few files
    sample_files = all_files[:5]

    for filepath in sample_files:
        print(f"\nValidating: {filepath.name}")

        # Determine expected type from filename or path
        expected_type = 'unknown'
        if 'positive' in str(filepath).lower():
            expected_type = 'positive'
        elif 'negative' in str(filepath).lower():
            expected_type = 'negative'

        result = validator.validate_document(str(filepath), expected_type)

        print(f"  Format: {result.file_format}")
        print(f"  Expected Type: {result.expected_phi_type}")
        print(f"  File Integrity: {'✓' if result.file_integrity_ok else '✗'}")
        print(f"  Validation: {'✓ PASSED' if result.is_valid else '✗ FAILED'}")
        print(f"  PHI Elements Found: {len(result.phi_elements_found)}")

        if result.phi_elements_found:
            phi_types = {}
            for elem in result.phi_elements_found:
                phi_types[elem.element_type] = phi_types.get(elem.element_type, 0) + 1

            print("  PHI Distribution:")
            for elem_type, count in sorted(phi_types.items()):
                print(f"    - {elem_type}: {count}")

        if result.validation_errors:
            print("  Errors:")
            for error in result.validation_errors:
                print(f"    - {error}")

        if result.validation_warnings:
            print("  Warnings:")
            for warning in result.validation_warnings:
                print(f"    - {warning}")

    # Generate batch report
    print("\n" + "=" * 60)
    print("Generating Batch Validation Report...")
    print("=" * 60)

    report_path = test_dir / "validation_report.json"

    # Categorize files by expected type
    phi_positive_files = [f for f in all_files if 'positive' in str(f).lower()]
    phi_negative_files = [f for f in all_files if 'negative' in str(f).lower()]

    if phi_positive_files:
        print(f"\nValidating {len(phi_positive_files)} PHI-positive files...")
        report = validate_batch(
            [str(f) for f in phi_positive_files],
            expected_phi_type='positive',
            output_report=str(report_path.parent / "validation_report_positive.json")
        )

        print(f"  Total: {report['summary']['total_documents']}")
        print(f"  Passed: {report['summary']['passed']}")
        print(f"  Failed: {report['summary']['failed']}")
        print(f"  Pass Rate: {report['summary']['pass_rate']}%")

    if phi_negative_files:
        print(f"\nValidating {len(phi_negative_files)} PHI-negative files...")
        report = validate_batch(
            [str(f) for f in phi_negative_files],
            expected_phi_type='negative',
            output_report=str(report_path.parent / "validation_report_negative.json")
        )

        print(f"  Total: {report['summary']['total_documents']}")
        print(f"  Passed: {report['summary']['passed']}")
        print(f"  Failed: {report['summary']['failed']}")
        print(f"  Pass Rate: {report['summary']['pass_rate']}%")

    print(f"\nValidation reports saved to: {report_path.parent}")
    print("\nTest complete!")


def test_single_file(filepath: str):
    """Test validation on a single file"""

    print(f"Validating single file: {filepath}")
    print("=" * 60)

    validator = PHIValidator()

    # Determine expected type
    expected_type = 'unknown'
    if 'positive' in filepath.lower():
        expected_type = 'positive'
    elif 'negative' in filepath.lower():
        expected_type = 'negative'

    result = validator.validate_document(filepath, expected_type)

    print(f"\nFile: {result.filepath}")
    print(f"Format: {result.file_format}")
    print(f"Expected Type: {result.expected_phi_type}")
    print(f"File Integrity: {'✓ OK' if result.file_integrity_ok else '✗ FAILED'}")
    print(f"Validation: {'✓ PASSED' if result.is_valid else '✗ FAILED'}")

    print("\nMetadata:")
    for key, value in result.metadata.items():
        print(f"  {key}: {value}")

    print(f"\nPHI Elements Found: {len(result.phi_elements_found)}")
    if result.phi_elements_found:
        print("\nDetailed PHI Elements:")
        for elem in result.phi_elements_found:
            print(f"  - Type: {elem.element_type}")
            print(f"    Value: {elem.value}")
            print(f"    Location: {elem.location}")
            print(f"    Confidence: {elem.confidence}")
            print()

    if result.validation_errors:
        print("\nValidation Errors:")
        for error in result.validation_errors:
            print(f"  ✗ {error}")

    if result.validation_warnings:
        print("\nValidation Warnings:")
        for warning in result.validation_warnings:
            print(f"  ⚠ {warning}")

    print("\n" + "=" * 60)
    print(f"Result: {'PASSED' if result.is_valid else 'FAILED'}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Test single file if path provided
        test_single_file(sys.argv[1])
    else:
        # Run general tests
        test_validator()
