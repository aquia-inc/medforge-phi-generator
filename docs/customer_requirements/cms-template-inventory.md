# CMS Customer Template Inventory

> Source: Templates provided by CMS (Elizabeth) throughout project engagement
> See also: [Adding Customer Templates](../adding-customer-templates.md) for the integration guide

---

## Active Templates (27)

### Procurement (9 templates)
| Template | Format | Fill Method | LLM Enrichable |
|----------|--------|-------------|----------------|
| IGCE | XLSX | Copy | No |
| CLIN Templates | XLSX | Copy | No |
| Market Research | DOCX | Placeholder substitution | Yes |
| RFC Memo | DOCX | Underline fill + table fill | Yes |
| AGX RFC Memo | DOCX | Placeholder substitution | Yes |
| JA Limited Source | DOCX | Placeholder substitution | Yes |
| JOFOC | DOCX | Placeholder substitution | Yes |
| OAGM Source Selection | DOCX | Placeholder substitution | Yes |
| Acquisition Plan | DOCX | Table fill | Yes |

### Critical Infrastructure (6 templates)
| Template | Format | Fill Method | LLM Enrichable |
|----------|--------|-------------|----------------|
| KMP (Key Management Plan) | DOCX | Placeholder substitution | Yes |
| Rules of Behavior | DOCX | Placeholder substitution | Yes |
| Incident Response Plan | DOCX | Table fill | Yes |
| HHS RBD | PDF | Copy | No |
| Test Validation MAC | PDF | Copy | No |
| Test Validation PC | PDF | Copy | No |

### Financial (5 templates)
| Template | Format | Fill Method | LLM Enrichable |
|----------|--------|-------------|----------------|
| AFR Additional Info | DOCX | Placeholder substitution (pos+neg pair) | No |
| DIBO AFR | DOCX | Placeholder substitution (pos+neg pair) | Yes |
| Supplemental AFR | DOCX | Placeholder substitution (pos+neg pair) | Yes |
| OIT FO Additional Info | DOCX | Placeholder substitution (pos+neg pair) | Yes |
| Supplemental AFR Blank | DOCX | Copy | No |

### Legal (7 templates)
| Template | Format | Fill Method | LLM Enrichable |
|----------|--------|-------------|----------------|
| Reasonable Accommodation Request | PDF | Fillable (pikepdf AcroForm) | No |
| B6 Letter | DOCX | Placeholder substitution | Yes |
| Full Release | DOCX | Placeholder substitution | Yes |
| Form339 Letter | DOCX | Placeholder substitution | Yes |
| Subpoena Response | DOCX | Placeholder substitution | Yes |
| FOIA Medicare Auth | PDF | Fillable (pikepdf AcroForm) | No |
| FOIA Request Deceased Beneficiary | PDF | Fillable / copy | No |

### PHI (1 template)
| Template | Format | Fill Method | LLM Enrichable |
|----------|--------|-------------|----------------|
| Medical Inquiry Form | PDF | Fillable (reportlab overlay) | No |

## Disabled Templates

| Template | Format | Reason |
|----------|--------|--------|
| EFT Authorization Form | PDF | Form fill unreliable — pikepdf cannot render fields consistently |

## Rejected Templates

| Template | Format | Reason |
|----------|--------|--------|
| FY25 FISMA Reporting | XLSX (5.8MB, 14 sheets) | Charts break on fill, data validation cascades, cross-sheet formulas, zero variance as copy, exceeds size limits. Better to build a programmatic generator. |
| CMS Things to Know (newsletter) | PDF | Static content with zero variance — every copy identical, no training value |

## Template Integration Details

- **Selection rate:** 20% of generated documents come from customer templates
- **Category-weighted selection:** Picks category first (uniform), then template within category — prevents bias when one category has more templates
- **Email wrapping:** 80% of templates wrapped in emails as attachments (configurable via `--template-email-ratio`)
- **Three wrapping body tiers:** minimal (stubs), medium (category boilerplate), detailed (LLM-generated cover email)
- **LLM enrichment:** 17 of 27 templates support LLM-generated narrative sections appended to Faker-populated base
- **Fill patterns supported:** PDF fillable (pikepdf AcroForm), PDF copy, DOCX placeholder substitution, DOCX table fill, DOCX underline fill
