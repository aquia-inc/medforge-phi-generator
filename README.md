# MedForge - Synthetic PHI/CUI Document Generator

Production-ready synthetic document generator for training Microsoft Purview DLP classifiers to detect Protected Health Information (PHI) and Controlled Unclassified Information (CUI).

**Customer:** CMS | **Purpose:** Training MS Purview to detect accidental PHI/CUI in SharePoint

## Quick Start

```bash
# PHI only — 100 positive (patient data) + 300 negative (medical context, no identifiers)
uv run python -m src.cli generate --phi-positive 100 --phi-negative 300

# CUI only — all 7 categories
uv run python -m src.cli generate --cui-positive 70 --cui-negative 210 --cui-all

# CUI single category
uv run python -m src.cli generate --cui-positive 50 --cui-negative 150 --cui-categories legal

# Mixed PHI + CUI in one run
uv run python -m src.cli generate --phi-positive 100 --phi-negative 200 --cui-positive 70 --cui-negative 210 --cui-all

# Validate generated documents
uv run python -m src.cli validate output/production_run_*/

# View statistics
uv run python -m src.cli stats output/production_run_*/ --tree
```

## Installation

```bash
# Install dependencies
uv sync

# Set API key for LLM enhancement (optional — generation works without it)
echo "ANTHROPIC_API_KEY=your-key-here" >> .env

# Verify environment
uv run python -m src.cli setup --check
```

## CLI Reference

### `medforge generate`

```
PHI Options:
  --count, -c INTEGER              Total PHI documents (80/20 positive/negative split) [default: 200]
  --phi-positive INTEGER           Explicit PHI positive count (overrides --count)
  --phi-negative INTEGER           Explicit PHI negative count (overrides --count)

CUI Options:
  --cui-positive INTEGER           CUI positive documents
  --cui-negative INTEGER           CUI negative documents
  --cui-categories TEXT            Specific categories (comma-separated)
  --cui-all                        Generate all 7 CUI categories
  --cui-notice TEXT                Confidentiality notice: random/always/never [default: random]
  --cui-classification TEXT        Classification headers: always/never [default: never]

General Options:
  --formats, -f TEXT               Formats: pdf,docx,xlsx,eml,pptx [default: all]
  --output, -o PATH                Output directory [default: output]
  --llm-percentage FLOAT           LLM enhancement rate 0.0-1.0 [default: 0.2]
  --seed, -s INTEGER               Random seed for reproducibility
  --parallel-workers, -p INTEGER   Worker count [default: 1]
  --config PATH                    YAML config file (see: medforge setup --example)
```

**Note:** `--count` applies an 80/20 positive/negative split automatically. Use `--phi-positive` / `--phi-negative` for explicit control. When `--seed` is set, output is fully deterministic for template selection and Faker data (LLM-enhanced content may vary).

### `medforge validate`

```bash
uv run python -m src.cli validate <path> [--verbose]
```

Checks file integrity, expected PHI patterns in positive documents, and absence of PHI in negative documents.

### `medforge stats`

```bash
uv run python -m src.cli stats <path> [--tree]
```

Displays document counts, format distribution, PHI/CUI breakdown, and file size statistics.

### `medforge setup`

```bash
uv run python -m src.cli setup --check     # Check environment and API key status
uv run python -m src.cli setup --prompt    # Interactively configure missing settings
uv run python -m src.cli setup --example   # Display example YAML config file
```

### `medforge version`

```bash
uv run python -m src.cli version           # Show version, Python version, LLM availability
```

---

## Generation Modes

### PHI Documents

**PHI Positive** documents always contain at least one patient identifier (name, MRN, insurance number) combined with one or more medical elements (diagnosis, medication, lab value, procedure, clinical note). These are what Purview should detect.

**PHI Negative** documents contain medical context (clinical policies, office announcements, educational materials, blank form templates, de-identified statistics) but no patient identifiers. These train Purview to avoid false positives on medical-themed content.

### CUI Documents

Seven CUI categories, each generating positive (contains sensitive data) and negative (template/redacted/blank) variants:

| Category | Examples |
|----------|----------|
| `critical_infrastructure` | System security plans, incident response, key management |
| `financial` | Budget memos, AFR forms, appropriations analysis |
| `law_enforcement` | Law enforcement sensitive information, investigations |
| `legal` | Legal memos, FOIA requests, subpoena responses, accommodation forms |
| `procurement` | Acquisition plans, source selection, vendor analysis, RFCs |
| `proprietary` | Proprietary business information, entity registration |
| `tax` | Federal taxpayer information, written determinations |

### Mixed Generation

PHI and CUI can be generated in the same run. Each gets its own output subdirectories and manifest files. Use `--phi-positive`/`--phi-negative` alongside `--cui-positive`/`--cui-negative` for full control.

