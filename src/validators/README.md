# PHI Document Validation System

A comprehensive validation system for Protected Health Information (PHI) documents across multiple file formats.

## Features

### Supported File Formats
- **DOCX** - Microsoft Word documents (using python-docx)
- **PDF** - Portable Document Format (using pdfplumber and PyPDF2)
- **XLSX** - Microsoft Excel spreadsheets (using openpyxl)
- **EML** - Email messages (using extract-msg)
- **PPTX** - Microsoft PowerPoint presentations (using python-pptx)

### Validation Capabilities

1. **PHI Element Detection**
   - Social Security Numbers (SSN): `###-##-####`
   - Medical Record Numbers (MRN): `MRN######`
   - Phone Numbers: `(###) ###-####` and variations
   - Date of Birth (DOB): `##/##/####`
   - Email Addresses
   - Physical Addresses
   - Patient Names
   - Insurance IDs

2. **File Integrity Checks**
   - Verifies files can be opened in their native format
   - Detects corrupted or invalid files
   - Validates file structure (ZIP-based formats)

3. **Validation Types**
   - **PHI-Positive**: Ensures documents contain all required PHI elements
   - **PHI-Negative**: Ensures documents contain NO patient identifiers
   - **Unknown**: General validation and PHI extraction

4. **Comprehensive Reporting**
   - JSON-formatted validation reports
   - Pass/fail statistics by document type
   - PHI element distribution analysis
   - Common error identification
   - Batch validation support

## Installation

The required dependencies are already included in the project's `pyproject.toml`:

```bash
# Install/update dependencies
uv sync
```

Key dependencies:
- `python-docx>=1.2.0` - Word document processing
- `pdfplumber>=0.11.0` - PDF text extraction
- `pypdf2>=3.0.0` - PDF parsing
- `openpyxl>=3.1.5` - Excel spreadsheet processing
- `python-pptx>=1.0.2` - PowerPoint processing
- `extract-msg>=0.55.0` - Email message parsing

## Usage

### Basic Usage

```python
from validators.phi_validator import PHIValidator

# Create validator instance
validator = PHIValidator()

# Validate a single document
result = validator.validate_document(
    '/path/to/document.docx',
    expected_phi_type='positive'  # or 'negative' or 'unknown'
)

# Check results
print(f"Valid: {result.is_valid}")
print(f"File Integrity: {result.file_integrity_ok}")
print(f"PHI Elements Found: {len(result.phi_elements_found)}")

# Display PHI elements
for elem in result.phi_elements_found:
    print(f"  {elem.element_type}: {elem.value} (at {elem.location})")
```

### Batch Validation

```python
from validators.phi_validator import validate_batch

# Validate multiple files
files = [
    '/path/to/doc1.docx',
    '/path/to/doc2.pdf',
    '/path/to/doc3.xlsx',
]

report = validate_batch(
    files,
    expected_phi_type='positive',
    output_report='/path/to/validation_report.json'
)

# View summary
print(f"Total: {report['summary']['total_documents']}")
print(f"Passed: {report['summary']['passed']}")
print(f"Failed: {report['summary']['failed']}")
print(f"Pass Rate: {report['summary']['pass_rate']}%")
```

### Check Specific Validation Types

```python
validator = PHIValidator()

# Check if PHI-positive document has required elements
is_valid = validator.check_phi_positive(
    '/path/to/document.pdf',
    expected_phi_elements={'name', 'dob', 'mrn', 'ssn', 'address', 'phone'}
)

# Check if PHI-negative document has no identifiers
is_clean = validator.check_phi_negative('/path/to/document.pdf')

# Check file integrity only
is_intact = validator.check_file_integrity('/path/to/document.pdf')

# Extract PHI elements without full validation
phi_elements = validator.extract_phi_elements('/path/to/document.pdf')
```

### Using the Test Script

```bash
# Test all files in output directory
python src/validators/test_validator.py

# Test a single file
python src/validators/test_validator.py /path/to/document.docx
```

