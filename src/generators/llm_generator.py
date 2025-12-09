"""
LLM Generator using Claude 4.5 Sonnet
Generates clinical narratives and template variations
"""
import json
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from anthropic import Anthropic
from dotenv import load_dotenv

# Force reload environment variables, override existing
load_dotenv(override=True)


def repair_json_string(text: str) -> str:
    """
    Repair common JSON issues from LLM responses, particularly
    unescaped newlines inside string values.

    Args:
        text: Raw JSON text that may have issues

    Returns:
        Repaired JSON string
    """
    text = text.strip()

    # Track whether we're inside a string
    result = []
    in_string = False
    escape_next = False

    for char in text:
        if escape_next:
            result.append(char)
            escape_next = False
            continue

        if char == '\\':
            result.append(char)
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            result.append(char)
            continue

        if in_string:
            # Replace literal newlines/tabs with escaped versions
            if char == '\n':
                result.append('\\n')
            elif char == '\r':
                result.append('\\r')
            elif char == '\t':
                result.append('\\t')
            else:
                result.append(char)
        else:
            result.append(char)

    return ''.join(result)


class ClinicalNarrative(BaseModel):
    """Structured output for clinical assessment narratives"""
    subjective: str = Field(description="Patient's reported symptoms and concerns")
    objective: str = Field(description="Clinical observations and findings")
    assessment: str = Field(description="Clinical assessment and diagnosis reasoning")
    plan: str = Field(description="Treatment plan and follow-up recommendations")


class EmailBody(BaseModel):
    """Structured output for professional email content"""
    greeting: str = Field(description="Professional email greeting")
    body: str = Field(description="Main email body content, 2-4 paragraphs")
    closing: str = Field(description="Professional email closing")


class ProviderCorrespondence(BaseModel):
    """Structured output for provider-to-provider communication"""
    subject: str = Field(description="Email subject line")
    introduction: str = Field(description="Opening paragraph introducing the case")
    clinical_summary: str = Field(description="Clinical details and current status")
    consultation_request: str = Field(description="Specific questions or requests for the specialist")
    closing_remarks: str = Field(description="Closing remarks and contact information")


# CUI-specific Pydantic models

class CUIDocumentNarrative(BaseModel):
    """Structured output for CUI document narrative content"""
    executive_summary: str = Field(description="Brief executive summary of the document")
    body_content: str = Field(description="Main body content with detailed information")
    recommendations: str = Field(description="Recommendations or action items")
    distribution_statement: str = Field(description="Distribution and handling statement")


class CUIBudgetMemo(BaseModel):
    """Structured output for budget-related CUI documents"""
    subject: str = Field(description="Memo subject line")
    purpose: str = Field(description="Purpose of the budget request or analysis")
    budget_justification: str = Field(description="Detailed budget justification")
    fiscal_impact: str = Field(description="Analysis of fiscal impact")
    recommendation: str = Field(description="Budget recommendation")


class CUISecurityReport(BaseModel):
    """Structured output for security-related CUI documents"""
    incident_summary: str = Field(description="Summary of security incident or finding")
    technical_details: str = Field(description="Technical details of the vulnerability or incident")
    risk_assessment: str = Field(description="Risk assessment and potential impact")
    mitigation_steps: str = Field(description="Recommended mitigation or remediation steps")
    timeline: str = Field(description="Timeline for resolution")


class CUILegalMemo(BaseModel):
    """Structured output for legal CUI documents"""
    subject: str = Field(description="Legal memo subject")
    question_presented: str = Field(description="Legal question presented")
    brief_answer: str = Field(description="Brief answer to the legal question")
    analysis: str = Field(description="Legal analysis with citations")
    conclusion: str = Field(description="Conclusion and recommendations")


class CUIProcurementDoc(BaseModel):
    """Structured output for procurement CUI documents"""
    acquisition_summary: str = Field(description="Summary of acquisition need")
    evaluation_criteria: str = Field(description="Evaluation criteria and methodology")
    vendor_analysis: str = Field(description="Analysis of vendor proposals or capabilities")
    recommendation: str = Field(description="Source selection recommendation")
    justification: str = Field(description="Detailed justification for recommendation")


