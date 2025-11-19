# MedForge CLI Usage Examples

Complete guide with practical examples for generating synthetic PHI data.

## Quick Start

```bash
# Method 1: Using wrapper script (recommended)
./medforge generate --count 100

# Method 2: Using Python directly
source .venv/bin/activate
python src/cli.py generate --count 100

# Method 3: Using installed command (after pip install -e .)
medforge generate --count 100
```

## Basic Examples

### Generate Default Dataset (200 documents)

```bash
./medforge generate
```

This generates:
- 160 PHI positive documents (80%)
- 40 PHI negative documents (20%)
- All formats: PDF, DOCX, XLSX, EML, PPTX
- 20% LLM-enhanced (if API key available)
- Output: `output/medforge/`

### Generate Small Test Dataset

```bash
./medforge generate --count 50 --output data/test --seed 42
```

Perfect for testing and development with reproducible results.

### Generate Specific Format Only

```bash
# Only Word documents
./medforge generate --formats docx --count 100

# Only PDFs and Word docs
./medforge generate --formats pdf,docx --count 200

# Only emails
./medforge generate --formats eml --count 50
```

## PHI Distribution Examples

### Custom PHI Positive/Negative Split

```bash
# 90% PHI positive, 10% PHI negative
./medforge generate --phi-positive 900 --phi-negative 100

# Equal split
./medforge generate --phi-positive 500 --phi-negative 500

# Mostly negative (for testing PHI detection false positives)
./medforge generate --phi-positive 50 --phi-negative 450
```

### Pure PHI Positive Dataset

```bash
./medforge generate --phi-positive 1000 --phi-negative 0
```

### Pure PHI Negative Dataset

```bash
./medforge generate --phi-positive 0 --phi-negative 500
```

## LLM Enhancement Examples

### No LLM (Template-Only)

```bash
./medforge generate --llm-percentage 0.0 --count 500
```

Fastest generation, no API costs.

### High LLM Usage

```bash
./medforge generate --llm-percentage 0.5 --count 200
```

50% of documents use Claude AI for realistic clinical narratives.

### Maximum LLM (All Documents)

```bash
./medforge generate --llm-percentage 1.0 --count 100
```

Best quality but slower and more API usage.

## Performance Examples

### Fast Sequential Generation

```bash
./medforge generate --count 100 --parallel-workers 1
```

Lower memory usage, good for laptops.

### Fast Parallel Generation

```bash
# 4 workers (good for most systems)
./medforge generate --count 1000 --parallel-workers 4

# 8 workers (high-end systems)
./medforge generate --count 5000 --parallel-workers 8
```

Faster but uses more memory.

### Large Dataset Generation

```bash
./medforge generate \
  --count 10000 \
  --phi-positive 8000 \
  --phi-negative 2000 \
  --parallel-workers 8 \
  --llm-percentage 0.15 \
  --seed 12345 \
  --output data/production
```

Production-scale dataset with reproducibility.

## Configuration File Examples

### Create Config File

```yaml
# config/small_test.yaml
count: 100
phi_positive: 80
phi_negative: 20
formats: "docx,pdf"
output: "data/small_test"
llm_percentage: 0.0
seed: 42
parallel_workers: 2
```

### Use Config File

```bash
./medforge generate --config config/small_test.yaml
```

### Override Config File Options

```bash
# Use config but override count
./medforge generate --config config/small_test.yaml --count 200
```

## Validation Examples

### Validate Directory

```bash
./medforge validate output/medforge
```

### Validate with Verbose Output

```bash
./medforge validate output/medforge --verbose
```

Shows detailed error messages for failed files.

### Validate Single File

```bash
./medforge validate output/medforge/PHI_POS_ProgressNote_0001.docx
```

## Statistics Examples

### Basic Statistics

```bash
./medforge stats output/medforge
```

Shows:
- Total files and size
- PHI positive/negative distribution
- Format breakdown
- Document type distribution

### Statistics with Directory Tree

```bash
./medforge stats output/medforge --tree
```

