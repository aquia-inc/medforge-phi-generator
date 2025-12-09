"""
Unit tests for CUI generators
"""
import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generators.cui import (
    CUIGeneratorFactory,
    CompositeCUIGenerator,
    BaseCUIGenerator,
    CriticalInfrastructureCUIGenerator,
    FinancialCUIGenerator,
    LawEnforcementCUIGenerator,
    LegalCUIGenerator,
    ProcurementCUIGenerator,
    ProprietaryCUIGenerator,
    TaxCUIGenerator,
)


class TestCUIGeneratorFactory:
    """Tests for the CUI generator factory"""

    def test_factory_has_all_categories(self):
        """Test that all 7 CUI categories are registered"""
        expected_categories = [
            'critical_infrastructure',
            'financial',
            'law_enforcement',
            'legal',
            'procurement',
            'proprietary',
            'tax',
        ]
        registered = CUIGeneratorFactory.get_all_categories()
        for category in expected_categories:
            assert category in registered, f"Category {category} not registered"

    def test_get_generator_returns_correct_type(self):
        """Test that factory returns correct generator types"""
        gen = CUIGeneratorFactory.get_generator('financial')
        assert isinstance(gen, FinancialCUIGenerator)

        gen = CUIGeneratorFactory.get_generator('legal')
        assert isinstance(gen, LegalCUIGenerator)

    def test_get_generator_invalid_category_raises(self):
        """Test that invalid category raises KeyError"""
        with pytest.raises(KeyError):
            CUIGeneratorFactory.get_generator('invalid_category')

    def test_create_composite_generator(self):
        """Test creating a composite generator"""
        gen = CUIGeneratorFactory.create_composite_generator()
        assert isinstance(gen, CompositeCUIGenerator)

    def test_create_composite_generator_with_categories(self):
        """Test creating a composite generator with specific categories"""
        categories = ['financial', 'legal']
        gen = CUIGeneratorFactory.create_composite_generator(categories=categories)
        assert isinstance(gen, CompositeCUIGenerator)
        assert len(gen.generators) == 2

    def test_create_composite_generator_with_seed(self):
        """Test composite generator with seed can be created"""
        gen = CUIGeneratorFactory.create_composite_generator(seed=42)
        assert gen is not None
        assert isinstance(gen, CompositeCUIGenerator)
        # Verify it can generate documents
        doc = gen.generate_positive()
        assert 'category' in doc


class TestIndividualGenerators:
    """Tests for individual CUI category generators"""

    @pytest.fixture
    def generators(self):
        """Fixture providing all generator instances"""
        return {
            'critical_infrastructure': CriticalInfrastructureCUIGenerator(seed=42),
            'financial': FinancialCUIGenerator(seed=42),
            'law_enforcement': LawEnforcementCUIGenerator(seed=42),
            'legal': LegalCUIGenerator(seed=42),
            'procurement': ProcurementCUIGenerator(seed=42),
            'proprietary': ProprietaryCUIGenerator(seed=42),
            'tax': TaxCUIGenerator(seed=42),
        }

    def test_all_generators_extend_base(self, generators):
        """Test that all generators extend BaseCUIGenerator"""
        for name, gen in generators.items():
            assert isinstance(gen, BaseCUIGenerator), f"{name} does not extend BaseCUIGenerator"

    def test_all_generators_have_category(self, generators):
        """Test that all generators have CATEGORY defined"""
        for name, gen in generators.items():
            assert gen.CATEGORY, f"{name} has no CATEGORY defined"
            assert gen.CATEGORY == name, f"{name} CATEGORY mismatch"

    def test_generate_positive_returns_dict(self, generators):
        """Test that generate_positive returns a dictionary"""
        for name, gen in generators.items():
            result = gen.generate_positive()
            assert isinstance(result, dict), f"{name}.generate_positive() did not return dict"

    def test_generate_negative_returns_dict(self, generators):
        """Test that generate_negative returns a dictionary"""
        for name, gen in generators.items():
            result = gen.generate_negative()
            assert isinstance(result, dict), f"{name}.generate_negative() did not return dict"

    def test_positive_documents_have_required_fields(self, generators):
        """Test that positive documents have required CUI fields"""
        required_fields = ['category', 'has_cui', 'classification']

        for name, gen in generators.items():
            result = gen.generate_positive()
            for field in required_fields:
                assert field in result, f"{name} positive doc missing '{field}'"
            assert result['has_cui'] is True, f"{name} positive doc should have has_cui=True"

    def test_negative_documents_have_required_fields(self, generators):
        """Test that negative documents have required fields"""
        required_fields = ['category', 'has_cui', 'document_type']

        for name, gen in generators.items():
            result = gen.generate_negative()
            for field in required_fields:
                assert field in result, f"{name} negative doc missing '{field}'"
            assert result['has_cui'] is False, f"{name} negative doc should have has_cui=False"

    def test_get_document_types_returns_dict(self, generators):
        """Test that get_document_types returns a dict with subcategories"""
        for name, gen in generators.items():
            result = gen.get_document_types()
            assert isinstance(result, dict), f"{name}.get_document_types() did not return dict"
            assert len(result) > 0, f"{name}.get_document_types() returned empty dict"
            # Each subcategory should have positive and/or negative doc types
            for subcategory, doc_types in result.items():
                assert 'positive' in doc_types or 'negative' in doc_types, \
                    f"{name}.{subcategory} missing positive/negative doc types"


