# Unimplemented Feature Specs

> **Status:** Not implemented — captured from original CMS requirements (AGENTS.md, meeting 11/14/2025)
> **Location:** `docs/feature_proposals/`

These features were scoped during initial project planning but never implemented. They are preserved here for future consideration.

---

## Multilingual Document Generation

**Original spec:** Generate documents in multiple languages to match CMS patient demographics.

### Language Distribution

| Locale | Percentage | Documents (of 2,000) |
|--------|-----------|---------------------|
| `en_US` (English) | 90% | 1,800 |
| `es_MX` (Spanish) | 5% | 100 |
| `zh_CN` (Chinese, Simplified) | 3% | 60 |
| `vi_VN` (Vietnamese) | 2% | 40 |

### Document Types by Language

**Spanish (100 documents):**
- Patient consent forms: 20
- Medication instructions: 15
- Lab results: 25
- Appointment letters: 15
- Patient education materials: 15
- Billing statements: 10

**Chinese (60 documents):**
- Patient registration forms: 15
- Lab results: 20
- Appointment notifications: 10
- Medical instructions: 10
- Insurance documents: 5

**Vietnamese (40 documents):**
- Patient intake forms: 10
- Lab results: 15
- Prescription instructions: 8
- Appointment reminders: 7

### Edge Cases
- Bilingual forms (English/Spanish): 10 documents
- English headers with non-English content: 5 documents
- Email threads with multiple languages: 5 documents

### Implementation Notes
- Faker already supports all four locales (`Faker('es_MX')`, etc.)
- Medical terminology is largely universal; form labels and narratives need translation
- LLM can generate clinical narratives in target languages
- Purview must be tested for PHI detection in non-English documents

---

## Quality Degradation Simulation

**Original spec:** Vary document quality to prevent Purview from overfitting on clean, perfectly-formatted training data.

### Quality Distribution

| Quality Level | Percentage | Description |
|--------------|-----------|-------------|
| Clean | 70% | Professional formatting, no errors |
| Messy | 20% | Slight formatting inconsistencies, minor spacing issues |
| Poor | 10% | Typos, OCR artifacts, inconsistent fonts, alignment problems |

### What "Messy" Means
- Extra whitespace or inconsistent spacing
- Slightly different font sizes within a section
- Minor alignment issues in tables
- Occasional missing punctuation

### What "Poor" Means
- Simulated OCR errors (character substitution: `l` -> `1`, `O` -> `0`)
- Random typos in non-PHI text
- Inconsistent date formats within the same document
- Missing or duplicate headers/footers
- Simulated fax noise (for PDFs — grayscale noise overlay)

### Why This Matters
Real-world documents that reach SharePoint are not perfectly formatted. If Purview only trains on clean documents, it may miss PHI in messy real-world content. Quality degradation makes the classifier more robust.

### Implementation Approach
- Apply degradation as a post-processing step after document generation
- Keep PHI elements clean (identifiers, medical data) so they remain detectable
- Degrade surrounding context and formatting only
- Flag degradation level in manifest for tracking
