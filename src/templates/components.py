"""
Template Component Mixing System for Synthetic PHI Data Generation

This module provides a flexible component-based system for generating diverse document layouts.
By mixing different headers, layouts, section orders, and styles, it can produce 240+ unique
document variations (5 headers × 3 layouts × 4 section orders × 4 styles = 240 combinations).
"""

import random
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


class HeaderVariant(Enum):
    """Header style variations for document letterheads."""
    CENTERED_LOGO = "centered_logo"
    LEFT_ALIGNED = "left_aligned"
    TWO_COLUMN = "two_column"
    MINIMAL = "minimal"
    FULL_WIDTH_BANNER = "full_width_banner"


class LayoutVariant(Enum):
    """Document layout types."""
    TABLE_BASED = "table_based"
    FORM_BASED = "form_based"
    NARRATIVE_BASED = "narrative_based"


class SectionOrderVariant(Enum):
    """Section ordering patterns."""
    STANDARD = "standard"
    CLINICAL_FIRST = "clinical_first"
    DEMOGRAPHIC_LAST = "demographic_last"
    ALTERNATING = "alternating"


class StyleVariant(Enum):
    """Visual style variations."""
    PROFESSIONAL = "professional"
    MINIMAL = "minimal"
    FORMAL = "formal"
    CLINICAL = "clinical"


@dataclass
class HeaderComponent:
    """Header component with different letterhead styles."""

    variant: HeaderVariant

    @staticmethod
    def get_all_variants() -> List[HeaderVariant]:
        """Return all available header variants."""
        return list(HeaderVariant)

    def get_config(self) -> Dict[str, Any]:
        """Return configuration dictionary for this header variant."""
        configs = {
            HeaderVariant.CENTERED_LOGO: {
                "alignment": "center",
                "logo_position": "top_center",
                "hospital_name_style": "bold_large",
                "address_style": "small_centered",
                "border": "none",
                "spacing_after": 20,
                "include_logo": True,
                "logo_size": (80, 80),
            },
            HeaderVariant.LEFT_ALIGNED: {
                "alignment": "left",
                "logo_position": "top_left",
                "hospital_name_style": "bold_medium",
                "address_style": "regular_left",
                "border": "bottom_line",
                "spacing_after": 15,
                "include_logo": True,
                "logo_size": (60, 60),
            },
            HeaderVariant.TWO_COLUMN: {
                "alignment": "split",
                "logo_position": "left_column",
                "hospital_name_style": "bold_medium",
                "address_style": "right_column",
                "border": "full_bottom",
                "spacing_after": 15,
                "include_logo": True,
                "logo_size": (70, 70),
            },
            HeaderVariant.MINIMAL: {
                "alignment": "left",
                "logo_position": None,
                "hospital_name_style": "regular_small",
                "address_style": "inline",
                "border": "none",
                "spacing_after": 10,
                "include_logo": False,
                "logo_size": None,
            },
            HeaderVariant.FULL_WIDTH_BANNER: {
                "alignment": "center",
                "logo_position": "left_banner",
                "hospital_name_style": "bold_large_white",
                "address_style": "banner_right",
                "border": "colored_background",
                "spacing_after": 20,
                "include_logo": True,
                "logo_size": (50, 50),
                "background_color": "#2C3E50",
                "text_color": "#FFFFFF",
            },
        }
        return configs[self.variant]