---

## How Documents Are Created

### Template-Based Generation (80% default)

Most documents are built from a component mixing system that combines headers, content blocks, footers, and formatting variations to produce ~240 unique layout combinations per template type. Documents are generated across 6 formats: DOCX, PDF, XLSX, PPTX, EML, and nested EML (emails with attachments).

For CUI email documents, the system routes through format variants probabilistically:
- ~50% flat plain-text emails
- ~30% HTML-styled emails (severity tables, budget tables, formal legal styling)
- ~7% nested emails with PDF/DOCX/ZIP attachments
- Snyk vulnerability alert emails for `critical_infrastructure` category

### LLM Enhancement (20% default)

Each document has a configurable chance (`--llm-percentage`, default 0.2) of being enhanced by Claude (Anthropic's LLM). LLM enhancement generates more realistic, varied content that prevents Purview from pattern-matching on template wording.

**What the LLM generates:**
- **PHI:** Clinical SOAP notes, provider-to-provider correspondence, patient communications
- **CUI Positive:** Budget memos, SAR narratives, comptroller findings, retirement analyses, security vulnerability reports, legal memos (IRAC format), procurement rationale, tax written determinations (facts/law/analysis/conclusion)
- **CUI Negative:** Public-facing prose for hard negatives — policy overviews, training descriptions, published guidance, taxpayer advice (at half the positive LLM rate)
- **Customer Templates:** 8 enrichable templates get LLM-generated narrative sections appended (acquisition strategy, market research, justification narratives, incident summaries)
- **Snyk Emails:** Highest-severity vulnerability finding gets LLM-generated description, impact analysis, and remediation narrative

**When the LLM is NOT used:**
- `ANTHROPIC_API_KEY` is not set — falls back silently to templates
- `--llm-percentage 0` is specified — fully offline, free generation
- The random roll doesn't select this document (80% of docs by default)
- The API call fails — automatic silent fallback to template-based generation

**CUI negative half-rate:** Negative documents use half the `--llm-percentage` rate (e.g., at 0.2, positives get 20% LLM and negatives get 10%). This balances realism against cost.

**Cost:** ~$0.02-0.03 per LLM-enhanced document. Set `--llm-percentage 0` for free generation.

### Customer Templates (20% of CUI documents)

27 registered CMS templates (from `cust_templates/`) are mixed into CUI generation with a 20% selection rate. Templates span 4 categories:

| Category | Count | Examples |
|----------|-------|----------|
| Procurement | 9 | IGCE, CLIN Templates, Market Research, RFC Memo, Acquisition Plan |
| Legal | 7 | B6 Letter, FOIA requests, Subpoena Response, Reasonable Accommodation |
| Critical Infrastructure | 6 | KMP, Rules of Behavior, Incident Response, Test Validation Reports |
| Financial | 5 | AFR Additional Info, DIBO AFR, Supplemental AFR, OIT FO |

**Category-weighted selection** picks a category first (uniform random), then a template within that category. This prevents bias when one category has more templates than others.

**Five fill patterns** are supported: PDF fillable (reportlab overlay), PDF copy pair, DOCX placeholder substitution, DOCX table fill, and DOCX underline fill. Synthetic data is generated via Faker (names, addresses, contract numbers, prices, system names).

**LLM-enriched templates:** 8 templates (AcquisitionPlan, IncidentResponse, KMP, MarketResearch, JOFOC, JALimitedSource, SubpoenaResponse, RFCMemo) can receive LLM-generated narrative sections appended to the filled document. This is controlled by the same `--llm-percentage` rate.

See [docs/adding-customer-templates.md](docs/adding-customer-templates.md) for the full registration guide.

### CUI Controls

**`--cui-notice`** controls generic "contains CUI" confidentiality footers:
- `random` (default) — 50% of documents include notices
- `always` — all CUI documents include notices
- `never` — no notices, forces Purview to learn content patterns

**`--cui-classification`** controls CUI classification headers (e.g., "CONTROLLED UNCLASSIFIED INFORMATION - TAX"):
- `never` (default) — no classification headers (recommended for Purview training)
- `always` — include authentic government classification markings

---

## Output Structure

```
output/production_run_YYYYMMDD_HHMMSS/
├── phi_positive/                      # PHI docs with patient data
├── phi_negative/                      # PHI docs without patient data
├── CUI-Critical_Infrastructure-Positive/
├── CUI-Critical_Infrastructure-Negative/
├── CUI-Financial-Positive/
├── CUI-Financial-Negative/
├── CUI-Legal-Positive/
├── CUI-Legal-Negative/
├── CUI-Procurement-Positive/
├── CUI-Procurement-Negative/
├── CUI-Proprietary Business-Positive/
├── CUI-Proprietary Business-Negative/
├── CUI-Law Enforcement-Positive/
├── CUI-Law Enforcement-Negative/
├── CUI-Tax-Positive/
├── CUI-Tax-Negative/
└── metadata/
    ├── manifest.json                  # PHI document index with PHI elements
    └── cui_manifest.json              # CUI document index with category, variant, source
```

Manifest files track each document's format, polarity, category, whether it was LLM-enhanced, and whether it came from a customer template. The CUI manifest also records the `variant` field (`standard`, `nested_attachment`, `html_styled`, `snyk_alert`).

---

## Testing

MedForge has a layered test suite: fast unit tests, integration tests that generate real documents, and standalone validation scripts for production runs.

```bash
# Run all unit + integration tests (~2 min)
uv run python -m pytest tests/ -v

# Run only fast unit tests (~1 sec)
uv run python -m pytest tests/test_component_mixer.py tests/test_email_formatters.py tests/test_cui_formatters.py tests/test_cui_generators.py -v

# Run integration tests (~2 min, generates documents)
uv run python -m pytest tests/test_integration.py -v

# Linting (syntax + ruff critical checks)
./lint.sh
```

### Standalone Validation Scripts

These scripts validate production output and require generated documents:

```bash
# Purview fidelity validation — 19 automated checks (MIME structure, encoding, file integrity)
uv run python tests/validate_file_fidelity.py output/production_run_*/

# Full artifact matrix — generates 114 artifacts covering all category x format x polarity combos
uv run python tests/generate_artifact_matrix.py

# LLM integration smoke test — validates LLM enhancement paths (requires ANTHROPIC_API_KEY, ~2-3 min)
uv run python tests/test_llm_smoke.py
```

See [docs/testing.md](docs/testing.md) for the full testing guide and [docs/test-coverage-tracker.md](docs/test-coverage-tracker.md) for coverage status.

---

## Performance & Cost

| Mode | Speed | Cost |
|------|-------|------|
| Template-only (`--llm-percentage 0`) | ~50 docs/second | Free |
| With LLM (20% default) | ~5-10 docs/minute | ~$0.02-0.03/doc |
| Parallel (4 workers + LLM) | ~20-40 docs/minute | Same per-doc cost |

**Estimates:** 500 docs ~$10-15, 1000 docs ~$20-30 (at 20% LLM). Template-only is always free.

---

## Project Structure

```
medforge-phi-generator/
├── src/
│   ├── cli.py                       # CLI interface (Typer)
│   ├── formatters/                  # Document generators (6 formats + customer templates)
│   │   ├── base_email_formatter.py  # Shared MIME construction base
│   │   ├── pdf_form_populator.py    # Customer template manager + PDF form filling
│   │   └── ...                      # DOCX, PDF, XLSX, PPTX, EML, nested, HTML, Snyk formatters
│   ├── generators/                  # Data & LLM generators
│   │   ├── patient_generator.py     # Faker-based synthetic patient/provider/facility data
│   │   └── llm_generator.py         # Claude API integration with structured outputs
│   ├── templates/                   # Component mixing system (~240 layout variations)
│   └── validators/                  # PHI validation
├── cust_templates/                  # 56 CMS template files (27 registered, 1 disabled)
├── tests/
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── test_component_mixer.py      # ComponentMixer + font mapping tests (17 tests)
│   ├── test_cui_formatters.py       # CUI formatter output validation (14 tests)
│   ├── test_cui_generators.py       # CUI generator data layer tests (23 tests)
│   ├── test_email_formatters.py     # Email/MIME construction + nested emails (9 tests)
│   ├── test_integration.py          # End-to-end generation tests (12 tests)
│   ├── test_llm_smoke.py            # LLM integration smoke test (standalone)
│   ├── generate_artifact_matrix.py  # Full format x category coverage (standalone)
│   └── validate_file_fidelity.py    # 19 Purview fidelity checks (standalone)
├── config/
│   └── example.yaml                 # Sample YAML configuration
├── docs/                            # Additional documentation
├── medforge                         # Bash CLI wrapper (alternative to uv run)
├── lint.sh                          # Linting script
└── .env                             # API keys (create this)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/testing.md](docs/testing.md) | Full testing guide: architecture, how to run, how to add tests |
| [docs/test-coverage-tracker.md](docs/test-coverage-tracker.md) | Test coverage status and outstanding gaps |
| [docs/adding-customer-templates.md](docs/adding-customer-templates.md) | Step-by-step guide for registering new CMS templates |
| [docs/DEMO.md](docs/DEMO.md) | Customer demo script with talking points |
| [CLAUDE.md](CLAUDE.md) | Developer notes: PDF filling, template patterns, CMS requirements |

## License

CMS Project - Internal Use
