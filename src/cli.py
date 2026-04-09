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
from formatters.html_lab_formatter import HTMLLabFormatter
from generators.llm_generator import is_llm_available

# CUI imports
from generators.cui import CUIGeneratorFactory
from formatters.cui_formatter import CUIDocxFormatter, CUIEmailFormatter, CUIPdfFormatter, CUIXlsxFormatter
from formatters.cui_pptx_formatter import CUIPPTXFormatter
from formatters.cui_nested_formatter import CUINestedEmailFormatter
from formatters.cui_html_email_formatter import CUIHTMLEmailFormatter
from formatters.template_email_wrapper import TemplateEmailWrapper
from formatters.snyk_email_generator import SnykEmailGenerator
from formatters.pdf_form_populator import CustomerTemplateManager
from templates.components import ComponentMixer, CUI_SECTION_ORDERS

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
            self.formatters["html_lab"] = HTMLLabFormatter(output_dir=str(self.output_dir))

    def generate_single_phi_positive(self, index: int) -> Optional[str]:
        """Generate a single PHI positive document"""
        try:
            patient = self.patient_gen.generate_patient()
            provider = self.provider_gen.generate_provider()
            facility = self.facility_gen.generate_facility()

            # Choose document type based on available formats
            # Add weighted probability for nested emails (~7% of total)
            nested_email_chance = random.random() < 0.07

            if nested_email_chance and "eml" in self.formats:
                doc_type = "nested_email"
            else:
                doc_types = []
                if "docx" in self.formats:
                    doc_types.extend(["progress_note", "lab_result_docx"])
                if "pdf" in self.formats:
                    doc_types.append("lab_result_pdf")
                if "eml" in self.formats:
                    doc_types.extend(["email", "html_lab_email", "immunization_email"])
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

            elif doc_type == "html_lab_email":
                # Professional HTML lab result email (Quest/LabCorp style)
                lab_data = self.patient_gen.generate_lab_results()
                filename = f"LabResults_{index:04d}.eml"
                self.formatters["html_lab"].output_dir = str(self.phi_positive_dir)
                filepath = self.formatters["html_lab"].create_lab_result_email_phi_positive(
                    patient, provider, facility, lab_data, filename
                )
                self.stats["by_format"]["eml"] += 1
                self.stats["by_category"]["lab_results"] += 1
                self.stats["template_based"] += 1

            elif doc_type == "immunization_email":
                # Immunization record email
                imm_data = self.patient_gen.generate_immunization_record()
                filename = f"ImmunizationRecord_{index:04d}.eml"
                self.formatters["html_lab"].output_dir = str(self.phi_positive_dir)
                filepath = self.formatters["html_lab"].create_immunization_record_email(
                    patient, provider, facility, imm_data, filename
                )
                self.stats["by_format"]["eml"] += 1
                self.stats["by_category"]["immunizations"] += 1
                self.stats["template_based"] += 1

            elif doc_type == "nested_email":
                # PHI POSITIVE email with embedded attachment (PDF, DOCX, or ZIP)
                try:
                    lab_data = self.patient_gen.generate_lab_results()
                    filename = f"EmailWithAttachment_{index:04d}.eml"
                    self.formatters["nested_eml"].output_dir = str(self.phi_positive_dir)
                    filepath = self.formatters["nested_eml"].create_phi_positive_email_with_attachment(
                        patient, provider, facility, lab_data, filename
                    )
                    self.stats["by_format"]["eml"] += 1
                    self.stats["by_category"]["nested_emails"] += 1
                    self.stats["template_based"] += 1
                except Exception as e:
                    # If nested email fails, generate regular email instead
                    filename = f"ProviderEmail_{index:04d}.eml"
                    self.formatters["eml"].output_dir = str(self.phi_positive_dir)
                    filepath = self.formatters["eml"].create_provider_to_provider_email(
                        patient, provider, self.provider_gen.generate_provider(), filename
                    )
                    self.stats["by_format"]["eml"] += 1
                    self.stats["by_category"]["correspondence"] += 1
                    self.stats["template_based"] += 1
                    self.stats["errors"].append(f"Nested email failed for doc {index}, used regular email: {str(e)}")

            self.stats["total_generated"] += 1
            self.stats["phi_positive"] += 1

            # Add to manifest with attachment info for nested emails
            manifest_entry = {
                "file_path": str(Path(filepath).relative_to(self.output_dir)),
                "phi_status": "positive",
                "document_type": doc_type,
                "index": index,
            }
            if doc_type == "nested_email":
                manifest_entry["has_attachments"] = True
                manifest_entry["attachment_type"] = "embedded"
            self.manifest.append(manifest_entry)

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
            # Add weighted probability for nested emails (~7% of total)
            nested_email_chance = random.random() < 0.07

            if nested_email_chance and "eml" in self.formats:
                doc_type = "nested_email"
            else:
                doc_types = []
                if "pdf" in self.formats:
                    doc_types.append("policy_pdf")
                if "docx" in self.formats:
                    doc_types.extend(["policy_docx", "blank_form"])
                if "eml" in self.formats:
                    doc_types.extend(["announcement", "lab_notification"])
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

            elif doc_type == "lab_notification":
                # PHI-negative lab notification - just a portal link, no patient data
                filename = f"LabNotification_{index:04d}.eml"
                self.formatters["html_lab"].output_dir = str(self.phi_negative_dir)
                filepath = self.formatters["html_lab"].create_lab_notification_phi_negative(facility, filename)
                self.stats["by_format"]["eml"] += 1
                self.stats["by_category"]["lab_notifications"] += 1

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

            elif doc_type == "nested_email":
                # PHI NEGATIVE email with embedded attachment (PDF, DOCX, or ZIP)
                # NO patient data in email or attachments
                try:
                    filename = f"PolicyEmailWithAttachment_{index:04d}.eml"
                    self.formatters["nested_eml"].output_dir = str(self.phi_negative_dir)
                    filepath = self.formatters["nested_eml"].create_phi_negative_email_with_attachment(
                        facility, filename
                    )
                    self.stats["by_format"]["eml"] += 1
                    self.stats["by_category"]["nested_emails"] += 1
                except Exception as e:
                    # If nested email fails, generate regular announcement instead
                    filename = f"Announcement_{index:04d}.eml"
                    self.formatters["eml"].output_dir = str(self.phi_negative_dir)
                    filepath = self.formatters["eml"].create_office_announcement(facility, filename)
                    self.stats["by_format"]["eml"] += 1
                    self.stats["by_category"]["announcements"] += 1
                    self.stats["errors"].append(f"Nested email failed for doc {index}, used regular announcement: {str(e)}")

            self.stats["total_generated"] += 1
            self.stats["phi_negative"] += 1
            self.stats["template_based"] += 1

            # Add to manifest with attachment info for nested emails
            manifest_entry = {
                "file_path": str(Path(filepath).relative_to(self.output_dir)),
                "phi_status": "negative",
                "document_type": doc_type,
                "index": index,
            }
            if doc_type == "nested_email":
                manifest_entry["has_attachments"] = True
                manifest_entry["attachment_type"] = "embedded"
            self.manifest.append(manifest_entry)

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


# Available CUI categories
CUI_CATEGORIES = [
    "critical_infrastructure",
    "financial",
    "law_enforcement",
    "legal",
    "procurement",
    "proprietary",
    "tax",
]

# Display names for CUI categories (used in folder naming)
CUI_CATEGORY_DISPLAY_NAMES = {
    "critical_infrastructure": "Critical Infrastructure",
    "financial": "Financial",
    "law_enforcement": "Law Enforcement",
    "legal": "Legal",
    "procurement": "Procurement",
    "proprietary": "Proprietary Business",
    "tax": "Tax",
}