class ClaudeGenerator:
    """Generates clinical narratives using Claude 4.5 Sonnet"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or parameters")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def generate_clinical_narrative(self, patient: dict, diagnoses: List[dict],
                                    medications: List[str], vitals: dict) -> ClinicalNarrative:
        """
        Generate a clinical SOAP note narrative using Claude

        Args:
            patient: Patient information dict
            diagnoses: List of diagnosis dicts with 'name' and 'icd10'
            medications: List of medication strings
            vitals: Vital signs dict

        Returns:
            ClinicalNarrative with SOAP components
        """
        # Build prompt with patient context
        diagnosis_list = ', '.join([d['name'] for d in diagnoses[:3]])
        med_list = ', '.join(medications[:5])

        prompt = f"""Generate a realistic clinical progress note in SOAP format for a patient with the following information:

Diagnoses: {diagnosis_list}
Current Medications: {med_list}
Vital Signs: BP {vitals['blood_pressure']}, HR {vitals['heart_rate']}, Temp {vitals['temperature']}°F

Requirements:
- Write as if you are the treating physician
- Use appropriate medical terminology
- Keep each section 2-3 sentences
- Make the narrative clinically realistic but varied
- Focus on the primary diagnosis: {diagnoses[0]['name']}
"""

        try:
            json_prompt = prompt + """

Return your response as valid JSON with these exact keys:
{"subjective": "...", "objective": "...", "assessment": "...", "plan": "..."}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": json_prompt
                }]
            )

            # Parse JSON from response
            text = response.content[0].text
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            # Repair common JSON issues (unescaped newlines, etc.)
            text = repair_json_string(text)
            data = json.loads(text)
            return ClinicalNarrative(**data)

        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            # Fallback to template-based narrative
            return self._fallback_narrative(patient, diagnoses, medications, vitals)

    def generate_provider_email(self, patient: dict, sender_provider: dict,
                               recipient_provider: dict, reason: str) -> ProviderCorrespondence:
        """
        Generate provider-to-provider consultation email

        Args:
            patient: Patient information
            sender_provider: Referring provider info
            recipient_provider: Specialist provider info
            reason: Reason for consultation

        Returns:
            ProviderCorrespondence with email components
        """
        prompt = f"""Generate a professional provider-to-provider consultation email with this context:

Patient: {patient['age']}-year-old with {patient['diagnoses'][0]['name']}
Sender: {sender_provider['specialty']} physician
Recipient: {recipient_provider['specialty']} specialist
Reason: {reason}

Requirements:
- Professional medical communication tone
- Include relevant clinical details
- Specify what input is being requested
- 3-4 paragraphs total
- Vary the phrasing to sound natural
"""

        try:
            json_prompt = prompt + """

Return your response as valid JSON with these exact keys:
{"subject": "...", "introduction": "...", "clinical_summary": "...", "consultation_request": "...", "closing_remarks": "..."}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": json_prompt
                }]
            )

            # Parse JSON from response
            text = response.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            # Repair common JSON issues (unescaped newlines, etc.)
            text = repair_json_string(text)
            data = json.loads(text)
            return ProviderCorrespondence(**data)

        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            return self._fallback_provider_email(patient, sender_provider, recipient_provider, reason)

    def generate_patient_communication(self, patient: dict, context: str,
                                      communication_type: str = "test_results") -> EmailBody:
        """
        Generate patient communication email

        Args:
            patient: Patient information
            context: Context for the email (e.g., test results summary)
            communication_type: Type of communication

        Returns:
            EmailBody with greeting, body, and closing
        """
        prompt = f"""Generate a patient communication email for the following:

Type: {communication_type}
Patient Age: {patient['age']}
Context: {context}

Requirements:
- Professional but patient-friendly tone
- Clear and reassuring language
- 2-3 paragraph body
- Appropriate medical explanation without jargon
"""

        try:
            json_prompt = prompt + """

Return your response as valid JSON with these exact keys:
{"greeting": "...", "body": "...", "closing": "..."}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{
                    "role": "user",
                    "content": json_prompt
                }]
            )

            # Parse JSON from response
            text = response.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            # Repair common JSON issues (unescaped newlines, etc.)
            text = repair_json_string(text)
            data = json.loads(text)
            return EmailBody(**data)

        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            return self._fallback_patient_email(patient, context)

    def generate_template_variation(self, base_template: str, variation_type: str) -> str:
        """
        Generate a variation of a document template

        Args:
            base_template: Description of base template
            variation_type: Type of variation to create

        Returns:
            Text description of the variation
        """
        prompt = f"""Create a variation of this medical document template:

Base: {base_template}
Variation Type: {variation_type}

Generate a brief description (2-3 sentences) of how this variation differs in:
- Layout/structure
- Tone/formality
- Content organization
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            return response.content[0].text

        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            return f"{base_template} - {variation_type} variation"

    # CUI Generation Methods

    def generate_cui_budget_memo(self, agency: str, program: str,
                                 fiscal_year: str, amount: str) -> CUIBudgetMemo:
        """
        Generate CUI budget memo content

        Args:
            agency: Government agency name
            program: Program or initiative name
            fiscal_year: Fiscal year
            amount: Budget amount

        Returns:
            CUIBudgetMemo with structured content
        """
        prompt = f"""Generate a realistic government budget memorandum for:

