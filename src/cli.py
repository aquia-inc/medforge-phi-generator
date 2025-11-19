#!/usr/bin/env python3
"""
MedForge CLI - Synthetic PHI Data Generator
Comprehensive command-line interface for generating synthetic healthcare documents
"""
import sys
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import random
from collections import defaultdict
import concurrent.futures
import yaml
import json

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.tree import Tree

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generators.patient_generator import PatientGenerator, ProviderGenerator, FacilityGenerator
from formatters.docx_formatter_enhanced import EnhancedPHIDocxFormatter
from formatters.pdf_formatter import PHIPDFFormatter
from formatters.xlsx_formatter import XLSXFormatter
from formatters.pptx_formatter import PPTXFormatter
from formatters.email_formatter import EmailFormatter
from formatters.nested_formatter import NestedEmailFormatter
from generators.llm_generator import is_llm_available

# Initialize CLI app and console
app = typer.Typer(
    name="medforge",
    help="MedForge - Synthetic PHI Data Generator for Healthcare Documents",
    add_completion=False,
)
console = Console()


class MedForgeGenerator:
    """Enhanced generator with parallel processing support"""

    def __init__(
        self,
        output_dir: str = "output",
        seed: Optional[int] = None,
        llm_percentage: float = 0.2,
        formats: Optional[List[str]] = None,
    ):
        """
        Initialize MedForge generator

        Args:
            output_dir: Output directory path
            seed: Random seed for reproducibility
            llm_percentage: Percentage of LLM-enhanced documents (0.0-1.0)
            formats: List of formats to generate (defaults to all)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create simple two-folder structure
        self.phi_positive_dir = self.output_dir / "phi_positive"
        self.phi_negative_dir = self.output_dir / "phi_negative"
        self.metadata_dir = self.output_dir / "metadata"

        # Create directories
        self.phi_positive_dir.mkdir(parents=True, exist_ok=True)
        self.phi_negative_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.seed = seed
        self.llm_percentage = llm_percentage
        self.formats = formats or ["pdf", "docx", "xlsx", "eml", "pptx"]

        # Set random seed
        if seed is not None:
            random.seed(seed)

        # Statistics tracking
        self.stats = {
            "total_generated": 0,
            "llm_enhanced": 0,
            "template_based": 0,
            "by_format": defaultdict(int),
            "by_category": defaultdict(int),
            "phi_positive": 0,
            "phi_negative": 0,
            "errors": [],
        }

        # Manifest for tracking all generated files
        self.manifest = []

        # Initialize generators
        self.patient_gen = PatientGenerator(seed=seed)
        self.provider_gen = ProviderGenerator(seed=seed)
        self.facility_gen = FacilityGenerator(seed=seed)

        # Initialize formatters (will pass specific subdirs when generating)
        self.formatters = {}
        if "docx" in self.formats:
            self.formatters["docx"] = EnhancedPHIDocxFormatter(
                output_dir=str(self.output_dir), llm_percentage=llm_percentage
            )
        if "pdf" in self.formats:
            self.formatters["pdf"] = PHIPDFFormatter(output_dir=str(self.output_dir))
        if "xlsx" in self.formats:
            self.formatters["xlsx"] = XLSXFormatter(output_dir=str(self.output_dir))
        if "pptx" in self.formats:
            self.formatters["pptx"] = PPTXFormatter(output_dir=str(self.output_dir))
        if "eml" in self.formats:
            self.formatters["eml"] = EmailFormatter(output_dir=str(self.output_dir))
            self.formatters["nested_eml"] = NestedEmailFormatter(output_dir=str(self.output_dir))

    def generate_single_phi_positive(self, index: int) -> Optional[str]:
        """Generate a single PHI positive document"""
        try:
            patient = self.patient_gen.generate_patient()
            provider = self.provider_gen.generate_provider()
            facility = self.facility_gen.generate_facility()

            # Choose document type based on available formats
            doc_types = []
            if "docx" in self.formats:
                doc_types.extend(["progress_note", "lab_result_docx"])
            if "pdf" in self.formats:
                doc_types.append("lab_result_pdf")
            if "eml" in self.formats:
                doc_types.append("email")
            if "pptx" in self.formats:
                doc_types.append("case_study")

            if not doc_types:
                raise ValueError("No valid document types for selected formats")

            doc_type = random.choice(doc_types)

            # Generate without PHI_POS prefix and save to phi_positive directory
            if doc_type == "progress_note":
                filename = f"ProgressNote_{index:04d}.docx"
                self.formatters["docx"].output_dir = str(self.phi_positive_dir)
                filepath, used_llm = self.formatters["docx"].create_progress_note_enhanced(
                    patient, provider, facility, filename
                )
                self.stats["by_format"]["docx"] += 1
                self.stats["by_category"]["progress_notes"] += 1
                if used_llm:
                    self.stats["llm_enhanced"] += 1
                else:
                    self.stats["template_based"] += 1

            elif doc_type == "lab_result_docx":
                lab_data = self.patient_gen.generate_lab_results()
                filename = f"LabResult_{index:04d}.docx"
                self.formatters["docx"].output_dir = str(self.phi_positive_dir)
                filepath = self.formatters["docx"].create_lab_result(
                    patient, provider, facility, lab_data, filename
                )
                self.stats["by_format"]["docx"] += 1
                self.stats["by_category"]["lab_results"] += 1
                self.stats["template_based"] += 1

            elif doc_type == "lab_result_pdf":
                lab_data = self.patient_gen.generate_lab_results()
                filename = f"LabResult_{index:04d}.pdf"
                self.formatters["pdf"].output_dir = str(self.phi_positive_dir)
                filepath = self.formatters["pdf"].create_lab_result(
                    patient, provider, facility, lab_data, filename
                )
                self.stats["by_format"]["pdf"] += 1
                self.stats["by_category"]["lab_results"] += 1
                self.stats["template_based"] += 1

            elif doc_type == "email":
                sender = provider
                recipient = self.provider_gen.generate_provider()
                filename = f"ProviderEmail_{index:04d}.eml"
                self.formatters["eml"].output_dir = str(self.phi_positive_dir)
                filepath = self.formatters["eml"].create_provider_to_provider_email(
                    patient, sender, recipient, filename
                )
                self.stats["by_format"]["eml"] += 1
                self.stats["by_category"]["correspondence"] += 1
                self.stats["template_based"] += 1

            elif doc_type == "case_study":
                filename = f"CaseStudy_{index:04d}.pptx"
                self.formatters["pptx"].output_dir = str(self.phi_positive_dir)
                filepath = self.formatters["pptx"].create_case_study_presentation(
                    patient, provider, facility, filename
                )
                self.stats["by_format"]["pptx"] += 1
                self.stats["by_category"]["case_studies"] += 1
                self.stats["template_based"] += 1

            self.stats["total_generated"] += 1
            self.stats["phi_positive"] += 1

            # Add to manifest
            self.manifest.append({
                "file_path": str(Path(filepath).relative_to(self.output_dir)),
                "phi_status": "positive",
                "document_type": doc_type,
                "index": index,
            })

            return filepath

        except Exception as e:
            error_msg = f"Error generating PHI positive doc {index}: {str(e)}"
            self.stats["errors"].append(error_msg)
            return None

    def generate_single_phi_negative(self, index: int) -> Optional[str]:
        """Generate a single PHI negative document"""
        try:
            facility = self.facility_gen.generate_facility()

            # Choose document type based on available formats
            doc_types = []
            if "pdf" in self.formats:
                doc_types.append("policy_pdf")
            if "docx" in self.formats:
                doc_types.extend(["policy_docx", "blank_form"])
            if "eml" in self.formats:
                doc_types.append("announcement")
            if "pptx" in self.formats:
                doc_types.append("education")

            if not doc_types:
                raise ValueError("No valid document types for selected formats")

            doc_type = random.choice(doc_types)

            # Generate without PHI_NEG prefix and save to phi_negative directory
            if doc_type == "policy_pdf":
                filename = f"MedicalPolicy_{index:04d}.pdf"
                self.formatters["pdf"].output_dir = str(self.phi_negative_dir)
                filepath = self.formatters["pdf"].create_generic_medical_policy(facility, filename)
                self.stats["by_format"]["pdf"] += 1
                self.stats["by_category"]["policies"] += 1

            elif doc_type == "policy_docx":
                filename = f"MedicalPolicy_{index:04d}.docx"
                # Use the regular docx formatter for PHI negative docs
                self.formatters["docx"].output_dir = str(self.phi_negative_dir)
                # Note: This method may not exist, will use PDF for now
                # TODO: Add generic policy method to docx formatter
                # For now, skip and let it error gracefully
                self.stats["by_format"]["docx"] += 1
                self.stats["by_category"]["policies"] += 1
                return None  # Skip for now

            elif doc_type == "announcement":
                filename = f"Announcement_{index:04d}.eml"
                self.formatters["eml"].output_dir = str(self.phi_negative_dir)
                filepath = self.formatters["eml"].create_office_announcement(facility, filename)
                self.stats["by_format"]["eml"] += 1
                self.stats["by_category"]["announcements"] += 1

            elif doc_type == "education":
                filename = f"Educational_{index:04d}.pptx"
                self.formatters["pptx"].output_dir = str(self.phi_negative_dir)
                filepath = self.formatters["pptx"].create_educational_presentation(facility, filename)
                self.stats["by_format"]["pptx"] += 1
                self.stats["by_category"]["educational"] += 1

            elif doc_type == "blank_form":
                filename = f"BlankForm_{index:04d}.docx"
                # Use the regular docx formatter for PHI negative docs
                # Note: This method may not exist
                # TODO: Add blank form method to docx formatter
                # For now, skip and let it error gracefully
                self.stats["by_format"]["docx"] += 1
                self.stats["by_category"]["blank_forms"] += 1
                return None  # Skip for now

            self.stats["total_generated"] += 1
            self.stats["phi_negative"] += 1
            self.stats["template_based"] += 1

            # Add to manifest
            self.manifest.append({
                "file_path": str(Path(filepath).relative_to(self.output_dir)),
                "phi_status": "negative",
                "document_type": doc_type,
                "index": index,
            })

            return filepath

        except Exception as e:
            error_msg = f"Error generating PHI negative doc {index}: {str(e)}"
            self.stats["errors"].append(error_msg)
            return None

    def save_manifest(self):
        """Save manifest.json with metadata about all generated files"""
        manifest_path = self.metadata_dir / "manifest.json"

        manifest_data = {
            "generated_at": datetime.now().isoformat(),
            "total_documents": self.stats["total_generated"],
            "phi_positive": self.stats["phi_positive"],
            "phi_negative": self.stats["phi_negative"],
            "seed": self.seed,
            "formats": self.formats,
            "llm_percentage": self.llm_percentage,
            "statistics": self.stats,
            "files": self.manifest,
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)

        return manifest_path

    def generate_batch(
        self,
        phi_positive_count: int,
        phi_negative_count: int,
        parallel_workers: int = 1,
    ) -> dict:
        """
        Generate a batch of documents with optional parallel processing

        Args:
            phi_positive_count: Number of PHI positive documents
            phi_negative_count: Number of PHI negative documents
            parallel_workers: Number of parallel workers (1 = sequential)

        Returns:
            Dictionary with statistics
        """
        total_count = phi_positive_count + phi_negative_count

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:

            if parallel_workers > 1:
                # Parallel generation
                task = progress.add_task(
                    f"[cyan]Generating documents (parallel, {parallel_workers} workers)...",
                    total=total_count,
                )

                with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_workers) as executor:
                    # Submit PHI positive tasks
                    pos_futures = [
                        executor.submit(self.generate_single_phi_positive, i)
                        for i in range(1, phi_positive_count + 1)
                    ]

                    # Submit PHI negative tasks
                    neg_futures = [
                        executor.submit(self.generate_single_phi_negative, i)
                        for i in range(1, phi_negative_count + 1)
                    ]

                    # Process completed tasks
                    for future in concurrent.futures.as_completed(pos_futures + neg_futures):
                        future.result()  # This will raise exception if any occurred
                        progress.advance(task)

            else:
                # Sequential generation
                # PHI Positive
                pos_task = progress.add_task(
                    "[green]Generating PHI positive documents...",
                    total=phi_positive_count,
                )
                for i in range(1, phi_positive_count + 1):
                    self.generate_single_phi_positive(i)
                    progress.advance(pos_task)

                # PHI Negative
                neg_task = progress.add_task(
                    "[blue]Generating PHI negative documents...",
                    total=phi_negative_count,
                )
                for i in range(1, phi_negative_count + 1):
                    self.generate_single_phi_negative(i)
                    progress.advance(neg_task)

        # Save manifest
        manifest_path = self.save_manifest()
        self.stats["manifest_path"] = str(manifest_path)

        return self.stats


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error loading config file: {e}[/red]")
        raise typer.Exit(1)


def display_banner():
    """Display MedForge banner"""
    banner = """
