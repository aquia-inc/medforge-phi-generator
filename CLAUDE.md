# MedForge - Synthetic PHI Training Data Generator

> **Alternative names:** PhantomPHI, SyntheticSentinel, DocuMimic
> _Select final name before implementation_

## Project Overview

**Customer:** CMS
**Purpose:** Training Microsoft Purview DLP to detect accidental PHI in SharePoint and other locations
**Repository:** `medforge` or `phantom-phi`
**Deliverables:**

- 1,500 true positive documents (containing PHI)
- 500 false positive documents (medical context, no PHI)
- Multiple formats: PDF, MSG, EML, DOCX, PPTX
- Nested scenarios: files in ZIPs, attachments in emails

---

## Working with Customer-Provided PDF Templates

### Problem
Customer-provided fillable PDF forms (from Elizabeth/CMS) need to be populated with synthetic data. Standard Python PDF libraries (PyPDF2, fillpdf, PyMuPDF) fail to properly render filled form fields in SharePoint/viewers.

### CORRECT Solution: Use `pikepdf` with NeedAppearances Flag

```python
import pikepdf

pdf = pikepdf.open("template.pdf")

# Fill form fields
for field in pdf.Root.AcroForm.Fields:
    field_name = str(field.T) if '/T' in field else None

    if field_name and field_name in your_data:
        value = your_data[field_name]

        # Set field value
        if value is True:
            field['/V'] = pikepdf.Name('/On')  # Checkboxes
        elif value is False:
            field['/V'] = pikepdf.Name('/Off')
        else:
            field['/V'] = str(value)  # Text fields

        # Delete appearance stream to force regeneration
        if '/AP' in field:
            del field['/AP']

# Critical: Tell PDF viewers to regenerate field appearances
pdf.Root.AcroForm['/NeedAppearances'] = True

# Save
pdf.save("output.pdf")
pdf.close()
```

### Why This Works
1. **Sets `/V` values** - Actual form field data
2. **Deletes `/AP`** - Removes stale appearance streams
3. **Sets `/NeedAppearances=True`** - Tells SharePoint/Adobe to regenerate appearances
4. **Result**: Data visible in SharePoint, Adobe, Office 365, but NOT in `pdftotext` (expected)

### What Doesn't Work
- ❌ `fillpdf` - Creates unfillable PDFs in SharePoint
- ❌ `PyMuPDF` (fitz) - "bad rect" errors on complex forms
- ❌ `PyPDF2.PdfWriter.update_page_form_field_values()` - Doesn't persist
- ❌ `pdfrw` - Sets values but doesn't render without appearance regeneration

### Verification
Data is in the PDF even if `pdftotext` doesn't show it. Verify with:
```python
import pikepdf
pdf = pikepdf.open("filled_form.pdf")
for field in pdf.Root.AcroForm.Fields:
    print(f"{field.T}: {field.V}")  # Should show your synthetic data
```

### Customer Templates Successfully Integrated
- ✅ Medical Inquiry Form (PHI) - 29 fields populated
- ✅ EFT Authorization Form (CUI-Finance) - 27 fields populated
- ✅ Reasonable Accommodation Request (CUI-Legal) - 8 fields populated

All use Faker for synthetic data (names, addresses, banks, TINs, medical conditions).

---

## Latest Requirements (Meeting Notes 11/14/2025)

### Project Scope Update: PHI & CUI

**Goal:** Generation of synthetic PHI and CUI materials for training MS Purview classifiers.

### Volume Guidelines

- **Minimum (Seed Sets):**
  - Positive: 50 docs
  - Negative: 150 docs (Microsoft recommends ~3x negatives)
- **Service Constraints:**
  - Max ~500 docs per set processed at training time (most recent 500 used).
- **Target Sweet Spot:**
  - Positives: 200–500
  - Negatives: 400–1,000 (≈2–3x positives)
  - _Rationale:_ Reduces false positives while staying within the effective 500-per-set ceiling.
