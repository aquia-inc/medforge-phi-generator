"""
Parallel Document Generator using Python multiprocessing
Efficiently generates large batches of PHI documents using process pools
"""
import sys
import os
import random
import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import multiprocessing as mp
from multiprocessing import Pool, Manager, Queue
from functools import partial
import traceback

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.patient_generator import PatientGenerator, ProviderGenerator, FacilityGenerator
from formatters.docx_formatter_enhanced import EnhancedPHIDocxFormatter
from formatters.pdf_formatter import PHIPDFFormatter
from formatters.xlsx_formatter import XLSXFormatter
from formatters.pptx_formatter import PPTXFormatter
from formatters.email_formatter import EmailFormatter
from formatters.nested_formatter import NestedEmailFormatter


@dataclass
class WorkerStats:
    """Statistics from a single worker process"""
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

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self):
        return asdict(self)


@dataclass
class BatchTask:
    """A batch of work for a single worker"""
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


class ProgressTracker:
    """Thread-safe progress tracking using multiprocessing.Manager"""

    def __init__(self, total_docs: int):
        self.manager = Manager()
        self.progress = self.manager.dict()
        self.progress['completed'] = 0
        self.progress['total'] = total_docs
        self.progress['errors'] = 0
        self.lock = self.manager.Lock()

    def update(self, increment: int = 1):
        """Thread-safe progress update"""
        with self.lock:
            self.progress['completed'] += increment

    def increment_errors(self):
        """Thread-safe error counter"""
        with self.lock:
            self.progress['errors'] += 1

    def get_progress(self) -> Tuple[int, int, int]:
        """Get current progress (completed, total, errors)"""
        with self.lock:
            return (
                self.progress['completed'],
                self.progress['total'],
                self.progress['errors']
            )

    def cleanup(self):
        """Clean up manager resources"""
        self.manager.shutdown()


