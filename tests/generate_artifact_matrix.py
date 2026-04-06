#!/usr/bin/env python3
"""
Artifact Matrix Verification Script

Generates a minimal set of artifacts covering every data type × format combination
and validates each one passes Purview fidelity checks.

Usage:
    uv run python tests/generate_artifact_matrix.py [--output OUTPUT_DIR]
"""
import sys
import os
import json
import random
from collections import defaultdict
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generators.cui import CUIGeneratorFactory
from formatters.cui_formatter import CUIDocxFormatter, CUIEmailFormatter, CUIPdfFormatter, CUIXlsxFormatter
from formatters.cui_pptx_formatter import CUIPPTXFormatter
from formatters.cui_nested_formatter import CUINestedEmailFormatter
from formatters.cui_html_email_formatter import CUIHTMLEmailFormatter
from formatters.snyk_email_generator import SnykEmailGenerator

# PHI formatters
from generators.patient_generator import PatientGenerator, ProviderGenerator, FacilityGenerator
from formatters.docx_formatter_enhanced import EnhancedPHIDocxFormatter
from formatters.pdf_formatter import PHIPDFFormatter
from formatters.xlsx_formatter import XLSXFormatter
from formatters.pptx_formatter import PPTXFormatter
from formatters.email_formatter import EmailFormatter
from formatters.nested_formatter import NestedEmailFormatter
from formatters.html_lab_formatter import HTMLLabFormatter

# Validator
sys.path.insert(0, os.path.dirname(__file__))
from validate_file_fidelity import PurviewFidelityValidator


CUI_CATEGORIES = [
    'critical_infrastructure',
    'financial',
    'law_enforcement',
    'legal',
    'procurement',
    'proprietary',
    'tax',
]

CUI_FORMATS = {
    'pdf': ('CUIPdfFormatter', 'create_cui_pdf'),
    'docx': ('CUIDocxFormatter', 'create_cui_document'),
    'xlsx': ('CUIXlsxFormatter', 'create_cui_xlsx'),
    'eml': ('CUIEmailFormatter', 'create_cui_email'),
    'pptx': ('CUIPPTXFormatter', 'create_cui_presentation'),
    'nested_eml': ('CUINestedEmailFormatter', 'create_cui_email_with_attachment'),
    'html_eml': ('CUIHTMLEmailFormatter', 'create_cui_html_email'),
    'snyk_eml': ('SnykEmailGenerator', 'create_snyk_vulnerability_alert'),
}


def generate_cui_matrix(output_dir: str, seed: int = 42):
    """Generate one CUI artifact per category × format combination."""
    random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    # Initialize CUI generator
    cui_gen = CUIGeneratorFactory.create_composite_generator(
        categories=CUI_CATEGORIES, seed=seed
    )

    # Initialize formatters
    formatters = {
        'pdf': CUIPdfFormatter(output_dir=output_dir),
        'docx': CUIDocxFormatter(output_dir=output_dir),
        'xlsx': CUIXlsxFormatter(output_dir=output_dir),
        'eml': CUIEmailFormatter(output_dir=output_dir),
        'pptx': CUIPPTXFormatter(output_dir=output_dir),
        'nested_eml': CUINestedEmailFormatter(output_dir=output_dir),
        'html_eml': CUIHTMLEmailFormatter(output_dir=output_dir),
        'snyk_eml': SnykEmailGenerator(output_dir=output_dir),
    }

    results = []
    index = 0

    for category in CUI_CATEGORIES:
        for is_positive in [True, False]:
            polarity = "positive" if is_positive else "negative"

            for fmt_key in CUI_FORMATS:
                index += 1
                # Snyk only applies to critical_infrastructure
                if fmt_key == 'snyk_eml' and category != 'critical_infrastructure':
                    continue

                # Generate doc data for this category
                if is_positive:
                    doc_data = cui_gen.generate_positive()
                    # Force category if needed
                    while doc_data.get('category') != category:
                        doc_data = cui_gen.generate_positive()
                else:
                    doc_data = cui_gen.generate_negative()
                    while doc_data.get('category') != category:
                        doc_data = cui_gen.generate_negative()

                ext = 'eml' if fmt_key.endswith('_eml') else fmt_key
                filename = f"matrix_{category}_{polarity}_{fmt_key}_{index:04d}.{ext}"

                try:
                    if fmt_key == 'snyk_eml':
                        filepath = formatters[fmt_key].create_snyk_vulnerability_alert(
                            filename, is_positive=is_positive)
                    elif fmt_key == 'nested_eml':
                        filepath = formatters[fmt_key].create_cui_email_with_attachment(
                            doc_data, filename, is_positive=is_positive)
                    elif fmt_key == 'html_eml':
                        filepath = formatters[fmt_key].create_cui_html_email(doc_data, filename)
                    elif fmt_key == 'pptx':
                        filepath = formatters[fmt_key].create_cui_presentation(doc_data, filename)
                    elif fmt_key == 'eml':
                        filepath = formatters[fmt_key].create_cui_email(doc_data, filename)
                    elif fmt_key == 'pdf':
                        filepath = formatters[fmt_key].create_cui_pdf(doc_data, filename)
                    elif fmt_key == 'docx':
                        filepath = formatters[fmt_key].create_cui_document(doc_data, filename)
                    elif fmt_key == 'xlsx':
                        filepath = formatters[fmt_key].create_cui_xlsx(doc_data, filename)

                    results.append({
                        'category': category,
                        'polarity': polarity,
                        'format': fmt_key,
                        'filename': filename,
                        'filepath': filepath,
                        'status': 'generated',
                    })
                except Exception as e:
                    results.append({
                        'category': category,
                        'polarity': polarity,
                        'format': fmt_key,
                        'filename': filename,
                        'filepath': None,
                        'status': f'ERROR: {e}',
                    })

    return results


