# Nested Email Requirements

## Critical Rule: PHI Consistency in Email Attachments

**Requirement:** Email attachments must match the PHI status of the parent email.

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

### Why This Matters:
Mixing PHI and non-PHI content in a single email could confuse Purview during training. The classifier needs clear examples where:
- Everything in the document is PHI (positive training)
- Nothing in the document is PHI (negative training)

### Implementation Notes:

When generating nested emails:
1. Determine if email will be PHI positive or negative
2. Generate parent email content accordingly
3. Generate attachments with matching PHI status
4. Save entire email (with attachments) to appropriate folder

### Current Status:
- ✅ Nested email formatter exists (`nested_formatter.py`)
- ✅ Methods for both PHI positive and PHI negative emails exist
- ❌ **NOT YET IMPLEMENTED** in CLI generation workflow
- ❌ Need to add nested email generation to `cli.py`

### Implementation Checklist:
- [ ] Add "nested_email" doc type to PHI positive generation
- [ ] Add "nested_email" doc type to PHI negative generation
- [ ] Ensure PHI positive nested emails:
  - Generate temporary PHI positive attachment (lab/note)
  - Create email with PHI patient data + attachment
  - Save to `phi_positive/` folder
  - Clean up temporary attachment files
- [ ] Ensure PHI negative nested emails:
  - Generate temporary PHI negative attachment (policy/form)
  - Create email with no patient data + attachment
  - Save to `phi_negative/` folder
  - Clean up temporary attachment files

### Example Scenarios:

**Good - PHI Positive:**
```
phi_positive/EmailWithAttachment_0001.eml
  ├── Email body: "Dear John Smith, MRN: 12345..."
  └── Attachment: LabResult_12345.pdf (contains patient data)
```

**Good - PHI Negative:**
```
phi_negative/PolicyEmail_0001.eml
  ├── Email body: "Dear team, see attached policy..."
  └── Attachment: InfectionControl_Policy.pdf (no patient data)
```

**BAD - Mixed (DO NOT DO THIS):**
```
❌ phi_positive/EmailWithAttachment_0001.eml
  ├── Email body: "Dear John Smith, MRN: 12345..."
  └── Attachment: BlankForm.pdf (no patient data) ← WRONG!

❌ phi_negative/PolicyEmail_0001.eml
  ├── Email body: "Dear team, see attached policy..."
  └── Attachment: LabResult_12345.pdf (contains patient data) ← WRONG!
```
