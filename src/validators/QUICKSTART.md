# PHI Validator - Quick Start Guide

## Installation

Ensure dependencies are installed:

```bash
cd /home/danielbowne/Desktop/synth_phi_data
uv sync
```

## Quick Usage

### 1. Validate a Single Document

```python
from src.validators.phi_validator import PHIValidator

validator = PHIValidator()
result = validator.validate_document('path/to/document.docx', expected_phi_type='positive')

print(f"Valid: {result.is_valid}")
print(f"PHI Elements: {len(result.phi_elements_found)}")
```

### 2. Batch Validation

```python
from src.validators.phi_validator import validate_batch

report = validate_batch(
    ['file1.pdf', 'file2.docx', 'file3.xlsx'],
    expected_phi_type='positive',
    output_report='report.json'
)

print(f"Pass Rate: {report['summary']['pass_rate']}%")
```

### 3. Using Test Scripts

```bash
# Test all files in output directory
python3 src/validators/test_validator.py

# Test specific file
python3 src/validators/test_validator.py /path/to/document.pdf

# Run example demonstrations
python3 src/validators/example_usage.py
```

## PHI Element Types Detected

- **name**: Patient names
- **dob**: Date of Birth (MM/DD/YYYY)
- **mrn**: Medical Record Number (MRN######)
- **ssn**: Social Security Number (###-##-####)
- **address**: Physical addresses
- **phone**: Phone numbers ((###) ###-####)
- **email**: Email addresses
- **insurance_id**: Insurance IDs

## Validation Types

1. **PHI-Positive**: Document MUST contain all required PHI elements
   ```python
   validator.check_phi_positive('file.pdf',
       expected_phi_elements={'name', 'dob', 'mrn', 'ssn', 'address', 'phone'})
   ```

2. **PHI-Negative**: Document MUST NOT contain any PHI elements
   ```python
   validator.check_phi_negative('file.pdf')
   ```

3. **Unknown**: Extract PHI without enforcing requirements
   ```python
   elements = validator.extract_phi_elements('file.pdf')
   ```

## Supported Formats

- `.docx` - Microsoft Word
- `.pdf` - PDF documents
- `.xlsx` - Microsoft Excel
- `.pptx` - Microsoft PowerPoint
- `.eml` - Email messages

## Common Patterns

### Check File Integrity Only
```python
is_ok = validator.check_file_integrity('document.pdf')
```

### Extract PHI Elements Only
```python
phi_elements = validator.extract_phi_elements('document.docx')
for elem in phi_elements:
    print(f"{elem.element_type}: {elem.value}")
```

### Generate Validation Report
```python
validator = PHIValidator()
results = [
    validator.validate_document(f, 'positive')
    for f in file_list
]
report = validator.generate_validation_report(
    results,
    output_path='validation_report.json'
)
```

## Output Examples

### ValidationResult Object
```python
result.is_valid              # True/False
result.file_integrity_ok     # True/False
result.phi_elements_found    # List[PHIElement]
result.validation_errors     # List[str]
result.validation_warnings   # List[str]
result.metadata              # Dict
```

### PHIElement Object
```python
elem.element_type    # 'name', 'dob', 'ssn', etc.
elem.value           # The actual value found
elem.location        # Where found (page_1, sheet_Data_row_5, etc.)
elem.confidence      # Confidence score (0.0-1.0)
```

### Validation Report Structure
```json
{
  "summary": {
    "total_documents": 100,
    "passed": 95,
    "failed": 5,
    "pass_rate": 95.0
  },
  "phi_element_distribution": {
    "name": 100,
    "dob": 100,
    "mrn": 100
  },
  "detailed_results": [...]
}
```

## Troubleshooting

### Import Errors
```bash
# Ensure you're in the project directory
cd /home/danielbowne/Desktop/synth_phi_data

# Install dependencies
uv sync
```

### No PHI Detected
- Check document actually contains PHI in expected format
- Review regex patterns in `PHIPatterns` class
- Some formats (scanned PDFs) may not extract text properly

### File Integrity Failures
- Verify file is not corrupted
- Check file extension matches actual format
- Ensure file has read permissions

## Next Steps

- See `README.md` for complete documentation
- Run `example_usage.py` for detailed examples
- Run `test_validator.py` to test your documents
- Review `phi_validator.py` source code for customization

## File Locations

```
/home/danielbowne/Desktop/synth_phi_data/src/validators/
├── phi_validator.py      # Main validator implementation
├── test_validator.py     # Test script
├── example_usage.py      # Usage examples
├── README.md             # Full documentation
└── QUICKSTART.md         # This file
```