## API Reference

### PHIValidator

Main validator class for PHI documents.

#### Methods

##### `validate_document(filepath, expected_phi_type='unknown')`
Validate a document for PHI content and integrity.

**Parameters:**
- `filepath` (str): Path to the document
- `expected_phi_type` (str): 'positive', 'negative', or 'unknown'

**Returns:** `ValidationResult` object

##### `check_phi_positive(filepath, expected_phi_elements=None)`
Check if a PHI-positive document contains required identifiers.

**Parameters:**
- `filepath` (str): Path to document
- `expected_phi_elements` (set): Set of required element types

**Returns:** bool

##### `check_phi_negative(filepath)`
Check if a PHI-negative document has NO patient identifiers.

**Returns:** bool

##### `check_file_integrity(filepath)`
Check if file can be opened and is not corrupted.

**Returns:** bool

##### `extract_phi_elements(filepath)`
Extract all PHI elements from a document.

**Returns:** List of `PHIElement` objects

##### `generate_validation_report(results, output_path=None)`
Generate a comprehensive validation report.

**Parameters:**
- `results` (List[ValidationResult]): Validation results
- `output_path` (str, optional): Path to save JSON report

**Returns:** dict

### PHIElement

Dataclass representing a detected PHI element.

**Attributes:**
- `element_type` (str): Type of element (name, dob, mrn, ssn, address, phone, email)
- `value` (str): The actual value found
- `location` (str): Where it was found (page, sheet, slide number, etc.)
- `confidence` (float): Confidence score (default: 1.0)

### ValidationResult

Dataclass containing validation results.

**Attributes:**
- `filepath` (str): Path to validated document
- `is_valid` (bool): Overall validation status
- `file_format` (str): File extension (.docx, .pdf, etc.)
- `file_integrity_ok` (bool): File integrity status
- `expected_phi_type` (str): Expected type (positive/negative/unknown)
- `phi_elements_found` (List[PHIElement]): All PHI elements detected
- `validation_errors` (List[str]): Validation errors
- `validation_warnings` (List[str]): Validation warnings
- `metadata` (dict): File metadata
- `validated_at` (str): ISO timestamp of validation

### PHIPatterns

Regular expression patterns for detecting PHI elements.

**Pattern Constants:**
- `SSN`: Social Security Number pattern
- `MRN`: Medical Record Number pattern
- `PHONE`: Primary phone number pattern
- `PHONE_ALT`: Alternative phone number patterns
- `DOB`: Date of Birth pattern
- `EMAIL`: Email address pattern
- `ADDRESS`: Physical address pattern
- `NAME`: Patient name pattern
- `INSURANCE_ID`: Insurance ID pattern
- `ZIP_CODE`: ZIP code pattern

## Validation Report Format

The JSON validation report includes:

```json
{
  "summary": {
    "total_documents": 100,
    "passed": 95,
    "failed": 5,
    "pass_rate": 95.0,
    "phi_positive_count": 50,
    "phi_negative_count": 50
  },
  "phi_positive_stats": {
    "count": 50,
    "passed": 48,
    "failed": 2,
    "pass_rate": 96.0
  },
  "phi_negative_stats": {
    "count": 50,
    "passed": 47,
    "failed": 3,
    "pass_rate": 94.0
  },
  "format_breakdown": {
    ".docx": {
      "total": 20,
      "passed": 19,
      "failed": 1,
      "pass_rate": 95.0
    }
  },
  "common_errors": [
    {
      "error": "Missing required PHI elements: name",
      "count": 3
    }
  ],
  "phi_element_distribution": {
    "name": 50,
    "dob": 50,
    "mrn": 50,
    "ssn": 50,
    "address": 50,
    "phone": 50
  },
  "generated_at": "2025-11-18T10:30:00",
  "detailed_results": [...]
}
```

## How It Works

### PHI Detection Process