def worker_process(task: BatchTask, progress_queue: Queue) -> WorkerStats:
    """
    Worker function that generates a batch of documents

    Args:
        task: BatchTask containing work assignment
        progress_queue: Queue for progress updates

    Returns:
        WorkerStats with results from this worker
    """
    start_time = datetime.now().timestamp()

    # Initialize statistics
    stats = {
        'documents_generated': 0,
        'llm_enhanced': 0,
        'template_based': 0,
        'by_format': defaultdict(int),
        'phi_positive': 0,
        'phi_negative': 0,
        'errors': 0
    }

    try:
        # Create worker-specific random state
        if task.seed is not None:
            worker_seed = task.seed + task.task_id
            random.seed(worker_seed)

        # Initialize formatters (each worker gets its own)
        docx_formatter = EnhancedPHIDocxFormatter(
            output_dir=task.output_dir,
            llm_percentage=task.llm_percentage,
            use_llm=False  # Disable LLM in parallel mode to avoid rate limits
        )
        pdf_formatter = PHIPDFFormatter(output_dir=task.output_dir)
        xlsx_formatter = XLSXFormatter(output_dir=task.output_dir)
        pptx_formatter = PPTXFormatter(output_dir=task.output_dir)
        email_formatter = EmailFormatter(output_dir=task.output_dir)
        nested_formatter = NestedEmailFormatter(output_dir=task.output_dir)

        # Generate patient data generator for lab results
        patient_gen = PatientGenerator(seed=worker_seed if task.seed else None)

        # Process documents in this batch
        for i in range(task.start_idx, task.end_idx):
            try:
                if task.phi_type == 'positive':
                    # PHI Positive document
                    patient = task.patients[i - task.start_idx]
                    provider = random.choice(task.providers)
                    facility = random.choice(task.facilities)

                    # Choose document type
                    doc_type = random.choice(['progress_note', 'lab_result', 'email', 'case_study'])

                    if doc_type == 'progress_note':
                        filename = f"PHI_POS_ProgressNote_W{task.task_id:02d}_{i:04d}.docx"
                        filepath, used_llm = docx_formatter.create_progress_note_enhanced(
                            patient, provider, facility, filename
                        )
                        stats['by_format']['docx'] += 1
                        if used_llm:
                            stats['llm_enhanced'] += 1
                        else:
                            stats['template_based'] += 1

                    elif doc_type == 'lab_result':
                        lab_data = patient_gen.generate_lab_results()
                        if i % 2 == 0:
                            filename = f"PHI_POS_LabResult_W{task.task_id:02d}_{i:04d}.pdf"
                            filepath = pdf_formatter.create_lab_result(
                                patient, provider, facility, lab_data, filename
                            )
                            stats['by_format']['pdf'] += 1
                        else:
                            filename = f"PHI_POS_LabResult_W{task.task_id:02d}_{i:04d}.docx"
                            filepath = docx_formatter.create_lab_result(
                                patient, provider, facility, lab_data, filename
                            )
                            stats['by_format']['docx'] += 1
                        stats['template_based'] += 1

                    elif doc_type == 'email':
                        sender = random.choice(task.providers)
                        recipient = random.choice([p for p in task.providers if p != sender])
                        filename = f"PHI_POS_ProviderEmail_W{task.task_id:02d}_{i:04d}.eml"
                        filepath = email_formatter.create_provider_to_provider_email(
                            patient, sender, recipient, filename
                        )
                        stats['by_format']['eml'] += 1
                        stats['template_based'] += 1

                    elif doc_type == 'case_study':
                        filename = f"PHI_POS_CaseStudy_W{task.task_id:02d}_{i:04d}.pptx"
                        filepath = pptx_formatter.create_case_study_presentation(
                            patient, provider, facility, filename
                        )
                        stats['by_format']['pptx'] += 1
                        stats['template_based'] += 1

                    stats['phi_positive'] += 1

                else:
                    # PHI Negative document
                    facility = random.choice(task.facilities)

                    doc_type = random.choice(['policy', 'announcement', 'education', 'blank_form'])

                    if doc_type == 'policy':
                        if i % 2 == 0:
                            filename = f"PHI_NEG_Policy_W{task.task_id:02d}_{i:04d}.pdf"
                            filepath = pdf_formatter.create_generic_medical_policy(facility, filename)
                            stats['by_format']['pdf'] += 1
                        else:
                            from formatters.docx_formatter import PHIDocxFormatter
                            docx_fmt = PHIDocxFormatter(output_dir=task.output_dir)
                            filename = f"PHI_NEG_Policy_W{task.task_id:02d}_{i:04d}.docx"
                            filepath = docx_fmt.create_generic_medical_policy(facility, filename)
                            stats['by_format']['docx'] += 1

                    elif doc_type == 'announcement':
                        filename = f"PHI_NEG_Announcement_W{task.task_id:02d}_{i:04d}.eml"
                        filepath = email_formatter.create_office_announcement(facility, filename)
                        stats['by_format']['eml'] += 1

                    elif doc_type == 'education':
                        filename = f"PHI_NEG_Education_W{task.task_id:02d}_{i:04d}.pptx"
                        filepath = pptx_formatter.create_educational_presentation(facility, filename)
                        stats['by_format']['pptx'] += 1

                    elif doc_type == 'blank_form':
                        from formatters.docx_formatter import PHIDocxFormatter
                        docx_fmt = PHIDocxFormatter(output_dir=task.output_dir)
                        filename = f"PHI_NEG_BlankForm_W{task.task_id:02d}_{i:04d}.docx"
                        filepath = docx_fmt.create_blank_form_template(facility, filename)
                        stats['by_format']['docx'] += 1

                    stats['phi_negative'] += 1
                    stats['template_based'] += 1

                stats['documents_generated'] += 1

                # Send progress update
                progress_queue.put(('progress', 1))

            except Exception as e:
                stats['errors'] += 1
                progress_queue.put(('error', 1))
                print(f"Worker {task.task_id} error on document {i}: {e}")
                traceback.print_exc()

    except Exception as e:
        print(f"Worker {task.task_id} failed catastrophically: {e}")
        traceback.print_exc()

    end_time = datetime.now().timestamp()

    # Create WorkerStats object
    worker_stats = WorkerStats(
        worker_id=task.task_id,
        documents_generated=stats['documents_generated'],
        llm_enhanced=stats['llm_enhanced'],
        template_based=stats['template_based'],
        by_format=dict(stats['by_format']),
        phi_positive=stats['phi_positive'],
        phi_negative=stats['phi_negative'],
        errors=stats['errors'],
        start_time=start_time,
        end_time=end_time
    )

    progress_queue.put(('done', worker_stats))
    return worker_stats


