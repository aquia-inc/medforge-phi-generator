# MedForge - Developer Notes & Architectural Context

> For user-facing documentation (CLI reference, getting started, generation modes), see [README.md](README.md).

## Project Overview

**Customer:** CMS
**Purpose:** Training Microsoft Purview DLP to detect accidental PHI/CUI in SharePoint and other locations
**Deliverables:**

- PHI: 200-500 positive + 400-1,000 negative documents
- CUI: 7 categories with positive/negative pairs
- Multiple formats: PDF, DOCX, XLSX, EML, PPTX, nested EML
- Customer templates integrated from CMS (27 active)

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
- `fillpdf` - Creates unfillable PDFs in SharePoint
- `PyMuPDF` (fitz) - "bad rect" errors on complex forms
- `PyPDF2.PdfWriter.update_page_form_field_values()` - Doesn't persist
- `pdfrw` - Sets values but doesn't render without appearance regeneration

### Verification
Data is in the PDF even if `pdftotext` doesn't show it. Verify with:
```python
import pikepdf
pdf = pikepdf.open("filled_form.pdf")
for field in pdf.Root.AcroForm.Fields:
    print(f"{field.T}: {field.V}")  # Should show your synthetic data
```

### Customer Templates Successfully Integrated

**Location:** All customer templates stored in `cust_templates/` directory (56 files)
**Full registration guide:** `docs/adding-customer-templates.md`

**27 Active Templates (4 categories):**

| Category | Templates | Fill Method |
|----------|-----------|-------------|
| Procurement (9) | IGCE, CLIN Templates, Market Research, RFC Memo, AGX RFC Memo, JA Limited Source, JOFOC, OAGM Source Selection, Acquisition Plan | XLSX copy / DOCX table fill / underline fill |
| Critical Infrastructure (6) | KMP, Rules of Behavior, Incident Response, HHS RBD, Test Validation MAC, Test Validation PC | DOCX sub / table fill / PDF copy |
| Financial (5) | AFR Additional Info, DIBO AFR, Supplemental AFR, OIT FO Additional Info, Supplemental AFR Blank | DOCX sub (pos+neg pairs) |
| Legal (7) | Reasonable Accommodation Request, B6 Letter, Full Release, Form339 Letter, Subpoena Response, FOIA Medicare Auth, FOIA Guidance, FOIA Request Deceased Bene | PDF fillable / DOCX sub / copy |
| PHI (1) | Medical Inquiry Form | PDF fillable (reportlab overlay) |
| Financial (1, disabled) | EFT Authorization Form | PDF copy pair (disabled — form fill unreliable) |

**Integration Details:**
- Customer templates mixed into generation at 20% rate
- **Category-weighted selection:** picks category first (uniform), then template within category — prevents bias when one category has more templates
- Synthetic data generated via Faker (names, addresses, contract numbers, prices, system names)
- Supports 5 fill patterns: PDF fillable, PDF copy, DOCX placeholder sub, DOCX table fill, DOCX underline fill
- Clean filenames (no positive/negative labels)
- **8 LLM-enrichable templates:** AcquisitionPlan, IncidentResponse, KMP, MarketResearch, JOFOC, JALimitedSource, SubpoenaResponse, RFCMemo — get LLM-generated narrative sections appended when `llm_percentage` roll succeeds

**Remaining Unintegrated Templates:**
- FISMA reporting XLSX (Critical Infrastructure) — ~6MB, verify Purview limits
- CMS Things to Know (TBD classification)
- Several FOIA letter variants (Legal) — exist in cust_templates/ but not registered

---

### Design Patterns for Template Generators

When adding new customer templates, follow these patterns:

**1. Generator methods go on `PDFFormPopulator` (not `CustomerTemplateManager`)**
- Location: `src/formatters/pdf_form_populator.py`
- Method naming: `generate_<template_name>_data(self) -> Dict[str, Any]`
- Use `self.fake` for Faker data, `random` for choices
- Helper methods: `self._contract_number()`, `self._task_order_number()`, `self.generate_currency_amount()`, `self.format_currency()`

**2. Three fill mechanisms (can be combined in one generator):**
```python
def generate_example_data(self) -> Dict[str, Any]:
    return {
        # Text placeholder substitution: replaces literal strings
        'MockSystem': self.fake.company(),

        # Underline fills: replaces ___ blanks in document order
        # WARNING: consumed in order: body paragraphs -> table cells -> headers/footers
        '_underline_fills': ['value1', 'value2'],

        # Table fills: writes into cells by position (None = skip/preserve)
        '_table_data': [
            {'table_index': 0, 'start_row': 1, 'rows': [['a', None, 'c']]}
        ],
    }
```

**3. Registration requires two locations:**
- `template_mappings` dict in `CustomerTemplateManager.__init__()` (~line 884)
- `template_category_map` dict in `_generate_from_customer_template()` (~line 686)

**4. Category values in `template_category_map` must be one of:**
`critical_infrastructure`, `financial`, `law_enforcement`, `legal`, `procurement`, `proprietary`, `tax`

**5. Template selection is category-weighted** — adding 10 procurement templates won't flood output; each category gets equal selection probability.

### Testing

```bash
# All pytest tests (75 tests, ~2 min)
uv run python -m pytest tests/ -v

# Fast unit tests only (~1 sec)
uv run python -m pytest tests/test_component_mixer.py tests/test_cui_generators.py -v

# Quick smoke test for a single customer template
uv run python -c "
from src.formatters.pdf_form_populator import CustomerTemplateManager
mgr = CustomerTemplateManager(template_dir='./cust_templates', output_dir='./output/test')
pos = mgr.generate_from_template('TemplateName', './output/test', 1, populate=True)
neg = mgr.generate_from_template('TemplateName', './output/test', 2, populate=False)
print(f'pos={pos} neg={neg}')
"

# Generate + validate
uv run python -m src.cli generate --cui-positive 10 --cui-negative 10 --cui-all --seed 99
latest=$(ls -td output/production_run_* | head -1)
uv run python tests/validate_file_fidelity.py "$latest"

# LLM smoke test (requires ANTHROPIC_API_KEY, ~2-3 min)
uv run python tests/test_llm_smoke.py
```

See [docs/testing.md](docs/testing.md) for the full testing guide.

---

## CUI Confidentiality Notice Control

`--cui-notice` flag controls generic "contains CUI" notices:

- `random` (default): 50% of documents have confidentiality notices
- `always`: All CUI documents include notices
- `never`: No confidentiality footers (forces Purview to learn content patterns)

```bash
uv run python -m src.cli generate --cui-positive 100 --cui-all --cui-notice random   # default
uv run python -m src.cli generate --cui-positive 100 --cui-all --cui-notice never    # forces pattern learning
uv run python -m src.cli generate --cui-positive 100 --cui-all --cui-notice always   # traditional approach
```

**Note:** CUI classification headers (e.g., "CONTROLLED UNCLASSIFIED INFORMATION - TAX") are controlled separately via `--cui-classification always|never`. Only generic footers are controlled by `--cui-notice`.

---

## CMS Requirements Reference (Meeting Notes 11/14/2025)

### Volume Guidelines

- **Minimum (Seed Sets):** 50 positive, 150 negative (Microsoft recommends ~3x negatives)
- **Service Constraints:** Max ~500 docs per set processed at training time (most recent 500 used)
- **Target Sweet Spot:** 200-500 positives, 400-1,000 negatives

### CUI Categories

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
- **Synthetic Data Approach:** Fully synthetic names, identifiers, and medical data via `faker` and `faker-healthcare-system`.
