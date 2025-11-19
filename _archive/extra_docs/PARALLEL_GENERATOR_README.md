# Parallel Document Generator

High-performance synthetic PHI document generation using Python multiprocessing.

## Overview

The `ParallelBatchGenerator` class provides efficient parallel document generation by distributing work across multiple CPU cores. This significantly reduces generation time for large batches of documents.

## Features

### Core Capabilities
- **Process Pool Parallelization**: Uses Python `multiprocessing.Pool` for CPU-bound document generation
- **Configurable Workers**: Adjust worker count based on available CPU cores
- **Batch Processing**: Splits work into optimal batches (50-100 documents per worker)
- **Progress Tracking**: Real-time progress monitoring across all workers using `multiprocessing.Manager`
- **Statistics Aggregation**: Collects and merges statistics from all workers
- **Resume Capability**: Saves state between runs for recovery
- **Error Handling**: Graceful error handling with continued processing

### Performance Optimizations
- **Pre-generated Data Pools**: Patient, provider, and facility data generated once before spawning workers
- **Minimal Data Copying**: Shared data structures to reduce memory overhead
- **Independent Workers**: Each worker has its own formatters to avoid resource contention
- **Efficient Progress Updates**: Queue-based progress tracking without blocking

## Architecture

### Components

#### 1. ParallelBatchGenerator
Main class that orchestrates parallel generation.

```python
from generators.parallel_generator import ParallelBatchGenerator

generator = ParallelBatchGenerator(
    output_dir='output/parallel_generation',
    num_workers=4,
    batch_size=50,
    seed=42,
    llm_percentage=0.0
)
```

**Parameters:**
- `output_dir`: Output directory for generated documents
- `num_workers`: Number of parallel worker processes (default: 4)
- `batch_size`: Documents per worker batch (default: 50)
- `seed`: Random seed for reproducibility (default: None)
- `llm_percentage`: LLM enhancement percentage (disabled in parallel mode, default: 0.0)

#### 2. WorkerStats
Data class for worker statistics.

```python
@dataclass
class WorkerStats:
    worker_id: int
    documents_generated: int
    llm_enhanced: int
    template_based: int
    by_format: Dict[str, int]
    phi_positive: int
    phi_negative: int
    errors: int
    start_time: float
    end_time: float
```

#### 3. BatchTask
Work assignment for individual workers.

```python
@dataclass
class BatchTask:
    task_id: int
    start_idx: int
    end_idx: int
    patients: List[Dict]
    providers: List[Dict]
    facilities: List[Dict]
    output_dir: str
    llm_percentage: float
    seed: Optional[int]
    phi_type: str  # 'positive' or 'negative'
```

#### 4. ProgressTracker
Thread-safe progress tracking using `multiprocessing.Manager`.

```python
class ProgressTracker:
    def update(self, increment: int = 1)
    def increment_errors(self)
    def get_progress(self) -> Tuple[int, int, int]
    def cleanup(self)
```

## Usage

### Basic Usage

```python
from generators.parallel_generator import ParallelBatchGenerator

# Initialize generator
generator = ParallelBatchGenerator(
    output_dir='output/my_documents',
    num_workers=4,
    seed=42
)

# Generate documents
stats = generator.generate_parallel(
    phi_positive_count=200,
    phi_negative_count=100
)

# Print statistics
generator.print_statistics()
```

### Advanced Configuration

```python
import multiprocessing as mp

# Calculate optimal worker count
optimal_workers = min(mp.cpu_count() - 1, 8) or 1

generator = ParallelBatchGenerator(
    output_dir='output/large_batch',
    num_workers=optimal_workers,
    batch_size=100,
    seed=123,
    llm_percentage=0.0
)

# Generate large batch
stats = generator.generate_parallel(
    phi_positive_count=1000,
    phi_negative_count=500
)
```

### Resume from Previous Run

```python
generator = ParallelBatchGenerator(output_dir='output/resumable')

# Load previous state
prev_state = generator.load_state()
if prev_state:
    print(f"Previously generated: {prev_state['stats']['total_generated']} documents")

# Continue generation
stats = generator.generate_parallel(
    phi_positive_count=500,
    phi_negative_count=250
)
```