class ParallelBatchGenerator:
    """
    Parallel document generator using process pools
    Efficiently generates large batches of PHI documents
    """

    def __init__(
        self,
        output_dir: str = 'output/parallel_generation',
        num_workers: int = 4,
        batch_size: int = 50,
        seed: Optional[int] = None,
        llm_percentage: float = 0.0  # Disabled in parallel mode
    ):
        """
        Initialize parallel batch generator

        Args:
            output_dir: Output directory for generated documents
            num_workers: Number of parallel worker processes
            batch_size: Documents per worker batch
            seed: Random seed for reproducibility
            llm_percentage: Percentage of LLM enhancement (disabled in parallel mode)
        """
        self.output_dir = output_dir
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.seed = seed
        self.llm_percentage = llm_percentage

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # State file for resume capability
        self.state_file = os.path.join(output_dir, '.generation_state.json')

        # Statistics
        self.stats = {
            'total_generated': 0,
            'llm_enhanced': 0,
            'template_based': 0,
            'by_format': defaultdict(int),
            'phi_positive': 0,
            'phi_negative': 0,
            'errors': 0,
            'worker_stats': []
        }

        # Pre-generated data pools
        self.patient_pool = []
        self.provider_pool = []
        self.facility_pool = []

    def _prepare_data_pools(self, num_patients: int, num_providers: int = 20, num_facilities: int = 10):
        """
        Pre-generate patient/provider/facility pools before spawning workers
        This minimizes data copying between processes

        Args:
            num_patients: Number of patients to pre-generate
            num_providers: Number of providers to pre-generate
            num_facilities: Number of facilities to pre-generate
        """
        print("\nPreparing data pools...")
        print(f"  - Generating {num_patients} patients...")

        patient_gen = PatientGenerator(seed=self.seed)
        self.patient_pool = [patient_gen.generate_patient() for _ in range(num_patients)]

        print(f"  - Generating {num_providers} providers...")
        provider_gen = ProviderGenerator(seed=self.seed)
        self.provider_pool = [provider_gen.generate_provider() for _ in range(num_providers)]

        print(f"  - Generating {num_facilities} facilities...")
        facility_gen = FacilityGenerator(seed=self.seed)
        self.facility_pool = [facility_gen.generate_facility() for _ in range(num_facilities)]

        print("  ✓ Data pools prepared")

    def _create_tasks(
        self,
        total_docs: int,
        phi_type: str = 'positive'
    ) -> List[BatchTask]:
        """
        Split work into batches for parallel processing

        Args:
            total_docs: Total number of documents to generate
            phi_type: 'positive' or 'negative'

        Returns:
            List of BatchTask objects
        """
        tasks = []
        docs_per_worker = max(1, total_docs // self.num_workers)

        for i in range(self.num_workers):
            start_idx = i * docs_per_worker
            end_idx = min((i + 1) * docs_per_worker, total_docs)

            # Handle remainder in last worker
            if i == self.num_workers - 1:
                end_idx = total_docs

            if start_idx >= end_idx:
                break

            # Select patients for this batch (if PHI positive)
            batch_patients = []
            if phi_type == 'positive':
                batch_patients = self.patient_pool[start_idx:end_idx]

            task = BatchTask(
                task_id=i,
                start_idx=start_idx,
                end_idx=end_idx,
                patients=batch_patients,
                providers=self.provider_pool,
                facilities=self.facility_pool,
                output_dir=self.output_dir,
                llm_percentage=self.llm_percentage,
                seed=self.seed,
                phi_type=phi_type
            )
            tasks.append(task)

        return tasks

    def _progress_monitor(self, progress_queue: Queue, total_docs: int):
        """
        Monitor progress from all workers

        Args:
            progress_queue: Queue for receiving progress updates
            total_docs: Total documents to generate
        """
        completed = 0
        errors = 0
        worker_stats = []

        while completed < total_docs:
            try:
                msg_type, data = progress_queue.get(timeout=1)

                if msg_type == 'progress':
                    completed += data
                    if completed % 10 == 0 or completed == total_docs:
                        print(f"  Progress: {completed}/{total_docs} documents ({completed*100//total_docs}%)", end='\r')

                elif msg_type == 'error':
                    errors += data

                elif msg_type == 'done':
                    worker_stats.append(data)

            except:
                continue

        print()  # New line after progress
        return worker_stats, errors

    def generate_parallel(
        self,
        phi_positive_count: int = 100,
        phi_negative_count: int = 50
    ) -> Dict[str, Any]:
        """
        Generate documents in parallel using process pool

        Args:
            phi_positive_count: Number of PHI positive documents
            phi_negative_count: Number of PHI negative documents

        Returns:
            Dictionary with generation statistics
        """
        total_docs = phi_positive_count + phi_negative_count

        print("=" * 80)
        print("PARALLEL DOCUMENT GENERATION")
        print("=" * 80)
        print("\nConfiguration:")
        print(f"  - Total Documents: {total_docs}")
        print(f"  - PHI Positive: {phi_positive_count}")
        print(f"  - PHI Negative: {phi_negative_count}")
        print(f"  - Worker Processes: {self.num_workers}")
        print(f"  - Batch Size: {self.batch_size}")
        print(f"  - Random Seed: {self.seed}")
        print(f"  - Output Directory: {self.output_dir}")
        print()

        start_time = datetime.now()

        # Prepare data pools
        self._prepare_data_pools(
            num_patients=phi_positive_count,
            num_providers=20,
            num_facilities=10
        )

        # Create progress queue
        manager = Manager()
        progress_queue = manager.Queue()

        all_worker_stats = []

        # Generate PHI Positive documents
        if phi_positive_count > 0:
            print(f"\nGenerating {phi_positive_count} PHI POSITIVE documents...")
            print("-" * 80)

            tasks = self._create_tasks(phi_positive_count, phi_type='positive')

            # Start process pool
            with Pool(processes=self.num_workers) as pool:
                # Create worker function with progress queue
                worker_func = partial(worker_process, progress_queue=progress_queue)

                # Start async tasks
                results = [pool.apply_async(worker_func, (task,)) for task in tasks]

                # Monitor progress
                worker_stats, errors = self._progress_monitor(progress_queue, phi_positive_count)

                # Wait for all workers to complete
                pool.close()
                pool.join()

            all_worker_stats.extend(worker_stats)
            print(f"  ✓ Completed: {phi_positive_count} PHI positive documents")

        # Generate PHI Negative documents
        if phi_negative_count > 0:
            print(f"\nGenerating {phi_negative_count} PHI NEGATIVE documents...")
            print("-" * 80)

            tasks = self._create_tasks(phi_negative_count, phi_type='negative')

            with Pool(processes=self.num_workers) as pool:
                worker_func = partial(worker_process, progress_queue=progress_queue)
                results = [pool.apply_async(worker_func, (task,)) for task in tasks]
                worker_stats, errors = self._progress_monitor(progress_queue, phi_negative_count)
                pool.close()
                pool.join()

            all_worker_stats.extend(worker_stats)
            print(f"  ✓ Completed: {phi_negative_count} PHI negative documents")

        # Cleanup manager
        manager.shutdown()

        end_time = datetime.now()

        # Aggregate statistics from all workers
        self._aggregate_statistics(all_worker_stats)

        # Add timing information
        duration = (end_time - start_time).total_seconds()
        self.stats['duration'] = duration
        self.stats['docs_per_second'] = total_docs / duration if duration > 0 else 0

        # Save state
        self._save_state()

        return self.stats

    def _aggregate_statistics(self, worker_stats: List[WorkerStats]):
        """
        Aggregate statistics from all workers

        Args:
            worker_stats: List of WorkerStats from each worker
        """
        for ws in worker_stats:
            self.stats['total_generated'] += ws.documents_generated
            self.stats['llm_enhanced'] += ws.llm_enhanced
            self.stats['template_based'] += ws.template_based
            self.stats['phi_positive'] += ws.phi_positive
            self.stats['phi_negative'] += ws.phi_negative
            self.stats['errors'] += ws.errors

            for fmt, count in ws.by_format.items():
                self.stats['by_format'][fmt] += count

            self.stats['worker_stats'].append(ws.to_dict())

    def _save_state(self):
        """Save generation state for resume capability"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'stats': {
                **self.stats,
                'by_format': dict(self.stats['by_format'])
            }
        }

        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")

    def load_state(self) -> Optional[Dict]:
        """
        Load previous generation state

        Returns:
            Previous state dict or None if not found
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load state: {e}")
        return None

    def print_statistics(self):
        """Print detailed generation statistics"""
        print("\n" + "=" * 80)
        print("GENERATION STATISTICS")
        print("=" * 80)
        print(f"\nTotal Documents Generated: {self.stats['total_generated']}")
        print(f"  - PHI Positive: {self.stats['phi_positive']}")
        print(f"  - PHI Negative: {self.stats['phi_negative']}")
        print(f"  - Errors: {self.stats['errors']}")
        print()

        print("Generation Method:")
        if self.stats['llm_enhanced'] > 0:
            llm_pct = (self.stats['llm_enhanced'] / self.stats['total_generated']) * 100
            print(f"  - LLM Enhanced: {self.stats['llm_enhanced']} ({llm_pct:.1f}%)")
        print(f"  - Template Based: {self.stats['template_based']}")
        print()

        print("By Format:")
        for fmt, count in sorted(self.stats['by_format'].items()):
            pct = (count / self.stats['total_generated']) * 100 if self.stats['total_generated'] > 0 else 0
            print(f"  - {fmt.upper()}: {count} ({pct:.1f}%)")
        print()

        if 'duration' in self.stats:
            print("Performance:")
            print(f"  - Total Time: {self.stats['duration']:.2f} seconds")
            print(f"  - Documents/Second: {self.stats['docs_per_second']:.2f}")
            print(f"  - Average Time/Document: {self.stats['duration']/self.stats['total_generated']:.3f} seconds")
            print()

        # Worker breakdown
        if self.stats['worker_stats']:
            print("Worker Performance:")
            for ws_dict in self.stats['worker_stats']:
                ws = WorkerStats(**ws_dict)
                print(f"  - Worker {ws.worker_id}: {ws.documents_generated} docs in {ws.duration:.2f}s ({ws.documents_generated/ws.duration:.2f} docs/s)")
            print()

        print(f"Output Directory: {os.path.abspath(self.output_dir)}")
        print("=" * 80)


def main():
    """Main entry point for parallel generation"""
    print("=" * 80)
    print("SYNTHETIC PHI PARALLEL BATCH GENERATOR")
    print("=" * 80)
    print()

    # Configuration
    PHI_POSITIVE_COUNT = 200
    PHI_NEGATIVE_COUNT = 100
    NUM_WORKERS = 4
    BATCH_SIZE = 50
    SEED = 42

    print("System Information:")
    print(f"  - CPU Cores: {mp.cpu_count()}")
    print(f"  - Workers: {NUM_WORKERS}")
    print()

    # Initialize generator
    generator = ParallelBatchGenerator(
        output_dir='output/parallel_generation',
        num_workers=NUM_WORKERS,
        batch_size=BATCH_SIZE,
        seed=SEED,
        llm_percentage=0.0  # Disabled in parallel mode
    )

    # Check for previous state
    prev_state = generator.load_state()
    if prev_state:
        print(f"Found previous generation from {prev_state['timestamp']}")
        print(f"  - Previously generated: {prev_state['stats']['total_generated']} documents")
        print()

    # Generate documents
    stats = generator.generate_parallel(
        phi_positive_count=PHI_POSITIVE_COUNT,
        phi_negative_count=PHI_NEGATIVE_COUNT
    )

    # Print statistics
    generator.print_statistics()
    print()
    print("✓ Parallel batch generation complete!")


if __name__ == '__main__':
    main()