- **Current Counts (11/14/25):**
  - PHI: 165 Positive / 190 Negative
  - CUI: 144/177 Positive

### CUI Categories (New Requirement)

Focus on these specific CUI elements:

- **Critical Infrastructure:** Emergency Management, Systems Vulnerability, Physical Security
- **Financial:** Bank Secrecy, Budget, EFT, Retirement
- **Law Enforcement:** Criminal History, Investigation
- **Legal:** Admin Proceedings, Collective Bargaining, Privilege
- **Procurement:** Source Selection, Small Business Research
- **Proprietary Business:** Entity Registration, General Proprietary Info
- **Tax:** Federal Taxpayer Info, Written Determinations
- **Other:** Security-related emails (e.g., Snyk reports)

### Negative Data Strategy

**Good Negatives (PHI):**

- Clinical templates/policies with NO identifiers
- Order forms with placeholders only
- De-identified case summaries (Safe Harbor)
- Device manuals, SOPs

**Good Negatives (PII):**

- HR/Finance templates without real data
- Generic announcements (first names only)
- System logs with ticket IDs (no people IDs)

**Hard Negatives (High Value):**

- Documents layout-matching positives but empty/generic
- Appointment reminders without specific details
- Billing statements with no member IDs

**Avoid:**

- Real PHI/PII hidden in metadata/headers
- Redacted positives (unless truly de-identified)
- Low-quality scans

### File Types & Quality

- **Formats:** DOCX/PDF (text or high-quality OCR), XLSX/CSV, EML/MSG, PPTX
- **Style:** Formatting must match positive set
- **Checklist (for Source Templates & Negatives):**
  - [ ] No **real** names, contact info, IDs, or dates tied to persons.
  - [ ] Metadata scrubbed.
  - [ ] Uses same templates/systems as positives.
- **Synthetic Data Approach:**
  - **Positive (PHI) examples:** Will be populated with **fully synthetic** names, identifiers, and medical data.
  - **Tools:** Generation will utilize Python libraries **`faker`** and **`faker-medical`** to create realistic but non-sensitive data.

---

## Command Line Interface Design

### Basic Usage

```bash
# Generate default dataset (1500 TP, 500 FP)
uv run medforge generate

# Custom counts
uv run medforge generate --true-positives 500 --false-positives 200

# Specify output directory
uv run medforge generate --output ./custom_output

# Generate specific file types only
uv run medforge generate --formats pdf,docx,email

# Generate with specific nesting scenarios
uv run medforge generate --nesting simple,complex

# Generate specific document categories
uv run medforge generate --categories lab_results,prescriptions,emails

# Multilingual generation
uv run medforge generate --languages en,es,zh

# Generate PII-only dataset (for comparison/testing)
uv run medforge generate-pii --count 200
```

### Configuration Options

```bash
medforge generate [OPTIONS]

Options:
  --true-positives, -tp INTEGER    Number of true positive documents [default: 1500]
  --false-positives, -fp INTEGER   Number of false positive documents [default: 500]
  --output, -o PATH                Output directory [default: ./output]
  --formats TEXT                   Comma-separated formats: pdf,docx,email,pptx,nested [default: all]
  --nesting TEXT                   Nesting levels: simple,multiple,complex [default: all]
  --categories TEXT                Document categories to generate [default: all]
  --languages TEXT                 Language codes: en,es,zh,vi [default: en]
  --quality TEXT                   Quality distribution: clean,messy,poor [default: 70,20,10]
  --config, -c PATH                Load configuration from YAML file
  --parallel, -p INTEGER           Number of parallel workers [default: 4]
  --dry-run                        Show what would be generated without creating files
  --seed INTEGER                   Random seed for reproducibility
  --pii-only                       Generate PII-only documents (no PHI)
  --validate                       Run validation after generation
  --help                           Show this message and exit
```

### Configuration File (YAML)