def generate_phi_matrix(output_dir: str, seed: int = 42):
    """Generate a minimal PHI artifact set across all formats."""
    random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    patient_gen = PatientGenerator(seed=seed)
    provider_gen = ProviderGenerator(seed=seed)
    facility_gen = FacilityGenerator(seed=seed)

    patient = patient_gen.generate_patient()
    provider = provider_gen.generate_provider()
    facility = facility_gen.generate_facility()

    phi_formatters = {
        'pdf': PHIPDFFormatter(output_dir=output_dir),
        'docx': EnhancedPHIDocxFormatter(output_dir=output_dir),
        'xlsx': XLSXFormatter(output_dir=output_dir),
        'eml': EmailFormatter(output_dir=output_dir),
        'pptx': PPTXFormatter(output_dir=output_dir),
        'nested_eml': NestedEmailFormatter(output_dir=output_dir),
        'html_eml': HTMLLabFormatter(output_dir=output_dir),
    }

    results = []
    index = 0
    lab = patient_gen.generate_lab_results()

    for is_positive in [True, False]:
        polarity = "positive" if is_positive else "negative"

        for fmt_key in phi_formatters:
            index += 1
            ext = 'eml' if fmt_key.endswith('_eml') else fmt_key
            filename = f"matrix_phi_{polarity}_{fmt_key}_{index:04d}.{ext}"

            try:
                if fmt_key == 'pdf':
                    if is_positive:
                        filepath = phi_formatters[fmt_key].create_lab_result(
                            patient, provider, facility, lab, filename)
                    else:
                        filepath = phi_formatters[fmt_key].create_generic_medical_policy(
                            facility, filename)

                elif fmt_key == 'docx':
                    if is_positive:
                        filepath = phi_formatters[fmt_key].create_lab_result(
                            patient, provider, facility, lab, filename)
                    else:
                        filepath = phi_formatters[fmt_key].create_progress_note_enhanced(
                            patient, provider, facility, filename)

                elif fmt_key == 'xlsx':
                    if is_positive:
                        filepath = phi_formatters[fmt_key].create_lab_results_spreadsheet(
                            patient, provider, facility, lab, filename)
                    else:
                        filepath = phi_formatters[fmt_key].create_billing_summary(
                            facility, filename)

                elif fmt_key == 'eml':
                    if is_positive:
                        filepath = phi_formatters[fmt_key].create_provider_to_provider_email(
                            patient, provider, provider, filename)
                    else:
                        filepath = phi_formatters[fmt_key].create_office_announcement(
                            facility, filename)

                elif fmt_key == 'pptx':
                    if is_positive:
                        filepath = phi_formatters[fmt_key].create_case_study_presentation(
                            patient, provider, facility, filename)
                    else:
                        filepath = phi_formatters[fmt_key].create_educational_presentation(
                            facility, filename)

                elif fmt_key == 'nested_eml':
                    if is_positive:
                        filepath = phi_formatters[fmt_key].create_phi_positive_email_with_attachment(
                            patient, provider, facility, lab, filename)
                    else:
                        filepath = phi_formatters[fmt_key].create_phi_negative_email_with_attachment(
                            facility, filename)

                elif fmt_key == 'html_eml':
                    if is_positive:
                        filepath = phi_formatters[fmt_key].create_lab_result_email_phi_positive(
                            patient, provider, facility, lab, filename)
                    else:
                        filepath = phi_formatters[fmt_key].create_lab_notification_phi_negative(
                            facility, filename)

                # Some PHI formatters return (filepath, was_enhanced) tuples
                if isinstance(filepath, tuple):
                    filepath = filepath[0]

                results.append({
                    'category': 'phi',
                    'polarity': polarity,
                    'format': fmt_key,
                    'filename': filename,
                    'filepath': filepath,
                    'status': 'generated',
                })
            except Exception as e:
                results.append({
                    'category': 'phi',
                    'polarity': polarity,
                    'format': fmt_key,
                    'filename': filename,
                    'filepath': None,
                    'status': f'ERROR: {e}',
                })

    return results


