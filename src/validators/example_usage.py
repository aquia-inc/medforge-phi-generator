#!/usr/bin/env python3
"""
Example usage of the PHI Validator

This script demonstrates common use cases for the PHI validation system.
"""

from pathlib import Path
from validators.phi_validator import PHIValidator, validate_batch


def example_1_single_document():
    """Example 1: Validate a single document"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Single Document Validation")
    print("=" * 70)

    validator = PHIValidator()

    # Replace with actual file path
    filepath = "path/to/your/document.docx"

    # Validate as PHI-positive (should contain PHI)
    result = validator.validate_document(filepath, expected_phi_type='positive')

    print(f"\nFile: {result.filepath}")
    print(f"Format: {result.file_format}")
    print(f"Valid: {result.is_valid}")
    print(f"File Integrity: {result.file_integrity_ok}")
    print(f"\nPHI Elements Found: {len(result.phi_elements_found)}")

    # Group by type
    from collections import defaultdict
    by_type = defaultdict(list)
    for elem in result.phi_elements_found:
        by_type[elem.element_type].append(elem)

    for elem_type, elements in sorted(by_type.items()):
        print(f"\n  {elem_type.upper()} ({len(elements)} found):")
        for elem in elements[:3]:  # Show first 3 of each type
            print(f"    - {elem.value} (at {elem.location})")

    if result.validation_errors:
        print("\nValidation Errors:")
        for error in result.validation_errors:
            print(f"  ✗ {error}")


def example_2_batch_validation():
    """Example 2: Batch validation with report generation"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Batch Validation")
    print("=" * 70)

    # Collect files to validate
    output_dir = Path("output/phi_positive")

    if not output_dir.exists():
        print(f"\nDirectory not found: {output_dir}")
        print("Please generate test documents first.")
        return

    # Get all DOCX files
    files = list(output_dir.glob("**/*.docx"))[:10]  # First 10 files

    print(f"\nValidating {len(files)} DOCX files...")

    # Run batch validation
    report = validate_batch(
        [str(f) for f in files],
        expected_phi_type='positive',
        output_report='validation_report.json'
    )

    # Display summary
    print("\n" + "-" * 70)
    print("VALIDATION SUMMARY")
    print("-" * 70)
    print(f"Total Documents: {report['summary']['total_documents']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Pass Rate: {report['summary']['pass_rate']}%")

    # PHI element distribution
    print("\nPHI Element Distribution:")
    for elem_type, count in sorted(report['phi_element_distribution'].items()):
        print(f"  {elem_type}: {count}")

    # Common errors
    if report['common_errors']:
        print("\nMost Common Errors:")
        for error_info in report['common_errors'][:5]:
            print(f"  [{error_info['count']}x] {error_info['error']}")

    print("\nFull report saved to: validation_report.json")


def example_3_quick_checks():
    """Example 3: Quick validation checks"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Quick Validation Checks")
    print("=" * 70)

    validator = PHIValidator()
    filepath = "path/to/document.pdf"

    # Quick integrity check
    print("\n1. File Integrity Check:")
    is_intact = validator.check_file_integrity(filepath)
    print(f"   File is {'intact' if is_intact else 'corrupted or invalid'}")

    # Check if PHI-positive
    print("\n2. PHI-Positive Check (requires all standard elements):")
    is_phi_positive = validator.check_phi_positive(filepath)
    print(f"   Document {'contains' if is_phi_positive else 'missing'} required PHI")

    # Check if PHI-negative
    print("\n3. PHI-Negative Check (should have no PHI):")
    is_phi_negative = validator.check_phi_negative(filepath)
    print(f"   Document is {'clean (no PHI)' if is_phi_negative else 'contains PHI'}")

    # Extract elements
    print("\n4. Extract PHI Elements:")
    elements = validator.extract_phi_elements(filepath)
    print(f"   Found {len(elements)} PHI elements")


def example_4_custom_requirements():
    """Example 4: Custom PHI element requirements"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Custom PHI Requirements")
    print("=" * 70)

    validator = PHIValidator()
    filepath = "path/to/minimal_document.pdf"

    # Only require name and DOB (relaxed requirements)
    print("\n1. Minimal Requirements (name + DOB only):")
    required = {'name', 'dob'}
    is_valid = validator.check_phi_positive(filepath, expected_phi_elements=required)
    print(f"   Valid with minimal requirements: {is_valid}")

    # Require full set (strict requirements)
    print("\n2. Full Requirements (all standard PHI):")
    required = {'name', 'dob', 'mrn', 'ssn', 'address', 'phone'}
    is_valid = validator.check_phi_positive(filepath, expected_phi_elements=required)
    print(f"   Valid with full requirements: {is_valid}")

    # Custom requirements
    print("\n3. Custom Requirements (name, MRN, phone only):")
    required = {'name', 'mrn', 'phone'}
    is_valid = validator.check_phi_positive(filepath, expected_phi_elements=required)
    print(f"   Valid with custom requirements: {is_valid}")


