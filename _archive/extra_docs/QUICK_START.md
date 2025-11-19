# MedForge Quick Start Guide

## Installation

```bash
# Clone/navigate to project
cd /home/danielbowne/Desktop/synth_phi_data

# Install dependencies
uv sync

# Test installation
./medforge version
```

## Basic Commands

### Generate Documents

```bash
# Default (200 documents)
./medforge generate

# Specify count
./medforge generate --count 100

# Specific formats only
./medforge generate --formats pdf,docx --count 50

# With reproducible seed
./medforge generate --seed 42 --count 100
```

### Validate Documents

```bash
# Validate directory
./medforge validate output/medforge

# Validate with details
./medforge validate output/medforge --verbose
```

### View Statistics

```bash
# Basic stats
./medforge stats output/medforge

# With directory tree
./medforge stats output/medforge --tree
```

## Common Scenarios

### Testing (Small Dataset)

```bash
./medforge generate --count 50 --output data/test --seed 1
```

### Production (Large Dataset)

```bash
./medforge generate \
  --count 5000 \
  --phi-positive 4000 \
  --phi-negative 1000 \
  --parallel-workers 4 \
  --output data/production
```

### Specific Use Cases

```bash
# Only clinical documents (DOCX)
./medforge generate --formats docx --count 200

# Only lab results (PDF)
./medforge generate --formats pdf --count 500

# Only emails
./medforge generate --formats eml --count 100
```

## Using Config Files

Create `config/my_config.yaml`:

```yaml
count: 1000
phi_positive: 800
phi_negative: 200
formats: "pdf,docx,eml"
output: "data/my_dataset"
llm_percentage: 0.2
seed: 42
parallel_workers: 4
```

Run with config:

```bash
./medforge generate --config config/my_config.yaml
```

## LLM Enhancement

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# High LLM usage (50%)
./medforge generate --llm-percentage 0.5

# No LLM (templates only)
./medforge generate --llm-percentage 0.0
```

## Complete Workflow

```bash
# 1. Generate
./medforge generate --count 100 --output data/test --seed 42

# 2. Validate
./medforge validate data/test

# 3. Check stats
./medforge stats data/test --tree
```

## All Options

```bash
./medforge generate \
  --count 1000              # Total documents
  --phi-positive 800        # PHI positive count
  --phi-negative 200        # PHI negative count
  --formats pdf,docx,eml    # Document formats
  --output data/custom      # Output directory
  --llm-percentage 0.2      # LLM enhancement (0.0-1.0)
  --seed 42                 # Random seed
  --parallel-workers 4      # Parallel workers
  --config config/file.yaml # Config file
```

## Help

```bash
# General help
./medforge --help

# Command-specific help
./medforge generate --help
./medforge validate --help
./medforge stats --help
```

## Troubleshooting

**Command not found?**
```bash
chmod +x medforge
./medforge version
```

**Import errors?**
```bash
uv sync
source .venv/bin/activate
```

**LLM not available?**
```bash
export ANTHROPIC_API_KEY="your-key"
./medforge version  # Check "LLM Available: Yes"
```

## Documentation

- **CLI_README.md** - Complete CLI documentation
- **USAGE_EXAMPLES.md** - 40+ detailed examples
- **CLI_IMPLEMENTATION_SUMMARY.md** - Technical details
- **config/example.yaml** - Configuration template

## Support

For detailed examples: `cat USAGE_EXAMPLES.md`
For full documentation: `cat CLI_README.md`
For help: `./medforge --help`