Agency: {agency}
Program: {program}
Fiscal Year: {fiscal_year}
Requested Amount: {amount}

Requirements:
- Use formal government memo style
- Include specific budget justifications
- Reference relevant appropriations or authorizations
- Use realistic government terminology
- Keep each section 2-3 sentences
- This is pre-decisional budget information (CUI)
"""

        try:
            json_prompt = prompt + """

Return your response as valid JSON with these exact keys:
{"subject": "...", "purpose": "...", "budget_justification": "...", "fiscal_impact": "...", "recommendation": "..."}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": json_prompt}]
            )

            text = response.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            # Repair common JSON issues (unescaped newlines, etc.)
            text = repair_json_string(text)
            data = json.loads(text)
            return CUIBudgetMemo(**data)

        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            return self._fallback_budget_memo(agency, program, fiscal_year, amount)

    def generate_cui_security_report(self, system_name: str, vulnerability_type: str,
                                     severity: str, agency: str) -> CUISecurityReport:
        """
        Generate CUI security vulnerability or incident report

        Args:
            system_name: Name of affected system
            vulnerability_type: Type of vulnerability or incident
            severity: Severity level (Critical, High, Medium, Low)
            agency: Agency responsible for the system

        Returns:
            CUISecurityReport with structured content
        """
        prompt = f"""Generate a realistic government security vulnerability report for:

System: {system_name}
Vulnerability Type: {vulnerability_type}
Severity: {severity}
Agency: {agency}

Requirements:
- Use formal FISMA/NIST security terminology
- Include realistic technical details
- Reference CVE patterns (use synthetic CVE numbers)
- Include risk assessment using NIST framework
- Provide actionable remediation steps
- Keep each section 2-4 sentences
- This is systems vulnerability information (CUI)
"""

        try:
            json_prompt = prompt + """

Return your response as valid JSON with these exact keys:
{"incident_summary": "...", "technical_details": "...", "risk_assessment": "...", "mitigation_steps": "...", "timeline": "..."}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": json_prompt}]
            )

            text = response.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            # Repair common JSON issues (unescaped newlines, etc.)
            text = repair_json_string(text)
            data = json.loads(text)
            return CUISecurityReport(**data)

        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            return self._fallback_security_report(system_name, vulnerability_type, severity, agency)

    def generate_cui_legal_memo(self, subject: str, agency: str,
                                legal_issue: str) -> CUILegalMemo:
        """
        Generate CUI legal memorandum

        Args:
            subject: Subject of the legal memo
            agency: Government agency
            legal_issue: Core legal issue

        Returns:
            CUILegalMemo with structured content
        """
        prompt = f"""Generate a realistic government legal memorandum for:

Subject: {subject}
Agency: {agency}
Legal Issue: {legal_issue}

Requirements:
- Use formal legal memo format (IRAC or similar)
- Reference relevant statutes and regulations
- Include analysis of legal authorities
- Use appropriate legal terminology
- Keep each section 2-4 sentences
- This is legally privileged information (CUI)
"""

        try:
            json_prompt = prompt + """

