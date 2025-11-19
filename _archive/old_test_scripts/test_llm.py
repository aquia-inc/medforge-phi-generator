#!/usr/bin/env python3
"""
Test Claude 4.5 Sonnet LLM Integration
Demonstrates structured outputs for clinical narratives
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generators.patient_generator import PatientGenerator, ProviderGenerator
from generators.llm_generator import ClaudeGenerator, is_llm_available


def main():
    print("=" * 80)
    print("CLAUDE 4.5 SONNET LLM INTEGRATION TEST")
    print("=" * 80)
    print()

    # Check if API key is available
    if not is_llm_available():
        print("❌ ERROR: ANTHROPIC_API_KEY not found in environment")
        print("Please set ANTHROPIC_API_KEY in .env file")
        return 1

    print("✓ API key found")
    print()

    # Initialize generators
    print("Initializing generators...")
    patient_gen = PatientGenerator(seed=42)
    provider_gen = ProviderGenerator(seed=42)
    claude_gen = ClaudeGenerator()

    print(f"✓ Using model: {claude_gen.model}")
    print(f"✓ Beta header: {claude_gen.beta_header}")
    print()

    # Generate sample patient
    print("Generating sample patient...")
    patient = patient_gen.generate_patient()
    provider1 = provider_gen.generate_provider()
    provider2 = provider_gen.generate_provider()

    print(f"  Patient: {patient['first_name']} {patient['last_name']}, Age {patient['age']}")
    print(f"  Primary Diagnosis: {patient['diagnoses'][0]['name']}")
    print(f"  Medications: {len(patient['medications'])} current")
    print()

    # Test 1: Clinical Narrative Generation
    print("=" * 80)
    print("TEST 1: Clinical SOAP Note Generation (Structured Output)")
    print("=" * 80)
    print()
    print("Calling Claude API to generate clinical narrative...")

    try:
        narrative = claude_gen.generate_clinical_narrative(
            patient=patient,
            diagnoses=patient['diagnoses'],
            medications=patient['medications'],
            vitals=patient['vital_signs']
        )

        print("✓ Success! Generated structured clinical narrative:")
        print()
        print("SUBJECTIVE:")
        print(f"  {narrative.subjective}")
        print()
        print("OBJECTIVE:")
        print(f"  {narrative.objective}")
        print()
        print("ASSESSMENT:")
        print(f"  {narrative.assessment}")
        print()
        print("PLAN:")
        print(f"  {narrative.plan}")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    # Test 2: Provider Email Generation
    print("=" * 80)
    print("TEST 2: Provider-to-Provider Email Generation (Structured Output)")
    print("=" * 80)
    print()
    print(f"From: Dr. {provider1['last_name']} ({provider1['specialty']})")
    print(f"To: Dr. {provider2['last_name']} ({provider2['specialty']})")
    print()
    print("Calling Claude API...")

    try:
        email = claude_gen.generate_provider_email(
            patient=patient,
            sender_provider=provider1,
            recipient_provider=provider2,
            reason=f"evaluation and management recommendations for {patient['diagnoses'][0]['name']}"
        )

        print("✓ Success! Generated provider correspondence:")
        print()
        print(f"SUBJECT: {email.subject}")
        print()
        print("INTRODUCTION:")
        print(f"  {email.introduction}")
        print()
        print("CLINICAL SUMMARY:")
        print(f"  {email.clinical_summary}")
        print()
        print("CONSULTATION REQUEST:")
        print(f"  {email.consultation_request}")
        print()
        print("CLOSING:")
        print(f"  {email.closing_remarks}")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    # Test 3: Patient Communication
    print("=" * 80)
    print("TEST 3: Patient Communication Email Generation (Structured Output)")
    print("=" * 80)
    print()
    print("Calling Claude API...")

    try:
        patient_email = claude_gen.generate_patient_communication(
            patient=patient,
            context="Your recent lab results show improvement in your A1C levels.",
            communication_type="test_results"
        )

        print("✓ Success! Generated patient email:")
        print()
        print(patient_email.greeting)
        print()
        print(patient_email.body)
        print()
        print(patient_email.closing)
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    # Summary
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print("✓ Claude 4.5 Sonnet integration working")
    print("✓ Structured outputs with Pydantic models successful")
    print("✓ All three use cases validated:")
    print("  1. Clinical SOAP notes")
    print("  2. Provider-to-provider emails")
    print("  3. Patient communication")
    print()
    print("Next: Integrate into document formatters for 20% LLM-enhanced generation")
    return 0


if __name__ == '__main__':
    sys.exit(main())
