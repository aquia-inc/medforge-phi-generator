# MedForge CLI Documentation

A comprehensive command-line interface for generating synthetic PHI (Protected Health Information) data in multiple formats.

## Installation

```bash
# Install with uv
uv sync

# Or install with pip
pip install -e .
```

This will install the `medforge` command globally.

## Quick Start

```bash
# Generate 200 documents with default settings
medforge generate

# Generate 100 documents (80 PHI positive, 20 PHI negative)
medforge generate --count 100

# Specify exact PHI distribution
medforge generate --phi-positive 80 --phi-negative 20

# Generate only specific formats
medforge generate --formats pdf,docx --count 50

# Use parallel processing for faster generation
medforge generate --count 1000 --parallel-workers 4

# Use a configuration file
medforge generate --config config/example.yaml
```

## Commands

### `medforge generate`

Generate synthetic PHI documents in multiple formats.

**Options:**

- `--count, -c INTEGER`: Total number of documents to generate (default: 200)
- `--phi-positive INTEGER`: Number of PHI positive documents (default: 80% of count)
- `--phi-negative INTEGER`: Number of PHI negative documents (default: 20% of count)
- `--formats, -f TEXT`: Comma-separated list of formats (default: "pdf,docx,xlsx,eml,pptx")
- `--output, -o TEXT`: Output directory (default: "output/medforge")
- `--llm-percentage FLOAT`: Percentage of LLM-enhanced docs, 0.0-1.0 (default: 0.2)
- `--seed, -s INTEGER`: Random seed for reproducibility
- `--parallel-workers, -p INTEGER`: Number of parallel workers (default: 1)
- `--config TEXT`: Path to YAML configuration file

**Valid Formats:**

- `pdf` - PDF documents (lab results, policies)
- `docx` - Word documents (progress notes, lab results, policies, forms)
- `xlsx` - Excel spreadsheets (lab data)
- `eml` - Email files (provider communications, announcements)
- `pptx` - PowerPoint presentations (case studies, educational materials)

**Examples:**

```bash
# Basic generation
medforge generate --count 100

# Custom PHI distribution
medforge generate --phi-positive 150 --phi-negative 50

# Only PDFs and Word docs
medforge generate --formats pdf,docx --count 200

# With reproducible seed
medforge generate --seed 42 --count 100

# Fast parallel generation
medforge generate --count 1000 --parallel-workers 8

# Custom output directory
medforge generate --output /path/to/my/data --count 500

# Using config file
medforge generate --config my_config.yaml
```

### `medforge validate`

Validate generated documents for integrity and correctness.

**Usage:**

```bash
# Validate all files in a directory
medforge validate output/medforge

# Validate a single file
medforge validate output/medforge/PHI_POS_ProgressNote_0001.docx

# Verbose output (show all errors)
medforge validate output/medforge --verbose
```

**What it checks:**

- File can be opened successfully
- File is not empty
- Format-specific validation:
  - **DOCX**: Valid Word document structure
  - **PDF**: Valid PDF header
  - **XLSX**: Valid Excel workbook
  - **EML**: Contains required email headers

### `medforge stats`

Show statistics about generated documents.

**Usage:**

```bash
# Basic statistics
medforge stats output/medforge

# Include directory tree
medforge stats output/medforge --tree
```

**Information displayed:**

- Total file count and size
- PHI positive vs negative distribution
- Format breakdown with sizes
- Document type distribution
- Average file sizes
- Optional directory tree view

### `medforge version`

Display version information.

```bash
medforge version
```

## Configuration File

You can use a YAML configuration file to set all options:

```yaml
# config/my_config.yaml
count: 500
phi_positive: 400
phi_negative: 100
formats: "pdf,docx,eml"
output: "output/my_dataset"
llm_percentage: 0.3
seed: 12345
parallel_workers: 4
```

Use it with:

```bash
medforge generate --config config/my_config.yaml
```