def example_5_detailed_analysis():
    """Example 5: Detailed PHI analysis"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Detailed PHI Analysis")
    print("=" * 70)

    validator = PHIValidator()
    filepath = "path/to/document.xlsx"

    # Extract all PHI elements
    elements = validator.extract_phi_elements(filepath)

    print(f"\nTotal PHI Elements: {len(elements)}")

    # Analyze by type
    from collections import Counter
    type_counts = Counter(elem.element_type for elem in elements)

    print("\nBy Type:")
    for elem_type, count in type_counts.most_common():
        print(f"  {elem_type}: {count}")

    # Analyze by location
    location_counts = Counter(elem.location.split('_')[0] for elem in elements)

    print("\nBy Location:")
    for location, count in location_counts.most_common(5):
        print(f"  {location}: {count} elements")

    # Show unique values for each type
    print("\nUnique Values by Type:")
    by_type = {}
    for elem in elements:
        if elem.element_type not in by_type:
            by_type[elem.element_type] = set()
        by_type[elem.element_type].add(elem.value)

    for elem_type, values in sorted(by_type.items()):
        print(f"\n  {elem_type.upper()} ({len(values)} unique):")
        for value in list(values)[:3]:  # Show first 3
            print(f"    - {value}")


def example_6_compare_formats():
    """Example 6: Compare validation across formats"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Compare Validation Across Formats")
    print("=" * 70)

    validator = PHIValidator()

    # Same content in different formats
    files = {
        'DOCX': 'path/to/patient_record.docx',
        'PDF': 'path/to/patient_record.pdf',
        'XLSX': 'path/to/patient_record.xlsx',
        'PPTX': 'path/to/patient_record.pptx',
    }

    results = {}
    for format_name, filepath in files.items():
        result = validator.validate_document(filepath, 'positive')
        results[format_name] = result

    # Compare results
    print("\nValidation Results by Format:")
    print("-" * 70)
    print(f"{'Format':<10} {'Valid':<8} {'Integrity':<12} {'PHI Found':<12}")
    print("-" * 70)

    for format_name, result in results.items():
        valid_icon = '✓' if result.is_valid else '✗'
        integrity_icon = '✓' if result.file_integrity_ok else '✗'
        phi_count = len(result.phi_elements_found)

        print(f"{format_name:<10} {valid_icon:<8} {integrity_icon:<12} {phi_count:<12}")

    # PHI detection comparison
    print("\nPHI Elements Detected by Format:")
    all_types = set()
    for result in results.values():
        all_types.update(elem.element_type for elem in result.phi_elements_found)

    for elem_type in sorted(all_types):
        counts = []
        for format_name in files.keys():
            count = sum(1 for elem in results[format_name].phi_elements_found
                       if elem.element_type == elem_type)
            counts.append(f"{format_name}:{count}")
        print(f"  {elem_type}: {', '.join(counts)}")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("PHI VALIDATOR - USAGE EXAMPLES")
    print("=" * 70)

    print("\nNote: Update file paths in the examples before running!")

    examples = [
        example_1_single_document,
        example_2_batch_validation,
        example_3_quick_checks,
        example_4_custom_requirements,
        example_5_detailed_analysis,
        example_6_compare_formats,
    ]

    for i, example_func in enumerate(examples, 1):
        print(f"\n\nRunning Example {i}...")
        try:
            example_func()
        except FileNotFoundError as e:
            print(f"  ⚠ File not found: {e}")
            print("  → Update the file path in the example")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        # Run specific example
        example_num = int(sys.argv[1])
        examples = [
            example_1_single_document,
            example_2_batch_validation,
            example_3_quick_checks,
            example_4_custom_requirements,
            example_5_detailed_analysis,
            example_6_compare_formats,
        ]
        if 1 <= example_num <= len(examples):
            examples[example_num - 1]()
        else:
            print(f"Invalid example number. Choose 1-{len(examples)}")
    else:
        main()