Return your response as valid JSON with these exact keys:
{"subject": "...", "question_presented": "...", "brief_answer": "...", "analysis": "...", "conclusion": "..."}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": json_prompt}]
            )

            text = response.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            # Repair common JSON issues (unescaped newlines, etc.)
            text = repair_json_string(text)
            data = json.loads(text)
            return CUILegalMemo(**data)

        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            return self._fallback_legal_memo(subject, agency, legal_issue)

    def generate_cui_procurement_doc(self, acquisition_name: str, agency: str,
                                     estimated_value: str, vendors: List[str]) -> CUIProcurementDoc:
        """
        Generate CUI source selection or procurement document

        Args:
            acquisition_name: Name of the acquisition
            agency: Procuring agency
            estimated_value: Estimated contract value
            vendors: List of vendor names being evaluated

        Returns:
            CUIProcurementDoc with structured content
        """
        vendor_list = ", ".join(vendors[:4])
        prompt = f"""Generate a realistic government source selection evaluation for:

Acquisition: {acquisition_name}
Agency: {agency}
Estimated Value: {estimated_value}
Vendors Under Evaluation: {vendor_list}

Requirements:
- Use FAR-compliant procurement terminology
- Include evaluation factors (technical, price, past performance)
- Provide competitive range analysis
- Include source selection recommendation
- Keep each section 2-4 sentences
- This is source selection information (CUI)
"""

        try:
            json_prompt = prompt + """

Return your response as valid JSON with these exact keys:
{"acquisition_summary": "...", "evaluation_criteria": "...", "vendor_analysis": "...", "recommendation": "...", "justification": "..."}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": json_prompt}]
            )

            text = response.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            # Repair common JSON issues (unescaped newlines, etc.)
            text = repair_json_string(text)
            data = json.loads(text)
            return CUIProcurementDoc(**data)

        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            return self._fallback_procurement_doc(acquisition_name, agency, estimated_value, vendors)

    def generate_cui_narrative(self, category: str, subcategory: str,
                               document_type: str, context: dict) -> CUIDocumentNarrative:
        """
        Generate generic CUI document narrative

        Args:
            category: CUI category (e.g., financial, legal)
            subcategory: CUI subcategory
            document_type: Type of document
            context: Additional context dict

        Returns:
            CUIDocumentNarrative with structured content
        """
        context_str = ", ".join([f"{k}: {v}" for k, v in context.items()])
        prompt = f"""Generate a realistic government document narrative for:

CUI Category: {category}
Subcategory: {subcategory}
Document Type: {document_type}
Context: {context_str}

Requirements:
- Use formal government document style
- Include appropriate technical or administrative detail
- Reference relevant authorities or regulations
- Keep each section 2-4 sentences
- This is Controlled Unclassified Information (CUI)
"""

        try:
            json_prompt = prompt + """