@dataclass
class LayoutComponent:
    """Layout component defining document structure."""

    variant: LayoutVariant

    @staticmethod
    def get_all_variants() -> List[LayoutVariant]:
        """Return all available layout variants."""
        return list(LayoutVariant)

    def get_config(self) -> Dict[str, Any]:
        """Return configuration dictionary for this layout variant."""
        configs = {
            LayoutVariant.TABLE_BASED: {
                "structure": "table",
                "use_tables": True,
                "table_style": "grid",
                "label_column_width": 0.3,
                "value_column_width": 0.7,
                "table_borders": True,
                "alternate_row_colors": True,
                "cell_padding": 8,
                "header_background": "#E8E8E8",
            },
            LayoutVariant.FORM_BASED: {
                "structure": "form",
                "use_tables": False,
                "label_style": "bold_with_colon",
                "value_style": "inline",
                "field_spacing": 10,
                "section_boxes": True,
                "box_border_width": 1,
                "use_fill_lines": True,
            },
            LayoutVariant.NARRATIVE_BASED: {
                "structure": "narrative",
                "use_tables": False,
                "paragraph_style": True,
                "section_headers": "underlined",
                "indentation": 20,
                "line_spacing": 1.5,
                "use_bullet_points": False,
                "flowing_text": True,
            },
        }
        return configs[self.variant]


@dataclass
class SectionOrderComponent:
    """Section ordering component defining content flow."""

    variant: SectionOrderVariant

    @staticmethod
    def get_all_variants() -> List[SectionOrderVariant]:
        """Return all available section order variants."""
        return list(SectionOrderVariant)

    def get_config(self) -> Dict[str, Any]:
        """Return configuration dictionary for this section order variant."""
        configs = {
            SectionOrderVariant.STANDARD: {
                "order": [
                    "patient_demographics",
                    "visit_information",
                    "chief_complaint",
                    "vital_signs",
                    "medical_history",
                    "physical_examination",
                    "assessment",
                    "plan",
                    "medications",
                    "follow_up",
                ],
                "description": "Standard medical record flow",
            },
            SectionOrderVariant.CLINICAL_FIRST: {
                "order": [
                    "chief_complaint",
                    "vital_signs",
                    "physical_examination",
                    "assessment",
                    "plan",
                    "patient_demographics",
                    "visit_information",
                    "medical_history",
                    "medications",
                    "follow_up",
                ],
                "description": "Clinical information prioritized first",
            },
            SectionOrderVariant.DEMOGRAPHIC_LAST: {
                "order": [
                    "visit_information",
                    "chief_complaint",
                    "medical_history",
                    "vital_signs",
                    "physical_examination",
                    "medications",
                    "assessment",
                    "plan",
                    "follow_up",
                    "patient_demographics",
                ],
                "description": "Demographics at the end",
            },
            SectionOrderVariant.ALTERNATING: {
                "order": [
                    "patient_demographics",
                    "chief_complaint",
                    "visit_information",
                    "vital_signs",
                    "medical_history",
                    "assessment",
                    "physical_examination",
                    "medications",
                    "plan",
                    "follow_up",
                ],
                "description": "Alternating between admin and clinical sections",
            },
        }
        return configs[self.variant]


@dataclass
class StyleComponent:
    """Visual style component defining appearance."""

    variant: StyleVariant

    @staticmethod
    def get_all_variants() -> List[StyleVariant]:
        """Return all available style variants."""
        return list(StyleVariant)

    def get_config(self) -> Dict[str, Any]:
        """Return configuration dictionary for this style variant."""
        configs = {
            StyleVariant.PROFESSIONAL: {
                "font_family": "Helvetica",
                "font_size_body": 11,
                "font_size_header": 14,
                "font_size_title": 16,
                "color_primary": "#2C3E50",
                "color_secondary": "#34495E",
                "color_accent": "#3498DB",
                "line_height": 1.4,
                "section_spacing": 15,
                "use_colors": True,
                "border_style": "solid",
            },
            StyleVariant.MINIMAL: {
                "font_family": "Arial",
                "font_size_body": 10,
                "font_size_header": 12,
                "font_size_title": 14,
                "color_primary": "#000000",
                "color_secondary": "#333333",
                "color_accent": "#666666",
                "line_height": 1.2,
                "section_spacing": 10,
                "use_colors": False,
                "border_style": "none",
            },
            StyleVariant.FORMAL: {
                "font_family": "Times-Roman",
                "font_size_body": 12,
                "font_size_header": 14,
                "font_size_title": 18,
                "color_primary": "#000000",
                "color_secondary": "#1A1A1A",
                "color_accent": "#4A4A4A",
                "line_height": 1.6,
                "section_spacing": 18,
                "use_colors": False,
                "border_style": "double",
            },
            StyleVariant.CLINICAL: {
                "font_family": "Courier",
                "font_size_body": 10,
                "font_size_header": 12,
                "font_size_title": 14,
                "color_primary": "#000080",
                "color_secondary": "#000060",
                "color_accent": "#0000A0",
                "line_height": 1.3,
                "section_spacing": 12,
                "use_colors": True,
                "border_style": "solid",
                "monospace": True,
            },
        }
        return configs[self.variant]