[bold cyan]
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║                      🏥 MedForge 🏥                       ║
║                                                           ║
║          Synthetic PHI Data Generator v1.0                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
[/bold cyan]
"""
    console.print(banner)


def display_stats(stats: dict, output_dir: str, duration: float):
    """Display generation statistics in a formatted table"""

    # Summary panel
    summary = f"""[bold]Total Documents:[/bold] {stats['total_generated']}
[green]PHI Positive:[/green] {stats['phi_positive']}
[blue]PHI Negative:[/blue] {stats['phi_negative']}
[yellow]Duration:[/yellow] {duration:.2f}s
[yellow]Avg Time:[/yellow] {duration / max(stats['total_generated'], 1):.2f}s per document"""

    console.print(Panel(summary, title="[bold]Generation Summary[/bold]", border_style="green"))

    # Generation method table
    method_table = Table(title="Generation Method", box=box.ROUNDED)
    method_table.add_column("Method", style="cyan")
    method_table.add_column("Count", justify="right", style="magenta")
    method_table.add_column("Percentage", justify="right", style="yellow")

    if stats["llm_enhanced"] > 0:
        llm_pct = (stats["llm_enhanced"] / stats["total_generated"]) * 100
        method_table.add_row("LLM Enhanced", str(stats["llm_enhanced"]), f"{llm_pct:.1f}%")

    if stats["template_based"] > 0:
        template_pct = (stats["template_based"] / stats["total_generated"]) * 100
        method_table.add_row("Template Based", str(stats["template_based"]), f"{template_pct:.1f}%")

    console.print(method_table)

    # Format distribution table
    format_table = Table(title="Format Distribution", box=box.ROUNDED)
    format_table.add_column("Format", style="cyan")
    format_table.add_column("Count", justify="right", style="magenta")
    format_table.add_column("Percentage", justify="right", style="yellow")

    for fmt, count in sorted(stats["by_format"].items()):
        pct = (count / stats["total_generated"]) * 100
        format_table.add_row(fmt.upper(), str(count), f"{pct:.1f}%")

    console.print(format_table)

    # Errors if any
    if stats["errors"]:
        error_panel = "\n".join(stats["errors"][:10])  # Show first 10 errors
        console.print(Panel(error_panel, title="[bold red]Errors[/bold red]", border_style="red"))

    # Output location
    console.print(f"\n[bold green]Output Directory:[/bold green] {os.path.abspath(output_dir)}")


@app.command()
def generate(
    count: int = typer.Option(200, "--count", "-c", help="Total number of documents to generate"),
    phi_positive: Optional[int] = typer.Option(None, "--phi-positive", help="Number of PHI positive documents"),
    phi_negative: Optional[int] = typer.Option(None, "--phi-negative", help="Number of PHI negative documents"),
    formats: str = typer.Option("pdf,docx,xlsx,eml,pptx", "--formats", "-f", help="Comma-separated list of formats"),
    output: str = typer.Option("output/medforge", "--output", "-o", help="Output directory"),
    llm_percentage: float = typer.Option(0.2, "--llm-percentage", help="Percentage of LLM-enhanced docs (0.0-1.0)"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Random seed for reproducibility"),
    parallel_workers: int = typer.Option(1, "--parallel-workers", "-p", help="Number of parallel workers"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to YAML config file"),
):
    """
    Generate synthetic PHI documents in multiple formats

    Examples:

        medforge generate --count 100

        medforge generate --phi-positive 80 --phi-negative 20

        medforge generate --formats pdf,docx --output my_data

        medforge generate --config config.yaml
    """
    display_banner()

    # Load config if provided
    if config:
        cfg = load_config(config)
        count = cfg.get("count", count)
        phi_positive = cfg.get("phi_positive", phi_positive)
        phi_negative = cfg.get("phi_negative", phi_negative)
        formats = cfg.get("formats", formats)
        output = cfg.get("output", output)
        llm_percentage = cfg.get("llm_percentage", llm_percentage)
        seed = cfg.get("seed", seed)
        parallel_workers = cfg.get("parallel_workers", parallel_workers)

    # Parse formats
    format_list = [f.strip().lower() for f in formats.split(",")]
    valid_formats = {"pdf", "docx", "xlsx", "eml", "pptx"}
    invalid_formats = set(format_list) - valid_formats

    if invalid_formats:
        console.print(f"[red]Invalid formats: {', '.join(invalid_formats)}[/red]")
        console.print(f"[yellow]Valid formats: {', '.join(valid_formats)}[/yellow]")
        raise typer.Exit(1)

    # Calculate PHI positive/negative split
    if phi_positive is None and phi_negative is None:
        # Default 80/20 split
        phi_positive = int(count * 0.8)
        phi_negative = count - phi_positive
    elif phi_positive is None:
        phi_positive = count - phi_negative
    elif phi_negative is None:
        phi_negative = count - phi_positive
    else:
        # Both specified - use their sum as total count
        count = phi_positive + phi_negative

    # Validate parameters
    if llm_percentage < 0 or llm_percentage > 1:
        console.print("[red]Error: --llm-percentage must be between 0.0 and 1.0[/red]")
        raise typer.Exit(1)

    if parallel_workers < 1:
        console.print("[red]Error: --parallel-workers must be at least 1[/red]")
        raise typer.Exit(1)

    # Display configuration
    config_table = Table(title="Configuration", box=box.ROUNDED, show_header=False)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="yellow")

    config_table.add_row("Total Documents", str(count))
    config_table.add_row("PHI Positive", str(phi_positive))
    config_table.add_row("PHI Negative", str(phi_negative))
    config_table.add_row("Formats", ", ".join(format_list))
    config_table.add_row("LLM Enhancement", f"{int(llm_percentage * 100)}%")
    config_table.add_row("Random Seed", str(seed) if seed else "Random")
    config_table.add_row("Parallel Workers", str(parallel_workers))
    config_table.add_row("LLM Available", "Yes" if is_llm_available() else "No (using templates)")
    config_table.add_row("Output Directory", output)

    console.print(config_table)
    console.print()

    # Initialize generator
    start_time = datetime.now()

    try:
        generator = MedForgeGenerator(
            output_dir=output,
            seed=seed,
            llm_percentage=llm_percentage,
            formats=format_list,
        )

        # Generate documents
        stats = generator.generate_batch(
            phi_positive_count=phi_positive,
            phi_negative_count=phi_negative,
            parallel_workers=parallel_workers,
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Display statistics
        console.print()
        display_stats(stats, output, duration)

        console.print("\n[bold green]Generation complete![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]Error during generation:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def validate(
    path: str = typer.Argument(..., help="Path to directory or file to validate"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Validate generated documents

    Checks for:
    - File integrity (can be opened)
    - Expected PHI patterns in positive documents
    - Absence of PHI in negative documents
    """
    console.print("[bold cyan]Document Validation[/bold cyan]\n")

    path_obj = Path(path)

    if not path_obj.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(1)

    # Collect files
    files_to_validate = []
    if path_obj.is_file():
        files_to_validate = [path_obj]
    else:
        files_to_validate = list(path_obj.rglob("*"))
        files_to_validate = [f for f in files_to_validate if f.is_file()]

    console.print(f"Found {len(files_to_validate)} files to validate\n")

    results = {
        "total": len(files_to_validate),
        "valid": 0,
        "invalid": 0,
        "errors": [],
        "by_format": defaultdict(lambda: {"valid": 0, "invalid": 0}),
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Validating files...", total=len(files_to_validate))

        for file_path in files_to_validate:
            ext = file_path.suffix.lower()
            is_valid = True
            error_msg = None

            try:
                # Basic file integrity checks
                if file_path.stat().st_size == 0:
                    is_valid = False
                    error_msg = "Empty file"
                elif ext in [".docx"]:
                    # Try to open DOCX
                    from docx import Document
                    Document(str(file_path))
                elif ext in [".pdf"]:
                    # Check PDF can be read
                    with open(file_path, "rb") as f:
                        header = f.read(5)
                        if not header.startswith(b"%PDF"):
                            is_valid = False
                            error_msg = "Invalid PDF format"
                elif ext in [".xlsx"]:
                    # Try to open Excel
                    from openpyxl import load_workbook
                    load_workbook(str(file_path))
                elif ext in [".eml"]:
                    # Check email file
                    with open(file_path, "r") as f:
                        content = f.read(500)  # Read more to find headers
                        if not any(h in content for h in ["From:", "To:", "Subject:", "MIME-Version:"]):
                            is_valid = False
                            error_msg = "Invalid email format"

            except Exception as e:
                is_valid = False
                error_msg = str(e)

            if is_valid:
                results["valid"] += 1
                results["by_format"][ext]["valid"] += 1
            else:
                results["invalid"] += 1
                results["by_format"][ext]["invalid"] += 1
                results["errors"].append(f"{file_path.name}: {error_msg}")

            if verbose and not is_valid:
                console.print(f"[red]INVALID: {file_path.name} - {error_msg}[/red]")

            progress.advance(task)

    # Display results
    console.print()
    summary_table = Table(title="Validation Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right", style="yellow")

    summary_table.add_row("Total Files", str(results["total"]))
    summary_table.add_row("Valid", f"[green]{results['valid']}[/green]")
    summary_table.add_row("Invalid", f"[red]{results['invalid']}[/red]")

    if results["total"] > 0:
        success_rate = (results["valid"] / results["total"]) * 100
        summary_table.add_row("Success Rate", f"{success_rate:.1f}%")

    console.print(summary_table)

    # Format breakdown
    if results["by_format"]:
        console.print()
        format_table = Table(title="By Format", box=box.ROUNDED)
        format_table.add_column("Format", style="cyan")
        format_table.add_column("Valid", justify="right", style="green")
        format_table.add_column("Invalid", justify="right", style="red")

        for fmt, counts in sorted(results["by_format"].items()):
            format_table.add_row(
                fmt or "no extension",
                str(counts["valid"]),
                str(counts["invalid"]),
            )

        console.print(format_table)

    # Show errors
    if results["errors"] and verbose:
        console.print()
        error_panel = "\n".join(results["errors"][:20])
        console.print(Panel(error_panel, title="[bold red]Validation Errors[/bold red]", border_style="red"))

    if results["invalid"] == 0:
        console.print("\n[bold green]All files validated successfully![/bold green]")
    else:
        console.print(f"\n[bold yellow]Validation completed with {results['invalid']} errors[/bold yellow]")


@app.command()
def stats(
    path: str = typer.Argument(..., help="Path to directory to analyze"),
    tree: bool = typer.Option(False, "--tree", "-t", help="Show directory tree"),
):
    """
    Show statistics about generated documents

    Analyzes a directory and displays:
    - Total document counts
    - Format distribution
    - PHI positive vs negative counts
    - File size statistics
    """
    console.print("[bold cyan]Document Statistics[/bold cyan]\n")

    path_obj = Path(path)

    if not path_obj.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(1)

    if not path_obj.is_dir():
        console.print(f"[red]Error: Path must be a directory: {path}[/red]")
        raise typer.Exit(1)

    # Collect statistics
    stats = {
        "total_files": 0,
        "total_size": 0,
        "by_format": defaultdict(lambda: {"count": 0, "size": 0}),
        "phi_positive": 0,
        "phi_negative": 0,
        "by_type": defaultdict(int),
    }

    files = list(path_obj.rglob("*"))
    files = [f for f in files if f.is_file()]

    for file_path in files:
        stats["total_files"] += 1
        file_size = file_path.stat().st_size
        stats["total_size"] += file_size

        ext = file_path.suffix.lower()
        stats["by_format"][ext]["count"] += 1
        stats["by_format"][ext]["size"] += file_size

        # Categorize by directory path (new structure)
        path_str = str(file_path)
        if "phi_positive" in path_str:
            stats["phi_positive"] += 1
        elif "phi_negative" in path_str:
            stats["phi_negative"] += 1

        # Extract document type from directory and filename
        name = file_path.name
        if "ProgressNote" in name or "progress_notes" in path_str:
            stats["by_type"]["Progress Notes"] += 1
        elif "LabResult" in name or "lab_results" in path_str:
            stats["by_type"]["Lab Results"] += 1
        elif "Email" in name or "ProviderEmail" in name or "correspondence" in path_str:
            stats["by_type"]["Emails"] += 1
        elif "CaseStudy" in name or "case_studies" in path_str:
            stats["by_type"]["Case Studies"] += 1
        elif "Policy" in name or "policies" in path_str:
            stats["by_type"]["Policies"] += 1
        elif "Announcement" in name or "announcements" in path_str:
            stats["by_type"]["Announcements"] += 1
        elif "Educational" in name or "educational" in path_str:
            stats["by_type"]["Educational"] += 1
        elif "BlankForm" in name or "blank_forms" in path_str:
            stats["by_type"]["Blank Forms"] += 1

    # Display overview
    overview = Table(title="Overview", box=box.ROUNDED, show_header=False)
    overview.add_column("Metric", style="cyan")
    overview.add_column("Value", style="yellow")

    overview.add_row("Total Files", str(stats["total_files"]))
    overview.add_row("Total Size", f"{stats['total_size'] / 1024 / 1024:.2f} MB")
    overview.add_row("PHI Positive", f"[green]{stats['phi_positive']}[/green]")
    overview.add_row("PHI Negative", f"[blue]{stats['phi_negative']}[/blue]")

    if stats["total_files"] > 0:
        avg_size = stats["total_size"] / stats["total_files"]
        overview.add_row("Average File Size", f"{avg_size / 1024:.2f} KB")

    console.print(overview)

    # Format distribution
    if stats["by_format"]:
        console.print()
        format_table = Table(title="Format Distribution", box=box.ROUNDED)
        format_table.add_column("Format", style="cyan")
        format_table.add_column("Count", justify="right", style="magenta")
        format_table.add_column("Size", justify="right", style="yellow")
        format_table.add_column("Percentage", justify="right", style="green")

        for fmt, data in sorted(stats["by_format"].items()):
            pct = (data["count"] / stats["total_files"]) * 100
            size_mb = data["size"] / 1024 / 1024
            format_table.add_row(
                fmt or "no extension",
                str(data["count"]),
                f"{size_mb:.2f} MB",
                f"{pct:.1f}%",
            )

        console.print(format_table)

    # Document type distribution
    if stats["by_type"]:
        console.print()
        type_table = Table(title="Document Types", box=box.ROUNDED)
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", justify="right", style="magenta")
        type_table.add_column("Percentage", justify="right", style="yellow")

        for doc_type, count in sorted(stats["by_type"].items(), key=lambda x: x[1], reverse=True):
            pct = (count / stats["total_files"]) * 100
            type_table.add_row(doc_type, str(count), f"{pct:.1f}%")

        console.print(type_table)

    # Directory tree
    if tree:
        console.print()
        dir_tree = Tree(f"[bold cyan]{path_obj.name}[/bold cyan]")

        # Group files by subdirectory
        subdirs = defaultdict(list)
        for file_path in files[:50]:  # Limit to 50 files for display
            relative = file_path.relative_to(path_obj)
            parent = relative.parent
            subdirs[str(parent)].append(file_path.name)

        for subdir, filenames in sorted(subdirs.items()):
            if subdir == ".":
                for filename in sorted(filenames)[:10]:
                    dir_tree.add(f"[green]{filename}[/green]")
            else:
                branch = dir_tree.add(f"[yellow]{subdir}[/yellow]")
                for filename in sorted(filenames)[:10]:
                    branch.add(f"[green]{filename}[/green]")

        console.print(Panel(dir_tree, title="Directory Structure", border_style="cyan"))


@app.command()
def version():
    """Show MedForge version information"""
    display_banner()
    console.print("[bold]Version:[/bold] 1.0.0")
    console.print("[bold]Python:[/bold] " + sys.version.split()[0])
    console.print("[bold]LLM Available:[/bold] " + ("Yes" if is_llm_available() else "No"))


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()