```yaml
# medforge_config.yaml
generation:
  true_positives: 1500
  false_positives: 500
  output_dir: "./synthetic_phi_dataset"

counts:
  patients: 750
  providers: 150
  facilities: 50

formats:
  pdf: 0.40
  docx: 0.25
  email: 0.20
  pptx: 0.10
  nested: 0.05

categories:
  clinical:
    lab_results: 200
    progress_notes: 150
    prescriptions: 100
  administrative:
    registration: 150
    billing: 100

languages:
  en_US: 0.90
  es_MX: 0.05
  zh_CN: 0.03
  vi_VN: 0.02

quality:
  clean: 0.70
  messy: 0.20
  poor: 0.10

nesting:
  simple: 0.60
  multiple: 0.30
  complex: 0.10

date_range:
  start: "2022-01-01"
  end: "2024-12-31"

llm:
  provider: "anthropic" # or "google"
  model: "claude-sonnet-4-20250514"
  api_key_env: "ANTHROPIC_API_KEY"

parallel:
  workers: 4

validation:
  auto_validate: true
  check_file_integrity: true
  verify_phi_presence: true
```

---

## PII vs PHI Distinction Strategy

### Problem Statement

**Challenge:** If training data contains too much basic PII (names, addresses, SSNs) without medical context, Purview will trigger on those basic patterns, making it harder to evaluate if the system truly detects PHI (medical information tied to individuals).

### Solution: Separate PII-Only Dataset

**Generate three distinct datasets:**

1. **PHI Dataset (1,500 docs)** - Contains medical + identifying info

   - Name + MRN + diagnosis
   - Name + DOB + lab results
   - Name + insurance + medical procedures
   - **Purpose:** Train Purview to recognize true PHI

2. **False Positive Dataset (500 docs)** - Medical context, NO patient data

   - Doctor office announcements
   - Medical equipment schedules
   - Generic health information
   - **Purpose:** Reduce false positives on medical-themed content

3. **PII-Only Dataset (300 docs)** - Identifying info, NO medical context
   - Employment records (name, SSN, address)
   - General business correspondence with personal info
   - Financial documents (non-medical)
   - **Purpose:** Train Purview to NOT trigger on PII without medical context

### PHI Elements to Always Include (True Positives)

Every true positive document should contain **at minimum**:

- **1 identifier:** Name, MRN, or insurance number
- **1+ medical element:** Diagnosis, medication, lab value, procedure, or clinical note

**Good PHI Examples:**

```
✅ Patient: John Smith, MRN: 123456, Diagnosis: Type 2 Diabetes
✅ Lab Report for Jane Doe (DOB: 01/15/1975) - A1C: 6.8%
✅ Prescription for Robert Lee - Metformin 500mg twice daily
```

### PII-Only Examples (Separate Dataset)

Documents with identifiers but NO medical context:

```
✅ Employee Record: Sarah Johnson, SSN: 123-45-6789, Address: 123 Main St
✅ Invoice to: Michael Chen, Account #98765, Payment due: $500
✅ Background Check for: David Wilson, DOB: 03/20/1980
```

These should **NOT** trigger PHI detection in Purview.

### Implementation in Code

```python
class DocumentGenerator:
    def generate_phi_document(self):
        """Always includes identifier + medical element"""
        doc = {
            'identifier': self.get_patient_identifier(),  # Name, MRN, Insurance
            'medical_element': self.get_medical_data(),   # Diagnosis, meds, labs
            'context': 'clinical'
        }
        return doc

    def generate_pii_document(self):
        """Identifier only, NO medical context"""
        doc = {
            'identifier': self.get_person_identifier(),   # Name, SSN, Address
            'business_context': self.get_business_data(), # Employment, financial
            'context': 'non_medical'
        }
        return doc

    def generate_false_positive(self):
        """Medical context, NO patient identifiers"""
        doc = {
            'medical_terminology': self.get_medical_terms(),
            'no_identifiers': True,
            'context': 'general_medical'
        }
        return doc
```

### Purview Training Strategy

Based on Microsoft's best practices:

