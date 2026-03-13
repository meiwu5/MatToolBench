#!/bin/bash
# =============================================================================
# Ablation experiments: test key parameters using GPT-5.
#
# Ablation dimensions:
#   1. Origin template scripts:  script vs no_script
#   2. GUI screen parser (SoM):  oss | a11y | mixed-oss | omni
#
# Note: max_steps (not a separate code_retries param) controls how many
# self-correction rounds the CodeAgent can perform.
#
# Usage (from the repo root):
#   bash scripts/run_ablations.sh [--emulator_ip <ip>]
#
# Results are written to client/results/ablation_*/
# After all runs, collect scores with:
#   python scripts/print_results.py --prefix ablation_
# =============================================================================

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLIENT_DIR="$SCRIPT_DIR/../src/mattoolbench-container/client"

EMULATOR_ARGS=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --emulator_ip) EMULATOR_ARGS="--emulator_ip $2"; shift 2;;
        *) shift;;
    esac
done

CONFIGS=(
    # ── Dimension 1: Origin template script ────────────────────────────────
    "experiment_configs/ablation_origin_script.json"
    "experiment_configs/ablation_origin_noscript.json"

    # ── Dimension 2: GUI screen parser (SoM mode) ──────────────────────────
    "experiment_configs/ablation_gui_som_oss.json"
    "experiment_configs/ablation_gui_som_a11y.json"
    "experiment_configs/ablation_gui_som_mixed.json"
    "experiment_configs/ablation_gui_som_omni.json"
)

cd "$CLIENT_DIR"

for cfg in "${CONFIGS[@]}"; do
    echo "======================================================"
    echo "Starting ablation: $cfg"
    echo "======================================================"
    python run.py --config "$cfg" $EMULATOR_ARGS
    echo "Finished: $cfg"
    echo ""
done

echo "======================================================"
echo "All ablations done."
echo "Collect results: python scripts/print_results.py --prefix ablation_"
echo "======================================================"