Includes visual directory structure.

## Complete Workflows

### Development Workflow

```bash
# 1. Generate small test dataset
./medforge generate --count 50 --formats docx --output data/dev --seed 1

# 2. Validate the output
./medforge validate data/dev

# 3. Check statistics
./medforge stats data/dev --tree
```

### Production Workflow

```bash
# 1. Create production config
cat > config/production.yaml << EOF
count: 10000
phi_positive: 8000
phi_negative: 2000
formats: "pdf,docx,xlsx,eml,pptx"
output: "data/production"
llm_percentage: 0.2
seed: 42
parallel_workers: 8
EOF

# 2. Generate dataset
./medforge generate --config config/production.yaml

# 3. Validate output
./medforge validate data/production --verbose > validation_report.txt

# 4. Generate statistics
./medforge stats data/production --tree > stats_report.txt
```

### Testing All Formats

```bash
# Generate 100 of each format
for format in pdf docx xlsx eml pptx; do
  ./medforge generate \
    --count 100 \
    --formats $format \
    --output data/format_test_$format \
    --seed 42
done

# Validate all
for format in pdf docx xlsx eml pptx; do
  ./medforge validate data/format_test_$format
done
```

### Reproducibility Testing

```bash
# Generate same dataset twice
./medforge generate --count 100 --seed 42 --output run1
./medforge generate --count 100 --seed 42 --output run2

# Compare outputs (should be identical)
diff -r run1 run2
```

## Advanced Examples

### Format-Specific Batches

```bash
# Clinical documents only (DOCX)
./medforge generate \
  --formats docx \
  --phi-positive 500 \
  --phi-negative 0 \
  --llm-percentage 0.3 \
  --output data/clinical_notes

# Lab results only (PDF)
./medforge generate \
  --formats pdf \
  --phi-positive 1000 \
  --phi-negative 0 \
  --output data/lab_results

# Communications only (EML)
./medforge generate \
  --formats eml \
  --phi-positive 300 \
  --phi-negative 200 \
  --output data/emails
```

### Incremental Generation

```bash
# Generate initial batch
./medforge generate --count 1000 --output data/batch1 --seed 1

# Add more later (different seed for variety)
./medforge generate --count 1000 --output data/batch2 --seed 2

# Combine for validation
mkdir data/combined
cp -r data/batch1/* data/combined/
cp -r data/batch2/* data/combined/
./medforge validate data/combined
```

### Performance Testing

```bash
# Test with different worker counts
for workers in 1 2 4 8; do
  echo "Testing with $workers workers..."
  time ./medforge generate \
    --count 100 \
    --parallel-workers $workers \
    --output data/perf_test_$workers \
    --seed 42
done
```

### Quality Testing

```bash
# Test different LLM percentages
for pct in 0.0 0.2 0.5 1.0; do
  echo "Testing LLM percentage: $pct"
  ./medforge generate \
    --count 50 \
    --llm-percentage $pct \
    --output data/llm_test_$pct \
    --seed 42
done

# Review quality differences
./medforge stats data/llm_test_0.0
./medforge stats data/llm_test_1.0
```

## Troubleshooting Examples

### Check LLM Availability

```bash
./medforge version
# Look for "LLM Available: Yes"
```

### Test Without LLM

```bash
# Temporarily unset API key
unset ANTHROPIC_API_KEY
./medforge generate --count 10 --output data/no_llm_test

# Restore API key
export ANTHROPIC_API_KEY="your-key"
```

### Memory-Constrained Generation

```bash
# Generate in smaller batches with 1 worker
./medforge generate --count 500 --parallel-workers 1 --output data/batch1
./medforge generate --count 500 --parallel-workers 1 --output data/batch2
./medforge generate --count 500 --parallel-workers 1 --output data/batch3
```

### Debug Validation Failures

```bash
# Validate with verbose output
./medforge validate output/medforge --verbose 2>&1 | tee validation.log

# Check specific format
find output/medforge -name "*.docx" | head -1 | xargs ./medforge validate --verbose
```