1. **File Format Detection**: Identifies file type by extension
2. **Integrity Check**: Attempts to open file in native format
3. **Text Extraction**: Extracts text content using format-specific libraries
4. **Pattern Matching**: Applies regex patterns to find PHI elements
5. **Deduplication**: Removes duplicate findings
6. **Validation**: Compares findings against expected criteria
7. **Reporting**: Generates detailed validation results

### Format-Specific Extraction

#### DOCX
- Extracts text from paragraphs
- Extracts text from table cells
- Preserves location information (paragraph/table/row/cell)

#### PDF
- Uses pdfplumber for superior text extraction (preferred)
- Falls back to PyPDF2 if pdfplumber fails
- Tracks findings by page number

#### XLSX
- Iterates through all sheets
- Reads cell values
- Tracks findings by sheet/row/column

#### EML
- Extracts subject and body text
- Uses extract-msg for Outlook messages
- Falls back to plain text parsing

#### PPTX
- Extracts text from slide shapes
- Reads table content within slides
- Tracks findings by slide number

## Examples

### Example 1: Validate PHI-Positive Documents

```python
from pathlib import Path
from validators.phi_validator import validate_batch

# Find all PHI-positive documents
phi_positive_dir = Path("output/phi_positive")
files = list(phi_positive_dir.rglob("*.*"))

# Validate and generate report
report = validate_batch(
    [str(f) for f in files],
    expected_phi_type='positive',
    output_report='validation_report_positive.json'
)

# Check for failures
if report['summary']['failed'] > 0:
    print("Failed validations:")
    for result in report['detailed_results']:
        if not result['is_valid']:
            print(f"  - {result['filepath']}")
            for error in result['validation_errors']:
                print(f"    Error: {error}")
```

### Example 2: Custom PHI Element Requirements

```python
validator = PHIValidator()

# Only require name, DOB, and MRN (relaxed requirements)
required_elements = {'name', 'dob', 'mrn'}

is_valid = validator.check_phi_positive(
    'patient_summary.pdf',
    expected_phi_elements=required_elements
)
```

### Example 3: Extract and Analyze PHI

```python
validator = PHIValidator()

# Extract PHI elements
elements = validator.extract_phi_elements('medical_record.docx')

# Analyze distribution
from collections import Counter

element_counts = Counter(elem.element_type for elem in elements)
print("PHI Element Distribution:")
for elem_type, count in element_counts.most_common():
    print(f"  {elem_type}: {count}")

# Find high-confidence names
names = [
    elem.value for elem in elements
    if elem.element_type == 'name' and elem.confidence > 0.8
]
print(f"\nHigh-confidence names: {names}")
```

## Troubleshooting

### Missing Dependencies

If you encounter import errors:

```bash
# Reinstall dependencies
uv sync

# Or install individually
pip install python-docx pdfplumber pypdf2 openpyxl python-pptx extract-msg
```

### PDF Extraction Issues

If PDF text extraction fails:
- Some PDFs may be image-based (scanned documents) - OCR is not currently supported
- Try both pdfplumber and PyPDF2 - validator automatically falls back
- Check if PDF is password-protected

### Pattern Matching Issues

If PHI elements are not being detected:
- Check that patterns match your data format
- Review the `PHIPatterns` class and adjust regex as needed
- Consider the confidence threshold for name detection

### File Integrity Failures

If files fail integrity checks:
- Verify the file is not corrupted
- Ensure file has correct extension
- Check file permissions

## Performance Considerations

- **Large files**: PDF and PPTX processing can be slow for large files
- **Batch validation**: Process files in parallel for better performance
- **Memory usage**: Large XLSX files load entire workbook into memory
- **Text extraction**: pdfplumber is more accurate but slower than PyPDF2

## Future Enhancements

Potential improvements:
- OCR support for image-based PDFs
- Parallel batch processing
- Confidence scoring for all PHI types
- Custom pattern configuration
- HTML and TXT format support
- Redaction suggestions for PHI-negative documents
- Machine learning-based name detection

## License

Part of the synth-phi-data project.
