# Adding Customer Templates to MedForge

This guide covers the exact steps to register a new customer-provided template so the generation pipeline picks it up automatically.

## How It Works

During generation, each document has a 20% chance of using a customer template instead of the programmatic generator. The pipeline:

1. Filters registered templates to only those matching the active `--cui-categories`
2. Picks one at random
3. For **positives**: populates it with Faker data (PDF/DOCX) or copies it as-is (XLSX/EML)
4. For **negatives**: copies the blank/negative variant, or skips if the template is positive-only
5. **Email wrapping** (default 80%): wraps the generated file in an email as an attachment with varying body detail (minimal/medium/LLM-detailed). Controlled by `--template-email-ratio`. The remaining 20% are output as bare files.

Templates are registered in two places:
- `src/formatters/pdf_form_populator.py` — the `template_mappings` dict (~line 345)
- `src/cli.py` — the `template_category_map` dict (~line 686)

---

## Step 1: Place the File in `cust_templates/saved_templates/`

Use the naming convention:

```
<Name>-<Variant>-CUI-<Category>-<Polarity>.<ext>
```

Examples:
```
FOIA-RequestLog-CUI-Legal-positive.docx
FOIA-RequestLog-CUI-Legal-negative.docx
IaaS Mainframe MFA IGCE OY1-CUI-Procurement and Acquisition-positive.xlsx
```

The filename itself doesn't affect pipeline behavior — it's just for your own organization. What matters is the registration in Step 3.

---

## Step 2: Inspect the Template

Determine what kind of template it is. This decides which registration pattern to use.

### PDF — check for fillable form fields

```bash
uv run python -c "
import pikepdf
pdf = pikepdf.open('cust_templates/YOUR_TEMPLATE.pdf')
if '/AcroForm' in pdf.Root and '/Fields' in pdf.Root.AcroForm:
    for field in pdf.Root.AcroForm.Fields:
        name = str(field.T) if '/T' in field else 'UNNAMED'
        ftype = str(field.get('/FT', 'unknown'))
        rect = [float(r) for r in field.Rect] if '/Rect' in field else None
        print(f'Field: {name!r}, Type: {ftype}, Rect: {rect}')
else:
    print('No fillable fields — use copy mode')
pdf.close()
"
```

- **Has fillable fields** → needs a Faker data generator + field coordinate map
- **No fillable fields** → use copy mode (just copies the file as-is)

### DOCX — check for placeholder text

```bash
uv run python -c "
from docx import Document
doc = Document('cust_templates/YOUR_TEMPLATE.docx')
for i, para in enumerate(doc.paragraphs):
    if para.text.strip():
        print(f'Para {i}: {para.text[:120]}')
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            if cell.text.strip():
                print(f'Cell: {cell.text[:80]}')
"
```

Look for placeholder strings like `MockSystem`, `MAC NAME`, `MockProject` — these get replaced with Faker values.

- **Has placeholders** → needs a Faker data generator that returns `{placeholder: replacement}` pairs
- **No placeholders** → use copy mode

### XLSX — check if openpyxl can read it

```bash
uv run python -c "
import openpyxl
wb = openpyxl.load_workbook('cust_templates/YOUR_TEMPLATE.xlsx')
print(f'Sheets: {wb.sheetnames}')
for sheet in wb.sheetnames[:2]:
    ws = wb[sheet]
    print(f'{sheet}: {ws.max_row} rows x {ws.max_column} cols')
"
```

If this errors (like the IGCE template does due to drawing effects), the template must use copy mode.

### EML — check structure

```bash
uv run python -c "
import email
with open('cust_templates/YOUR_TEMPLATE.eml', 'r', errors='ignore') as f:
    msg = email.message_from_file(f)
print(f'Subject: {msg[\"Subject\"]}')
print(f'From: {msg[\"From\"]}')
print(f'Multipart: {msg.is_multipart()}')
"
```

EML templates typically use copy mode.

---

## Step 3: Register the Template

You need to edit two files. The pattern depends on your template type.

### 3A: Choose Your Registration Pattern

There are four patterns. Pick the one that matches:

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Copy-only, positive+negative pair** | You have both a filled positive and blank negative file | EFT Authorization Form |
| **Copy-only, positive only** | You have only a positive file, no negative variant | IGCE XLSX |
| **Fillable PDF with generator** | PDF has AcroForm fields you want to fill with Faker data | Reasonable Accommodation |
| **DOCX with placeholder substitution** | DOCX has placeholder text to replace with Faker values | (future KMP, AFR templates) |

### 3B: Add to `template_mappings` in `src/formatters/pdf_form_populator.py`

Open the file and find the `template_mappings` dict (around line 345). Add your entry using the appropriate pattern:

#### Pattern: Copy-only, positive + negative pair

```python
'MyTemplate': {
    'template_positive': 'MyTemplate-CUI-Category-positive.xlsx',
    'template_negative': 'MyTemplate-CUI-Category-negative.xlsx',
    'category': 'CUI-Legal',     # Any string — only used internally by template manager
    'clean_name': 'MyTemplate',  # Used in output filename: MyTemplate_0001.xlsx
},
```

#### Pattern: Copy-only, positive only

```python
'MyTemplate': {
    'template_positive': 'MyTemplate-CUI-Category-positive.xlsx',
    'category': 'CUI-Procurement',
    'clean_name': 'MyTemplate',
    'positive_only': True,       # Skipped during negative generation
},
```

