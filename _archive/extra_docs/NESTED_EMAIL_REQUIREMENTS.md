# Nested Email Requirements

> **ARCHIVED** — This spec is fully implemented and all checklist items are complete.
> Moved from `docs/` on 2026-04-06.
>
> **Why completed:** Both PHI and CUI nested email formatters are wired into the CLI
> generation workflow. `NestedEmailFormatter` handles PHI; `CUINestedEmailFormatter`
> handles CUI with in-memory attachment generation and ~7% routing probability.
> The critical rule (attachment polarity must match parent email) is enforced in both
> formatters. CUI email variant routing (~7% nested, ~30% HTML, ~50% Snyk for
> critical_infrastructure) is tracked via the `variant` field in `cui_manifest.json`.
>
> **Canonical code locations:**
> - `src/formatters/nested_formatter.py` (PHI)
> - `src/formatters/cui_nested_formatter.py` (CUI)

## Critical Rule: PHI Consistency in Email Attachments

**Requirement:** Email attachments must match the PHI/CUI status of the parent email.

### Rules:
1. **PHI Positive Emails** (in `phi_positive/` folder)
   - Can contain PHI in email body
   - All attachments MUST also contain PHI
   - Example: Provider email with lab result PDF attached
   - Example: Referral email with progress note attached

2. **PHI Negative Emails** (in `phi_negative/` folder)
   - Cannot contain patient data in email body
   - All attachments MUST NOT contain PHI
   - Example: Policy distribution email with policy PDF attached
   - Example: Office announcement with blank registration form attached

3. **CUI Positive/Negative Emails** follow the same rule within CUI category directories.

### Why This Matters:
Mixing PHI and non-PHI content in a single email could confuse Purview during training. The classifier needs clear examples where:
- Everything in the document is PHI/CUI (positive training)
- Nothing in the document is PHI/CUI (negative training)

### Implementation Notes:

When generating nested emails:
1. Determine if email will be positive or negative
2. Generate parent email content accordingly
3. Generate attachments with matching polarity
4. Save entire email (with attachments) to appropriate folder

### Implementation Status:
- [x] Nested email formatter for PHI (`nested_formatter.py`)
- [x] Nested email formatter for CUI (`cui_nested_formatter.py`)
- [x] Both wired into CLI generation workflow
- [x] PHI positive nested emails generate PHI positive attachments
- [x] PHI negative nested emails generate PHI negative attachments
- [x] CUI nested emails route through `CUINestedEmailFormatter` with in-memory attachment generation
- [x] Temporary attachment files cleaned up
- [x] CUI email variant routing: ~7% nested, ~30% HTML, ~50% Snyk (critical_infrastructure)

### Example Scenarios:

**Good - PHI Positive:**
```
phi_positive/EmailWithAttachment_0001.eml
  |- Email body: "Dear John Smith, MRN: 12345..."
  \- Attachment: LabResult_12345.pdf (contains patient data)
```

**Good - PHI Negative:**
```
phi_negative/PolicyEmail_0001.eml
  |- Email body: "Dear team, see attached policy..."
  \- Attachment: InfectionControl_Policy.pdf (no patient data)
```

**BAD - Mixed (DO NOT DO THIS):**
```
phi_positive/EmailWithAttachment_0001.eml
  |- Email body: "Dear John Smith, MRN: 12345..."
  \- Attachment: BlankForm.pdf (no patient data)    <-- WRONG!

phi_negative/PolicyEmail_0001.eml
  |- Email body: "Dear team, see attached policy..."
  \- Attachment: LabResult_12345.pdf (contains PHI) <-- WRONG!
```
