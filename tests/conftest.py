"""
Shared pytest fixtures for MedForge tests.
"""
import os
import sys
import tempfile
import shutil

import pytest

# Add src to path so imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def tmp_output_dir():
    """Create a temporary output directory, cleaned up after test."""
    temp_dir = tempfile.mkdtemp(prefix="medforge_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def patient_generator():
    """Pre-seeded PatientGenerator for deterministic tests."""
    from generators.patient_generator import PatientGenerator
    return PatientGenerator(seed=42)


@pytest.fixture
def provider_generator():
    """Pre-seeded ProviderGenerator for deterministic tests."""
    from generators.patient_generator import ProviderGenerator
    return ProviderGenerator(seed=42)


@pytest.fixture
def facility_generator():
    """Pre-seeded FacilityGenerator for deterministic tests."""
    from generators.patient_generator import FacilityGenerator
    return FacilityGenerator(seed=42)


@pytest.fixture
def sample_phi_patient(patient_generator):
    """A reusable patient dict from Faker."""
    return patient_generator.generate_patient()


@pytest.fixture
def sample_phi_provider(provider_generator):
    """A reusable provider dict from Faker."""
    return provider_generator.generate_provider()


@pytest.fixture
def sample_phi_facility(facility_generator):
    """A reusable facility dict from Faker."""
    return facility_generator.generate_facility()


@pytest.fixture
def sample_cui_data():
    """Generate one CUI positive doc_data dict per category."""
    from generators.cui import CUIGeneratorFactory
    data = {}
    categories = CUIGeneratorFactory.get_all_categories()
    for category in categories:
        gen = CUIGeneratorFactory.get_generator(category, seed=42)
        data[category] = gen.generate_positive()
    return data
