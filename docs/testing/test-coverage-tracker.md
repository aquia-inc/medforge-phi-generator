# Test Coverage Tracker

Current: **75 tests**, all passing. Last updated: 2026-04-06.

## Coverage by Module

### Fully Tested

| Module | Test File | Tests | Status |
|--------|-----------|-------|--------|
| `templates/components.py` (ComponentMixer) | `test_component_mixer.py` | 17 | Complete |
| `generators/cui/*.py` (all 7 generators + factory) | `test_cui_generators.py` | 23 | Complete |
| `formatters/base_email_formatter.py` | `test_email_formatters.py` | 4 | Complete |
| `formatters/nested_formatter.py` | `test_email_formatters.py` | 3 | Core paths covered |
| `formatters/cui_nested_formatter.py` | `test_email_formatters.py` | 2 | Core paths covered |

### Partially Tested

| Module | Test File | Tests | What's Covered | What's Missing |
|--------|-----------|-------|---------------|----------------|
| `formatters/cui_formatter.py` | `test_cui_formatters.py` | 7 | CUIDocxFormatter (3), CUIPdfFormatter (2), CUIXlsxFormatter (1), CUIEmailFormatter (1) | Individual `_add_*_content()` handlers (12 type-specific methods), `_add_narrative_paragraphs()`, `_add_styled_heading()` |
| `formatters/cui_pptx_formatter.py` | `test_cui_formatters.py` | 2 | Output validity, component config | `_add_narrative_slides()`, `_add_text_slide()` per-slide content |
| `formatters/cui_html_email_formatter.py` | `test_cui_formatters.py` | 1 | HTML email output validity | Per-type HTML builders (vulnerability, financial, legal), palette selection |
| `formatters/snyk_email_generator.py` | `test_cui_formatters.py` | 2 | Positive/negative output validity | LLM enrichment path, finding count variation, severity routing |
| `cli.py` (CUI generator) | `test_integration.py` | 12 | Full pipeline, manifests, directory structure, stats | `_enhance_with_llm()` branches, `_enhance_negative_with_llm()`, `_enrich_template_data_with_llm()`, customer template selection logic |

### Not Tested

| Module | Lines | Risk | Recommended Tests |
|--------|-------|------|-------------------|
| `cli.py` — PHI generator (`MedForgeGenerator`) | ~480 | Medium | `test_phi_generator.py`: positive/negative generation, format selection, nested email probability, LLM enhancement |
| `formatters/docx_formatter_enhanced.py` | ~200 | Medium | `test_phi_formatters.py`: progress note, lab result, referral letter, each with/without LLM |
| `formatters/pdf_formatter.py` | ~300 | Medium | `test_phi_formatters.py`: lab result PDF, medical policy PDF |
| `formatters/xlsx_formatter.py` | ~150 | Low | Output validity, PHI content checks |
| `formatters/pptx_formatter.py` | ~200 | Low | Output validity, case study presentation |
| `formatters/email_formatter.py` | ~400 | Medium | Provider-to-provider, patient notification, referral emails |
| `formatters/html_lab_formatter.py` | ~250 | Low | HTML lab report generation |
| `formatters/pdf_form_populator.py` | ~1670 | Medium | Customer template fill methods (30+ generator methods), `_underline_fills`, `_table_data` processing |
| `formatters/snyk_template_populator.py` | ~200 | Low | Snyk template population |
| `generators/patient_generator.py` | ~600 | Low | Patient/provider/facility data generation (used via fixtures, but no direct tests) |
| `generators/llm_generator.py` | ~1040 | High | All LLM methods (requires mocking Anthropic client) |
| `generators/parallel_generator.py` | ~680 | Medium | Multiprocessing orchestration, progress tracking, state save/load |
| `validators/phi_validator.py` | ~650 | Low | PHI detection, format-specific extraction |

---

## Outstanding Test Cases

### High Priority

These cover code paths that have known bug risk or handle critical functionality:

| # | Test | Module | Why |
|---|------|--------|-----|
| 1 | LLM enhancement routing per CUI category | `cli.py` `_enhance_with_llm()` | 175-line switch with 12+ branches; bug in field mapping silently produces empty content |
| 2 | LLM negative content safety | `cli.py` `_enhance_negative_with_llm()` | Negative docs must never contain CUI indicators; currently only validated in `test_llm_smoke.py` (standalone, needs API key) |
| 3 | Customer template selection + category weighting | `cli.py` `_generate_from_customer_template()` | 134-line method with category-weighted selection; template data mismatch bug was found and fixed here |
| 4 | LLM generator methods (mocked) | `generators/llm_generator.py` | 10+ methods with manual JSON extraction; no unit tests without API key |
| 5 | PHI positive generation pipeline | `cli.py` `generate_single_phi_positive()` | 156-line if-elif chain; document type routing never unit tested |

### Medium Priority

| # | Test | Module | Why |
|---|------|--------|-----|
| 6 | PHI email formatters | `formatters/email_formatter.py` | 12 methods, 0 tests; provider emails, patient notifications |
| 7 | PHI DOCX formatter (enhanced) | `formatters/docx_formatter_enhanced.py` | LLM-enhanced progress notes, clinical narratives |
| 8 | Customer template fill patterns | `formatters/pdf_form_populator.py` | 30+ generator methods; `_underline_fills` consumes in document order (body -> table -> header), which is subtle |
| 9 | CUI type-specific content handlers | `formatters/cui_formatter.py` | 12 `_add_*_content()` methods (SAR, written_determination, comptroller, bargaining, testimony, retirement, etc.) |
| 10 | Parallel generation | `generators/parallel_generator.py` | Multiprocessing pool, progress monitoring, state save/load |

### Low Priority

| # | Test | Module | Why |
|---|------|--------|-----|
| 11 | PHI PDF formatter | `formatters/pdf_formatter.py` | Lab result PDFs, medical policies |
| 12 | PHI PPTX formatter | `formatters/pptx_formatter.py` | Case study presentations, educational materials |
| 13 | PHI XLSX formatter | `formatters/xlsx_formatter.py` | Lab result spreadsheets |
| 14 | HTML lab formatter | `formatters/html_lab_formatter.py` | HTML-formatted lab reports |
| 15 | Patient/Provider/Facility generators | `generators/patient_generator.py` | Data generation (low risk, used indirectly via fixtures) |
| 16 | PHI validator | `validators/phi_validator.py` | PHI detection rules (low risk, mostly regex) |

---

## Coverage Summary

| Layer | Files | Tested | Coverage |
|-------|-------|--------|----------|
| CUI Generators (data) | 9 | 9 | 100% |
| CUI Formatters (output) | 6 | 6 | ~40% (output validity, not content-specific) |
| Email/MIME | 4 | 3 | ~60% (core paths, not all email types) |
| Component System | 1 | 1 | 100% |
| PHI Formatters | 7 | 0 | 0% |
| PHI Generator (CLI) | 1 | 0 | 0% (via integration only) |
| LLM Generator | 1 | 0 | 0% (needs mocking) |
| Parallel Generator | 1 | 0 | 0% |
| Validators | 1 | 0 | 0% (standalone script only) |
| **Total** | **31** | **10+** | **~35%** |