## Integration Examples

### CI/CD Pipeline

```bash
#!/bin/bash
# generate_test_data.sh

set -e  # Exit on error

# Generate test dataset
./medforge generate \
  --count 100 \
  --formats pdf,docx \
  --output data/ci_test \
  --seed 42 \
  --llm-percentage 0.0  # Disable LLM for CI

# Validate
if ./medforge validate data/ci_test; then
  echo "✓ Test data generated and validated successfully"
else
  echo "✗ Validation failed"
  exit 1
fi

# Check statistics
./medforge stats data/ci_test
```

### Data Refresh Script

```bash
#!/bin/bash
# refresh_test_data.sh

BACKUP_DIR="data/backup_$(date +%Y%m%d_%H%M%S)"

# Backup existing data
if [ -d "data/test" ]; then
  mv data/test "$BACKUP_DIR"
  echo "Backed up to $BACKUP_DIR"
fi

# Generate fresh data
./medforge generate --config config/test.yaml

# Validate
if ./medforge validate data/test; then
  echo "✓ Test data refreshed successfully"
  rm -rf "$BACKUP_DIR"
else
  echo "✗ Validation failed, restoring backup"
  mv "$BACKUP_DIR" data/test
  exit 1
fi
```

### Quality Assurance

```bash
#!/bin/bash
# qa_check.sh

OUTPUT_DIR="data/qa_$(date +%Y%m%d)"

# Generate QA dataset
./medforge generate \
  --count 1000 \
  --output "$OUTPUT_DIR" \
  --seed 42

# Run checks
echo "Running validation..."
./medforge validate "$OUTPUT_DIR" --verbose > "${OUTPUT_DIR}_validation.txt"

echo "Generating statistics..."
./medforge stats "$OUTPUT_DIR" --tree > "${OUTPUT_DIR}_stats.txt"

# Check for expected distribution
TOTAL=$(find "$OUTPUT_DIR" -type f | wc -l)
if [ "$TOTAL" -eq 1000 ]; then
  echo "✓ Generated expected number of files: $TOTAL"
else
  echo "✗ Unexpected file count: $TOTAL (expected 1000)"
  exit 1
fi
```

## Tips and Best Practices

### 1. Always Use Seeds for Testing

```bash
# Good - reproducible
./medforge generate --seed 42 --count 100

# Avoid for testing - random every time
./medforge generate --count 100
```

### 2. Start Small, Scale Up

```bash
# Test first with small count
./medforge generate --count 10 --output data/smoke_test

# Then scale to production
./medforge generate --count 10000 --output data/production
```

### 3. Use Config Files for Complex Setups

```bash
# Easier to maintain than long command lines
./medforge generate --config config/production.yaml
```

### 4. Validate Immediately After Generation

```bash
# Generate and validate in one go
./medforge generate --count 100 --output data/test && \
  ./medforge validate data/test
```

### 5. Monitor Resource Usage

```bash
# Watch memory usage during generation
./medforge generate --count 5000 --parallel-workers 8 &
PID=$!
while kill -0 $PID 2>/dev/null; do
  ps -p $PID -o %cpu,%mem,cmd
  sleep 5
done
```

## Environment-Specific Examples

### Local Development

```bash
./medforge generate \
  --count 50 \
  --formats docx \
  --output data/dev \
  --llm-percentage 0.0 \
  --seed 1
```

### Staging

```bash
./medforge generate \
  --count 500 \
  --formats pdf,docx,eml \
  --output data/staging \
  --llm-percentage 0.1 \
  --seed 42
```

### Production

```bash
./medforge generate \
  --config config/production.yaml \
  --parallel-workers 8
```

## Next Steps

After generating data, you can:

1. **Use for PHI detection testing**: Test your detection algorithms
2. **Train ML models**: Use as training data for classification models
3. **System testing**: Load test document processing systems
4. **Demo purposes**: Showcase PHI handling capabilities

For more information, see [CLI_README.md](CLI_README.md)