1. **Phase 1 - Simulation Mode:**

   - Load all three datasets
   - Run in simulation mode (no blocking)
   - Analyze what Purview detects

2. **Phase 2 - Tuning:**

   - Adjust sensitive information types
   - Create custom classifiers if needed
   - Verify PHI detection vs PII-only

3. **Phase 3 - Validation:**
   - PHI docs should trigger: ~95%+ detection
   - False positives should NOT trigger: <5% false alarms
   - PII-only should NOT trigger: <10% false alarms

### Dataset Distribution (Updated)

**Total: 2,300 documents**

- **PHI (True Positives):** 1,500 documents (65%)
  - All contain identifier + medical element
- **False Positives:** 500 documents (22%)
  - Medical context, no patient data
- **PII-Only (Control Group):** 300 documents (13%)
  - Personal identifiers, no medical context

---

## Architecture Overview

### Core Components

1. **Data Generation Engine** - Creates synthetic patient/provider data
2. **Template System** - Document templates for each category
3. **File Generator** - Creates files in various formats
4. **Composition Engine** - Handles nested scenarios (emails with attachments, ZIPs)
5. **Validation Layer** - Ensures quality and PHI presence/absence

### Technology Stack

- **Python 3.11+**
- **Package Manager:** `uv` (use for all dependency management - faster than pip)
- **Core Libraries:**
  - `Faker` + `faker_medical` - PII/PHI generation
  - `Synthea` - Complete patient medical histories (optional, for realism)
  - `python-docx` - Word document generation
  - `python-pptx` - PowerPoint generation
  - `reportlab` or `fpdf2` - PDF generation
  - `email` library + `msgpack` or `win32com` - MSG/EML creation
  - `zipfile` - Creating nested archives
- **LLM API:** Gemini or Claude API - Template variation generation

### Package Management with uv

```bash
# Initialize project with uv
uv init synthetic-phi-generator
cd synthetic-phi-generator

# Add dependencies
uv add faker faker-medical python-docx python-pptx reportlab

# Run scripts
uv run python generate_data.py

# Sync dependencies
uv sync
```

---

## Data Generation Strategy

### Phase 1: Foundation Data Creation

**Patient Pool (500-1000 synthetic patients):**

```
For each patient generate:
- Demographics (name, DOB, SSN, address, phone, email)
- Medical Record Number (MRN)
- Insurance info (Medicare/Medicaid numbers)
- Medical history:
  - Chronic conditions (2-5 per patient)
  - Current medications (3-10)
  - Allergies
  - Recent visits/encounters
  - Lab results history
  - Procedures/treatments
```

**Provider Pool (100-200 providers):**

```
For each provider:
- Name, NPI number
- Practice name and address
- Specialty
- Contact info
- DEA number (for prescriptions)
- Letterhead design elements
```

**Facility Pool (50 facilities):**

```
- Hospital/clinic names
- Addresses
- Contact information
- Branding elements
```

### Phase 2: Document Category Distribution

**TRUE POSITIVES (1,500 total)**

**Clinical Documents (600 documents, 40%):**

- Lab Results: 200
  - Blood panels (CBC, CMP, lipid panels)
  - Urinalysis
  - COVID/flu tests
  - A1C results
  - Radiology reports
- Progress Notes/SOAP Notes: 150
- Discharge Summaries: 100
- Prescriptions: 100
- Immunization Records: 50

**Administrative/Billing (450 documents, 30%):**

- Patient Registration Forms: 150
- Insurance Verification: 100
- Explanation of Benefits (EOB): 100
- Billing Statements with diagnosis codes: 75
- Prior Authorization Forms: 25

**Correspondence (300 documents, 20%):**

- Provider-to-provider emails: 100
- Provider-to-patient messages: 100
- Care coordination emails: 50
- Test result notifications: 50

**Medicare/Medicaid Specific (150 documents, 10%):**

- CMS-1500 claim forms: 50
- Medicare enrollment documents: 50
- Medicaid eligibility documentation: 50

