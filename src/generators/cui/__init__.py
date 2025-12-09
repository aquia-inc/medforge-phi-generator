"""
CUI (Controlled Unclassified Information) generators.

This package provides generators for creating synthetic CUI documents
across various categories like financial, legal, procurement, etc.

All generated data is synthetic using Faker - no real CUI data is used.

Usage:
    from src.generators.cui import CUIGeneratorFactory

    # Get a specific category generator
    generator = CUIGeneratorFactory.get_generator('financial')
    doc = generator.generate_positive()

    # Get a composite generator for multiple categories
    composite = CUIGeneratorFactory.create_composite_generator(
        categories=['financial', 'legal', 'procurement']
    )
    docs = composite.generate_batch(positive_count=100, negative_count=50)

Available Categories:
    - critical_infrastructure: Emergency mgmt, vulnerability, physical security
    - financial: Budget, bank secrecy, EFT, retirement
    - law_enforcement: Criminal history, investigation
    - legal: Privilege, collective bargaining, legislative, administrative
    - procurement: Source selection, small business research
    - proprietary: Entity registration, proprietary business info
    - tax: Federal taxpayer info, written determinations
"""

from .base import BaseCUIGenerator
from .factory import CUIGeneratorFactory, CompositeCUIGenerator

# Import all generators to trigger registration
from .critical_infrastructure_generator import CriticalInfrastructureCUIGenerator
from .financial_generator import FinancialCUIGenerator
from .law_enforcement_generator import LawEnforcementCUIGenerator
from .legal_generator import LegalCUIGenerator
from .procurement_generator import ProcurementCUIGenerator
from .proprietary_generator import ProprietaryCUIGenerator
from .tax_generator import TaxCUIGenerator

__all__ = [
    'BaseCUIGenerator',
    'CUIGeneratorFactory',
    'CompositeCUIGenerator',
    'CriticalInfrastructureCUIGenerator',
    'FinancialCUIGenerator',
    'LawEnforcementCUIGenerator',
    'LegalCUIGenerator',
    'ProcurementCUIGenerator',
    'ProprietaryCUIGenerator',
    'TaxCUIGenerator',
]
