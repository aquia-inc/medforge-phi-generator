# PR Summary: CUI Pipeline Enhancement & LLM Expansion

**Branch:** `SHEG/add_templates`
**Base:** `main`
**Scope:** 46 files changed, +6,038 / -1,820 lines

---

## What This PR Does

This PR brings the CUI document generation pipeline to feature parity with PHI, then significantly expands LLM integration across all CUI categories, formats, and document types. It also overhauls project documentation, adds visual variety to generated documents, and introduces automated testing for LLM-enhanced output.

---

## Changes by Area

### 1. Email Formatter Deduplication

Extracted shared MIME construction logic from 5 email formatters into `BaseEmailFormatter`, reducing duplicated boilerplate by ~400 LOC. All email formatters (PHI and CUI) now inherit from this base class.

**Files:** `src/formatters/base_email_formatter.py` (new), 5 existing formatters modified to inherit

### 2. CUI Format Parity

Added three new CUI formatters that previously only existed for PHI:
- `CUIPPTXFormatter` — PowerPoint with classification banners and metadata slides
- `CUINestedEmailFormatter` — emails with in-memory PDF/DOCX/ZIP attachments
- `CUIHTMLEmailFormatter` — professional HTML emails with content-type routing

CUI emails now route probabilistically: ~50% plain text, ~30% HTML, ~7% nested, ~50% Snyk for critical_infrastructure.

### 3. Customer Template Integration (27 active)

Integrated 27 CMS-provided templates across 4 categories:

| Category | Count | Fill Method |
|----------|-------|-------------|
| Procurement | 9 | XLSX copy, DOCX table fill, underline fill |
| Legal | 7 | PDF fillable, DOCX substitution, copy |
| Critical Infrastructure | 6 | DOCX substitution, table fill, PDF copy |
| Financial | 5 | DOCX substitution (positive + negative pairs) |

Features:
- Category-weighted selection prevents bias when categories have unequal template counts
- 5 fill patterns: PDF fillable (reportlab overlay), PDF copy, DOCX placeholder sub, DOCX table fill, DOCX underline fill
- Generalized `populate_docx_template()` supporting all three DOCX fill mechanisms simultaneously

### 4. Component Mixing for Visual Variety

Applied the existing 240-combination `ComponentMixer` (5 headers x 3 layouts x 4 styles x 4 section orders) to CUI document generation:

- **DOCX:** Font family, font size, heading color, alignment vary per document
- **PDF:** Font, title size, alignment, leading applied via `ParagraphStyle`
- **PPTX:** Slide title font/color, body text font/size vary per presentation
- **HTML Email:** 4-5 color palettes per content type (vulnerability, financial, legal, generic), randomized per email

Added 4 CUI-specific section order variants and font name mapping (PostScript for ReportLab, Windows names for python-docx/python-pptx).

### 5. LLM Field Mapping Fix

Fixed the disconnect between LLM-generated content and CUI formatter type handlers. Previously, LLM output went to generic keys (`body`, `executive_summary`) that type-specific handlers didn't read.

Now correctly mapped:
- **Legal:** `question_presented`, `brief_answer`, `analysis`, `recommendation`
- **Budget:** `subject`, `decision`, `key_decision_points`
- **Procurement:** `evaluation_factors` (parsed into structured list), `justification`
- **Security:** `description`, `remediation` dict with `action`/`deadline`

### 6. LLM Enhancement Across All CUI Categories

Expanded `_enhance_with_llm()` from 4 category handlers to cover tax and all financial subcategories:

| Category | Subcategory | LLM Method | Fields Enhanced |
|----------|------------|------------|-----------------|
| Financial | bank_secrecy | `generate_cui_narrative()` | `suspicious_activity.narrative` |
| Financial | retirement | `generate_cui_narrative()` | `disclaimer`, `executive_summary` |
| Financial | comptroller | `generate_cui_narrative()` | `findings[].description`, `executive_summary` |
| Tax | written_determinations | `generate_cui_tax_determination()` | `facts`, `law_and_analysis`, `conclusion` (IRAC) |
| Tax | general | `generate_cui_narrative()` | `executive_summary`, `body_content` |

New Pydantic model: `CUITaxDetermination` with IRS PLR-style prompt.

### 7. Type-Specific Formatter Handlers

Added 6 new DOCX content handlers for document types that previously fell through to a flat key-value renderer:

| Handler | Document Types | Rendering |
|---------|---------------|-----------|
| `_add_sar_content()` | SAR | Subject info, suspicious activity narrative, filing details |
| `_add_written_determination_content()` | written_determination | IRAC format (Issues, Facts, Law & Analysis, Conclusion) |
| `_add_comptroller_content()` | comptroller_report | Findings with significance, recommendations, savings |
| `_add_bargaining_content()` | bargaining_proposal | Articles table, ground rules, team leads |
| `_add_testimony_content()` | congressional_testimony | Witness info, prepared statement, key messages |
| `_add_retirement_content()` | retirement_estimate | Service computation, salary, estimated benefits |