**FALSE POSITIVES (500 total)**

**Office Communications (200, 40%):**

- Holiday closure notices: 50
- Office policy updates: 50
- Staff meeting agendas: 50
- General announcements: 50

**Administrative (150, 30%):**

- Provider credentialing (no patients): 40
- Equipment maintenance schedules: 30
- Billing policy explanations (generic): 40
- Quality metrics (aggregated, de-identified): 40

**Marketing/Educational (100, 20%):**

- Health system newsletters: 30
- Wellness tips: 30
- Service announcements: 20
- Patient satisfaction surveys (blank): 20

**HR/Operations (50, 10%):**

- Job postings: 20
- Training announcements: 15
- Conference materials: 15

---

## Template Structure

### Template Categories

Each template will have:

- **Base layout** (structure, headers, footers)
- **Variable fields** (marked for data injection)
- **Style variations** (fonts, colors, formatting)
- **Format-specific elements** (letterheads, logos, etc.)

### Example Template Types

**Lab Result Template:**

```
Elements:
- Facility letterhead
- Patient demographics section
- Test information (date collected, date reported)
- Results table (test name, value, reference range, flag)
- Ordering provider info
- Medical director signature
- Standard disclaimers
```

**Progress Note Template:**

```
Elements:
- SOAP format (Subjective, Objective, Assessment, Plan)
- Patient header (name, DOB, MRN)
- Visit date/time
- Chief complaint
- Vital signs
- Clinical narrative
- ICD-10 codes
- Provider signature
```

**Email Templates:**

```
- Professional email signature
- Subject line patterns
- Body content variations
- Attachment references
```

---

## File Format Distribution

### Format Split (across all 2,000 documents)

- **PDF:** 40% (800 files) - Most common for clinical documents
- **DOCX:** 25% (500 files) - Notes, letters, forms
- **MSG/EML:** 20% (400 files) - Email communications
- **PPTX:** 10% (200 files) - Case studies, presentations
- **Nested (ZIP with mixed):** 5% (100 files)

---

## Nested Complexity Scenarios

**Level 1 - Simple Attachments (60%):**

- Email with single PDF attachment
- Email with single DOCX attachment

**Level 2 - Multiple Attachments (30%):**

- Email with 2-3 attachments (mixed formats)
- ZIP file with 3-5 documents

**Level 3 - Complex Nesting (10%):**

- Email thread (3-4 messages) with attachments
- ZIP containing multiple folders with documents
- Email with ZIP attachment containing PHI
- PPTX with embedded images of PHI documents

---

## Realism Features

### Variation Techniques

1. **Temporal spread:** Documents span 2-3 years
2. **Quality variation:**
   - Clean, professional documents (70%)
   - Slightly messy formatting (20%)
   - Poor quality/typos (10%)
3. **Style variation:** Multiple letterhead designs per facility
4. **Content variation:** Use LLM to generate narrative variations
5. **Handwriting simulation:** Some forms have "handwritten" sections (image overlays)

### Edge Cases to Include

- Partially redacted documents (blackout bars but PHI visible)
- Faxed documents (low quality, noise)
- Scanned documents (OCR text with artifacts)
- Documents with PHI in headers/footers
- PHI in image metadata
- PHI in email signatures
- Forms with some fields blank

---

## Generation Workflow

### Step 1: Data Preparation

```
1. Generate patient pool using Faker + faker_medical
2. Generate provider pool
3. Generate facility pool
4. Create relationships (patients to providers, providers to facilities)
5. Generate medical events (visits, tests, procedures) for each patient
```

### Step 2: Template Creation

```
1. Build base templates for each document category
2. Use LLM to generate variations of each base template (3-5 variations per type)
3. Store templates with variable markers
4. Create styling profiles for each facility
```

### Step 3: Document Generation

```
For each document in manifest:
  1. Select template based on category
  2. Select patient + provider + facility
  3. Populate template with data
  4. Apply styling/formatting
  5. Generate in target format
  6. Add any quality degradation effects
  7. Save with metadata
```