def create_production_run_folder(base_output_dir: str) -> Path:
    """
    Create a timestamped production run folder.

    Args:
        base_output_dir: Base output directory path

    Returns:
        Path to the created production_run_* folder
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(base_output_dir) / f"production_run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


class MedForgeCUIGenerator:
    """CUI document generator with support for all 7 categories"""

    def __init__(
        self,
        output_dir: str = "output",
        seed: Optional[int] = None,
        categories: Optional[List[str]] = None,
        formats: Optional[List[str]] = None,
        llm_percentage: float = 0.2,
        cui_notice: str = "random",
        cui_classification: str = "never",
        template_email_ratio: float = 0.8,
    ):
        """
        Initialize CUI generator

        Args:
            output_dir: Output directory path
            seed: Random seed for reproducibility
            categories: List of CUI categories to generate (defaults to all)
            formats: List of formats to generate (defaults to all)
            llm_percentage: Percentage of LLM-enhanced documents (0.0-1.0)
            cui_notice: Include CUI notice (random/always/never)
            cui_classification: Include CUI classification headers (always/never)
            template_email_ratio: Fraction of customer templates wrapped in email (0.0-1.0)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata directory
        self.metadata_dir = self.output_dir / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Create CUI folder structure with display names
        # Folders: CUI-{DisplayName}-Positive/, CUI-{DisplayName}-Negative/
        self.categories = categories or CUI_CATEGORIES

        # Map category to folder paths
        self.category_positive_dirs = {}
        self.category_negative_dirs = {}

        for category in self.categories:
            display_name = CUI_CATEGORY_DISPLAY_NAMES.get(category, category.replace("_", " ").title())
            positive_folder = f"CUI-{display_name}-Positive"
            negative_folder = f"CUI-{display_name}-Negative"

            positive_dir = self.output_dir / positive_folder
            negative_dir = self.output_dir / negative_folder

            positive_dir.mkdir(parents=True, exist_ok=True)
            negative_dir.mkdir(parents=True, exist_ok=True)

            self.category_positive_dirs[category] = positive_dir
            self.category_negative_dirs[category] = negative_dir

        self.seed = seed
        self.formats = formats or ["pdf", "docx", "xlsx", "eml", "pptx"]
        self.llm_percentage = llm_percentage
        self.cui_notice = cui_notice
        self.cui_classification = cui_classification
        self.template_email_ratio = template_email_ratio

        if seed is not None:
            random.seed(seed)

        # Statistics tracking
        self.stats = {
            "total_generated": 0,
            "llm_enhanced": 0,
            "template_based": 0,
            "by_format": defaultdict(int),
            "by_category": defaultdict(int),
            "cui_positive": 0,
            "cui_negative": 0,
            "errors": [],
        }

        self.manifest = []

        # Initialize component mixer for visual variety in DOCX/PDF
        self.component_mixer = ComponentMixer(seed=seed)

        # Initialize CUI generator factory
        self.cui_generator = CUIGeneratorFactory.create_composite_generator(
            categories=self.categories,
            seed=seed,
        )

        # Initialize LLM generator if available
        self.llm_generator = None
        if is_llm_available() and llm_percentage > 0:
            try:
                from generators.llm_generator import ClaudeGenerator
                self.llm_generator = ClaudeGenerator()
            except Exception as e:
                console.print(f"[yellow]Warning: Could not initialize LLM generator: {e}[/yellow]")

        # Initialize formatters
        self.formatters = {
            "docx": CUIDocxFormatter(output_dir=str(self.output_dir)),
            "pdf": CUIPdfFormatter(output_dir=str(self.output_dir)),
            "xlsx": CUIXlsxFormatter(output_dir=str(self.output_dir)),
            "eml": CUIEmailFormatter(output_dir=str(self.output_dir)),
            "pptx": CUIPPTXFormatter(output_dir=str(self.output_dir)),
            "nested_eml": CUINestedEmailFormatter(output_dir=str(self.output_dir)),
            "html_eml": CUIHTMLEmailFormatter(output_dir=str(self.output_dir)),
            "snyk_eml": SnykEmailGenerator(
                output_dir=str(self.output_dir),
                llm_generator=self.llm_generator,
                llm_percentage=llm_percentage,
            ),
        }

        # Initialize template email wrapper for wrapping templates as attachments
        self.template_email_wrapper = TemplateEmailWrapper(
            output_dir=str(self.output_dir), seed=seed)

        # Initialize customer template manager for real CMS forms
        # Templates are in ./cust_templates directory
        self.customer_templates = CustomerTemplateManager(
            template_dir='./cust_templates',
            output_dir=str(self.output_dir)
        )

    def _generate_from_customer_template(self, index: int, populate: bool, is_positive: bool) -> Optional[str]:
        """
        Generate a document from customer CMS template.

        Args:
            index: Document index
            populate: Whether to populate fields or use blank
            is_positive: True for positive (CUI-containing), False for negative

        Returns:
            Path to created file or None if no templates available
        """
        try:
            # Map customer templates to CUI categories
            # NOTE: EFT disabled - form fill not working reliably
            template_category_map = {
                'EFT Authorization Form': 'financial',
                'ReasonableAccommodationRequest': 'legal',
                'IGCE': 'procurement',
                'CLINTemplates': 'procurement',
                'MarketResearch': 'procurement',
                'RFCMemo': 'procurement',
                'AGXRFCMemo': 'procurement',
                'JALimitedSource': 'procurement',
                'JOFOC': 'procurement',
                'OAGMSourceSelection': 'procurement',
                'AcquisitionPlan': 'procurement',
                'KMP': 'critical_infrastructure',
                'RulesOfBehavior': 'critical_infrastructure',
                'IncidentResponse': 'critical_infrastructure',
                'AFRAdditionalInfo': 'financial',
                'DIBOAFR': 'financial',
                'SupplementalAFR': 'financial',
                'OITFOAdditionalInfo': 'financial',
                'SupplementalAFRBlank': 'financial',
                'HHSRBD': 'critical_infrastructure',
                'B6Letter': 'legal',
                'FullRelease': 'legal',
                'Form339Letter': 'legal',
                'SubpoenaResponse': 'legal',
                'FOIAMedicareAuth': 'legal',
                'FOIAGuidance': 'legal',
                'FOIARequestDeceasedBene': 'legal',
            }

            # Group templates by active category, then select category-first
            # to avoid bias when one category has many more templates than others
            templates_by_category = {}
            for k, cat in template_category_map.items():
                if cat in self.categories:
                    templates_by_category.setdefault(cat, []).append(k)

            if not templates_by_category:
                return None

            category = random.choice(list(templates_by_category.keys()))
            template_key = random.choice(templates_by_category[category])

            # Get correct output directory
            if is_positive:
                output_subdir = str(self.category_positive_dirs.get(category, self.output_dir))
            else:
                output_subdir = str(self.category_negative_dirs.get(category, self.output_dir))

            # Optionally enrich template with LLM narratives (positive only)
            # Pre-generate Faker data so LLM enrichment and template fill
            # use the same values (avoids name/number mismatch)
            pre_generated_data = None
            extra_data = None
            llm_enriched = False
            template_info = self.customer_templates.template_mappings.get(template_key, {})
            generator = template_info.get('generator')

            if populate and generator:
                pre_generated_data = generator()

                if self.llm_generator and random.random() < self.llm_percentage:
                    extra_data = self._enrich_template_data_with_llm(
                        template_key, context=pre_generated_data)
                    if extra_data:
                        llm_enriched = True

            # Generate from template
            filepath = self.customer_templates.generate_from_template(
                template_key,
                output_subdir,
                index,
                populate=populate,
                extra_data=extra_data,
                field_data=pre_generated_data,
            )

            template_info = self.customer_templates.template_mappings[template_key]
            clean_name = template_info['clean_name']

            # Decide whether to wrap in email or return bare file
            wrap_in_email = random.random() < self.template_email_ratio
            email_llm_used = False

            if wrap_in_email and filepath:
                # Pick tier: LLM (detailed) or random minimal/medium
                if self.llm_generator and random.random() < self.llm_percentage:
                    # Tier 3: LLM-generated cover email
                    llm_email = self.llm_generator.generate_cover_email(
                        template_key, category, clean_name,
                        pre_generated_data or {})
                    if llm_email.get('subject') and llm_email.get('body'):
                        subject = llm_email['subject']
                        body = llm_email['body']
                        email_llm_used = True
                    else:
                        # LLM failed, fall back to medium
                        sender_name, _, sender_title, sender_office = self.template_email_wrapper._get_sender()
                        subject, body = self.template_email_wrapper._medium_body(
                            clean_name, category, sender_name, sender_title, sender_office)
                elif random.random() < 0.5:
                    # Tier 1: Minimal
                    subject, body = self.template_email_wrapper._minimal_body(clean_name)
                else:
                    # Tier 2: Medium
                    sender_name, _, sender_title, sender_office = self.template_email_wrapper._get_sender()
                    subject, body = self.template_email_wrapper._medium_body(
                        clean_name, category, sender_name, sender_title, sender_office)

                # Wrap the template file in an email
                eml_path = self.template_email_wrapper.wrap(
                    template_path=filepath,
                    template_key=template_key,
                    clean_name=clean_name,
                    category=category,
                    subject=subject,
                    body=body,
                    output_dir=output_subdir,
                    index=index,
                )

                # Delete the intermediate bare file — content is now in the .eml
                try:
                    os.remove(filepath)
                except OSError:
                    pass

                filepath = eml_path

            # Detect format from output filepath extension
            detected_ext = os.path.splitext(filepath)[1].lstrip('.').lower()
            detected_format = detected_ext if detected_ext else 'pdf'

            # Update statistics
            self.stats["total_generated"] += 1
            self.stats["template_based"] += 1
            self.stats["by_format"][detected_format] += 1
            self.stats["by_category"][category] += 1

            if is_positive:
                self.stats["cui_positive"] += 1
            else:
                self.stats["cui_negative"] += 1

            # Add to manifest
            was_llm_enhanced = (llm_enriched if populate else False) or email_llm_used
            variant = 'email_wrapped' if wrap_in_email else 'standard'
            self.manifest.append({
                "file_path": str(Path(filepath).relative_to(self.output_dir)),
                "cui_status": "positive" if is_positive else "negative",
                "category": category,
                "subcategory": "",
                "document_type": clean_name,
                "classification": "CUI" if is_positive else "",
                "authority": "",
                "format": detected_format,
                "index": index,
                "llm_enhanced": was_llm_enhanced,
                "source": "customer_template",
                "variant": variant,
            })

            if was_llm_enhanced:
                self.stats["llm_enhanced"] += 1

            return filepath

        except Exception:
            # Fail silently and let regular generation take over
            return None

    def _enrich_template_data_with_llm(self, template_key: str,
                                       context: Optional[dict] = None) -> Optional[dict]:
        """
        Generate LLM narrative content for a customer template.

        Args:
            template_key: Template identifier
            context: Pre-generated Faker data to use as LLM context (avoids
                     generating different data than what fills the template)

        Returns dict of extra fields to merge into template data, or None.
        The LLM narratives are converted to _append_paragraphs format for DOCX
        and plain text substitutions for other formats.
        """
        # DOCX templates: LLM narratives are appended as labelled paragraphs
        DOCX_ENRICHABLE = {
            'AcquisitionPlan', 'IncidentResponse', 'KMP',
            'MarketResearch', 'JOFOC', 'JALimitedSource', 'SubpoenaResponse', 'RFCMemo',
            'B6Letter', 'Form339Letter', 'FullRelease',
            'DIBOAFR', 'SupplementalAFR', 'OITFOAdditionalInfo',
            'RulesOfBehavior', 'AGXRFCMemo', 'OAGMSourceSelection',
        }
        # PDF templates: LLM narratives are injected as free-text field values
        PDF_ENRICHABLE = {
            'EFT Authorization Form', 'FOIAMedicareAuth',
            'Medical Inquiry  Form', 'ReasonableAccommodationRequest',
        }
        if template_key not in DOCX_ENRICHABLE and template_key not in PDF_ENRICHABLE:
            return None

        try:
            if context is None:
                template_info = self.customer_templates.template_mappings.get(template_key, {})
                generator = template_info.get('generator')
                context = generator() if generator else {}

            narratives = self.llm_generator.generate_template_narrative(template_key, context)
            if not narratives:
                return None

            # PDF templates: return LLM values as direct field substitutions
            # Field names match or approximate PDF form field names; unmatched keys
            # are silently ignored by the PDF populator.
            if template_key in PDF_ENRICHABLE:
                return {k: v for k, v in narratives.items() if isinstance(v, str) and v.strip()}

            # DOCX templates: convert to _append_paragraphs sections
            heading_map = {
                # KMP
                'system_description': 'System Description',
                'key_management_procedures': 'Key Management Procedures',
                'compliance_justification': 'Compliance Justification',
                # Incident Response
                'incident_summary': 'Incident Summary',
                'containment_actions': 'Containment Actions',
                'lessons_learned': 'Lessons Learned',
                # Acquisition Plan
                'acquisition_strategy': 'Acquisition Strategy',
                'market_research_summary': 'Market Research Summary',
                'cost_justification': 'Cost Justification',
                # Market Research
                'market_overview': 'Market Overview',
                'capability_assessment': 'Capability Assessment',
                'small_business_analysis': 'Small Business Analysis',
                # JOFOC
                'justification_narrative': 'Justification',
                'market_research_findings': 'Market Research Findings',
                'determination_rationale': 'Determination Rationale',
                # JA Limited Source
                'competition_justification': 'Competition Justification',
                'efforts_to_compete': 'Efforts to Obtain Competition',
                'fair_pricing_determination': 'Fair Pricing Determination',
                # Subpoena Response
                'response_narrative': 'Response',
                'privilege_log_summary': 'Privilege Log Summary',
                'production_scope': 'Document Production Scope',
                # RFC Memo
                'change_justification': 'Change Justification',
                'impact_analysis': 'Impact Analysis',
                'stakeholder_assessment': 'Stakeholder Assessment',
                # B6 Letter
                'response_rationale': 'Response Rationale',
                'exemption_analysis': 'Exemption Analysis',
                'disclosure_determination': 'Disclosure Determination',
                # Form 339 Letter
                'withholding_justification': 'Withholding Justification',
                'submitter_notice_summary': 'Submitter Notice Summary',
                'exemption_4_analysis': 'Exemption 4 Analysis',
                # Full Release
                'release_summary': 'Release Summary',
                'search_methodology': 'Search Methodology',
                'processing_notes': 'Processing Notes',
                # DIBO AFR
                'funding_justification': 'Funding Justification',
                'cost_analysis': 'Cost Analysis',
                'operational_impact': 'Operational Impact',
                # Supplemental AFR
                'supplemental_justification': 'Supplemental Justification',
                'product_rationale': 'Product Rationale',
                'budget_impact': 'Budget Impact',
                # OIT FO Additional Info
                'strategic_alignment': 'Strategic Alignment',
                'investment_analysis': 'Investment Analysis',
                'stakeholder_impact': 'Stakeholder Impact',
                # Rules of Behavior
                'assessment_scope': 'Assessment Scope',
                'compliance_findings': 'Compliance Findings',
                'remediation_plan': 'Remediation Plan',
                # OAGM Source Selection
                'evaluation_summary': 'Evaluation Summary',
                'tradeoff_analysis': 'Tradeoff Analysis',
                'selection_rationale': 'Selection Rationale',
            }

            sections = []
            for key, text in narratives.items():
                if isinstance(text, str) and text.strip():
                    sections.append({
                        'heading': heading_map.get(key, key.replace('_', ' ').title()),
                        'text': text,
                    })

            if sections:
                return {'_append_paragraphs': sections}
            return None

        except Exception as e:
            self.stats["errors"].append(f"Template LLM enrichment failed for {template_key}: {str(e)}")
            return None

    def _apply_cui_notice_policy(self, doc_data: dict) -> dict:
        """Apply CUI confidentiality notice based on policy setting."""
        if self.cui_notice == "never":
            if 'confidentiality_notice' in doc_data:
                del doc_data['confidentiality_notice']
        elif self.cui_notice == "random":
            if random.random() < 0.5 and 'confidentiality_notice' in doc_data:
                del doc_data['confidentiality_notice']
        # "always" keeps notice
        return doc_data

    def _apply_cui_classification_policy(self, doc_data: dict) -> dict:
        """Apply CUI classification header based on policy setting."""
        if self.cui_classification == "never":
            if 'classification' in doc_data:
                del doc_data['classification']
        # "always" keeps classification
        return doc_data

    def _enhance_with_llm(self, doc_data: dict) -> tuple[dict, bool]:
        """
        Enhance document content using LLM if available and selected

        Returns:
            Tuple of (enhanced_doc_data, was_enhanced)
        """
        # Check if we should use LLM for this document
        use_llm = (
            self.llm_generator is not None
            and random.random() < self.llm_percentage
        )

        if not use_llm:
            return doc_data, False

        try:
            category = doc_data.get("category", "")
            subcategory = doc_data.get("subcategory", "")
            doc_type = doc_data.get("document_type", "")

            # Generate enhanced content based on category.
            # Field names must match what CUI formatter type handlers read
            # (see cui_formatter.py _add_*_content methods).
            if category == "financial" and "bank_secrecy" in subcategory:
                enhanced = self.llm_generator.generate_cui_narrative(
                    category=category, subcategory=subcategory,
                    document_type=doc_type,
                    context={"organization": doc_data.get("organization", ""),
                             "subject": doc_data.get("subject", "")}
                )
                # SAR handler reads suspicious_activity dict with narrative field
                if "suspicious_activity" in doc_data and isinstance(doc_data["suspicious_activity"], dict):
                    doc_data["suspicious_activity"]["narrative"] = enhanced.body_content
                doc_data["executive_summary"] = enhanced.executive_summary

            elif category == "financial" and "retirement" in subcategory:
                enhanced = self.llm_generator.generate_cui_narrative(
                    category=category, subcategory=subcategory,
                    document_type=doc_type,
                    context={"organization": doc_data.get("organization", ""),
                             "employee": doc_data.get("employee", {}).get("name", "")}
                )
                doc_data["executive_summary"] = enhanced.executive_summary
                doc_data["disclaimer"] = enhanced.body_content

            elif category == "financial" and "comptroller" in subcategory:
                enhanced = self.llm_generator.generate_cui_narrative(
                    category=category, subcategory=subcategory,
                    document_type=doc_type,
                    context={"organization": doc_data.get("agency_reviewed", ""),
                             "topic": doc_data.get("topic", "")}
                )
                doc_data["executive_summary"] = enhanced.executive_summary
                # Enrich first finding description if present
                findings = doc_data.get("findings", [])
                if findings and isinstance(findings[0], dict):
                    findings[0]["description"] = enhanced.body_content

            elif category == "financial" and "budget" in subcategory:
                enhanced = self.llm_generator.generate_cui_budget_memo(
                    agency=doc_data.get("organization", "Government Agency"),
                    program=doc_data.get("program", "Federal Program"),
                    fiscal_year=str(doc_data.get("fiscal_year", "2025")),
                    amount=doc_data.get("amount", "$1,000,000")
                )
                # budget_memo handler reads: to, from, subject, decision, key_decision_points
                doc_data["subject"] = enhanced.subject
                doc_data["decision"] = enhanced.budget_justification
                doc_data["key_decision_points"] = [
                    enhanced.purpose,
                    enhanced.fiscal_impact,
                    enhanced.recommendation,
                ]
                # Also store for generic/email formatters
                doc_data["executive_summary"] = enhanced.purpose
                doc_data["fiscal_impact"] = enhanced.fiscal_impact

            elif category == "critical_infrastructure" or "vulnerability" in doc_type:
                enhanced = self.llm_generator.generate_cui_security_report(
                    system_name=doc_data.get("system_name", "Enterprise System"),
                    vulnerability_type=doc_data.get("vulnerability_type", "Security Vulnerability"),
                    severity=doc_data.get("severity", "High"),
                    agency=doc_data.get("organization", "Government Agency")
                )
                # vulnerability_alert handler reads: alert_id, severity, cvss_score,
                # cve_id, affected_system, affected_versions, description, remediation
                doc_data["description"] = enhanced.technical_details
                doc_data["remediation"] = {
                    "action": enhanced.mitigation_steps,
                    "target_version": doc_data.get("remediation", {}).get("target_version", "Latest"),
                    "deadline": enhanced.timeline,
                }
                # Also store for generic/email/coop formatters
                doc_data["executive_summary"] = enhanced.incident_summary
                doc_data["risk_assessment"] = enhanced.risk_assessment

            elif category == "legal":
                enhanced = self.llm_generator.generate_cui_legal_memo(
                    subject=doc_data.get("subject", "Legal Matter"),
                    agency=doc_data.get("organization", "Government Agency"),
                    legal_issue=doc_data.get("legal_issue", "regulatory compliance")
                )
                # attorney_memo handler reads: privilege_assertion, attorney, client,
                # subject, question_presented, brief_answer, analysis, recommendation
                doc_data["subject"] = enhanced.subject
                doc_data["question_presented"] = enhanced.question_presented
                doc_data["brief_answer"] = enhanced.brief_answer
                doc_data["analysis"] = enhanced.analysis
                doc_data["recommendation"] = enhanced.conclusion

            elif category == "procurement":
                vendors = doc_data.get("vendors", ["Vendor A", "Vendor B", "Vendor C"])
                enhanced = self.llm_generator.generate_cui_procurement_doc(
                    acquisition_name=doc_data.get("acquisition_name", "IT Services"),
                    agency=doc_data.get("organization", "Government Agency"),
                    estimated_value=doc_data.get("estimated_value", "$500,000"),
                    vendors=vendors if isinstance(vendors, list) else [vendors]
                )
                # source_selection_plan handler reads: solicitation_number, program,
                # estimated_value, contract_type, evaluation_factors
                doc_data["executive_summary"] = enhanced.acquisition_summary
                criteria = enhanced.evaluation_criteria
                if criteria and isinstance(criteria, str):
                    doc_data["evaluation_factors"] = [
                        {"factor": line.strip().rstrip('.'), "weight": random.randint(15, 40)}
                        for line in criteria.split('.')
                        if line.strip()
                    ][:4]
                doc_data["justification"] = enhanced.justification
                doc_data["recommendation"] = enhanced.recommendation

            elif category == "tax" and "written" in subcategory:
                enhanced = self.llm_generator.generate_cui_tax_determination(
                    issue=doc_data.get("issues", ["tax treatment"])[0] if isinstance(doc_data.get("issues"), list) else doc_data.get("issues", "tax treatment"),
                    code_sections=", ".join(doc_data.get("code_sections", ["IRC Section 61"])) if isinstance(doc_data.get("code_sections"), list) else doc_data.get("code_sections", "IRC Section 61"),
                )
                # written_determination handler reads: facts, law_and_analysis, conclusion
                doc_data["facts"] = enhanced.facts
                doc_data["law_and_analysis"] = enhanced.law_and_analysis
                doc_data["conclusion"] = enhanced.conclusion

            elif category == "tax":
                enhanced = self.llm_generator.generate_cui_narrative(
                    category=category, subcategory=subcategory,
                    document_type=doc_type,
                    context={
                        "organization": doc_data.get("organization", "Internal Revenue Service"),
                        "subject": doc_data.get("subject", "tax matter"),
                    }
                )
                doc_data["executive_summary"] = enhanced.executive_summary
                doc_data["body_content"] = enhanced.body_content

            else:
                # Generic CUI narrative enhancement
                enhanced = self.llm_generator.generate_cui_narrative(
                    category=category,
                    subcategory=subcategory,
                    document_type=doc_type,
                    context={
                        "organization": doc_data.get("organization", ""),
                        "subject": doc_data.get("subject", ""),
                    }
                )
                doc_data["executive_summary"] = enhanced.executive_summary
                doc_data["body_content"] = enhanced.body_content
                doc_data["recommendations"] = enhanced.recommendations

            return doc_data, True

        except Exception as e:
            # If LLM enhancement fails, return original data
            self.stats["errors"].append(f"LLM enhancement failed: {str(e)}")
            return doc_data, False

    def _enhance_negative_with_llm(self, doc_data: dict) -> tuple[dict, bool]:
        """
        Enhance CUI negative document with LLM-generated public-facing prose.

        Generates realistic but non-sensitive content suitable for unlimited
        public distribution. No names, case numbers, or pre-decisional markers.

        Returns:
            Tuple of (enhanced_doc_data, was_enhanced)
        """
        try:
            category = doc_data.get("category", "")
            doc_type = doc_data.get("document_type", "")

            enhanced = self.llm_generator.generate_cui_negative_narrative(
                category=category,
                document_type=doc_type,
                context={
                    "title": doc_data.get("title", ""),
                    "publisher": doc_data.get("publisher", ""),
                }
            )

            doc_data["executive_summary"] = enhanced.executive_summary
            doc_data["body_content"] = enhanced.body_content
            if enhanced.recommendations:
                doc_data["recommendations"] = enhanced.recommendations

            return doc_data, True

        except Exception as e:
            self.stats["errors"].append(f"Negative LLM enhancement failed: {str(e)}")
            return doc_data, False

    def generate_single_cui_positive(self, index: int) -> Optional[str]:
        """Generate a single CUI positive document"""
        try:
            # 20% chance to use customer CMS template
            use_customer_template = random.random() < 0.2

            if use_customer_template and {'pdf', 'docx', 'xlsx', 'eml'} & set(self.formats):
                # Try to use a customer template
                template_result = self._generate_from_customer_template(index, populate=True, is_positive=True)
                if template_result:
                    return template_result
                # Fall through to regular generation if template fails

            # Generate document data
            doc_data = self.cui_generator.generate_positive()
            category = doc_data.get("category", "general")
            doc_type = doc_data.get("document_type", "document")

            # Try LLM enhancement
            doc_data, was_enhanced = self._enhance_with_llm(doc_data)
            if was_enhanced:
                self.stats["llm_enhanced"] += 1
            else:
                self.stats["template_based"] += 1

            # Apply CUI notice policy
            doc_data = self._apply_cui_notice_policy(doc_data)

            # Apply CUI classification policy
            doc_data = self._apply_cui_classification_policy(doc_data)

            # Choose format
            available_formats = [f for f in self.formats if f in self.formatters]
            if not available_formats:
                return None

            # ~7% chance of nested email (matching PHI pipeline)
            use_nested = random.random() < 0.07 and "eml" in available_formats
            # ~50% Snyk for critical_infrastructure vulnerability alerts
            use_snyk = (
                category == "critical_infrastructure"
                and doc_type in ["vulnerability_alert", "fisma_report"]
                and "eml" in available_formats
                and random.random() < 0.5
            )
            # ~30% HTML email for vulnerability alerts
            use_html_email = (
                doc_type in ["vulnerability_alert", "budget_memo", "investigation_summary"]
                and "eml" in available_formats
                and random.random() < 0.3
                and not use_snyk
            )

            if use_snyk:
                fmt = "eml"
            elif use_nested:
                fmt = "eml"
            elif use_html_email:
                fmt = "eml"
            elif doc_type in ["vulnerability_alert", "servicenow_ticket"]:
                fmt = "eml" if "eml" in available_formats else random.choice(available_formats)
            elif doc_type in ["taxpayer_record", "eft_authorization", "sam_registration"]:
                fmt = "xlsx" if "xlsx" in available_formats else random.choice(available_formats)
            else:
                fmt = random.choice(available_formats)

            # Generate filename
            type_prefix = doc_type.replace("_", "").title()[:15]
            filename = f"{type_prefix}_{index:04d}.{fmt}"

            # Set output directory for formatter (use display name folder)
            category_dir = self.category_positive_dirs.get(category, self.output_dir)

            # Create document based on format and variant
            if use_snyk:
                self.formatters["snyk_eml"].output_dir = str(category_dir)
                filepath = self.formatters["snyk_eml"].create_snyk_vulnerability_alert(
                    filename, is_positive=True)
                fmt = "eml"
            elif use_nested:
                self.formatters["nested_eml"].output_dir = str(category_dir)
                filepath = self.formatters["nested_eml"].create_cui_email_with_attachment(
                    doc_data, filename, is_positive=True)
                fmt = "eml"
            elif use_html_email:
                self.formatters["html_eml"].output_dir = str(category_dir)
                filepath = self.formatters["html_eml"].create_cui_html_email(doc_data, filename)
                fmt = "eml"
            elif fmt == "docx":
                self.formatters[fmt].output_dir = str(category_dir)
                component_config = self.component_mixer.get_random_configuration(
                    avoid_duplicates=False,
                    force_variant={"section_order": random.choice(CUI_SECTION_ORDERS)},
                )
                filepath = self.formatters[fmt].create_cui_document(
                    doc_data, filename, component_config=component_config)
            elif fmt == "pdf":
                self.formatters[fmt].output_dir = str(category_dir)
                component_config = self.component_mixer.get_random_configuration(
                    avoid_duplicates=False,
                    force_variant={"section_order": random.choice(CUI_SECTION_ORDERS)},
                )
                filepath = self.formatters[fmt].create_cui_pdf(
                    doc_data, filename, component_config=component_config)
            elif fmt == "xlsx":
                self.formatters[fmt].output_dir = str(category_dir)
                filepath = self.formatters[fmt].create_cui_xlsx(doc_data, filename)
            elif fmt == "eml":
                self.formatters[fmt].output_dir = str(category_dir)
                filepath = self.formatters[fmt].create_cui_email(doc_data, filename)
            elif fmt == "pptx":
                self.formatters[fmt].output_dir = str(category_dir)
                pptx_config = self.component_mixer.get_random_configuration(
                    avoid_duplicates=False,
                    force_variant={"section_order": random.choice(CUI_SECTION_ORDERS)},
                )
                filepath = self.formatters[fmt].create_cui_presentation(
                    doc_data, filename, component_config=pptx_config)
            else:
                return None

            # Update statistics
            self.stats["total_generated"] += 1
            self.stats["cui_positive"] += 1
            self.stats["by_format"][fmt] += 1
            self.stats["by_category"][category] += 1

            # Determine variant for manifest
            variant = "standard"
            if use_snyk:
                variant = "snyk_alert"
            elif use_nested:
                variant = "nested_attachment"
            elif use_html_email:
                variant = "html_styled"

            # Add to manifest
            manifest_entry = {
                "file_path": str(Path(filepath).relative_to(self.output_dir)),
                "cui_status": "positive",
                "category": category,
                "subcategory": doc_data.get("subcategory", ""),
                "document_type": doc_type,
                "classification": doc_data.get("classification", ""),
                "authority": doc_data.get("authority", ""),
                "format": fmt,
                "variant": variant,
                "index": index,
                "llm_enhanced": was_enhanced,
            }
            self.manifest.append(manifest_entry)

            return filepath

        except Exception as e:
            error_msg = f"Error generating CUI positive doc {index}: {str(e)}"
            self.stats["errors"].append(error_msg)
            return None

    def generate_single_cui_negative(self, index: int) -> Optional[str]:
        """Generate a single CUI negative document"""
        try:
            # 20% chance to use customer CMS template
            use_customer_template = random.random() < 0.2

            if use_customer_template and {'pdf', 'docx', 'xlsx', 'eml'} & set(self.formats):
                # Try to use a customer template (blank/unpopulated)
                template_result = self._generate_from_customer_template(index, populate=False, is_positive=False)
                if template_result:
                    return template_result
                # Fall through to regular generation if template fails

            # Generate document data
            doc_data = self.cui_generator.generate_negative()
            category = doc_data.get("category", "general")
            doc_type = doc_data.get("document_type", "document")

            # CUI negatives use half the positive LLM rate for public-facing prose
            neg_llm_rate = self.llm_percentage / 2
            was_enhanced = False
            if self.llm_generator and random.random() < neg_llm_rate:
                doc_data, was_enhanced = self._enhance_negative_with_llm(doc_data)

            if was_enhanced:
                self.stats["llm_enhanced"] += 1
            else:
                self.stats["template_based"] += 1

            # Choose format
            available_formats = [f for f in self.formats if f in self.formatters]
            if not available_formats:
                return None

            # ~7% nested email, ~50% Snyk for servicenow_ticket negatives
            use_nested = random.random() < 0.07 and "eml" in available_formats
            use_snyk = (
                category == "critical_infrastructure"
                and doc_type == "servicenow_ticket"
                and "eml" in available_formats
                and random.random() < 0.5
            )
            use_html_email = (
                doc_type in ["servicenow_ticket", "policy_update", "compliance_report"]
                and "eml" in available_formats
                and random.random() < 0.3
                and not use_snyk
            )

            if use_snyk:
                fmt = "eml"
            elif use_nested:
                fmt = "eml"
            elif use_html_email:
                fmt = "eml"
            else:
                fmt = random.choice(available_formats)

            # Generate filename
            type_prefix = doc_type.replace("_", "").title()[:15]
            filename = f"{type_prefix}_{index:04d}.{fmt}"

            # Set output directory for formatter (use display name folder)
            category_dir = self.category_negative_dirs.get(category, self.output_dir)

            # Create document based on format and variant
            if use_snyk:
                self.formatters["snyk_eml"].output_dir = str(category_dir)
                filepath = self.formatters["snyk_eml"].create_snyk_vulnerability_alert(
                    filename, is_positive=False)
                fmt = "eml"
            elif use_nested:
                self.formatters["nested_eml"].output_dir = str(category_dir)
                filepath = self.formatters["nested_eml"].create_cui_email_with_attachment(
                    doc_data, filename, is_positive=False)
                fmt = "eml"
            elif use_html_email:
                self.formatters["html_eml"].output_dir = str(category_dir)
                filepath = self.formatters["html_eml"].create_cui_html_email(doc_data, filename)
                fmt = "eml"
            elif fmt == "docx":
                self.formatters[fmt].output_dir = str(category_dir)
                component_config = self.component_mixer.get_random_configuration(
                    avoid_duplicates=False,
                    force_variant={"section_order": random.choice(CUI_SECTION_ORDERS)},
                )
                filepath = self.formatters[fmt].create_cui_document(
                    doc_data, filename, component_config=component_config)
            elif fmt == "pdf":
                self.formatters[fmt].output_dir = str(category_dir)
                component_config = self.component_mixer.get_random_configuration(
                    avoid_duplicates=False,
                    force_variant={"section_order": random.choice(CUI_SECTION_ORDERS)},
                )
                filepath = self.formatters[fmt].create_cui_pdf(
                    doc_data, filename, component_config=component_config)
            elif fmt == "xlsx":
                self.formatters[fmt].output_dir = str(category_dir)
                filepath = self.formatters[fmt].create_cui_xlsx(doc_data, filename)
            elif fmt == "eml":
                self.formatters[fmt].output_dir = str(category_dir)
                filepath = self.formatters[fmt].create_cui_email(doc_data, filename)
            elif fmt == "pptx":
                self.formatters[fmt].output_dir = str(category_dir)
                pptx_config = self.component_mixer.get_random_configuration(
                    avoid_duplicates=False,
                    force_variant={"section_order": random.choice(CUI_SECTION_ORDERS)},
                )
                filepath = self.formatters[fmt].create_cui_presentation(
                    doc_data, filename, component_config=pptx_config)
            else:
                return None

            # Determine variant for manifest
            variant = "standard"
            if use_snyk:
                variant = "snyk_alert"
            elif use_nested:
                variant = "nested_attachment"
            elif use_html_email:
                variant = "html_styled"

            # Update statistics
            self.stats["total_generated"] += 1
            self.stats["cui_negative"] += 1
            self.stats["by_format"][fmt] += 1
            self.stats["by_category"][category] += 1

            # Add to manifest (standardized schema matching positive docs)
            self.manifest.append({
                "file_path": str(Path(filepath).relative_to(self.output_dir)),
                "cui_status": "negative",
                "category": category,
                "subcategory": "",
                "document_type": doc_type,
                "classification": "",
                "authority": "",
                "format": fmt,
                "variant": variant,
                "index": index,
                "llm_enhanced": was_enhanced,
            })

            return filepath

        except Exception as e:
            error_msg = f"Error generating CUI negative doc {index}: {str(e)}"
            self.stats["errors"].append(error_msg)
            return None

    def save_manifest(self):
        """Save CUI manifest.json"""
        manifest_path = self.metadata_dir / "cui_manifest.json"

        manifest_data = {
            "generated_at": datetime.now().isoformat(),
            "total_documents": self.stats["total_generated"],
            "cui_positive": self.stats["cui_positive"],
            "cui_negative": self.stats["cui_negative"],
            "seed": self.seed,
            "categories": self.categories,
            "formats": self.formats,
            "statistics": dict(self.stats),
            "files": self.manifest,
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2, default=str)

        return manifest_path

    def generate_batch(
        self,
        cui_positive_count: int,
        cui_negative_count: int,
        parallel_workers: int = 1,
    ) -> dict:
        """Generate a batch of CUI documents"""
        total_count = cui_positive_count + cui_negative_count

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
                task = progress.add_task(
                    f"[cyan]Generating CUI documents (parallel, {parallel_workers} workers)...",
                    total=total_count,
                )

                with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_workers) as executor:
                    pos_futures = [
                        executor.submit(self.generate_single_cui_positive, i)
                        for i in range(1, cui_positive_count + 1)
                    ]
                    neg_futures = [
                        executor.submit(self.generate_single_cui_negative, i)
                        for i in range(1, cui_negative_count + 1)
                    ]

                    for future in concurrent.futures.as_completed(pos_futures + neg_futures):
                        future.result()
                        progress.advance(task)
            else:
                # Sequential generation
                pos_task = progress.add_task(
                    "[green]Generating CUI positive documents...",
                    total=cui_positive_count,
                )
                for i in range(1, cui_positive_count + 1):
                    self.generate_single_cui_positive(i)
                    progress.advance(pos_task)

                neg_task = progress.add_task(
                    "[blue]Generating CUI negative documents...",
                    total=cui_negative_count,
                )
                for i in range(1, cui_negative_count + 1):
                    self.generate_single_cui_negative(i)
                    progress.advance(neg_task)

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


