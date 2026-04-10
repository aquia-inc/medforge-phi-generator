# CMS Purview DLP Training Requirements

> Source: CMS stakeholder meeting, November 14, 2025
> Customer: Centers for Medicare & Medicaid Services (CMS)
> Purpose: Train Microsoft Purview DLP classifiers to detect accidental PHI and CUI in SharePoint and other M365 locations

---

## Volume Guidelines

- **Minimum (Seed Sets):** 50 positive, 150 negative (Microsoft recommends ~3x negatives)
- **Service Constraints:** Max ~500 docs per set processed at training time (most recent 500 used)
- **Target Sweet Spot:** 200-500 positives, 400-1,000 negatives

## Deliverables

- PHI: 200-500 positive + 400-1,000 negative documents
- CUI: 7 categories with positive/negative pairs
- Multiple formats: PDF, DOCX, XLSX, EML, PPTX, nested EML
- Customer templates integrated from CMS

## CUI Categories

| Category | Subcategories |
|----------|---------------|
| **Critical Infrastructure** | Emergency Management, Systems Vulnerability, Physical Security |
| **Financial** | Bank Secrecy, Budget, EFT, Retirement |
| **Law Enforcement** | Criminal History, Investigation |
| **Legal** | Admin Proceedings, Collective Bargaining, Privilege |
| **Procurement** | Source Selection, Small Business Research |
| **Proprietary Business** | Entity Registration, General Proprietary Info |
| **Tax** | Federal Taxpayer Info, Written Determinations |
| **Other** | Security-related emails (e.g., Snyk vulnerability reports) |

## File Types & Quality

- **Formats:** DOCX/PDF (text or high-quality OCR), XLSX/CSV, EML/MSG, PPTX
- **Style:** Formatting must match positive set
- **Checklist (for Source Templates & Negatives):**
  - No real names, contact info, IDs, or dates tied to persons
  - Metadata scrubbed
  - Uses same templates/systems as positives
- **Synthetic Data Approach:** Fully synthetic names, identifiers, and medical data via Faker and faker-healthcare-system

## Negative Data Strategy

### Good Negatives (PHI)
- Clinical templates/policies with NO identifiers
- Order forms with placeholders only
- De-identified case summaries (Safe Harbor)
- Device manuals, SOPs

### Good Negatives (PII)
- HR/Finance templates without real data
- Generic announcements (first names only)
- System logs with ticket IDs (no people IDs)

### Hard Negatives (High Value)
- Documents layout-matching positives but empty/generic
- Appointment reminders without specific details
- Billing statements with no member IDs

### Avoid
- Real PHI/PII hidden in metadata/headers
- Redacted positives (unless truly de-identified)
- Low-quality scans
