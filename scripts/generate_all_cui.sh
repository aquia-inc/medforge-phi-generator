#!/bin/bash
# MedForge - Generate all CUI categories (500 positive, 1500 negative each)
# Optimized for HIGH RATE LIMITS (2K requests/min)
# Total output: ~14,000 CUI documents + 2,000 PHI documents = 16,000 documents
#
# Features:
#   - Tracks completed categories in a status file
#   - Can be restarted to continue from where it left off
#   - High parallelization for fast generation
#
# Usage:
#   ./scripts/generate_all_cui.sh          # Start fresh or resume
#   ./scripts/generate_all_cui.sh --reset  # Clear status and start fresh

# Change to project root directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

OUTPUT_DIR="temp/output"
LLM_PERCENT="0.8"       # 80% LLM enhancement (you have the capacity now!)
WORKERS="8"             # 8 parallel workers to maximize throughput
FORMATS="pdf,docx,xlsx,eml"
PAUSE_BETWEEN_CATEGORIES=5  # Short pause between categories

# Status tracking file
STATUS_FILE="$OUTPUT_DIR/.generation_status"

# All categories to generate
CATEGORIES=(
    "critical_infrastructure:Critical Infrastructure"
    "financial:Financial"
    "law_enforcement:Law Enforcement"
    "legal:Legal"
    "procurement:Procurement"
    "proprietary:Proprietary Business"
    "tax:Tax"
    "phi:PHI Documents"
)

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a category is completed
is_completed() {
    local category=$1
    if [[ -f "$STATUS_FILE" ]]; then
        grep -q "^$category:COMPLETED$" "$STATUS_FILE" 2>/dev/null
        return $?
    fi
    return 1
}

# Function to mark a category as completed
mark_completed() {
    local category=$1
    echo "$category:COMPLETED" >> "$STATUS_FILE"
    log "Marked $category as COMPLETED"
}

# Function to mark a category as in-progress
mark_in_progress() {
    local category=$1
    # Remove any existing status for this category
    if [[ -f "$STATUS_FILE" ]]; then
        grep -v "^$category:" "$STATUS_FILE" > "$STATUS_FILE.tmp" 2>/dev/null || true
        mv "$STATUS_FILE.tmp" "$STATUS_FILE"
    fi
    echo "$category:IN_PROGRESS:$(date '+%Y-%m-%d %H:%M:%S')" >> "$STATUS_FILE"
}

# Function to show current status
show_status() {
    echo ""
    echo "=============================================="
    echo "GENERATION STATUS"
    echo "=============================================="

    local completed=0
    local pending=0

    for entry in "${CATEGORIES[@]}"; do
        local category="${entry%%:*}"
        local display_name="${entry#*:}"

        if is_completed "$category"; then
            echo "  [✓] $display_name - COMPLETED"
            ((completed++))
        else
            echo "  [ ] $display_name - PENDING"
            ((pending++))
        fi
    done

    echo ""
    echo "Completed: $completed / ${#CATEGORIES[@]}"
    echo "Pending: $pending"
    echo "=============================================="
    echo ""
}

# Function to run a CUI category
run_cui_category() {
    local category=$1
    local display_name=$2

    if is_completed "$category"; then
        log "SKIPPING $display_name (already completed)"
        return 0
    fi

    log "========== Starting: $display_name =========="
    mark_in_progress "$category"

    if uv run python -m src.cli generate \
        --cui-positive 500 \
        --cui-negative 1500 \
        --cui-categories "$category" \
        --cui-notice never \
        --cui-classification never \
        --llm-percentage "$LLM_PERCENT" \
        --formats "$FORMATS" \
        --output "$OUTPUT_DIR" \
        --parallel-workers "$WORKERS"; then

        mark_completed "$category"
        log "========== Completed: $display_name =========="
        return 0
    else
        log "========== FAILED: $display_name =========="
        log "Run ./scripts/generate_all_cui.sh to retry from this point"
        return 1
    fi
}

# Function to run PHI generation
run_phi() {
    local category="phi"
    local display_name="PHI Documents"

    if is_completed "$category"; then
        log "SKIPPING $display_name (already completed)"
        return 0
    fi

    log "========== Starting: $display_name =========="
    mark_in_progress "$category"

    if uv run python -m src.cli generate \
        --phi-positive 500 \
        --phi-negative 1500 \
        --llm-percentage "$LLM_PERCENT" \
        --formats "$FORMATS" \
        --output "$OUTPUT_DIR" \
        --parallel-workers "$WORKERS"; then

        mark_completed "$category"
        log "========== Completed: $display_name =========="
        return 0
    else
        log "========== FAILED: $display_name =========="
        log "Run ./scripts/generate_all_cui.sh to retry from this point"
        return 1
    fi
}

