# MedForge Demo Guide

## Synthetic PHI & CUI Document Generator for MS Purview DLP Training

**Audience:** CMS stakeholders, Purview administrators, security teams
**Goal:** Demonstrate MedForge's ability to generate realistic synthetic documents across all PHI/CUI categories, formats, and variance levels

---

## Pre-Demo Setup

```bash
# Install dependencies (one-time)
uv sync

# Generate a small mixed batch to walk through
uv run python -m src.cli generate \
  --phi-positive 20 --phi-negative 40 \
  --cui-positive 30 --cui-negative 60 --cui-all \
  --llm-percentage 0.2 --seed 42
```

---

## 1. The Problem We're Solving

- Microsoft Purview DLP classifiers need 200-500 positive examples and 2-3x negatives
- Real PHI/CUI cannot be used for training (HIPAA, CUI handling requirements)
- MedForge generates realistic synthetic documents that look like real PHI/CUI but contain zero actual sensitive data
- Output structure is ready for direct upload to Purview classifier training

---

## 2. Generation Modes

MedForge supports three generation modes: PHI-only, CUI-only, or mixed.

### PHI Only (default)
```bash
# Simple count (80/20 positive/negative split)
uv run python -m src.cli generate --count 200

# Explicit positive/negative counts
uv run python -m src.cli generate --phi-positive 100 --phi-negative 300
```

### CUI Only — All 7 Categories
```bash
uv run python -m src.cli generate \
  --cui-positive 200 --cui-negative 400 --cui-all
```

### CUI — Specific Categories
```bash
# Single category
uv run python -m src.cli generate \
  --cui-positive 50 --cui-negative 100 \
  --cui-categories financial

# Multiple categories
uv run python -m src.cli generate \
  --cui-positive 100 --cui-negative 200 \
  --cui-categories "financial,tax,legal"
```

### Mixed PHI + CUI
```bash
uv run python -m src.cli generate \
  --phi-positive 100 --phi-negative 200 \
  --cui-positive 100 --cui-negative 200 --cui-all
```

---

## 3. The 7 CUI Categories

Each category produces distinct document types with category-specific content:

| Category | What It Generates | Example Documents |
|----------|-------------------|-------------------|
| **critical_infrastructure** | Emergency plans, system vulnerability reports, physical security | KMP, Rules of Behavior, Incident Response, HHS RBD |
| **financial** | Budget data, EFT details, retirement info | AFR reports, DIBO AFR, OIT FO, Supplemental AFR |
| **law_enforcement** | Criminal history, investigation details | Investigative summaries, criminal history reports |
| **legal** | Admin proceedings, privilege, collective bargaining | B6 Letters, FOIA requests, Subpoena responses, Accommodation forms |
| **procurement** | Source selection, contract details, market research | IGCE, CLIN, Market Research, JOFOC, Acquisition Plans |
| **proprietary** | Internal CMS communications, business info | Internal announcements, newsletters, leadership messages |
| **tax** | Federal taxpayer info, written determinations | Tax processing letters, IRS correspondence |

**Demo: Generate a single category and inspect**
```bash
uv run python -m src.cli generate \
  --cui-positive 20 --cui-negative 40 \
  --cui-categories procurement --seed 42

# View the output
uv run python -m src.cli stats output/production_run_*/ --tree
```

---

## 4. Controlling LLM Enhancement

The `--llm-percentage` flag controls what fraction of documents get AI-generated narrative content (via Claude). The rest use template-based generation with Faker synthetic data.

### Zero LLM (fully offline, fastest)
```bash
uv run python -m src.cli generate --count 500 --llm-percentage 0
```
- All documents use Faker-generated data with template structures
- No API key required, no network needed
- Fastest generation (~1-2 docs/second)
- Good for: initial Purview training, testing pipelines, demos without API access

### Low LLM (20%, default)
```bash
uv run python -m src.cli generate --count 500 --llm-percentage 0.2
```
- 80% template-based, 20% get LLM-enhanced narratives
- LLM adds: varied clinical prose, natural email tone, realistic report language
- Good for: production training data with enough variety to prevent template overfitting

