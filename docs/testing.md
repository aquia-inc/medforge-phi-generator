# MedForge Testing Guide

## Quick Reference

```bash
# All tests (~2 min)
uv run python -m pytest tests/ -v

# Fast unit tests only (~1 sec)
uv run python -m pytest tests/test_component_mixer.py tests/test_cui_generators.py -v

# Single test file
uv run python -m pytest tests/test_email_formatters.py -v

# Single test
uv run python -m pytest tests/test_cui_formatters.py::TestCUIDocxFormatter::test_creates_valid_docx -v

# Lint check
./lint.sh
```

---

## Test Architecture

Tests are organized into three layers:

### Layer 1: Unit Tests (~1 second)

Fast, isolated tests that verify individual components without generating documents.

| File | Tests | What it covers |
|------|-------|----------------|
| `test_component_mixer.py` | 17 | ComponentMixer seeding, deduplication, exhaustion, font name mapping (Arial/Helvetica), CUI section order variants |
| `test_cui_generators.py` | 23 | CUIGeneratorFactory registry, all 7 category generators produce valid data dicts, composite generator batching, classification markings |

### Layer 2: Functional Tests (~5 seconds)

Tests that create real document files and verify they are valid/openable.

| File | Tests | What it covers |
|------|-------|----------------|
| `test_email_formatters.py` | 9 | BaseEmailFormatter MIME construction (plain, HTML, attachments), NestedEmailFormatter `_attach_file()` for PDF/DOCX, CUI nested email roundtrip (generate -> parse -> verify attachments) |
| `test_cui_formatters.py` | 14 | Every CUI formatter produces valid output: DOCX (openable, has paragraphs), PDF (valid header), XLSX (openable workbook), EML (parseable MIME), PPTX (has slides), HTML email (has HTML part), Snyk (positive/negative), component config application, classification headers, negative document structure |

### Layer 3: Integration Tests (~2 minutes)

End-to-end tests that run the full generation pipeline.

| File | Tests | What it covers |
|------|-------|----------------|
| `test_integration.py` | 12 | Full `MedForgeCUIGenerator` pipeline: directory structure creation, manifest generation, classification markings, category filtering, mixed PHI+CUI runs, format-specific output (PDF/DOCX/EML), stats tracking, LLM stats tracking |

### Standalone Validation Scripts

These are not pytest tests. They run independently against generated output or require API keys.

| Script | Purpose | Requires |
|--------|---------|----------|
| `validate_file_fidelity.py` | 19 Purview fidelity checks: MIME structure, encoding, file integrity, content validation, attachment MIME types, charset consistency | Generated output directory |
| `generate_artifact_matrix.py` | Generates 114 artifacts covering every category x format x polarity combination, then validates each | ~2 min, no API key |
| `test_llm_smoke.py` | Validates LLM enhancement paths: tax/financial handlers, template enrichment, negative content safety (greps for forbidden patterns like SSN regex, PRE-DECISIONAL) | `ANTHROPIC_API_KEY`, ~2-3 min |

---

## Shared Fixtures (`conftest.py`)

All pytest test files share these fixtures defined in `tests/conftest.py`:

| Fixture | Type | Description |
|---------|------|-------------|
| `tmp_output_dir` | `str` | Temporary directory, auto-cleaned after test |
| `patient_generator` | `PatientGenerator` | Pre-seeded (seed=42) for deterministic patient data |
| `provider_generator` | `ProviderGenerator` | Pre-seeded (seed=42) for deterministic provider data |
| `facility_generator` | `FacilityGenerator` | Pre-seeded (seed=42) for deterministic facility data |
| `sample_phi_patient` | `dict` | A reusable patient dict |
| `sample_phi_provider` | `dict` | A reusable provider dict |
| `sample_phi_facility` | `dict` | A reusable facility dict |
| `sample_cui_data` | `dict[str, dict]` | One CUI positive doc_data per category (all 7 categories) |

Usage in tests:

```python
def test_something(self, tmp_output_dir, sample_cui_data):
    from formatters.cui_formatter import CUIDocxFormatter

    fmt = CUIDocxFormatter(output_dir=tmp_output_dir)
    doc_data = sample_cui_data['legal']
    filepath = fmt.create_cui_document(doc_data, "test.docx")
    assert os.path.exists(filepath)
```

---

## How to Add Tests

### Adding a unit test for a formatter

1. Choose the appropriate file (`test_cui_formatters.py` for CUI formatters, `test_email_formatters.py` for email formatters)
2. Use the `tmp_output_dir` and `sample_cui_data` fixtures
3. Instantiate the formatter, call its create method, verify the output

```python
def test_new_formatter_feature(self, tmp_output_dir, sample_cui_data):
    from formatters.cui_formatter import CUIDocxFormatter

    fmt = CUIDocxFormatter(output_dir=tmp_output_dir)
    doc_data = sample_cui_data['financial']
    filepath = fmt.create_cui_document(doc_data, "test.docx")

    # Verify the document
    from docx import Document
    doc = Document(filepath)
    full_text = '\n'.join(p.text for p in doc.paragraphs)
    assert 'expected content' in full_text
```

### Adding a unit test for a generator

Add to `test_cui_generators.py`. Generators don't need `tmp_output_dir` since they return data dicts, not files.

```python
def test_new_generator_field(self):
    from generators.cui import CUIGeneratorFactory
    gen = CUIGeneratorFactory.get_generator('financial', seed=42)
    doc = gen.generate_positive()
    assert 'new_field' in doc
```

### Adding a component mixer test

Add to `test_component_mixer.py`. No fixtures needed — `ComponentMixer` is self-contained.

### Adding an integration test

Add to `test_integration.py`. Use the `temp_output_dir` fixture (note: this file has its own fixture, not the shared one from conftest.py).

---

## Validation Checks (`validate_file_fidelity.py`)

The fidelity validator runs 19 checks organized by severity:

| # | Check | Severity | Description |
|---|-------|----------|-------------|
| 1 | File opens | FATAL | File exists and can be read |
| 2 | MIME parse | FATAL | EML files parse as valid MIME |
| 3 | MIME boundaries | HIGH | Multipart boundaries are correct |
| 4 | Attachment MIME | HIGH | Attachment content types are valid |
| 5 | UTF-8 encoding | HIGH | Text content is valid UTF-8 |
| 6 | Charset consistency | HIGH | Declared charset matches content |
| 7 | File size | WARN | Not empty, not over 25MB |
| 8 | DOCX integrity | HIGH | DOCX opens as valid ZIP/XML |
| 9 | PDF integrity | HIGH | PDF has valid header |
| 10 | XLSX integrity | HIGH | XLSX opens as valid workbook |
| 11 | EML headers | WARN | Required email headers present |
| 12 | PPTX integrity | HIGH | PPTX opens and has slides |
| 13-15 | PHI content | WARN | Positive docs contain expected PHI patterns |
| 16-17 | Negative safety | HIGH | Negative docs don't contain PHI |
| 18 | Classification | WARN | CUI markings present when expected |
| 19 | PPTX content | WARN | Slides have text content |

---

## CI Integration

Tests can be run in CI without an API key. Only `test_llm_smoke.py` requires `ANTHROPIC_API_KEY`:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    uv sync
    uv run python -m pytest tests/ -v --tb=short
    ./lint.sh
```
