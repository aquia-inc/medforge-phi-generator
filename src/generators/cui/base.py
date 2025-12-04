"""
Base CUI generator abstract class.

All CUI category generators inherit from this class.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from faker import Faker
from datetime import datetime, timedelta
import random
import json
import os


class BaseCUIGenerator(ABC):
    """
    Abstract base class for CUI document generators.

    Each CUI category (financial, legal, procurement, etc.) has its own
    generator that inherits from this class. All generated data is synthetic
    using Faker - no real CUI data should ever be stored or used.
    """

    # Class-level attributes to be overridden by subclasses
    CATEGORY: str = ""
    SUBCATEGORIES: List[str] = []
    CUI_MARKINGS: List[str] = []
    AUTHORITIES: List[str] = []

    # Path to reference data files
    DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'templates', 'cui', 'data')

    def __init__(self, locale: str = 'en_US', seed: Optional[int] = None):
        """
        Initialize the CUI generator.

        Args:
            locale: Faker locale for generating synthetic data
            seed: Random seed for reproducibility
        """
        self.fake = Faker(locale)
        self.locale = locale
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        # Load reference data
        self._authorities = self._load_json('authorities.json')
        self._markings = self._load_json('markings.json')
        self._agencies = self._load_json('agencies.json')
        self._document_types = self._load_json('document_types.json')
        self._field_definitions = self._load_json('field_definitions.json')

    def _load_json(self, filename: str) -> Dict:
        """Load a JSON reference data file."""
        filepath = os.path.join(self.DATA_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @abstractmethod
    def generate_positive(self) -> Dict[str, Any]:
        """
        Generate a CUI-positive document containing controlled information.

        Returns:
            Dictionary containing document data with CUI content
        """
        pass

    @abstractmethod
    def generate_negative(self) -> Dict[str, Any]:
        """
        Generate a CUI-negative document (no controlled information).

        These are documents that look similar to CUI documents but contain
        only public/non-sensitive information.

        Returns:
            Dictionary containing document data without CUI content
        """
        pass

    @abstractmethod
    def get_document_types(self) -> List[Dict[str, Any]]:
        """
        Get the list of document types this generator can produce.

        Returns:
            List of document type definitions from document_types.json
        """
        pass

    def generate(self, is_positive: bool = True) -> Dict[str, Any]:
        """
        Generate a document, either positive or negative.

        Args:
            is_positive: If True, generate CUI-positive document;
                        if False, generate CUI-negative document

        Returns:
            Generated document dictionary
        """
        if is_positive:
            return self.generate_positive()
        else:
            return self.generate_negative()

    def get_classification_header(self, subcategory: Optional[str] = None) -> str:
        """
        Get the formatted classification header for this CUI category.

        Args:
            subcategory: Optional subcategory for more specific marking

        Returns:
            Formatted classification header string
        """
        if subcategory:
            return f"CONTROLLED UNCLASSIFIED INFORMATION - {subcategory.upper().replace('_', ' ')}"
        return f"CONTROLLED UNCLASSIFIED INFORMATION - {self.CATEGORY.upper().replace('_', ' ')}"

    def get_marking(self, abbreviated: bool = False) -> str:
        """
        Get a random CUI marking appropriate for this category.

        Args:
            abbreviated: If True, return abbreviated marking (e.g., CUI//SP-BUDG)

        Returns:
            CUI marking string
        """
        category_markings = self._markings.get('banner_markings', {}).get(self.CATEGORY, {})
        if abbreviated:
            markings = category_markings.get('abbreviated', self.CUI_MARKINGS)
        else:
            markings = category_markings.get('category_specific', [self.get_classification_header()])

        return random.choice(markings) if markings else self.get_classification_header()

    def get_authority(self, subcategory: Optional[str] = None) -> str:
        """
        Get an appropriate authority reference for this CUI category.

        Args:
            subcategory: Optional subcategory for specific authority

        Returns:
            Authority reference string (e.g., CFR/FAR/USC reference)
        """
        category_authorities = self._authorities.get(self.CATEGORY, {})
        if subcategory and subcategory in category_authorities:
            authorities = category_authorities[subcategory]
        elif 'general' in category_authorities:
            authorities = category_authorities['general']
        else:
            # Flatten all subcategory authorities
            authorities = []
            for subcat_auths in category_authorities.values():
                if isinstance(subcat_auths, list):
                    authorities.extend(subcat_auths)

        return random.choice(authorities) if authorities else ""

    def get_distribution_statement(self) -> str:
        """Get a distribution statement for the document."""
        statements = self._markings.get('distribution_statements', {})
        return random.choice(list(statements.values())) if statements else ""

    def get_confidentiality_notice(self, notice_type: str = 'standard') -> str:
        """
        Get a confidentiality notice for the document.

        Args:
            notice_type: Type of notice (standard, budget, law_enforcement, etc.)

        Returns:
            Confidentiality notice string
        """
        notices = self._markings.get('confidentiality_notices', {})
        return notices.get(notice_type, notices.get('standard', ''))

    def get_agency(self, agency_type: str = 'cabinet_departments') -> str:
        """
        Get a random government agency name.

        Args:
            agency_type: Type of agency (cabinet_departments, independent_agencies, etc.)

        Returns:
            Agency name string
        """
        agencies = self._agencies.get(agency_type, [])
        return random.choice(agencies) if agencies else self.fake.company()

    def get_agency_title(self, title_type: str = 'executive') -> str:
        """
        Get a random government title.

        Args:
            title_type: Type of title (executive, management, legal, investigative)

        Returns:
            Title string
        """
        titles = self._agencies.get('titles', {}).get(title_type, [])
        return random.choice(titles) if titles else "Director"

    def generate_document_id(self) -> str:
        """Generate a unique document ID."""
        prefix = self.CATEGORY[:4].upper()
        return f"{prefix}_{self.fake.uuid4()[:8].upper()}"

    def generate_date_in_range(self, start_days: int = -730, end_days: int = 0) -> datetime:
        """
        Generate a random date within a range.

        Args:
            start_days: Days before today (negative) or after (positive)
            end_days: Days before today (negative) or after (positive)

        Returns:
            Random datetime within range
        """
        start_date = datetime.now() + timedelta(days=start_days)
        end_date = datetime.now() + timedelta(days=end_days)
        return self.fake.date_time_between(start_date=start_date, end_date=end_date)

    def generate_fiscal_year(self) -> int:
        """Generate a valid fiscal year."""
        return random.randint(2024, 2030)

    def generate_currency_amount(self, min_amt: int = 1000, max_amt: int = 10000000) -> float:
        """Generate a currency amount."""
        return round(random.uniform(min_amt, max_amt), 2)

    def format_currency(self, amount: float) -> str:
        """Format a currency amount."""
        return f"${amount:,.2f}"

    def _build_base_document(self, doc_type: str, subcategory: str, is_positive: bool) -> Dict[str, Any]:
        """
        Build the base document structure common to all CUI documents.

        Args:
            doc_type: Type of document being generated
            subcategory: Subcategory of CUI
            is_positive: Whether this is a CUI-positive document

        Returns:
            Base document dictionary
        """
        return {
            'document_id': self.generate_document_id(),
            'document_type': doc_type,
            'category': self.CATEGORY,
            'subcategory': subcategory,
            'has_cui': is_positive,
            'classification': self.get_marking() if is_positive else None,
            'authority': self.get_authority(subcategory) if is_positive else None,
            'distribution': self.get_distribution_statement() if is_positive else None,
            'generated_date': datetime.now().isoformat(),
            'document_date': self.generate_date_in_range().strftime('%B %d, %Y'),
            'agency': self.get_agency(),
        }
