# Synthetic PHI Data Generator (MedForge)

Production-ready synthetic Protected Health Information (PHI) document generator for training Microsoft Purview DLP systems.

## Quick Start

```bash
# Generate PHI documents (default mix)
uv run medforge generate --phi-positive 100 --phi-negative 300

# Generate CUI documents (all types)
uv run medforge generate --cui-positive 70 --cui-negative 210 --cui-all

# Generate with specific formats only
uv run medforge generate --cui-positive 50 --cui-all --formats pdf,docx

# Control CUI confidentiality notices and classification headers
uv run medforge generate --cui-positive 50 --cui-all --cui-notice random  # 50% have notices (default)
uv run medforge generate --cui-positive 50 --cui-all --cui-notice never   # No notices
uv run medforge generate --cui-positive 50 --cui-all --cui-notice always  # All have notices

# Remove generic CUI classification headers (recommended for Purview training)
uv run medforge generate --cui-positive 70 --cui-negative 210 --cui-all --cui-classification never
uv run medforge generate --cui-positive 50 --cui-all --cui-classification always  # Keep authentic headers

# Validate generated documents
./medforge validate output/medforge

# View statistics
./medforge stats output/medforge --tree
```

## Requirements

- Python 3.11+
- uv (package manager)
- Anthropic API key (for LLM enhancement)

## Setup

```bash
# Install dependencies
uv sync

# Make CLI executable
chmod +x medforge
```

### Configure LLM Enhancement (Required for --llm-percentage > 0)

1. **Create a `.env` file** in the project root with your Anthropic API key:

```bash
# Create .env file (note: KEY=VALUE format, no spaces or quotes)
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" > .env
```

**Important:** The `.env` file must use the format `KEY=VALUE`:
- Correct: `ANTHROPIC_API_KEY=sk-ant-api03-xxxxx`
- Wrong: `sk-ant-api03-xxxxx` (missing key name)
- Wrong: `ANTHROPIC_API_KEY = sk-ant-api03-xxxxx` (spaces around `=`)
- Wrong: `ANTHROPIC_API_KEY="sk-ant-api03-xxxxx"` (quotes may cause issues)

2. **Verify your configuration:**

```bash
uv run python -m src.cli setup --check
```

You should see:
```
┌───────────────────┬──────────┬─────────────────────────┐
│ Setting           │ Status   │ Details                 │
├───────────────────┼──────────┼─────────────────────────┤
│ .env file         │ ✓ Found  │ /path/to/.env           │
│ ANTHROPIC_API_KEY │ ✓ Set    │ Value: sk-ant-a...xxxx  │
│ LLM Generator     │ ✓ Ready  │ Model: claude-sonnet-4  │
└───────────────────┴──────────┴─────────────────────────┘
```

3. **If you don't have an API key**, you can still generate documents without LLM enhancement:

```bash
uv run medforge generate --cui-positive 50 --cui-all --llm-percentage 0
```

### Other Setup Commands

```bash
# Interactive configuration
uv run python -m src.cli setup --prompt

# Show example YAML config
uv run python -m src.cli setup --example

# Run linting checks (optional)
./lint.sh
```

## Features

✅ **6 File Formats**: DOCX, PDF, XLSX, PPTX, EML, Nested (emails with attachments)
✅ **PHI & CUI Support**: Generate both Protected Health Information and Controlled Unclassified Information
✅ **Customer Templates**: Integrates 37 real CMS templates (PDFs, DOCX, XLSX, EML)
✅ **LLM Enhancement**: Claude 4.5 Sonnet for clinical narratives (20% default)
✅ **Configurable CUI Controls**: Control confidentiality notices and classification headers (random/always/never)
✅ **Component Mixing**: 240 unique layout variations per template
✅ **Parallel Processing**: Multi-worker generation for speed
✅ **Validation System**: Automated PHI detection and file integrity checks
✅ **Statistics & Reporting**: Comprehensive analysis of generated datasets
✅ **No Training Labels**: All documents are realistic without positive/negative markers in content

## Project Structure

```
medforge-phi-generator/
├── src/
│   ├── cli.py                   # Main CLI interface
│   ├── formatters/              # Document generators (6 formats + customer templates)
│   ├── generators/              # Data & LLM generators (PHI + CUI)
│   ├── templates/               # Component mixing system
│   └── validators/              # PHI validation
├── scripts/
│   └── generate_all_cui.sh      # Bulk generation script (all categories)
├── cust_templates/              # Elizabeth's 37 real CMS templates (PDF, DOCX, XLSX, EML)
├── config/
│   └── example.yaml             # Sample configuration
├── output/                      # Generated documents
├── temp/output/                 # Temporary test outputs
├── medforge                     # CLI executable
└── .env                         # API keys (create this)
```

## Documentation

- `CLAUDE.md` - Original project plan
- `PROJECT_STATUS.md` - Implementation details
- `config/example.yaml` - Configuration reference
- `_archive/extra_docs/` - Additional documentation

## Archived Files

Test scripts and old implementations are in `_archive/`:
- `old_test_scripts/` - POC and test generators
- `old_formatters/` - Superseded formatter versions
- `test_outputs/` - 120 test documents (3.1MB)
- `extra_docs/` - Implementation notes

## CLI Commands

### Generate Documents
```bash
medforge generate [OPTIONS]

PHI Options:
  --count, -c INTEGER              Total PHI documents [default: 200]
  --phi-positive INTEGER           PHI positive documents
  --phi-negative INTEGER           PHI negative documents

CUI Options:
  --cui-positive INTEGER           CUI positive documents
  --cui-negative INTEGER           CUI negative documents
  --cui-categories TEXT            Specific categories (comma-separated)
  --cui-all                        Generate all 7 CUI categories
  --cui-notice TEXT                Confidentiality notice: random/always/never [default: random]
  --cui-classification TEXT        Classification headers: always/never [default: never]

General Options:
  --formats, -f TEXT               Formats: pdf,docx,xlsx,eml,pptx
  --output, -o PATH                Output directory [default: output]
  --llm-percentage FLOAT           LLM enhancement 0.0-1.0 [default: 0.2]
  --seed, -s INTEGER               Random seed for reproducibility
  --parallel-workers, -p INTEGER   Worker count [default: 1]
  --config PATH                    YAML config file
```

### Validate Documents
```bash
medforge validate <path> [--verbose]
```

### View Statistics
```bash
medforge stats <path> [--tree]
```

## Bulk Generation Script

For generating large datasets across all CUI categories:

```bash
# Generate all categories (500 positive + 1500 negative each)
./scripts/generate_all_cui.sh

# Reset and start fresh
./scripts/generate_all_cui.sh --reset
```

Features:
- Generates 7 CUI categories + PHI documents (~16,000 total)
- Tracks progress with resume capability
- 8 parallel workers with 80% LLM enhancement
- Outputs to `temp/output/`

## Performance

- **Template-based**: ~50 docs/second
- **With LLM (20%)**: ~5-10 docs/minute
- **Parallel (4 workers)**: ~20-40 docs/minute with LLM

## Cost Estimates

- **500 documents**: ~$10-15 (with 20% LLM)
- **1000 documents**: ~$20-30 (with 20% LLM)
- **Template-only**: Free (set `--llm-percentage 0`)

## License

CMS Project - Internal Use

---

**Generated by:** Claude 4.5 Sonnet (Anthropic)
**Status:** Production Ready