class TestFinancialGenerator:
    """Specific tests for Financial CUI generator"""

    @pytest.fixture
    def generator(self):
        return FinancialCUIGenerator(seed=42)

    def test_subcategories(self, generator):
        """Test that financial generator has expected subcategories"""
        expected = ['budget', 'bank_secrecy', 'eft', 'retirement', 'comptroller_general']
        for sub in expected:
            assert sub in generator.SUBCATEGORIES

    def test_budget_memo_has_fiscal_data(self, generator):
        """Test that budget memos include fiscal data"""
        # Generate multiple to find a budget memo
        for _ in range(20):
            doc = generator.generate_positive()
            if doc.get('document_type') == 'budget_memo':
                assert 'fiscal_year' in doc
                assert 'amount' in doc
                break


class TestProcurementGenerator:
    """Specific tests for Procurement CUI generator"""

    @pytest.fixture
    def generator(self):
        return ProcurementCUIGenerator(seed=42)

    def test_source_selection_has_evaluation_data(self, generator):
        """Test that source selection docs have evaluation data"""
        for _ in range(20):
            doc = generator.generate_positive()
            if doc.get('document_type') == 'source_selection_plan':
                assert 'evaluation_factors' in doc or 'solicitation_number' in doc
                break


class TestLegalGenerator:
    """Specific tests for Legal CUI generator"""

    @pytest.fixture
    def generator(self):
        return LegalCUIGenerator(seed=42)

    def test_legal_memo_has_privilege_marker(self, generator):
        """Test that legal memos include privilege information"""
        for _ in range(20):
            doc = generator.generate_positive()
            if doc.get('subcategory') == 'legal_privilege':
                assert 'classification' in doc
                assert 'PRIVILEGE' in doc['classification'].upper() or 'ATTORNEY' in doc['classification'].upper()
                break


class TestCompositeCUIGenerator:
    """Tests for the composite CUI generator"""

    @pytest.fixture
    def composite(self):
        return CUIGeneratorFactory.create_composite_generator(seed=42)

    def test_generate_batch(self, composite):
        """Test batch generation"""
        docs = composite.generate_batch(positive_count=5, negative_count=3)
        assert len(docs) == 8

        positive_count = sum(1 for d in docs if d.get('has_cui') is True)
        negative_count = sum(1 for d in docs if d.get('has_cui') is False)

        assert positive_count == 5
        assert negative_count == 3

    def test_category_distribution(self, composite):
        """Test that batch generates across categories"""
        docs = composite.generate_batch(positive_count=50, negative_count=20)

        categories = set(d.get('category') for d in docs)
        # With 70 documents, we should hit multiple categories
        assert len(categories) >= 3, "Expected documents from at least 3 categories"

    def test_batch_has_correct_count(self):
        """Test that batch produces correct number of documents"""
        gen = CUIGeneratorFactory.create_composite_generator(seed=12345)
        docs = gen.generate_batch(positive_count=10, negative_count=5)

        assert len(docs) == 15
        positive_count = sum(1 for d in docs if d.get('has_cui') is True)
        negative_count = sum(1 for d in docs if d.get('has_cui') is False)
        assert positive_count == 10
        assert negative_count == 5


class TestCUIClassifications:
    """Test CUI classification markings"""

    def test_financial_classifications(self):
        gen = FinancialCUIGenerator(seed=42)
        for _ in range(10):
            doc = gen.generate_positive()
            classification = doc.get('classification', '')
            # Should contain CUI or specific financial marking
            assert any(marker in classification.upper() for marker in [
                'CUI', 'CONTROLLED', 'BUDGET', 'BANK', 'EFT', 'RETIREMENT'
            ]), f"Unexpected classification: {classification}"

    def test_law_enforcement_classifications(self):
        gen = LawEnforcementCUIGenerator(seed=42)
        for _ in range(10):
            doc = gen.generate_positive()
            classification = doc.get('classification', '')
            assert any(marker in classification.upper() for marker in [
                'CUI', 'LAW ENFORCEMENT', 'LES', 'SENSITIVE', 'CRIMINAL', 'INVESTIGATION'
            ]), f"Unexpected classification: {classification}"

    def test_procurement_classifications(self):
        gen = ProcurementCUIGenerator(seed=42)
        for _ in range(10):
            doc = gen.generate_positive()
            classification = doc.get('classification', '')
            assert any(marker in classification.upper() for marker in [
                'CUI', 'SOURCE SELECTION', 'FAR', 'PROCUREMENT', 'ACQUISITION'
            ]), f"Unexpected classification: {classification}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
