# Template Evaluation Criteria

> Guidelines for assessing whether a customer-provided file is a good candidate for integration into MedForge's generation pipeline.

---

## Evaluation Matrix

| Criteria | Good Template | Bad Template |
|----------|---------------|--------------|
| **Fillability** | Has clear placeholder text, blank fields, or form fields that can be programmatically replaced | Deeply structured with cross-sheet formulas, charts tied to data ranges, data validation cascades |
| **Variance potential** | Faker/LLM can produce meaningfully different content each generation | Every copy would be identical (static content, no fill points) |
| **File size** | Under 1MB bare, under 2MB when email-wrapped | Multi-MB files risk hitting Purview upload limits and bloating .eml attachments |
| **Format compatibility** | DOCX, PDF (fillable or placeholder-based), simple XLSX | Complex XLSX with charts/images, PNG/XML diagrams, scanned PDFs |
| **Training signal** | Contains text patterns Purview can learn from (names, numbers, narrative) | Value is in visual layout, charts, or images (Purview classifies text, not visuals) |

## Case Study: Why the FISMA Reporting XLSX Was Rejected

The `FY25 Q1 Final FISMA Reporting Template` (5.8MB, 14 sheets) was evaluated and skipped because:

1. **Charts break on fill:** 2 dashboard charts are bound to specific cell ranges. Changing numeric data without updating chart references produces corrupt visualizations.
2. **Data validation cascades:** 282-column DropDown sheet drives validation across all other sheets. Modifying values risks breaking dependent dropdowns.
3. **Cross-sheet formulas:** Roll-Up sheet (492 rows) aggregates from other sheets. Changing source data without recalculating creates inconsistent totals.
4. **Copy-only = zero variance:** Using it as a static copy means every generated document is identical — no training value for Purview.
5. **Size risk:** At 5.8MB bare (8-10MB email-wrapped), it risks exceeding Purview's per-document processing limits.

**Better alternative:** A simplified FISMA-style XLSX could be generated from scratch via `CUIXlsxFormatter` with Faker data, producing infinite variance at ~50KB per file.

## Decision Framework

When a customer provides a complex file, the right approach is to extract the *document type pattern* (e.g., "FISMA quarterly metrics report") and build a lightweight programmatic generator, not to force-fill the original.

```
Customer provides file
  → Can it be filled programmatically?
    → YES: Integrate as template (PDF fillable, DOCX sub, XLSX copy)
    → NO: Can the document *type* be generated from scratch?
      → YES: Build a format-specific generator (CUIDocxFormatter, CUIXlsxFormatter, etc.)
      → NO: Skip — the file adds no training value
```