All handlers use `_add_styled_heading()` and `_add_narrative_paragraphs()` for component mixing and multi-paragraph LLM rendering.

### 8. LLM-Enriched Customer Templates (8 of 27)

8 DOCX templates receive LLM-generated narrative sections appended after the Faker-filled content:

| Template | LLM Generates |
|----------|--------------|
| AcquisitionPlan | Acquisition strategy, market research summary, cost justification |
| IncidentResponse | Incident summary, containment actions, lessons learned |
| KMP | System description, key management procedures, compliance justification |
| MarketResearch | Vendor landscape, capability assessment, small business analysis |
| JOFOC | Justification narrative, market research findings, determination rationale |
| JALimitedSource | Competition justification, efforts to compete, fair pricing determination |
| SubpoenaResponse | Response narrative, privilege log summary, production scope |
| RFCMemo | Change justification, impact analysis, stakeholder assessment |

**Bug fix:** Faker data is now generated once and passed to both LLM enrichment and template fill, preventing data mismatches (e.g., LLM referencing "Smith LLC" while template fills "Jones Corp").

### 9. PPTX LLM Narrative Slides

CUI PPTX presentations now render LLM-enriched fields as dedicated slides:
- Executive Summary, Analysis, Risk Assessment, Recommendations, Justification
- Multi-paragraph text split across slides with component-config styling

### 10. LLM-Enhanced Snyk Vulnerability Descriptions

The highest-severity finding per Snyk email gets LLM-generated description, impact analysis, and remediation narrative (via existing `generate_cui_security_report()`). Only 1 finding per email is enriched to limit API calls. CUI-negative Snyk emails are not enriched.

### 11. LLM-Enhanced CUI Negatives

CUI negative documents now receive LLM-generated public-facing prose at **half the positive rate** (e.g., `--llm-percentage 0.2` gives positives 20% and negatives 10%). This creates "hard negatives" that use the same government terminology and formatting as CUI positives but contain genuinely non-sensitive content.

Prompt constraint: "Generate publicly available, non-sensitive government content. No names, identification numbers, case numbers, or pre-decisional information."

### 12. Documentation Overhaul

- **README.md** — Rewritten with Quick Start examples for PHI-only, CUI-only, single category, and mixed generation. Added LLM section, customer template section, test section, `setup`/`version` commands.
- **CLAUDE.md** — Trimmed from 1,259 to ~250 lines. Removed ~1,000 lines of aspirational/unimplemented features. Focused on developer reference (pikepdf solution, template patterns, CMS requirements).
- **docs/PROJECT_STATUS.md** — Archived (stale, referenced deleted scripts).
- **docs/NESTED_EMAIL_REQUIREMENTS.md** — Archived (fully implemented).
- **docs/summary.md** — Archived (completed branch changelog).
- **docs/DEMO.md** — Updated commands and stale Q&A.

### 13. Automated Testing

- **`tests/test_llm_smoke.py`** (new) — Validates all LLM enhancement paths in ~2-3 min: tax/financial handlers, template enrichment, negative LLM content, and negative content safety (greps for forbidden CUI indicators like SSN patterns, PRE-DECISIONAL, ATTORNEY-CLIENT PRIVILEGED).
- **`tests/validate_file_fidelity.py`** — 19 Purview fidelity checks.
- **`tests/generate_artifact_matrix.py`** — 114-artifact format x category coverage.

---

## Cost & Performance Impact

At production scale (3,500 positive + 7,000 negative docs, 7 categories):

| | Before | After | Delta |
|---|---|---|---|
| LLM calls | ~705 | ~1,460 | +755 (~2x) |
| Time (4 workers) | ~32 min | ~1 hr | +28 min |
| API cost | ~$7 | ~$14.60 | +$7.60 |
| `--llm-percentage 0` | Free, instant | Free, instant | No change |

---

## Verification

```bash
# LLM smoke test (all enhancement paths, ~2-3 min)
uv run python tests/test_llm_smoke.py

# Full artifact matrix (114 artifacts, all format x category combos)
uv run python tests/generate_artifact_matrix.py

# Purview fidelity validation
uv run python tests/validate_file_fidelity.py output/production_run_*/

# Quick generation test
uv run python -m src.cli generate --cui-positive 10 --cui-negative 5 --cui-all --seed 42 --llm-percentage 0.5
```

---

## Customer Template Audit (pending)

The `cust_templates/` directory contains 56 files. A filename-based audit identified ~12 files that likely contain real CMS data (BugCrowd emails, Snyk alerts naming real CMS systems, ServiceNow tickets with real ticket numbers, FISMA reports, infrastructure diagrams). These require manual review before any public sharing of the repository.