# Function to pause between categories
pause_between() {
    log "Brief pause for $PAUSE_BETWEEN_CATEGORIES seconds..."
    sleep "$PAUSE_BETWEEN_CATEGORIES"
}

# Handle --reset flag
if [[ "$1" == "--reset" ]]; then
    log "Resetting generation status..."
    rm -f "$STATUS_FILE"
    log "Status cleared. Run ./generate_all_cui.sh to start fresh."
    exit 0
fi

# Create output directory if needed
mkdir -p "$OUTPUT_DIR"

# Show banner
echo "=============================================="
echo "MedForge - Full CUI + PHI Generation"
echo "=============================================="
echo "Output directory: $OUTPUT_DIR"
echo "LLM percentage: $LLM_PERCENT (80%)"
echo "Parallel workers: $WORKERS"
echo "Formats: $FORMATS"
echo "=============================================="
echo ""
echo "This will generate:"
echo "  - 7 CUI categories × (500 positive + 1500 negative) = 14,000 CUI docs"
echo "  - 500 PHI positive + 1500 PHI negative = 2,000 PHI docs"
echo "  - Total: ~16,000 documents"
echo ""
echo "With 2K req/min rate limit and 8 workers:"
echo "  Estimated time: ~1-2 hours"
echo "  Estimated size: ~1.2-1.6 GB"
echo ""

# Check for existing status
if [[ -f "$STATUS_FILE" ]]; then
    log "Found existing status file. Resuming from last checkpoint..."
    show_status
    echo "To start fresh, run: ./scripts/generate_all_cui.sh --reset"
    echo ""
else
    log "Starting fresh generation..."
fi

echo "Starting in 5 seconds... (Ctrl+C to cancel)"
sleep 5

START_TIME=$(date +%s)

# Track if any failures occurred
FAILED=0

# Generate all 7 CUI categories
log "Starting CUI generation..."
echo ""

# Critical Infrastructure
if ! run_cui_category "critical_infrastructure" "Critical Infrastructure"; then
    FAILED=1
else
    show_status
    pause_between
fi

# Financial
if [[ $FAILED -eq 0 ]]; then
    if ! run_cui_category "financial" "Financial"; then
        FAILED=1
    else
        show_status
        pause_between
    fi
fi

# Law Enforcement
if [[ $FAILED -eq 0 ]]; then
    if ! run_cui_category "law_enforcement" "Law Enforcement"; then
        FAILED=1
    else
        show_status
        pause_between
    fi
fi

# Legal
if [[ $FAILED -eq 0 ]]; then
    if ! run_cui_category "legal" "Legal"; then
        FAILED=1
    else
        show_status
        pause_between
    fi
fi

# Procurement
if [[ $FAILED -eq 0 ]]; then
    if ! run_cui_category "procurement" "Procurement"; then
        FAILED=1
    else
        show_status
        pause_between
    fi
fi

# Proprietary
if [[ $FAILED -eq 0 ]]; then
    if ! run_cui_category "proprietary" "Proprietary Business"; then
        FAILED=1
    else
        show_status
        pause_between
    fi
fi

# Tax
if [[ $FAILED -eq 0 ]]; then
    if ! run_cui_category "tax" "Tax"; then
        FAILED=1
    else
        show_status
        pause_between
    fi
fi

# PHI Documents
if [[ $FAILED -eq 0 ]]; then
    if ! run_phi; then
        FAILED=1
    else
        show_status
    fi
fi

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "=============================================="
if [[ $FAILED -eq 0 ]]; then
    log "ALL GENERATION COMPLETE!"
    echo "=============================================="
    echo "Total time: ${HOURS}h ${MINUTES}m ${SECONDS}s"
    echo "Output location: $OUTPUT_DIR"
    echo ""
    echo "To view statistics:"
    echo "  uv run python -m src.cli stats $OUTPUT_DIR --tree"
    echo ""
    echo "To validate documents:"
    echo "  uv run python -m src.cli validate $OUTPUT_DIR"
else
    log "GENERATION INCOMPLETE - Some categories failed"
    echo "=============================================="
    show_status
    echo "To resume from where you left off, run:"
    echo "  ./scripts/generate_all_cui.sh"
    echo ""
    echo "To start completely fresh, run:"
    echo "  ./scripts/generate_all_cui.sh --reset"
fi
echo "=============================================="