#### Pattern: Fillable PDF with Faker generator

```python
'MyTemplate': {
    'template': 'MyTemplate-blank.pdf',           # The blank form
    'generator': self.populator.generate_my_template_data,  # Method on PDFFormPopulator
    'category': 'CUI-Legal',
    'clean_name': 'MyTemplate',
    'field_positions': {                           # Optional: coordinates for reportlab overlay
        'FieldName1': (x, y),                      # (x, y) from bottom-left in points
        'FieldName2': (x, y),
    },
},
```

You also need to add a `generate_my_template_data()` method to the `PDFFormPopulator` class (earlier in the same file). It must return a `Dict[str, Any]` where keys match the PDF field names (from the Step 2 inspection). Example:

```python
def generate_my_template_data(self) -> Dict[str, Any]:
    return {
        'EmployeeName': self.fake.name(),
        'SSN': self.fake.ssn(),
        'Date': datetime.now().strftime('%m/%d/%Y'),
    }
```

#### Pattern: DOCX with placeholder substitution

```python
'MyTemplate': {
    'template': 'MyTemplate-MockProject-CUI-Category-positive.docx',
    'generator': self.populator.generate_my_template_data,
    'category': 'CUI-Financial',
    'clean_name': 'MyTemplate',
},
```

The generator returns `{placeholder_string: replacement_value}` pairs:

```python
def generate_my_template_data(self) -> Dict[str, Any]:
    return {
        'MockProject': self.fake.catch_phrase(),
        'Mock System': f'{self.fake.company()} Platform',
    }
```

### 3C: Add to `template_category_map` in `src/cli.py`

Open `src/cli.py` and find the `template_category_map` dict (around line 686). Add your template key mapped to its CUI category:

```python
template_category_map = {
    # 'EFT Authorization Form': 'financial',  # DISABLED
    'ReasonableAccommodationRequest': 'legal',
    'IGCE': 'procurement',
    'MyTemplate': 'legal',          # <-- add this line
}
```

The category value **must** be one of:
- `critical_infrastructure`
- `financial`
- `law_enforcement`
- `legal`
- `procurement`
- `proprietary`
- `tax`

This controls which `--cui-categories` filter includes your template, and which output folder it lands in (`CUI-Legal-Positive/`, etc.).

---

## Step 4: Test

### Quick smoke test — generate a small batch for your category

```bash
uv run python -m src.cli generate \
  --cui-positive 10 --cui-negative 5 \
  --cui-categories <your_category> \
  --seed 42
```

### Verify the template was used

```bash
# Check for your template's output files
find output/production_run_* -name "MyTemplate_*"

# Check the manifest for customer_template entries
uv run python -c "
import json, glob
manifest_path = sorted(glob.glob('output/production_run_*/metadata/cui_manifest.json'))[-1]
with open(manifest_path) as f:
    manifest = json.load(f)
for entry in manifest['files']:
    if entry.get('source') == 'customer_template':
        print(json.dumps(entry, indent=2))
"
```

You should see entries with:
- `"source": "customer_template"`
- `"category": "<your_category>"`
- `"format": "<detected extension>"`
- `"document_type": "<your clean_name>"`

### Verify negatives are handled correctly

- **Positive+negative pair**: negative files should appear in `CUI-<Category>-Negative/`
- **Positive-only**: no files with your template name should appear in the negative folder

```bash
# Should be empty for positive-only templates
find output/production_run_*/CUI-*-Negative/ -name "MyTemplate_*"
```

### Run validation

```bash
uv run python tests/validate_file_fidelity.py output/production_run_*
```

Expect 0 FATAL and 0 HIGH findings.

### Full regression (all categories)

```bash
uv run python -m src.cli generate \
  --cui-positive 10 --cui-negative 10 \
  --cui-all --seed 99

uv run python tests/validate_file_fidelity.py output/production_run_*
```

---

## Quick Reference: Existing Templates

| Key | Format | Pattern | Category | Status |
|-----|--------|---------|----------|--------|
| `Medical Inquiry  Form` | PDF | Fillable + generator | PHI | Active |
| `EFT Authorization Form` | PDF | Copy pair | financial | Disabled |
| `ReasonableAccommodationRequest` | PDF | Fillable + generator | legal | Active |
| `IGCE` | XLSX | Copy, positive-only | procurement | Active |

---

## Troubleshooting

**Template never gets picked**: The 20% random chance means small batches may not trigger it. Run with `--cui-positive 20` or higher to increase odds. Also confirm your category is included in `--cui-categories` or use `--cui-all`.

**"No populated fields" warning on positive PDFs**: This fires when the pikepdf validation can't find AcroForm field values. For reportlab-overlay PDFs (like Reasonable Accommodation), the text is baked into the page content stream, not form fields — the warning is harmless.

**DOCX substitution doesn't replace text**: The placeholder must appear as literal text in the DOCX paragraph. If Word split the placeholder across multiple XML runs (common with spell-check), the replacement won't match. Open the DOCX, select the placeholder text, delete it, and retype it in one go, then re-save.

**openpyxl can't read XLSX**: Some Excel files have drawing effects or charts that openpyxl can't parse. Use copy mode (`template_positive` without a `generator`).