def validate_results(results: list) -> dict:
    """Validate all generated files against Purview fidelity checks."""
    validator = PurviewFidelityValidator()
    validation_results = []

    for entry in results:
        if entry['status'] != 'generated' or not entry['filepath']:
            entry['validation'] = 'SKIPPED (generation failed)'
            continue

        filepath = entry['filepath']
        if not os.path.exists(filepath):
            entry['validation'] = 'SKIPPED (file not found)'
            continue

        result = validator.validate_file(filepath)
        entry['validation'] = 'SAFE' if result.is_purview_safe else 'UNSAFE'
        entry['fatal_issues'] = result.fatal_count
        entry['high_issues'] = result.high_count
        entry['medium_issues'] = result.medium_count
        entry['issues'] = [
            {'check': num, 'severity': sev, 'description': desc}
            for num, sev, desc in result.issues
        ]
        validation_results.append(result)

    return {
        'total': len(results),
        'generated': sum(1 for r in results if r['status'] == 'generated'),
        'errors': sum(1 for r in results if r['status'].startswith('ERROR')),
        'safe': sum(1 for r in results if r.get('validation') == 'SAFE'),
        'unsafe': sum(1 for r in results if r.get('validation') == 'UNSAFE'),
    }


def print_matrix(results: list, summary: dict):
    """Print a formatted matrix table."""
    print("\n" + "=" * 80)
    print("ARTIFACT MATRIX VERIFICATION REPORT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 80)

    print(f"\nTotal artifacts:   {summary['total']}")
    print(f"Generated:         {summary['generated']}")
    print(f"Generation errors: {summary['errors']}")
    print(f"Purview SAFE:      {summary['safe']}")
    print(f"Purview UNSAFE:    {summary['unsafe']}")

    # Group by category
    by_category = defaultdict(list)
    for r in results:
        by_category[r['category']].append(r)

    for category in sorted(by_category.keys()):
        entries = by_category[category]
        print(f"\n--- {category.upper()} ---")
        for e in entries:
            status_icon = "OK" if e.get('validation') == 'SAFE' else \
                         "!!" if e.get('validation') == 'UNSAFE' else \
                         "XX" if e['status'].startswith('ERROR') else "??"
            fmt_display = f"{e['format']:12s}"
            polarity_display = f"{e['polarity']:8s}"
            print(f"  [{status_icon}] {polarity_display} {fmt_display} {e['filename']}")
            if e['status'].startswith('ERROR'):
                print(f"       {e['status']}")
            elif e.get('validation') == 'UNSAFE':
                for issue in e.get('issues', []):
                    if issue['severity'] == 'FATAL':
                        print(f"       !!! [{issue['severity']}] Check {issue['check']}: {issue['description']}")

    # Summary
    errors = [r for r in results if r['status'].startswith('ERROR')]
    unsafe = [r for r in results if r.get('validation') == 'UNSAFE']

    if errors:
        print(f"\nGENERATION ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e['category']}/{e['polarity']}/{e['format']}: {e['status']}")

    if unsafe:
        print(f"\nPURVIEW UNSAFE ({len(unsafe)}):")
        for e in unsafe:
            print(f"  {e['filename']}")

    if not errors and not unsafe:
        print("\nAll artifacts generated and validated successfully!")

    print("=" * 80)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Artifact Matrix Verification")
    parser.add_argument("--output", "-o", default="output/artifact_matrix",
                        help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    print(f"Generating artifact matrix in: {args.output}")

    # Generate CUI matrix
    cui_dir = os.path.join(args.output, 'cui')
    print("\nGenerating CUI artifacts...")
    cui_results = generate_cui_matrix(cui_dir, seed=args.seed)
    print(f"  Generated {sum(1 for r in cui_results if r['status'] == 'generated')} CUI artifacts "
          f"({sum(1 for r in cui_results if r['status'].startswith('ERROR'))} errors)")

    # Generate PHI matrix
    phi_dir = os.path.join(args.output, 'phi')
    print("\nGenerating PHI artifacts...")
    phi_results = generate_phi_matrix(phi_dir, seed=args.seed)
    print(f"  Generated {sum(1 for r in phi_results if r['status'] == 'generated')} PHI artifacts "
          f"({sum(1 for r in phi_results if r['status'].startswith('ERROR'))} errors)")

    all_results = cui_results + phi_results

    # Validate
    print("\nValidating all artifacts...")
    summary = validate_results(all_results)

    if args.json:
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': summary,
            'results': all_results,
        }
        report_path = os.path.join(args.output, 'matrix_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"JSON report written to: {report_path}")
    else:
        print_matrix(all_results, summary)

    # Exit code
    if summary['errors'] > 0 or summary['unsafe'] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