### Step 4: Composition

```
For nested documents:
  1. Generate constituent files first
  2. Create email wrapper or ZIP archive
  3. Set appropriate metadata (timestamps, email headers)
  4. Save composite file
```

### Step 5: Validation

```
For each document:
  1. Verify file opens correctly
  2. Check PHI presence/absence matches category
  3. Validate format compliance
  4. Log metadata for tracking
```

---

## Output Structure

```
synthetic_phi_dataset/
├── phi_documents/              # 1,500 PHI true positives
│   ├── clinical/
│   │   ├── lab_results/
│   │   ├── progress_notes/
│   │   └── prescriptions/
│   ├── administrative/
│   │   ├── registration/
│   │   └── billing/
│   ├── correspondence/
│   └── medicare_medicaid/
├── false_positives/            # 500 medical context, no patient data
│   ├── office_communications/
│   ├── administrative/
│   ├── marketing/
│   └── hr_operations/
├── pii_only/                   # 300 control group - PII without medical context
│   ├── employment/
│   ├── financial/
│   └── general_business/
├── metadata/
│   ├── manifest.json           # Complete index of all files
│   ├── patient_data.json       # Generated patient pool
│   ├── provider_data.json      # Generated provider pool
│   ├── phi_validation.json     # PHI element verification
│   └── validation_report.json  # QA results
└── templates/
    ├── base_templates/
    └── variations/
```

### Manifest Format

```json
{
  "file_id": "PHI_0001",
  "dataset_type": "phi_document",
  "subcategory": "lab_result",
  "format": "pdf",
  "phi_elements": {
    "identifiers": ["name", "dob", "mrn"],
    "medical_elements": ["lab_values", "diagnosis"]
  },
  "patient_id": "PAT_0042",
  "provider_id": "PROV_0015",
  "facility_id": "FAC_0003",
  "created_date": "2024-03-15",
  "language": "en_US",
  "file_path": "phi_documents/clinical/lab_results/PHI_0001.pdf",
  "complexity": "simple",
  "quality": "clean"
}
```

**Example PII-Only Document:**

```json
{
  "file_id": "PII_0001",
  "dataset_type": "pii_only",
  "subcategory": "employment_record",
  "format": "docx",
  "pii_elements": ["name", "ssn", "address", "phone"],
  "medical_elements": [],
  "person_id": "PERSON_0123",
  "created_date": "2024-05-20",
  "language": "en_US",
  "file_path": "pii_only/employment/PII_0001.docx",
  "complexity": "simple",
  "quality": "clean"
}
```

---

## Implementation Phases

### Phase 1: Proof of Concept (Week 1)

- Generate 10 patients, 5 providers, 3 facilities
- Create 3 template types (lab result, progress note, email)
- Generate 50 documents (40 true positives, 10 false positives)
- Validate with customer

### Phase 2: Template Expansion (Week 2)

- Create all 20+ template types
- Generate LLM variations
- Implement all file formats
- Test nested scenarios

### Phase 3: Full Generation (Week 3)

- Generate complete patient/provider pools
- Run full document generation
- Quality validation
- Package for delivery

### Phase 4: Refinement (Week 4)

- Customer feedback incorporation
- Edge case additions
- Final validation
- Documentation and handoff

---

## Quality Assurance Checklist

**Per Document:**

- [ ] Opens without errors in native application
- [ ] PHI presence matches category (TP vs FP)
- [ ] Realistic formatting and content
- [ ] Proper metadata
- [ ] Correct file format

**Per Category:**

- [ ] Appropriate distribution of document types
- [ ] Variety in templates and styling
- [ ] No duplicate content
- [ ] Realistic temporal distribution

**Overall Dataset:**

- [ ] Correct count (1,500 TP, 500 FP)
- [ ] Format distribution matches target
- [ ] Nested complexity represented
- [ ] Edge cases included
- [ ] Manifest complete and accurate

---

## Multilingual Support

### Language Distribution (across all 2,000 documents)

