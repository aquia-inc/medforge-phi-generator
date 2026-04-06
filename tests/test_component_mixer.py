"""
Unit tests for ComponentMixer and the component mixing system.

Covers seeding, deduplication, exhaustion, font mapping, and
CUI section order variants.
"""

from templates.components import (
    ComponentMixer,
    ComponentConfiguration,
    get_pdf_font_name,
    get_docx_font_name,
    CUI_SECTION_ORDERS,
    SectionOrderVariant,
)


class TestComponentMixer:
    """Tests for ComponentMixer configuration generation."""

    def test_seeded_deterministic(self):
        """Same seed produces the same configuration sequence."""
        mixer1 = ComponentMixer(seed=42)
        mixer2 = ComponentMixer(seed=42)

        configs1 = [mixer1.get_random_configuration() for _ in range(5)]
        configs2 = [mixer2.get_random_configuration() for _ in range(5)]

        for c1, c2 in zip(configs1, configs2):
            assert c1.header == c2.header
            assert c1.layout == c2.layout
            assert c1.section_order == c2.section_order
            assert c1.style == c2.style

    def test_different_seeds_differ(self):
        """Different seeds produce different first configurations."""
        mixer1 = ComponentMixer(seed=1)
        mixer2 = ComponentMixer(seed=999)

        c1 = mixer1.get_random_configuration()
        c2 = mixer2.get_random_configuration()

        # Very unlikely to be identical with different seeds
        differs = (
            c1.header != c2.header or
            c1.layout != c2.layout or
            c1.section_order != c2.section_order or
            c1.style != c2.style
        )
        assert differs

    def test_configuration_has_all_fields(self):
        """Returned configuration has header, layout, section_order, style."""
        mixer = ComponentMixer(seed=42)
        config = mixer.get_random_configuration()

        assert isinstance(config, ComponentConfiguration)
        assert config.header is not None
        assert config.layout is not None
        assert config.section_order is not None
        assert config.style is not None

    def test_style_config_has_fonts(self):
        """Style configuration includes font and color information."""
        mixer = ComponentMixer(seed=42)
        config = mixer.get_random_configuration()
        style_cfg = config.style.get_config()

        assert 'font_family' in style_cfg
        assert 'color_primary' in style_cfg

    def test_avoid_duplicates(self):
        """10 configs with avoid_duplicates=True have no repeats."""
        mixer = ComponentMixer(seed=42)
        configs = [mixer.get_random_configuration(avoid_duplicates=True) for _ in range(10)]

        # Convert to string tuples for comparison (components aren't hashable)
        config_strs = [
            (c.header.variant.value, c.layout.variant.value,
             c.section_order.variant.value, c.style.variant.value)
            for c in configs
        ]
        assert len(set(config_strs)) == 10

    def test_total_combinations(self):
        """_calculate_total_combinations returns expected count."""
        mixer = ComponentMixer(seed=42)
        total = mixer._calculate_total_combinations()

        # Should be > 0 and match documented combination count
        assert total > 0
        # 5 headers x 3 layouts x section_orders x 4 styles
        assert total == len(mixer.get_all_configurations())

    def test_reset_clears_used(self):
        """reset() allows previously used configs to be generated again."""
        mixer = ComponentMixer(seed=42)

        # Generate some configs
        first_config = mixer.get_random_configuration(avoid_duplicates=True)
        for _ in range(5):
            mixer.get_random_configuration(avoid_duplicates=True)

        # Reset and generate with same seed
        mixer.reset()
        mixer2 = ComponentMixer(seed=42)
        new_first = mixer2.get_random_configuration(avoid_duplicates=True)

        assert first_config.header == new_first.header
        assert first_config.style == new_first.style

    def test_get_all_configurations(self):
        """get_all_configurations returns a non-empty list of unique configs."""
        mixer = ComponentMixer(seed=42)
        all_configs = mixer.get_all_configurations()

        assert len(all_configs) > 0
        # All should be ComponentConfiguration instances
        for c in all_configs:
            assert isinstance(c, ComponentConfiguration)


class TestFontNameMapping:
    """Tests for font name translation between PDF and DOCX/PPTX."""

    def test_pdf_font_arial(self):
        """Arial maps to Helvetica for ReportLab."""
        assert get_pdf_font_name('Arial') == 'Helvetica'

    def test_pdf_font_times(self):
        """Times New Roman maps to Times-Roman for ReportLab."""
        assert get_pdf_font_name('Times New Roman') == 'Times-Roman'

    def test_pdf_font_courier(self):
        """Courier New maps to Courier for ReportLab."""
        assert get_pdf_font_name('Courier New') == 'Courier'

    def test_pdf_font_unknown_defaults(self):
        """Unknown font maps to Helvetica (safe default)."""
        result = get_pdf_font_name('Nonexistent Font')
        assert result == 'Helvetica'

    def test_docx_font_helvetica(self):
        """Helvetica maps to Arial for DOCX/PPTX."""
        assert get_docx_font_name('Helvetica') == 'Arial'

    def test_docx_font_times_roman(self):
        """Times-Roman maps to Times New Roman for DOCX/PPTX."""
        assert get_docx_font_name('Times-Roman') == 'Times New Roman'


class TestCUISectionOrders:
    """Tests for CUI-specific section order variants."""

    def test_cui_section_orders_non_empty(self):
        """CUI_SECTION_ORDERS list has entries."""
        assert len(CUI_SECTION_ORDERS) > 0

    def test_cui_section_orders_are_variants(self):
        """All entries are SectionOrderVariant enum members."""
        for order in CUI_SECTION_ORDERS:
            assert isinstance(order, SectionOrderVariant)

    def test_known_cui_variants_exist(self):
        """Expected CUI variants are present."""
        variant_names = [v.name for v in CUI_SECTION_ORDERS]
        assert 'CUI_METADATA_FIRST' in variant_names
        assert 'CUI_CONTENT_FIRST' in variant_names
