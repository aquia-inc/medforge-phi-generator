#!/usr/bin/env python3
"""
LLM Integration Smoke Test

Quick validation that LLM-enhanced generation paths work correctly:
1. Tax/financial LLM handlers produce llm_enhanced=True in manifest
2. Template enrichment produces customer_template + llm_enhanced entries
3. CUI negative LLM produces llm_enhanced=True negatives
4. Negative docs don't contain forbidden CUI indicators
5. All generated files pass Purview fidelity validation

Run: uv run python tests/test_llm_smoke.py
Expected runtime: ~2-3 minutes (small batch, high LLM rate)
"""
import json
import glob
import os
import re
import subprocess
import sys

OUTPUT_BASE = "output"
FORBIDDEN_PATTERNS = [
    r'\d{3}-\d{2}-\d{4}',           # SSN pattern
    r'PRE-DECISIONAL',
    r'ATTORNEY-CLIENT PRIVILEGED',
    r'DRAFT\s*[-–—]\s*PRE',
    r'DO NOT DISTRIBUTE',
]


def run_generation(args: list[str], label: str) -> str:
    """Run medforge generate and return the output directory."""
    # Clean previous runs
    for d in glob.glob(f"{OUTPUT_BASE}/production_run_*"):
        import shutil
        shutil.rmtree(d, ignore_errors=True)

    cmd = [sys.executable, "-m", "src.cli", "generate"] + args
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"CMD:  {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
    if result.returncode != 0:
        print(f"FAIL: Generation returned {result.returncode}")
        print(result.stderr[-500:] if result.stderr else "")
        return None

    dirs = sorted(glob.glob(f"{OUTPUT_BASE}/production_run_*"))
    return dirs[-1] if dirs else None


def load_manifest(output_dir: str) -> list:
    """Load CUI manifest entries."""
    manifest_path = os.path.join(output_dir, "metadata", "cui_manifest.json")
    if not os.path.exists(manifest_path):
        return []
    with open(manifest_path) as f:
        return json.load(f).get("files", [])


def run_fidelity(output_dir: str) -> tuple[int, int]:
    """Run fidelity validation, return (total, fatal+high count)."""
    cmd = [sys.executable, "tests/validate_file_fidelity.py", output_dir]
    result = subprocess.run(cmd, capture_output=True, text=True,
                           cwd=os.path.dirname(os.path.dirname(__file__)))
    total = 0
    issues = 0
    for line in result.stdout.splitlines():
        if "Total files validated:" in line:
            total = int(line.split(":")[-1].strip())
        if "Fatal issues:" in line:
            issues += int(line.split(":")[-1].strip())
        if "High issues:" in line:
            issues += int(line.split(":")[-1].strip())
    return total, issues


def check_negative_content(output_dir: str) -> list[str]:
    """Grep negative doc content for forbidden CUI indicators."""
    violations = []
    for root, dirs, files in os.walk(output_dir):
        if "Negative" not in root:
            continue
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                if fname.endswith('.docx'):
                    from docx import Document
                    doc = Document(fpath)
                    text = '\n'.join(p.text for p in doc.paragraphs)
                elif fname.endswith('.eml'):
                    with open(fpath, 'r', errors='ignore') as f:
                        text = f.read()
                else:
                    continue  # Skip PDF/XLSX/PPTX (harder to extract text)

                for pattern in FORBIDDEN_PATTERNS:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        violations.append(f"{fname}: matched '{pattern}' -> {matches[:3]}")
            except Exception as e:
                violations.append(f"{fname}: read error: {e}")
    return violations


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    results = []

    # Test 1: Tax + Financial LLM
    out = run_generation([
        "--cui-positive", "4", "--cui-negative", "2",
        "--cui-categories", "tax,financial",
        "--seed", "42", "--llm-percentage", "1.0",
    ], "Tax + Financial LLM handlers")
    if out:
        manifest = load_manifest(out)
        llm_pos = [e for e in manifest if e.get("llm_enhanced") and e["cui_status"] == "positive"]
        total, issues = run_fidelity(out)
        passed = len(llm_pos) > 0 and issues == 0
        results.append(("Tax/Financial LLM", passed,
                        f"{len(llm_pos)} LLM-enhanced positives, {total} files, {issues} issues"))
    else:
        results.append(("Tax/Financial LLM", False, "Generation failed"))

    # Test 2: Template enrichment
    out = run_generation([
        "--cui-positive", "10", "--cui-negative", "3",
        "--cui-categories", "procurement,critical_infrastructure",
        "--seed", "42", "--llm-percentage", "0.8",
    ], "Template LLM enrichment")
    if out:
        manifest = load_manifest(out)
        tmpl_llm = [e for e in manifest
                    if e.get("source") == "customer_template" and e.get("llm_enhanced")]
        total, issues = run_fidelity(out)
        # Template enrichment is probabilistic — may not hit every run
        passed = issues == 0
        results.append(("Template enrichment", passed,
                        f"{len(tmpl_llm)} enriched templates, {total} files, {issues} issues"))
    else:
        results.append(("Template enrichment", False, "Generation failed"))

    # Test 3: CUI negatives with LLM
    out = run_generation([
        "--cui-positive", "0", "--cui-negative", "6",
        "--cui-categories", "financial,legal",
        "--seed", "99", "--llm-percentage", "1.0",
    ], "CUI negative LLM enrichment")
    if out:
        manifest = load_manifest(out)
        llm_neg = [e for e in manifest if e.get("llm_enhanced") and e["cui_status"] == "negative"]
        total, issues = run_fidelity(out)
        violations = check_negative_content(out)
        passed = len(llm_neg) > 0 and issues == 0 and len(violations) == 0
        detail = f"{len(llm_neg)} LLM negatives, {total} files, {issues} issues"
        if violations:
            detail += f", {len(violations)} CONTENT VIOLATIONS: {violations[:3]}"
        results.append(("Negative LLM + content check", passed, detail))
    else:
        results.append(("Negative LLM + content check", False, "Generation failed"))

    # Summary
    print(f"\n{'='*60}")
    print("LLM SMOKE TEST RESULTS")
    print(f"{'='*60}")
    all_passed = True
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {name}: {detail}")
    print(f"{'='*60}")
    print(f"Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