- **English:** 90% (1,800 files) - Primary language
- **Spanish:** 5% (100 files) - Common in healthcare settings
- **Chinese (Simplified):** 3% (60 files) - Large patient population
- **Vietnamese:** 2% (40 files) - Significant healthcare demographic

### Implementation Strategy

**Faker Localization:**

```python
# Faker supports multiple locales
from faker import Faker

fake_en = Faker('en_US')
fake_es = Faker('es_MX')  # Mexican Spanish
fake_zh = Faker('zh_CN')  # Simplified Chinese
fake_vi = Faker('vi_VN')  # Vietnamese
```

**Translation Approach:**

1. **Patient Demographics:** Use locale-appropriate Faker for names, addresses
2. **Medical Terminology:** Keep standardized (many medical terms are universal)
3. **Form Instructions/Labels:** Translate using templates
4. **Clinical Narratives:** Use LLM to generate in target language or translation service

**Document Types by Language:**

**Spanish Documents (100 total):**

- Patient consent forms: 20
- Medication instructions: 15
- Lab results: 25
- Appointment letters: 15
- Patient education materials: 15
- Billing statements: 10

**Chinese Documents (60 total):**

- Patient registration forms: 15
- Lab results: 20
- Appointment notifications: 10
- Medical instructions: 10
- Insurance documents: 5

**Vietnamese Documents (40 total):**

- Patient intake forms: 10
- Lab results: 15
- Prescription instructions: 8
- Appointment reminders: 7

**Mixed Language Edge Cases:**

- Bilingual forms (English/Spanish): 10 documents
- Documents with English headers but non-English content: 5 documents
- Email threads with multiple languages: 5 documents

### Faker Locale Codes

```python
LOCALE_CONFIG = {
    "en_US": 0.90,  # English (United States)
    "es_MX": 0.05,  # Spanish (Mexico)
    "zh_CN": 0.03,  # Chinese (Simplified)
    "vi_VN": 0.02   # Vietnamese
}
```

### Medical Translation Resources

- **Medical terminology databases** (for consistent translation)
- **LLM prompts** for generating clinical narratives in target languages
- **Template translations** for common form fields

### Quality Considerations

- Ensure PHI elements are still detectable in non-English documents
- Test that Purview can identify translated PHI elements
- Include both native names and transliterated names where appropriate
- Consider cultural variations in date formats, address formats

---

## Configuration Parameters

```python
CONFIG = {
    "counts": {
        "phi_documents": 1500,      # True positives - PHI
        "false_positives": 500,     # Medical context, no patient data
        "pii_only": 300,            # Control group - PII without medical context
        "patients": 750,
        "providers": 150,
        "facilities": 50
    },
    "format_distribution": {
        "pdf": 0.40,
        "docx": 0.25,
        "msg_eml": 0.20,
        "pptx": 0.10,
        "nested": 0.05
    },
    "quality_distribution": {
        "clean": 0.70,
        "messy": 0.20,
        "poor": 0.10
    },
    "complexity_distribution": {
        "simple": 0.60,
        "multiple_attachments": 0.30,
        "complex_nesting": 0.10
    },
    "language_distribution": {
        "en_US": 0.90,
        "es_MX": 0.05,
        "zh_CN": 0.03,
        "vi_VN": 0.02
    },
    "date_range": {
        "start": "2022-01-01",
        "end": "2024-12-31"
    },
    "phi_requirements": {
        # Every PHI doc must have at least:
        "min_identifiers": 1,       # Name, MRN, or Insurance ID
        "min_medical_elements": 1   # Diagnosis, med, lab, procedure
    }
}
```

---

## Development Environment Setup

### Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create new project
uv init synthetic-phi-generator
cd synthetic-phi-generator

# Add core dependencies
uv add faker faker-medical python-docx python-pptx reportlab

# Add multilingual support
uv add googletrans==4.0.0-rc1  # For translation if needed
# Note: Faker already supports multiple locales natively