@dataclass
class ComponentConfiguration:
    """Complete component configuration for a document."""

    header: HeaderComponent
    layout: LayoutComponent
    section_order: SectionOrderComponent
    style: StyleComponent
    seed: Optional[int] = None

    def get_combination_id(self) -> str:
        """Return unique identifier for this component combination."""
        return f"{self.header.variant.value}_{self.layout.variant.value}_{self.section_order.variant.value}_{self.style.variant.value}"

    def get_full_config(self) -> Dict[str, Any]:
        """Return complete configuration dictionary merging all components."""
        return {
            "header": self.header.get_config(),
            "layout": self.layout.get_config(),
            "section_order": self.section_order.get_config(),
            "style": self.style.get_config(),
            "combination_id": self.get_combination_id(),
            "seed": self.seed,
        }


class ComponentMixer:
    """
    Mixes components to create unique document configurations.

    Ensures no duplicate combinations within a batch and provides
    random selection based on seed for reproducibility.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the component mixer.

        Args:
            seed: Random seed for reproducible component selection
        """
        self.seed = seed
        self.rng = random.Random(seed)
        self.used_combinations: Set[str] = set()
        self.total_combinations = self._calculate_total_combinations()

    def _calculate_total_combinations(self) -> int:
        """Calculate total number of possible component combinations."""
        return (
            len(HeaderComponent.get_all_variants()) *
            len(LayoutComponent.get_all_variants()) *
            len(SectionOrderComponent.get_all_variants()) *
            len(StyleComponent.get_all_variants())
        )

    def get_random_configuration(
        self,
        avoid_duplicates: bool = True,
        force_variant: Optional[Dict[str, Any]] = None
    ) -> ComponentConfiguration:
        """
        Generate a random component configuration.

        Args:
            avoid_duplicates: If True, ensure this combination hasn't been used yet
            force_variant: Optional dict to force specific variants, e.g.,
                          {"header": HeaderVariant.CENTERED_LOGO}

        Returns:
            ComponentConfiguration with randomly selected components

        Raises:
            ValueError: If all combinations have been exhausted
        """
        if avoid_duplicates and len(self.used_combinations) >= self.total_combinations:
            raise ValueError(
                f"All {self.total_combinations} combinations have been used. "
                "Set avoid_duplicates=False to allow reuse."
            )

        max_attempts = 1000
        attempts = 0

        while attempts < max_attempts:
            # Select components
            header_variant = (
                force_variant.get("header") if force_variant and "header" in force_variant
                else self.rng.choice(HeaderComponent.get_all_variants())
            )
            layout_variant = (
                force_variant.get("layout") if force_variant and "layout" in force_variant
                else self.rng.choice(LayoutComponent.get_all_variants())
            )
            section_order_variant = (
                force_variant.get("section_order") if force_variant and "section_order" in force_variant
                else self.rng.choice(SectionOrderComponent.get_all_variants())
            )
            style_variant = (
                force_variant.get("style") if force_variant and "style" in force_variant
                else self.rng.choice(StyleComponent.get_all_variants())
            )

            # Create configuration
            config = ComponentConfiguration(
                header=HeaderComponent(header_variant),
                layout=LayoutComponent(layout_variant),
                section_order=SectionOrderComponent(section_order_variant),
                style=StyleComponent(style_variant),
                seed=self.seed,
            )

            combination_id = config.get_combination_id()

            # Check if this combination is new
            if not avoid_duplicates or combination_id not in self.used_combinations:
                if avoid_duplicates:
                    self.used_combinations.add(combination_id)
                return config

            attempts += 1

        raise ValueError(
            f"Could not find unique combination after {max_attempts} attempts. "
            f"{len(self.used_combinations)}/{self.total_combinations} combinations used."
        )

    def get_all_configurations(self) -> List[ComponentConfiguration]:
        """
        Generate all possible component configurations.

        Returns:
            List of all 240 possible component configurations
        """
        configurations = []

        for header_variant in HeaderComponent.get_all_variants():
            for layout_variant in LayoutComponent.get_all_variants():
                for section_order_variant in SectionOrderComponent.get_all_variants():
                    for style_variant in StyleComponent.get_all_variants():
                        config = ComponentConfiguration(
                            header=HeaderComponent(header_variant),
                            layout=LayoutComponent(layout_variant),
                            section_order=SectionOrderComponent(section_order_variant),
                            style=StyleComponent(style_variant),
                            seed=self.seed,
                        )
                        configurations.append(config)

        return configurations

    def get_batch_configurations(
        self,
        batch_size: int,
        avoid_duplicates: bool = True
    ) -> List[ComponentConfiguration]:
        """
        Generate a batch of component configurations.

        Args:
            batch_size: Number of configurations to generate
            avoid_duplicates: If True, ensure unique combinations in batch

        Returns:
            List of component configurations
        """
        configurations = []
        for _ in range(batch_size):
            config = self.get_random_configuration(avoid_duplicates=avoid_duplicates)
            configurations.append(config)
        return configurations

    def reset(self):
        """Reset the used combinations tracker."""
        self.used_combinations.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about component usage.

        Returns:
            Dictionary with usage statistics
        """
        return {
            "total_combinations": self.total_combinations,
            "used_combinations": len(self.used_combinations),
            "remaining_combinations": self.total_combinations - len(self.used_combinations),
            "usage_percentage": (len(self.used_combinations) / self.total_combinations) * 100,
            "seed": self.seed,
        }


# Integration Helper Functions

def apply_header_style(doc: Any, header_variant: HeaderComponent) -> None:
    """
    Apply header style to a document.

    Args:
        doc: Document object (e.g., ReportLab canvas or similar)
        header_variant: HeaderComponent instance with style configuration
    """
    config = header_variant.get_config()

    # This is a template function - actual implementation depends on your document library
    # Example pseudo-code:
    # if config["include_logo"] and config["logo_position"]:
    #     doc.add_logo(position=config["logo_position"], size=config["logo_size"])
    #
    # if config["alignment"] == "center":
    #     doc.add_centered_text(hospital_name, style=config["hospital_name_style"])
    # elif config["alignment"] == "left":
    #     doc.add_left_aligned_text(hospital_name, style=config["hospital_name_style"])
    #
    # if config["border"] != "none":
    #     doc.add_border(style=config["border"])

    pass


def apply_layout(doc: Any, layout_variant: LayoutComponent, content: Dict[str, Any]) -> None:
    """
    Apply layout structure to document content.

    Args:
        doc: Document object
        layout_variant: LayoutComponent instance with layout configuration
        content: Content dictionary with section data
    """
    config = layout_variant.get_config()

    # Template function - implement based on your document library
    # Example pseudo-code:
    # if config["structure"] == "table":
    #     for section, data in content.items():
    #         doc.add_table(data, style=config["table_style"],
    #                      borders=config["table_borders"])
    #
    # elif config["structure"] == "form":
    #     for section, data in content.items():
    #         doc.add_form_section(data, label_style=config["label_style"])
    #
    # elif config["structure"] == "narrative":
    #     for section, data in content.items():
    #         doc.add_narrative_section(data, paragraph_style=True)

    pass


def apply_section_order(sections: Dict[str, Any], order_variant: SectionOrderComponent) -> List[Tuple[str, Any]]:
    """
    Reorder sections according to the order variant.

    Args:
        sections: Dictionary of section names to content
        order_variant: SectionOrderComponent instance with ordering configuration

    Returns:
        List of (section_name, content) tuples in the specified order
    """
    config = order_variant.get_config()
    order = config["order"]

    ordered_sections = []

    # Add sections in the specified order
    for section_name in order:
        if section_name in sections:
            ordered_sections.append((section_name, sections[section_name]))

    # Add any remaining sections not in the order list
    for section_name, content in sections.items():
        if section_name not in order:
            ordered_sections.append((section_name, content))

    return ordered_sections


def apply_visual_style(doc: Any, style_variant: StyleComponent) -> None:
    """
    Apply visual styling to the document.

    Args:
        doc: Document object
        style_variant: StyleComponent instance with style configuration
    """
    config = style_variant.get_config()

    # Template function - implement based on your document library
    # Example pseudo-code:
    # doc.set_font(config["font_family"])
    # doc.set_font_size(config["font_size_body"])
    # doc.set_line_height(config["line_height"])
    # doc.set_section_spacing(config["section_spacing"])
    #
    # if config["use_colors"]:
    #     doc.set_primary_color(config["color_primary"])
    #     doc.set_accent_color(config["color_accent"])

    pass


def create_document_from_configuration(
    config: ComponentConfiguration,
    content: Dict[str, Any],
    doc: Any
) -> Any:
    """
    Create a complete document using a component configuration.

    This is a convenience function that applies all components in sequence.

    Args:
        config: ComponentConfiguration instance
        content: Dictionary with document content
        doc: Document object to apply configuration to

    Returns:
        Configured document object
    """
    # Apply visual style first (sets base formatting)
    apply_visual_style(doc, config.style)

    # Apply header
    apply_header_style(doc, config.header)

    # Reorder sections
    ordered_sections = apply_section_order(content, config.section_order)
    ordered_content = dict(ordered_sections)

    # Apply layout
    apply_layout(doc, config.layout, ordered_content)

    return doc


# Example usage and testing
if __name__ == "__main__":
    # Initialize mixer with a seed for reproducibility
    mixer = ComponentMixer(seed=42)

    print("Component Mixing System Statistics:")
    print(f"Total possible combinations: {mixer.total_combinations}")
    print()

    # Generate a few random configurations
    print("Sample Random Configurations:")
    for i in range(5):
        config = mixer.get_random_configuration()
        print(f"\nConfiguration {i+1}:")
        print(f"  ID: {config.get_combination_id()}")
        print(f"  Header: {config.header.variant.value}")
        print(f"  Layout: {config.layout.variant.value}")
        print(f"  Section Order: {config.section_order.variant.value}")
        print(f"  Style: {config.style.variant.value}")

    print("\n" + "="*60)
    print("Usage Statistics:")
    stats = mixer.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "="*60)
    print("Sample Configuration Details:")
    sample_config = mixer.get_random_configuration()
    full_config = sample_config.get_full_config()
    print(f"\nCombination ID: {full_config['combination_id']}")
    print("\nHeader Config:")
    for key, value in full_config['header'].items():
        print(f"  {key}: {value}")
    print("\nLayout Config:")
    for key, value in full_config['layout'].items():
        print(f"  {key}: {value}")
    print("\nSection Order Config:")
    print(f"  Order: {full_config['section_order']['order']}")
    print("\nStyle Config:")
    for key, value in full_config['style'].items():
        print(f"  {key}: {value}")

    print("\n" + "="*60)
    print("Batch Generation Test:")
    mixer.reset()
    batch = mixer.get_batch_configurations(batch_size=10)
    print(f"Generated {len(batch)} unique configurations")
    print("Unique IDs:", len(set(c.get_combination_id() for c in batch)))
