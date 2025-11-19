#!/usr/bin/env python3
"""
Example script demonstrating parallel document generation

This shows how to use the ParallelBatchGenerator for high-performance
document generation using multiprocessing.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from generators.parallel_generator import ParallelBatchGenerator
import multiprocessing as mp


def main():
    print("=" * 80)
    print("PARALLEL DOCUMENT GENERATION EXAMPLE")
    print("=" * 80)
    print()

    # Show system information
    print(f"System Configuration:")
    print(f"  - Available CPU Cores: {mp.cpu_count()}")
    print(f"  - Recommended Workers: {mp.cpu_count() - 1 or 1}")
    print()

    # Example 1: Small batch with 2 workers
    print("Example 1: Small Batch Generation")
    print("-" * 80)

    generator_small = ParallelBatchGenerator(
        output_dir='output/example_small',
        num_workers=2,
        batch_size=25,
        seed=42
    )

    stats = generator_small.generate_parallel(
        phi_positive_count=50,
        phi_negative_count=25
    )

    generator_small.print_statistics()
    print()

    # Example 2: Large batch with maximum workers
    print("\nExample 2: Large Batch Generation (High Performance)")
    print("-" * 80)

    optimal_workers = min(mp.cpu_count() - 1, 8) or 1  # Leave 1 core free, max 8

    generator_large = ParallelBatchGenerator(
        output_dir='output/example_large',
        num_workers=optimal_workers,
        batch_size=100,
        seed=123
    )

    stats = generator_large.generate_parallel(
        phi_positive_count=500,
        phi_negative_count=250
    )

    generator_large.print_statistics()
    print()

    # Example 3: Custom configuration
    print("\nExample 3: Custom Configuration")
    print("-" * 80)

    generator_custom = ParallelBatchGenerator(
        output_dir='output/example_custom',
        num_workers=4,
        batch_size=50,
        seed=999,
        llm_percentage=0.0  # LLM disabled in parallel mode by default
    )

    stats = generator_custom.generate_parallel(
        phi_positive_count=100,
        phi_negative_count=50
    )

    generator_custom.print_statistics()

    # Show how to load previous state
    print("\n" + "=" * 80)
    print("LOADING PREVIOUS STATE")
    print("=" * 80)

    prev_state = generator_custom.load_state()
    if prev_state:
        print(f"\nSuccessfully loaded previous generation state:")
        print(f"  - Timestamp: {prev_state['timestamp']}")
        print(f"  - Documents Generated: {prev_state['stats']['total_generated']}")
        print(f"  - Duration: {prev_state['stats'].get('duration', 'N/A')} seconds")
    else:
        print("\nNo previous state found.")

    print("\n" + "=" * 80)
    print("✓ All examples completed successfully!")
    print("=" * 80)


if __name__ == '__main__':
    # Only run small example by default to avoid generating too many files
    print("=" * 80)
    print("QUICK PARALLEL GENERATION DEMO")
    print("=" * 80)
    print()

    # Quick demo with minimal documents
    demo_generator = ParallelBatchGenerator(
        output_dir='output/parallel_demo',
        num_workers=2,
        batch_size=10,
        seed=42
    )

    print("Generating small demo batch (20 PHI positive + 10 PHI negative)...")
    stats = demo_generator.generate_parallel(
        phi_positive_count=20,
        phi_negative_count=10
    )

    demo_generator.print_statistics()

    print("\n" + "=" * 80)
    print("Demo complete! To run full examples, modify this script.")
    print("=" * 80)