# Add additional dependencies as needed
uv add anthropic  # or google-generativeai for Gemini

# Create and activate virtual environment automatically
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run scripts
uv run python src/generate_data.py

# Install from requirements if provided
uv pip install -r requirements.txt
```

### Project Structure

```
synthetic-phi-generator/
├── pyproject.toml          # uv project configuration
├── uv.lock                 # Locked dependencies
├── src/
│   ├── generators/
│   │   ├── patient_generator.py
│   │   ├── provider_generator.py
│   │   └── document_generator.py
│   ├── templates/
│   │   ├── base_templates/
│   │   └── template_engine.py
│   ├── formatters/
│   │   ├── pdf_formatter.py
│   │   ├── docx_formatter.py
│   │   ├── email_formatter.py
│   │   └── pptx_formatter.py
│   ├── validators/
│   │   └── document_validator.py
│   └── main.py
├── config/
│   └── generation_config.yaml
├── output/
│   └── synthetic_phi_dataset/
└── tests/
```

---

## Next Steps for Claude Code

1. **Review this plan** - Confirm approach aligns with requirements
2. **Receive actual forms** - Customer will provide real CMS forms as templates
3. **Set up development environment using uv:**
   ```bash
   uv init synthetic-phi-generator
   uv add faker faker-medical python-docx python-pptx reportlab
   ```
4. **Build foundation modules:**
   - Data generation module (Faker + faker_medical)
   - Template system with variable substitution
   - File format generators for each type
5. **Create proof of concept** - 50 sample documents
6. **Iterate based on feedback**
7. **Scale to full production**

---

## Notes for Implementation

- **Performance:** With 2,000 documents, consider parallel processing (multiprocessing or asyncio)
- **Storage:** Estimate ~2-3GB for full dataset
- **LLM usage:** Batch template variations upfront to minimize API costs
- **Validation:** Build automated checks early to catch issues
- **Versioning:** Track generated datasets (may need multiple iterations)
- **Privacy:** Ensure all data is synthetic and no real PHI leaks in
- **Use uv for all package management** - It's significantly faster than pip and handles virtual environments automatically

---

## Open Questions for Customer

1. Do you have specific CMS form templates we should use?
2. Are there particular Medicare/Medicaid forms that are high priority?
3. Should we include specific adversarial examples (e.g., attempted obfuscation)?
4. What level of OCR errors are realistic for scanned documents?
5. Do you need specific date ranges or temporal patterns?
6. Are there particular Purview sensitive info types we should target?
7. Do you want any documents that combine PHI with other sensitive data (PCI, PII-only)?
8. What's the timeline for proof of concept vs. full delivery?
9. Do you have sample false positives you'd like us to model after?
10. **Confirm language distribution:** English (90%), Spanish (5%), Chinese (3%), Vietnamese (2%) - does this match your patient demographics?
11. **Language-specific requirements:** Do you need any particular regional dialects (e.g., Cantonese vs Mandarin, European Spanish vs Latin American)?
12. **Bilingual documents:** Should we include mixed-language documents (e.g., English form with Spanish instructions)?

---

## Additional Resources

**Faker Documentation:**

- https://faker.readthedocs.io/
- https://pypi.org/project/faker-medical/

**Document Generation Libraries:**

- python-docx: https://python-docx.readthedocs.io/
- python-pptx: https://python-pptx.readthedocs.io/
- ReportLab: https://www.reportlab.com/docs/reportlab-userguide.pdf

**uv Documentation:**

- https://docs.astral.sh/uv/

**Microsoft Purview Resources:**

- https://learn.microsoft.com/en-us/purview/
- Sensitive Information Types: https://learn.microsoft.com/en-us/purview/sensitive-information-type-entity-definitions

**HIPAA PHI Reference:**

- https://www.hhs.gov/hipaa/for-professionals/privacy/laws-regulations/index.html

---

**Ready for handoff to Claude Code with additional customer documentation.**
**Remember to use `uv` for all package management and dependency handling.**