def display_cui_stats(stats: dict, output_dir: str, duration: float):
    """Display CUI generation statistics in a formatted table"""

    # Summary panel
    summary = f"""[bold]Total CUI Documents:[/bold] {stats['total_generated']}
[green]CUI Positive:[/green] {stats['cui_positive']}
[blue]CUI Negative:[/blue] {stats['cui_negative']}
[yellow]Duration:[/yellow] {duration:.2f}s
[yellow]Avg Time:[/yellow] {duration / max(stats['total_generated'], 1):.2f}s per document"""

    console.print(Panel(summary, title="[bold]CUI Generation Summary[/bold]", border_style="cyan"))

    # Generation method table (if LLM was used)
    llm_enhanced = stats.get("llm_enhanced", 0)
    template_based = stats.get("template_based", 0)

    if llm_enhanced > 0 or template_based > 0:
        method_table = Table(title="Generation Method", box=box.ROUNDED)
        method_table.add_column("Method", style="cyan")
        method_table.add_column("Count", justify="right", style="magenta")
        method_table.add_column("Percentage", justify="right", style="yellow")

        total = llm_enhanced + template_based
        if llm_enhanced > 0:
            llm_pct = (llm_enhanced / total) * 100
            method_table.add_row("LLM Enhanced", str(llm_enhanced), f"{llm_pct:.1f}%")

        if template_based > 0:
            template_pct = (template_based / total) * 100
            method_table.add_row("Template Based", str(template_based), f"{template_pct:.1f}%")

        console.print(method_table)

    # Category distribution table
    if stats.get("by_category"):
        category_table = Table(title="CUI Category Distribution", box=box.ROUNDED)
        category_table.add_column("Category", style="cyan")
        category_table.add_column("Count", justify="right", style="magenta")
        category_table.add_column("Percentage", justify="right", style="yellow")

        for category, count in sorted(stats["by_category"].items()):
            pct = (count / stats["total_generated"]) * 100 if stats["total_generated"] > 0 else 0
            display_name = CUI_CATEGORY_DISPLAY_NAMES.get(category, category.replace("_", " ").title())
            category_table.add_row(display_name, str(count), f"{pct:.1f}%")

        console.print(category_table)

    # Format distribution table
    if stats.get("by_format"):
        format_table = Table(title="Format Distribution", box=box.ROUNDED)
        format_table.add_column("Format", style="cyan")
        format_table.add_column("Count", justify="right", style="magenta")
        format_table.add_column("Percentage", justify="right", style="yellow")

        for fmt, count in sorted(stats["by_format"].items()):
            pct = (count / stats["total_generated"]) * 100 if stats["total_generated"] > 0 else 0
            format_table.add_row(fmt.upper(), str(count), f"{pct:.1f}%")

        console.print(format_table)

    # Errors if any
    if stats.get("errors"):
        error_panel = "\n".join(stats["errors"][:10])  # Show first 10 errors
        console.print(Panel(error_panel, title="[bold red]Errors[/bold red]", border_style="red"))