See `config/example.yaml` for a complete example.

## LLM Enhancement

MedForge can use Claude AI to generate more realistic clinical narratives:

1. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   ```

2. Configure LLM percentage (default 20%):
   ```bash
   medforge generate --llm-percentage 0.3  # 30% LLM-enhanced
   ```

Without an API key, MedForge will use template-based generation for all documents.

## Output Structure

Generated files follow this naming convention:

```
output/
└── medforge/
    ├── PHI_POS_ProgressNote_0001.docx
    ├── PHI_POS_LabResult_0002.pdf
    ├── PHI_POS_ProviderEmail_0003.eml
    ├── PHI_POS_CaseStudy_0004.pptx
    ├── PHI_NEG_Policy_0001.pdf
    ├── PHI_NEG_Announcement_0002.eml
    └── ...
```

**Filename components:**

- `PHI_POS` - Contains PHI (patient identifiers, medical records)
- `PHI_NEG` - No PHI (policies, blank forms, announcements)
- Document type (ProgressNote, LabResult, etc.)
- Sequential number

## Performance Tips

### Parallel Processing

For large batches, use parallel workers:

```bash
# Fast generation with 8 workers
medforge generate --count 5000 --parallel-workers 8
```

**Considerations:**

- More workers = faster generation but higher memory usage
- Recommended: 1-8 workers depending on CPU cores
- Sequential (1 worker) is more memory-efficient for large LLM batches

### Reproducibility

Use a seed for consistent results:

```bash
medforge generate --seed 42 --count 100
```

This ensures:
- Same patients, providers, facilities
- Same document selections
- Identical output across runs

### Format Selection

Generate only needed formats to save time:

```bash
# Just PDFs and Word docs
medforge generate --formats pdf,docx --count 1000
```

## Examples

### Small Development Dataset

```bash
medforge generate \
  --count 50 \
  --formats docx,pdf \
  --output data/dev \
  --seed 1
```

### Large Production Dataset

```bash
medforge generate \
  --count 10000 \
  --phi-positive 8000 \
  --phi-negative 2000 \
  --parallel-workers 8 \
  --llm-percentage 0.2 \
  --output data/production \
  --seed 42
```

### Testing All Formats

```bash
medforge generate \
  --count 500 \
  --formats pdf,docx,xlsx,eml,pptx \
  --output data/all_formats
```

### Validation Workflow

```bash
# Generate documents
medforge generate --count 100 --output data/test

# Validate output
medforge validate data/test --verbose

# View statistics
medforge stats data/test --tree
```

## Troubleshooting

### "LLM Available: No"

The Anthropic API key is not set. Either:

1. Set the API key:
   ```bash
   export ANTHROPIC_API_KEY="your-key"
   ```

2. Or use template-only generation (no LLM):
   ```bash
   medforge generate --llm-percentage 0
   ```

### Memory Issues

If running out of memory with parallel workers:

1. Reduce workers:
   ```bash
   medforge generate --parallel-workers 1
   ```

2. Generate in smaller batches:
   ```bash
   medforge generate --count 1000
   medforge generate --count 1000 --output output/batch2
   ```

### File Permission Errors

Ensure output directory is writable:

```bash
chmod -R u+w output/
```

## Advanced Usage

### Custom Python Script

You can also import the generator in your own scripts:

```python
from src.cli import MedForgeGenerator

generator = MedForgeGenerator(
    output_dir="my_output",
    seed=42,
    llm_percentage=0.2,
    formats=["pdf", "docx"]
)

stats = generator.generate_batch(
    phi_positive_count=80,
    phi_negative_count=20,
    parallel_workers=4
)

print(stats)
```

## Support

For issues or questions:

1. Check the documentation
2. Review `config/example.yaml` for configuration examples
3. Use `--help` on any command for detailed options
4. Enable verbose mode for debugging: `--verbose`

## License

See LICENSE file for details.