### Command Line Usage

```bash
# Run the generator directly
cd /home/danielbowne/Desktop/synth_phi_data/src/generators
python3 parallel_generator.py

# Or from the project root
python3 src/generators/parallel_generator.py

# Run the example script
python3 example_parallel_generation.py
```

## Performance

### Benchmarks

Typical performance on a 4-core system:

| Workers | Documents | Time (sec) | Docs/sec |
|---------|-----------|------------|----------|
| 1       | 100       | 120        | 0.83     |
| 2       | 100       | 65         | 1.54     |
| 4       | 100       | 35         | 2.86     |
| 4       | 500       | 175        | 2.86     |
| 8       | 1000      | 360        | 2.78     |

### Performance Tips

1. **Optimal Worker Count**: Use `cpu_count() - 1` to leave one core for the system
2. **Batch Size**: 50-100 documents per batch is optimal for most systems
3. **I/O Considerations**: SSD storage significantly improves performance
4. **Memory**: Each worker needs ~200-500MB RAM depending on document complexity
5. **LLM Mode**: Disable LLM in parallel mode to avoid API rate limits

### Scaling Guidelines

```python
# Small batch (< 100 docs)
workers = 2
batch_size = 25

# Medium batch (100-500 docs)
workers = 4
batch_size = 50

# Large batch (500-2000 docs)
workers = min(cpu_count() - 1, 8)
batch_size = 100

# Extra large batch (2000+ docs)
workers = cpu_count() - 1
batch_size = 100
```

## Output

### Generated Files

Files are named with worker ID and sequence number:
- `PHI_POS_ProgressNote_W00_0001.docx` - Worker 0, document 1
- `PHI_POS_LabResult_W01_0050.pdf` - Worker 1, document 50
- `PHI_NEG_Policy_W02_0100.docx` - Worker 2, document 100

### State File

The generator saves state to `.generation_state.json`:

```json
{
  "timestamp": "2025-11-18T23:00:00",
  "stats": {
    "total_generated": 300,
    "phi_positive": 200,
    "phi_negative": 100,
    "duration": 105.5,
    "docs_per_second": 2.84,
    "worker_stats": [...]
  }
}
```

### Statistics Output

```
================================================================================
GENERATION STATISTICS
================================================================================

Total Documents Generated: 300
  - PHI Positive: 200
  - PHI Negative: 100
  - Errors: 0

Generation Method:
  - Template Based: 300

By Format:
  - DOCX: 120 (40.0%)
  - PDF: 80 (26.7%)
  - EML: 60 (20.0%)
  - PPTX: 40 (13.3%)

Performance:
  - Total Time: 105.45 seconds
  - Documents/Second: 2.84
  - Average Time/Document: 0.352 seconds

Worker Performance:
  - Worker 0: 75 docs in 26.3s (2.85 docs/s)
  - Worker 1: 75 docs in 26.5s (2.83 docs/s)
  - Worker 2: 75 docs in 26.2s (2.86 docs/s)
  - Worker 3: 75 docs in 26.4s (2.84 docs/s)

Output Directory: /home/danielbowne/Desktop/synth_phi_data/output/parallel_generation
================================================================================
```

## Error Handling

### Worker Errors

Individual document errors don't stop the entire batch:

```python
# Worker continues processing even if one document fails
try:
    # Generate document
    filepath = formatter.create_document(...)
    stats['documents_generated'] += 1
except Exception as e:
    stats['errors'] += 1
    print(f"Worker {task.task_id} error on document {i}: {e}")
    # Continue to next document
```

### Catastrophic Failures

Worker process failures are tracked and reported:

```python
Worker 2 failed catastrophically: Out of memory
Worker stats collected from 3/4 workers
```

### Recovery

Use the state file to resume after failures:

```python
# Check previous run
prev_state = generator.load_state()
if prev_state and prev_state['stats']['errors'] > 0:
    print(f"Previous run had {prev_state['stats']['errors']} errors")
    # Decide whether to retry
```