@app.command()
def generate(
    count: int = typer.Option(200, "--count", "-c", help="Total number of PHI documents to generate"),
    phi_positive: Optional[int] = typer.Option(None, "--phi-positive", help="Number of PHI positive documents"),
    phi_negative: Optional[int] = typer.Option(None, "--phi-negative", help="Number of PHI negative documents"),
    # CUI options
    cui_positive: Optional[int] = typer.Option(None, "--cui-positive", help="Number of CUI positive documents"),
    cui_negative: Optional[int] = typer.Option(None, "--cui-negative", help="Number of CUI negative documents"),
    cui_categories: Optional[str] = typer.Option(None, "--cui-categories", help="Comma-separated CUI categories: financial,legal,tax,procurement,proprietary,law_enforcement,critical_infrastructure"),
    cui_all: bool = typer.Option(False, "--cui-all", help="Generate all CUI categories"),
    cui_notice: str = typer.Option("random", "--cui-notice", help="CUI confidentiality notice: random (default), always, never"),
    cui_classification: str = typer.Option("never", "--cui-classification", help="CUI classification headers: always, never (default)"),
    # General options
    formats: str = typer.Option("pdf,docx,xlsx,eml,pptx", "--formats", "-f", help="Comma-separated list of formats"),
    output: str = typer.Option("output", "--output", "-o", help="Output directory"),
    llm_percentage: float = typer.Option(0.2, "--llm-percentage", help="Percentage of LLM-enhanced docs (0.0-1.0)"),
    template_email_ratio: float = typer.Option(0.8, "--template-email-ratio", help="Fraction of customer templates wrapped in email (0.0=all bare, 1.0=all email)"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Random seed for reproducibility"),
    parallel_workers: int = typer.Option(1, "--parallel-workers", "-p", help="Number of parallel workers"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to YAML config file"),
):
    """
    Generate synthetic PHI and/or CUI documents in multiple formats

    Examples:

        # PHI only (default)
        medforge generate --count 100

        medforge generate --phi-positive 80 --phi-negative 20

        # CUI only
        medforge generate --cui-positive 100 --cui-negative 50

        # Specific CUI categories
        medforge generate --cui-positive 100 --cui-categories financial,tax,legal

        # All CUI categories
        medforge generate --cui-positive 200 --cui-all

        # Mixed PHI + CUI
        medforge generate --phi-positive 100 --cui-positive 100 --cui-all

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
        cui_positive = cfg.get("cui_positive", cui_positive)
        cui_negative = cfg.get("cui_negative", cui_negative)
        cui_categories = cfg.get("cui_categories", cui_categories)
        cui_all = cfg.get("cui_all", cui_all)
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

    # Determine what to generate
    generate_phi = phi_positive is not None or phi_negative is not None or (cui_positive is None and cui_negative is None)
    generate_cui = cui_positive is not None or cui_negative is not None or cui_all

    # Calculate PHI positive/negative split (if generating PHI)
    if generate_phi:
        if phi_positive is None and phi_negative is None:
            # Default 80/20 split
            phi_positive = int(count * 0.8)
            phi_negative = count - phi_positive
        elif phi_positive is None:
            phi_positive = max(0, count - (phi_negative or 0))
        elif phi_negative is None:
            phi_negative = max(0, count - (phi_positive or 0))
    else:
        phi_positive = 0
        phi_negative = 0

    # Calculate CUI positive/negative split (if generating CUI)
    if generate_cui:
        if cui_positive is None and cui_negative is None:
            # Default 80/20 split for CUI if --cui-all specified
            cui_count = 100 if cui_all else 0
            cui_positive = int(cui_count * 0.8)
            cui_negative = cui_count - cui_positive
        elif cui_positive is None:
            cui_positive = 0
        elif cui_negative is None:
            # Don't auto-generate negatives unless explicitly requested
            cui_negative = 0
    else:
        cui_positive = 0
        cui_negative = 0

    # Parse CUI categories
    selected_categories = None
    if generate_cui:
        if cui_all:
            selected_categories = CUI_CATEGORIES
        elif cui_categories:
            selected_categories = [c.strip().lower() for c in cui_categories.split(",")]
            invalid_categories = set(selected_categories) - set(CUI_CATEGORIES)
            if invalid_categories:
                console.print(f"[red]Invalid CUI categories: {', '.join(invalid_categories)}[/red]")
                console.print(f"[yellow]Valid categories: {', '.join(CUI_CATEGORIES)}[/yellow]")
                raise typer.Exit(1)
        else:
            selected_categories = CUI_CATEGORIES  # Default to all

    # Validate parameters
    if llm_percentage < 0 or llm_percentage > 1:
        console.print("[red]Error: --llm-percentage must be between 0.0 and 1.0[/red]")
        raise typer.Exit(1)

    # Check LLM configuration when llm_percentage > 0
    if llm_percentage > 0 and not is_llm_available():
        console.print("[red]Error: --llm-percentage is set but ANTHROPIC_API_KEY is not configured.[/red]")
        console.print("[yellow]To fix this, either:[/yellow]")
        console.print("  1. Set ANTHROPIC_API_KEY in your .env file")
        console.print("  2. Export ANTHROPIC_API_KEY in your shell")
        console.print("  3. Use --llm-percentage 0 to disable LLM enhancement")
        raise typer.Exit(1)

    if parallel_workers < 1:
        console.print("[red]Error: --parallel-workers must be at least 1[/red]")
        raise typer.Exit(1)

    # Display configuration
    config_table = Table(title="Configuration", box=box.ROUNDED, show_header=False)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="yellow")

    total_docs = phi_positive + phi_negative + cui_positive + cui_negative
    config_table.add_row("Total Documents", str(total_docs))

    if generate_phi:
        config_table.add_row("PHI Positive", str(phi_positive))
        config_table.add_row("PHI Negative", str(phi_negative))

    if generate_cui:
        config_table.add_row("CUI Positive", str(cui_positive))
        config_table.add_row("CUI Negative", str(cui_negative))
        config_table.add_row("CUI Categories", ", ".join(selected_categories) if selected_categories else "All")

    config_table.add_row("Formats", ", ".join(format_list))
    if generate_phi or generate_cui:
        config_table.add_row("LLM Enhancement", f"{int(llm_percentage * 100)}%")
        config_table.add_row("LLM Available", "Yes" if is_llm_available() else "No (using templates)")
    config_table.add_row("Random Seed", str(seed) if seed else "Random")
    config_table.add_row("Parallel Workers", str(parallel_workers))
    config_table.add_row("Output Directory", output)

    console.print(config_table)
    console.print()

    # Initialize generators and generate documents
    start_time = datetime.now()

    # Create timestamped production run folder
    run_dir = create_production_run_folder(output)
    console.print(f"[bold green]Output folder:[/bold green] {run_dir}\n")

    try:
        all_stats = {"phi": None, "cui": None}

        # Generate PHI documents
        if generate_phi and (phi_positive > 0 or phi_negative > 0):
            console.print("[bold cyan]Generating PHI documents...[/bold cyan]\n")
            phi_generator = MedForgeGenerator(
                output_dir=str(run_dir),
                seed=seed,
                llm_percentage=llm_percentage,
                formats=format_list,
            )
            all_stats["phi"] = phi_generator.generate_batch(
                phi_positive_count=phi_positive,
                phi_negative_count=phi_negative,
                parallel_workers=parallel_workers,
            )

        # Generate CUI documents
        if generate_cui and (cui_positive > 0 or cui_negative > 0):
            console.print("\n[bold cyan]Generating CUI documents...[/bold cyan]\n")
            cui_generator = MedForgeCUIGenerator(
                output_dir=str(run_dir),
                seed=seed,
                categories=selected_categories,
                formats=format_list,
                llm_percentage=llm_percentage,
                cui_notice=cui_notice,
                cui_classification=cui_classification,
                template_email_ratio=template_email_ratio,
            )
            all_stats["cui"] = cui_generator.generate_batch(
                cui_positive_count=cui_positive,
                cui_negative_count=cui_negative,
                parallel_workers=parallel_workers,
            )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Display statistics
        console.print()

        if all_stats["phi"]:
            console.print("[bold green]PHI Generation Results:[/bold green]")
            display_stats(all_stats["phi"], output, duration if not all_stats["cui"] else duration / 2)

        if all_stats["cui"]:
            console.print("\n[bold green]CUI Generation Results:[/bold green]")
            display_cui_stats(all_stats["cui"], output, duration if not all_stats["phi"] else duration / 2)

        console.print("\n[bold green]Generation complete![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]Error during generation:[/bold red] {str(e)}")
        import traceback
        traceback.print_exc()
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
def setup(
    check: bool = typer.Option(False, "--check", "-c", help="Check current environment and configuration status"),
    prompt: bool = typer.Option(False, "--prompt", "-p", help="Interactively configure missing settings"),
    show_example: bool = typer.Option(False, "--example", "-e", help="Show example YAML config file for --config flag"),
):
    """
    Set up and verify MedForge environment (API keys, .env file)

    Examples:

        medforge setup --check

        medforge setup --prompt

        medforge setup --example
    """
    from pathlib import Path
    import os

    display_banner()

    if not check and not prompt and not show_example:
        # Default to --check if no option specified
        check = True

    if show_example:
        example_yaml = """# MedForge Configuration File
# Save as medforge_config.yaml and use with: medforge generate --config medforge_config.yaml

# Document counts (use either 'count' for total, or specific positive/negative counts)
# count: 100  # Total documents (80% positive, 20% negative split)
phi_positive: 80          # Number of PHI positive documents
phi_negative: 20          # Number of PHI negative documents
cui_positive: 0           # Number of CUI positive documents
cui_negative: 0           # Number of CUI negative documents

# CUI options
cui_all: false            # Generate all CUI categories
cui_categories: null      # Or specify: "financial,legal,tax,procurement"

# Output settings
output: "output"          # Base output directory (creates production_run_TIMESTAMP inside)
formats: "pdf,docx,xlsx,eml,pptx"  # Comma-separated formats

# LLM settings (requires ANTHROPIC_API_KEY in .env or environment)
llm_percentage: 0.2       # Percentage of docs to enhance with LLM (0.0-1.0)

# Other settings
seed: null                # Random seed for reproducibility (null = random)
parallel_workers: 1       # Number of parallel workers
"""
        console.print(Panel(example_yaml, title="Example YAML Config", border_style="cyan"))
        return

    if check:
        console.print("\n[bold cyan]Configuration Check[/bold cyan]\n")

        # Check .env file
        env_file = Path(".env")
        env_exists = env_file.exists()

        config_table = Table(box=box.ROUNDED, show_header=True)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Status", style="bold")
        config_table.add_column("Details")

        # .env file check
        if env_exists:
            config_table.add_row(
                ".env file",
                "[green]✓ Found[/green]",
                str(env_file.absolute())
            )
        else:
            config_table.add_row(
                ".env file",
                "[yellow]⚠ Not found[/yellow]",
                "Create .env in project root"
            )

        # ANTHROPIC_API_KEY check
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            # Mask the key for display
            masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            config_table.add_row(
                "ANTHROPIC_API_KEY",
                "[green]✓ Set[/green]",
                f"Value: {masked}"
            )
        else:
            config_table.add_row(
                "ANTHROPIC_API_KEY",
                "[red]✗ Not set[/red]",
                "Required for LLM enhancement"
            )

        # LLM availability check
        if is_llm_available():
            try:
                from generators.llm_generator import ClaudeGenerator
                gen = ClaudeGenerator()
                config_table.add_row(
                    "LLM Generator",
                    "[green]✓ Ready[/green]",
                    f"Model: {gen.model}"
                )
            except Exception as e:
                config_table.add_row(
                    "LLM Generator",
                    "[red]✗ Error[/red]",
                    str(e)[:50]
                )
        else:
            config_table.add_row(
                "LLM Generator",
                "[yellow]⚠ Disabled[/yellow]",
                "Set ANTHROPIC_API_KEY to enable"
            )

        # Check for config file in current directory
        yaml_configs = list(Path(".").glob("*.yaml")) + list(Path(".").glob("*.yml"))
        medforge_configs = [f for f in yaml_configs if "medforge" in f.name.lower() or "config" in f.name.lower()]
        if medforge_configs:
            config_table.add_row(
                "YAML Config",
                "[green]✓ Found[/green]",
                ", ".join(str(f) for f in medforge_configs[:3])
            )
        else:
            config_table.add_row(
                "YAML Config",
                "[dim]○ Optional[/dim]",
                "Use --config flag or medforge setup --example"
            )

        console.print(config_table)

        # Summary
        console.print()
        if api_key and is_llm_available():
            console.print("[green]✓ Configuration is complete. LLM enhancement is available.[/green]")
        elif not api_key:
            console.print("[yellow]⚠ LLM enhancement disabled. Run 'medforge setup --prompt' to configure.[/yellow]")

    if prompt:
        console.print("\n[bold cyan]Interactive Configuration[/bold cyan]\n")

        env_file = Path(".env")
        env_content = {}

        # Read existing .env if it exists
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key.strip()] = value.strip()

        # Check ANTHROPIC_API_KEY
        current_key = os.getenv('ANTHROPIC_API_KEY') or env_content.get('ANTHROPIC_API_KEY', '')

        if current_key:
            masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
            console.print(f"[green]ANTHROPIC_API_KEY is already set:[/green] {masked}")
            update = typer.confirm("Do you want to update it?", default=False)
            if not update:
                console.print("[dim]Keeping existing API key.[/dim]")
                return
        else:
            console.print("[yellow]ANTHROPIC_API_KEY is not set.[/yellow]")

        # Prompt for API key
        console.print("\nGet your API key from: [link=https://console.anthropic.com/]https://console.anthropic.com/[/link]")
        new_key = typer.prompt("Enter your Anthropic API key", hide_input=True)

        if new_key:
            env_content['ANTHROPIC_API_KEY'] = new_key

            # Write to .env
            with open(env_file, "w") as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")

            console.print(f"\n[green]✓ Saved ANTHROPIC_API_KEY to {env_file.absolute()}[/green]")
            console.print("[yellow]Note: Restart your terminal or run 'source .env' to apply changes.[/yellow]")

            # Test the connection
            console.print("\n[dim]Testing API connection...[/dim]")
            os.environ['ANTHROPIC_API_KEY'] = new_key
            try:
                from generators.llm_generator import ClaudeGenerator
                gen = ClaudeGenerator()
                console.print(f"[green]✓ Successfully connected! Using model: {gen.model}[/green]")
            except Exception as e:
                console.print(f"[red]✗ Connection failed: {e}[/red]")
                console.print("[yellow]Please verify your API key is correct.[/yellow]")


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