### High LLM (50-100%)
```bash
uv run python -m src.cli generate --count 200 --llm-percentage 0.5
```
- More documents get unique AI-generated content
- Higher variety but slower generation and higher API cost
- Good for: small, high-quality training sets where every document should be unique

### What LLM Enhancement Does

| Without LLM | With LLM |
|--------------|----------|
| Faker names, addresses, dates | Same Faker data PLUS natural-language narratives |
| Template sentence structures | Varied prose that reads like a human wrote it |
| Predictable patterns per format | Each document has unique phrasing |
| Fast, deterministic | Slower, non-deterministic (even with same seed) |

**17 customer templates** support LLM enrichment — the AI generates realistic narrative sections (clinical notes, legal reasoning, procurement justifications) that get appended to the Faker-populated base document.

**Demo: Compare LLM vs non-LLM output**
```bash
# Generate without LLM
uv run python -m src.cli generate --cui-positive 5 --cui-categories legal --llm-percentage 0 --seed 42

# Generate with full LLM
uv run python -m src.cli generate --cui-positive 5 --cui-categories legal --llm-percentage 1.0 --seed 42

# Open and compare documents side by side
```

---

## 5. Output Structure

Every generation run creates a timestamped directory:

```
output/production_run_20260409_153000/
  phi_positive/           # Documents containing synthetic PHI (Purview should CATCH)
    ProgressNote_0001.docx
    LabResult_0002.pdf
    EmailWithAttachment_0003.eml
    CaseStudy_0004.pptx
    ...
  phi_negative/           # Medical context, NO patient identifiers (Purview should IGNORE)
    Announcement_0001.eml
    Educational_0002.pptx
    MedicalPolicy_0003.pdf
    ...
  cui_positive/           # Documents containing CUI indicators (Purview should CATCH)
    financial_0001.docx
    procurement_0002.pdf
    legal_email_0003.eml
    ...
  cui_negative/           # Business content, NO CUI indicators (Purview should IGNORE)
    financial_0001.docx
    legal_email_0002.eml
    ...
  metadata/
    manifest.json         # Complete manifest: file list, stats, generation parameters
    cui_manifest.json     # CUI-specific manifest with category and variant tracking
```

### Manifest Tracking

The manifest records every generated file with its metadata:

```bash
# View generation summary
cat output/production_run_*/metadata/manifest.json | python -m json.tool | head -30
```

Each file entry tracks: path, polarity (positive/negative), document type, format, category (for CUI), variant (standard/nested/html/snyk/bugcrowd/email_wrapped), and whether it was LLM-enhanced.

---

## 6. Document Diversity

MedForge produces documents across 5 formats with multiple variant types per format:

### Format Distribution
| Format | PHI Types | CUI Types |
|--------|-----------|-----------|
| **DOCX** | Progress notes, registration forms | Category-specific reports, customer templates |
| **PDF** | Lab results, official documents | Category-specific reports, filled CMS forms |
| **EML** | Provider emails, patient notifications, nested emails with attachments | Category-specific emails, ServiceNow tickets, BugCrowd alerts, internal announcements |
| **PPTX** | Case studies, educational materials | Category-specific presentations |
| **XLSX** | Lab panels, patient lists | Category-specific spreadsheets (budgets, contracts) |

### Email Variants (CUI)
CUI email generation includes several realistic variant types:
- **Standard emails** — plain-text category-specific emails
- **Nested attachments** — emails with PDF/DOCX/ZIP attachments
- **HTML-styled** — rich HTML emails with category-appropriate styling
- **Snyk alerts** — vulnerability disclosure emails (critical_infrastructure)
- **BugCrowd reports** — bug bounty vulnerability emails (critical_infrastructure)
- **Internal announcements** — CMS newsletters, leadership messages (proprietary)
- **ServiceNow tickets** — CMSConnect ticket notifications
- **Email-wrapped templates** — customer CMS forms attached to cover emails

### Customer Template Integration
27 real CMS form templates are integrated and populated with synthetic data:
- 80% of templates are wrapped in emails as attachments (configurable via `--template-email-ratio`)
- Templates get Faker-generated data appropriate to their category
- 17 templates support LLM narrative enrichment