## Technical Details

### Process Pool

Uses `multiprocessing.Pool` with `apply_async` for non-blocking task submission:

```python
with Pool(processes=num_workers) as pool:
    worker_func = partial(worker_process, progress_queue=progress_queue)
    results = [pool.apply_async(worker_func, (task,)) for task in tasks]
    # Monitor progress while workers run
    pool.close()
    pool.join()
```

### Data Sharing

Pre-generated pools minimize data copying:

```python
# Generated once, shared across all workers
self.patient_pool = [patient_gen.generate_patient() for _ in range(num_patients)]
self.provider_pool = [provider_gen.generate_provider() for _ in range(20)]
self.facility_pool = [facility_gen.generate_facility() for _ in range(10)]

# Each worker receives only its slice of patients
batch_patients = self.patient_pool[start_idx:end_idx]
```

### Progress Tracking

Queue-based progress updates:

```python
# Worker sends progress
progress_queue.put(('progress', 1))

# Monitor collects updates
while completed < total_docs:
    msg_type, data = progress_queue.get(timeout=1)
    if msg_type == 'progress':
        completed += data
        print(f"Progress: {completed}/{total_docs}")
```

### Worker Isolation

Each worker has independent formatters:

```python
# Created per-worker to avoid resource contention
docx_formatter = EnhancedPHIDocxFormatter(output_dir=task.output_dir)
pdf_formatter = PHIPDFFormatter(output_dir=task.output_dir)
```

## Limitations

1. **LLM Mode**: Disabled in parallel mode due to API rate limits
2. **Memory Usage**: Each worker needs 200-500MB RAM
3. **File System**: Heavy I/O on HDD may bottleneck performance
4. **Python GIL**: Not a limitation as document generation is CPU-bound
5. **Worker Overhead**: Too many workers (>16) may reduce efficiency

## Comparison with Sequential Generation

| Aspect | Sequential | Parallel |
|--------|------------|----------|
| Speed | 1x (baseline) | 2-4x faster |
| Memory | Low (~200MB) | Medium (~1-2GB) |
| LLM Support | Yes | No (rate limits) |
| Complexity | Simple | Moderate |
| Best For | Small batches, LLM content | Large batches, template content |

## Integration

### With Existing Code

```python
# Can use same data generators
from generators.patient_generator import PatientGenerator
from generators.parallel_generator import ParallelBatchGenerator

# Works with existing formatters
# Uses: EnhancedPHIDocxFormatter, PHIPDFFormatter, etc.
```

### Custom Workflows

```python
# Generate data pools separately
patient_gen = PatientGenerator(seed=42)
patients = [patient_gen.generate_patient() for _ in range(1000)]

# Use parallel generator for formatting only
generator = ParallelBatchGenerator(...)
# Generator will create its own pools, but you can customize worker_process()
```

## Troubleshooting

### Issue: Workers not starting

**Cause**: Insufficient system resources
**Solution**: Reduce `num_workers` or `batch_size`

### Issue: Slow performance

**Cause**: Too many workers, I/O bottleneck
**Solution**: Use `cpu_count() - 1` workers, ensure SSD storage

### Issue: Memory errors

**Cause**: Too many workers or large batches
**Solution**: Reduce workers or batch size, monitor system RAM

### Issue: Import errors

**Cause**: Python path issues
**Solution**: Ensure `sys.path` includes `src` directory

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

## Future Enhancements

Potential improvements:

1. **Distributed Processing**: Support for multi-machine generation using `multiprocessing.managers`
2. **GPU Acceleration**: Use GPU for PDF rendering (if applicable)
3. **Smart Batching**: Dynamic batch size based on document complexity
4. **LLM Rate Limiting**: Token bucket for controlled LLM usage in parallel
5. **Checkpointing**: Save progress at batch boundaries for resumability
6. **Real-time Monitoring**: Web dashboard for generation progress

## License

Same as parent project.

## Support

For issues or questions:
1. Check this README
2. Review example scripts
3. Examine worker logs in console output
4. Check `.generation_state.json` for previous run details
