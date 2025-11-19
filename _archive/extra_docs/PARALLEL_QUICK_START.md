# Parallel Generator - Quick Start Guide

## 30-Second Start

```python
from generators.parallel_generator import ParallelBatchGenerator

generator = ParallelBatchGenerator(num_workers=4, seed=42)
stats = generator.generate_parallel(phi_positive_count=100, phi_negative_count=50)
generator.print_statistics()
```

## Common Use Cases

### 1. Generate 1000 Documents Fast

```python
from generators.parallel_generator import ParallelBatchGenerator
import multiprocessing as mp

# Use all cores minus one
workers = mp.cpu_count() - 1

generator = ParallelBatchGenerator(
    output_dir='output/large_batch',
    num_workers=workers,
    batch_size=100,
    seed=42
)

stats = generator.generate_parallel(
    phi_positive_count=700,
    phi_negative_count=300
)

generator.print_statistics()
```

**Expected Performance**: ~2-3 documents/second on 4-core system = ~6-7 minutes for 1000 docs

### 2. Small Test Batch

```python
generator = ParallelBatchGenerator(
    output_dir='output/test',
    num_workers=2,
    seed=42
)

stats = generator.generate_parallel(
    phi_positive_count=20,
    phi_negative_count=10
)
```

**Expected Performance**: ~30 seconds

### 3. Production Batch with Resume

```python
generator = ParallelBatchGenerator(
    output_dir='output/production',
    num_workers=8,
    batch_size=100,
    seed=12345
)

# Check previous run
prev_state = generator.load_state()
if prev_state:
    print(f"Resuming from: {prev_state['stats']['total_generated']} docs")

# Generate
stats = generator.generate_parallel(
    phi_positive_count=5000,
    phi_negative_count=2500
)
```

**Expected Performance**: ~45-60 minutes on 8-core system

## Command Line

```bash
# Run default configuration (200 PHI+, 100 PHI-)
python3 src/generators/parallel_generator.py

# Run example/demo
python3 example_parallel_generation.py
```

## Key Parameters

| Parameter | Default | Recommended | Purpose |
|-----------|---------|-------------|---------|
| `num_workers` | 4 | `cpu_count() - 1` | Parallel processes |
| `batch_size` | 50 | 50-100 | Docs per worker |
| `seed` | None | Any int | Reproducibility |
| `output_dir` | `output/parallel_generation` | Custom | Where to save |
| `llm_percentage` | 0.0 | 0.0 | LLM disabled in parallel |

## Performance Expectations

### Documents per Second (by worker count)

- **1 worker**: 0.8-1.0 docs/sec
- **2 workers**: 1.5-1.8 docs/sec
- **4 workers**: 2.5-3.0 docs/sec
- **8 workers**: 2.7-3.2 docs/sec (diminishing returns)

### Generation Time Estimates

| Documents | Workers | Time |
|-----------|---------|------|
| 100 | 2 | 1-2 min |
| 100 | 4 | 35-45 sec |
| 500 | 4 | 3-4 min |
| 1000 | 4 | 6-7 min |
| 1000 | 8 | 5-6 min |
| 5000 | 8 | 25-30 min |

## Output Files

Files named with worker ID:
```
output/parallel_generation/
├── PHI_POS_ProgressNote_W00_0001.docx
├── PHI_POS_LabResult_W01_0050.pdf
├── PHI_NEG_Policy_W02_0100.docx
└── .generation_state.json
```

## Statistics Output

```
Total Documents Generated: 300
  - PHI Positive: 200
  - PHI Negative: 100
  - Errors: 0

Performance:
  - Total Time: 105.45 seconds
  - Documents/Second: 2.84
  - Average Time/Document: 0.352 seconds

Worker Performance:
  - Worker 0: 75 docs in 26.3s (2.85 docs/s)
  - Worker 1: 75 docs in 26.5s (2.83 docs/s)
  - Worker 2: 75 docs in 26.2s (2.86 docs/s)
  - Worker 3: 75 docs in 26.4s (2.84 docs/s)
```

## Common Patterns

### Pattern 1: Balanced Mix (70% PHI+, 30% PHI-)

```python
total = 1000
generator.generate_parallel(
    phi_positive_count=int(total * 0.7),
    phi_negative_count=int(total * 0.3)
)
```

### Pattern 2: PHI-Heavy (90% PHI+)

```python
total = 1000
generator.generate_parallel(
    phi_positive_count=900,
    phi_negative_count=100
)
```

### Pattern 3: Testing Dataset (Small, Diverse)

```python
generator.generate_parallel(
    phi_positive_count=50,
    phi_negative_count=50
)
```

## Troubleshooting

### Too Slow?
- Increase `num_workers` to `cpu_count() - 1`
- Ensure using SSD, not HDD
- Check system resources (RAM, CPU)

### Out of Memory?
- Reduce `num_workers` (try 2 or 4)
- Reduce `batch_size` to 25
- Close other applications

### Import Errors?
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

## Resource Requirements

### Memory (RAM)
- 2 workers: ~500MB
- 4 workers: ~1GB
- 8 workers: ~2GB

### Storage
- 100 docs: ~10-20MB
- 1000 docs: ~100-200MB
- 10000 docs: ~1-2GB

### CPU
- Recommended: 4+ cores
- Minimum: 2 cores
- Optimal: 8 cores

## Next Steps

1. **Start Small**: Run with 20-50 documents to test
2. **Scale Up**: Increase to 500-1000 documents
3. **Production**: Generate large batches (5000+)
4. **Monitor**: Check statistics and worker performance
5. **Optimize**: Adjust workers/batch size based on results

## More Information

See `PARALLEL_GENERATOR_README.md` for:
- Detailed architecture
- Advanced configurations
- Performance tuning
- Error handling
- Integration examples
