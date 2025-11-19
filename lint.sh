#!/bin/bash
# Quick lint check for the project

echo "🔍 Running linting checks..."
echo

# Syntax check
echo "1. Python syntax check..."
python3 -m py_compile src/cli.py src/formatters/*.py src/generators/*.py 2>&1 && echo "✓ Syntax OK" || exit 1
echo

# Ruff linting (ignore minor issues)
echo "2. Ruff linting (critical issues only)..."
uv run ruff check src/cli.py src/formatters/ src/generators/llm_generator.py src/generators/patient_generator.py --select F,E --ignore E501 && echo "✓ No critical issues" || exit 1
echo

echo "✅ All checks passed!"
