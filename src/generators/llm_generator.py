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
            data = json.loads(text.strip())
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
            data = json.loads(text.strip())
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
            data = json.loads(text.strip())
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