Return your response as valid JSON with these exact keys:
{"executive_summary": "...", "body_content": "...", "recommendations": "...", "distribution_statement": "..."}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": json_prompt}]
            )

            text = response.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            # Repair common JSON issues (unescaped newlines, etc.)
            text = repair_json_string(text)
            data = json.loads(text)
            return CUIDocumentNarrative(**data)

        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            return self._fallback_cui_narrative(category, subcategory, document_type, context)

    # CUI Fallback methods

    def _fallback_budget_memo(self, agency, program, fiscal_year, amount) -> CUIBudgetMemo:
        """Fallback template for budget memos"""
        return CUIBudgetMemo(
            subject=f"FY {fiscal_year} Budget Request - {program}",
            purpose=f"This memorandum requests approval for {amount} in funding for the {program} program for Fiscal Year {fiscal_year}.",
            budget_justification=f"The {agency} requires this funding to maintain critical program operations and meet statutory requirements. Current appropriations are insufficient to address increased demand and operational costs.",
            fiscal_impact=f"Approval of this request will enable continued program operations. Denial may result in service disruptions and failure to meet compliance requirements.",
            recommendation=f"Recommend approval of the {amount} funding request for {program} in FY {fiscal_year}."
        )

    def _fallback_security_report(self, system_name, vulnerability_type, severity, agency) -> CUISecurityReport:
        """Fallback template for security reports"""
        return CUISecurityReport(
            incident_summary=f"A {severity} severity {vulnerability_type} vulnerability has been identified in the {system_name} system operated by {agency}.",
            technical_details=f"The vulnerability affects the system's authentication and access control mechanisms. Exploitation could allow unauthorized access to sensitive data.",
            risk_assessment=f"Risk Level: {severity}. Potential impact includes unauthorized data disclosure and system compromise. Likelihood of exploitation is assessed as moderate.",
            mitigation_steps="Apply vendor security patch immediately. Implement additional access controls. Review audit logs for signs of exploitation. Update security monitoring rules.",
            timeline="Immediate: Apply patches within 72 hours. Short-term: Complete security assessment within 30 days. Long-term: Implement enhanced monitoring within 90 days."
        )

    def _fallback_legal_memo(self, subject, agency, legal_issue) -> CUILegalMemo:
        """Fallback template for legal memos"""
        return CUILegalMemo(
            subject=f"Legal Analysis: {subject}",
            question_presented=f"Whether {agency} may {legal_issue} consistent with applicable statutory and regulatory requirements.",
            brief_answer=f"Based on review of relevant authorities, {agency} has authority to proceed, subject to compliance with specified procedural requirements.",
            analysis="Review of applicable statutes, regulations, and case law supports the proposed action. The agency must ensure compliance with Administrative Procedure Act requirements and applicable agency regulations.",
            conclusion=f"Recommend proceeding with the proposed action, subject to implementation of recommended procedural safeguards."
        )

    def _fallback_procurement_doc(self, acquisition_name, agency, estimated_value, vendors) -> CUIProcurementDoc:
        """Fallback template for procurement documents"""
        return CUIProcurementDoc(
            acquisition_summary=f"The {agency} is acquiring {acquisition_name} with an estimated value of {estimated_value}. This acquisition supports critical agency mission requirements.",
            evaluation_criteria="Proposals were evaluated against the following factors: Technical Approach (40%), Past Performance (30%), and Price (30%). Technical and past performance factors were significantly more important than price.",
            vendor_analysis=f"A total of {len(vendors)} proposals were received and evaluated. All proposals were found to be within the competitive range for further consideration.",
            recommendation="Based on the integrated assessment of all evaluation factors, the Source Selection Authority recommends award to the highest-rated offeror.",
            justification="The recommended offeror demonstrated superior technical approach and excellent past performance. While not the lowest-priced proposal, the technical advantages provide best value to the Government."
        )

    def _fallback_cui_narrative(self, category, subcategory, document_type, context) -> CUIDocumentNarrative:
        """Fallback template for generic CUI narratives"""
        return CUIDocumentNarrative(
            executive_summary=f"This {document_type} document pertains to {category}/{subcategory} information requiring protection under CUI guidelines.",
            body_content=f"The information contained herein relates to {category} matters and has been designated as Controlled Unclassified Information. Proper handling and dissemination controls must be observed.",
            recommendations="Continue to apply appropriate safeguards consistent with CUI program requirements. Report any unauthorized disclosures immediately.",
            distribution_statement="Distribution is limited to authorized personnel with a legitimate need to know. Further dissemination is prohibited without prior authorization."
        )

    # Fallback methods (template-based when API fails)

    def _fallback_narrative(self, patient, diagnoses, medications, vitals) -> ClinicalNarrative:
        """Fallback template-based narrative when API unavailable"""
        return ClinicalNarrative(
            subjective=f"Patient presents for follow-up of {diagnoses[0]['name']}. Reports feeling generally well with current medication regimen of {', '.join(medications[:3])}.",
            objective=f"Physical exam shows patient in no acute distress. Vital signs: BP {vitals['blood_pressure']}, HR {vitals['heart_rate']}, Temp {vitals['temperature']}°F. Exam findings consistent with stable chronic disease.",
            assessment=f"Assessment: {diagnoses[0]['name']} currently well-controlled on current therapy. Additional diagnoses include {', '.join([d['name'] for d in diagnoses[1:3]])}.",
            plan="Continue current medications as prescribed. Follow-up lab work in 3 months. Patient education reinforced regarding disease management and medication compliance."
        )

    def _fallback_provider_email(self, patient, sender, recipient, reason) -> ProviderCorrespondence:
        """Fallback template for provider emails"""
        return ProviderCorrespondence(
            subject=f"Patient Consultation Request - {patient['diagnoses'][0]['name']}",
            introduction=f"Dear Dr. {recipient['last_name']}, I am writing to request your consultation for a patient under my care.",
            clinical_summary=f"The patient is a {patient['age']}-year-old with {patient['diagnoses'][0]['name']}. Current management includes {', '.join(patient['medications'][:3])}.",
            consultation_request=f"I would appreciate your input regarding {reason}. Recent findings suggest specialist evaluation would be beneficial.",
            closing_remarks="Please let me know your availability to see this patient. Thank you for your assistance."
        )

    def _fallback_patient_email(self, patient, context) -> EmailBody:
        """Fallback template for patient emails"""
        return EmailBody(
            greeting=f"Dear {patient['first_name']} {patient['last_name']},",
            body=f"Your recent test results are now available. {context}\n\nPlease contact our office if you have any questions about these results. We are here to help.",
            closing="Thank you,\nYour Healthcare Team"
        )


# Utility function to check if API key is available
def is_llm_available() -> bool:
    """Check if Claude API key is configured"""
    return bool(os.getenv('ANTHROPIC_API_KEY'))
