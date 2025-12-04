"""
CUI Generator Factory with registry pattern.

Provides a central registry for all CUI category generators and
factory methods for creating them.
"""
from typing import Dict, List, Optional, Type, Any
import random

from .base import BaseCUIGenerator


class CUIGeneratorFactory:
    """
    Factory class for creating CUI generators.

    Uses a registry pattern where each generator class registers itself
    with a category name. This allows adding new CUI categories without
    modifying the factory.

    Usage:
        # Register a generator (typically done via decorator)
        @CUIGeneratorFactory.register('financial')
        class FinancialCUIGenerator(BaseCUIGenerator):
            ...

        # Create a generator
        generator = CUIGeneratorFactory.get_generator('financial')

        # Create a composite generator for multiple categories
        generator = CUIGeneratorFactory.create_composite_generator(
            categories=['financial', 'legal']
        )
    """

    _registry: Dict[str, Type[BaseCUIGenerator]] = {}

    @classmethod
    def register(cls, category: str):
        """
        Decorator to register a generator class for a CUI category.

        Args:
            category: The CUI category name (e.g., 'financial', 'legal')

        Returns:
            Decorator function

        Example:
            @CUIGeneratorFactory.register('financial')
            class FinancialCUIGenerator(BaseCUIGenerator):
                CATEGORY = 'financial'
                ...
        """
        def decorator(generator_class: Type[BaseCUIGenerator]):
            if not issubclass(generator_class, BaseCUIGenerator):
                raise TypeError(
                    f"Generator class must inherit from BaseCUIGenerator, "
                    f"got {generator_class.__name__}"
                )
            cls._registry[category] = generator_class
            return generator_class
        return decorator

    @classmethod
    def get_generator(
        cls,
        category: str,
        locale: str = 'en_US',
        seed: Optional[int] = None
    ) -> BaseCUIGenerator:
        """
        Get a generator instance for a specific CUI category.

        Args:
            category: The CUI category name
            locale: Faker locale for synthetic data generation
            seed: Random seed for reproducibility

        Returns:
            Instance of the appropriate CUI generator

        Raises:
            KeyError: If category is not registered
        """
        if category not in cls._registry:
            available = ', '.join(cls._registry.keys())
            raise KeyError(
                f"Unknown CUI category: '{category}'. "
                f"Available categories: {available}"
            )
        return cls._registry[category](locale=locale, seed=seed)

    @classmethod
    def get_all_categories(cls) -> List[str]:
        """
        Get a list of all registered CUI categories.

        Returns:
            List of category names
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, category: str) -> bool:
        """
        Check if a category is registered.

        Args:
            category: The CUI category name

        Returns:
            True if category is registered, False otherwise
        """
        return category in cls._registry

    @classmethod
    def create_composite_generator(
        cls,
        categories: Optional[List[str]] = None,
        locale: str = 'en_US',
        seed: Optional[int] = None
    ) -> 'CompositeCUIGenerator':
        """
        Create a generator that spans multiple CUI categories.

        Args:
            categories: List of category names to include.
                       If None, includes all registered categories.
            locale: Faker locale for synthetic data generation
            seed: Random seed for reproducibility

        Returns:
            CompositeCUIGenerator instance
        """
        if categories is None:
            categories = cls.get_all_categories()

        # Validate categories
        invalid = [c for c in categories if c not in cls._registry]
        if invalid:
            raise KeyError(f"Unknown CUI categories: {invalid}")

        generators = {
            category: cls.get_generator(category, locale, seed)
            for category in categories
        }

        return CompositeCUIGenerator(generators, seed=seed)


class CompositeCUIGenerator:
    """
    A generator that can produce documents from multiple CUI categories.

    This is useful when you want to generate a mixed dataset across
    several CUI categories while maintaining consistent distribution.
    """

    def __init__(
        self,
        generators: Dict[str, BaseCUIGenerator],
        weights: Optional[Dict[str, float]] = None,
        seed: Optional[int] = None
    ):
        """
        Initialize the composite generator.

        Args:
            generators: Dictionary mapping category names to generator instances
            weights: Optional dictionary of category weights for distribution.
                    If None, equal weights are used.
            seed: Random seed for reproducibility
        """
        self.generators = generators
        self.categories = list(generators.keys())

        if weights is None:
            # Equal weights
            self.weights = {cat: 1.0 for cat in self.categories}
        else:
            self.weights = weights

        if seed is not None:
            random.seed(seed)

    def generate_positive(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a CUI-positive document.

        Args:
            category: Specific category to generate from.
                     If None, randomly selects based on weights.

        Returns:
            Generated CUI-positive document
        """
        if category is None:
            category = self._select_category()
        return self.generators[category].generate_positive()

    def generate_negative(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a CUI-negative document.

        Args:
            category: Specific category to generate from.
                     If None, randomly selects based on weights.

        Returns:
            Generated CUI-negative document
        """
        if category is None:
            category = self._select_category()
        return self.generators[category].generate_negative()

    def generate(self, is_positive: bool = True, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a document, either positive or negative.

        Args:
            is_positive: If True, generate CUI-positive document
            category: Specific category to generate from

        Returns:
            Generated document
        """
        if is_positive:
            return self.generate_positive(category)
        else:
            return self.generate_negative(category)

    def generate_batch(
        self,
        positive_count: int,
        negative_count: int,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of documents.

        Args:
            positive_count: Number of CUI-positive documents
            negative_count: Number of CUI-negative documents
            category: Specific category to generate from (optional)

        Returns:
            List of generated documents
        """
        documents = []

        for _ in range(positive_count):
            documents.append(self.generate_positive(category))

        for _ in range(negative_count):
            documents.append(self.generate_negative(category))

        # Shuffle to mix positive and negative
        random.shuffle(documents)
        return documents

    def _select_category(self) -> str:
        """Select a category based on weights."""
        total_weight = sum(self.weights.values())
        normalized_weights = [self.weights[c] / total_weight for c in self.categories]
        return random.choices(self.categories, weights=normalized_weights, k=1)[0]

    def get_categories(self) -> List[str]:
        """Get list of categories in this composite generator."""
        return self.categories.copy()