```bash
# Control template email wrapping
uv run python -m src.cli generate --cui-positive 50 --cui-all \
  --template-email-ratio 0.8   # 80% wrapped in emails (default)

uv run python -m src.cli generate --cui-positive 50 --cui-all \
  --template-email-ratio 0.0   # All bare files, no email wrapping
```

---

## 7. Controlling CUI Markers

Two flags control how CUI documents are labeled:

```bash
# Confidentiality notice footers: random (50%), always, or never
uv run python -m src.cli generate --cui-positive 100 --cui-all --cui-notice random
uv run python -m src.cli generate --cui-positive 100 --cui-all --cui-notice never

# Classification headers (e.g., "CUI - TAX"): always or never
uv run python -m src.cli generate --cui-positive 100 --cui-all --cui-classification always
```

Setting `--cui-notice never` forces Purview to learn content patterns rather than relying on banner text.

---

## 8. Reproducibility & Scale

```bash
# Reproducible: same seed = same documents (except LLM-enhanced content)
uv run python -m src.cli generate --count 500 --seed 42
uv run python -m src.cli generate --count 500 --seed 42  # identical output

# Scale with parallel workers
uv run python -m src.cli generate --count 1000 --parallel-workers 4

# Validate output integrity
uv run python -m src.cli validate output/production_run_*/

# View statistics and format distribution
uv run python -m src.cli stats output/production_run_*/
uv run python -m src.cli stats output/production_run_*/ --tree
```

---

## 9. Validation & Stats

```bash
# Validate generated documents (file integrity, MIME structure, PHI patterns)
uv run python -m src.cli validate output/production_run_*/

# View generation statistics
uv run python -m src.cli stats output/production_run_*/

# Detailed tree view of all generated files
uv run python -m src.cli stats output/production_run_*/ --tree
```

The built-in validator runs 19 fidelity checks: file integrity, MIME structure, encoding, attachment types, PHI content presence/absence, and CUI markings.

---

## Quick Reference: Key Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--count` | 200 | Total PHI documents (80/20 pos/neg split) |
| `--phi-positive` / `--phi-negative` | — | Explicit PHI counts |
| `--cui-positive` / `--cui-negative` | — | Explicit CUI counts |
| `--cui-categories` | — | Comma-separated: `financial,tax,legal,...` |
| `--cui-all` | false | Generate all 7 CUI categories |
| `--llm-percentage` | 0.2 | Fraction of docs with LLM enhancement (0.0-1.0) |
| `--template-email-ratio` | 0.8 | Fraction of templates wrapped in emails (0.0-1.0) |
| `--cui-notice` | random | Confidentiality footers: `random`, `always`, `never` |
| `--cui-classification` | never | Classification headers: `always`, `never` |
| `--formats` | pdf,docx,xlsx,eml,pptx | Output format filter |
| `--seed` | — | Random seed for reproducibility |
| `--parallel-workers` | 1 | Parallel generation workers |
| `--output` | output | Output directory |
| `--config` | — | YAML config file path |

---

## Commands Cheat Sheet

```bash
# Quick demo (small batch, no LLM)
uv run python -m src.cli generate --count 50 --llm-percentage 0

# Production PHI training set
uv run python -m src.cli generate --phi-positive 400 --phi-negative 800 --llm-percentage 0.2

# Production CUI training set (all categories)
uv run python -m src.cli generate --cui-positive 200 --cui-negative 400 --cui-all --llm-percentage 0.2

# Single CUI category deep dive
uv run python -m src.cli generate --cui-positive 50 --cui-negative 100 --cui-categories financial

# Full mixed generation
uv run python -m src.cli generate \
  --phi-positive 200 --phi-negative 400 \
  --cui-positive 200 --cui-negative 400 --cui-all \
  --llm-percentage 0.2 --parallel-workers 4

# Inspect results
uv run python -m src.cli stats output/production_run_*/ --tree
uv run python -m src.cli validate output/production_run_*/
```
