#!/bin/bash
# Run all ablation experiments sequentially.
# Usage: bash run_ablations.sh [--emulator_ip <ip>]
#
# Each experiment writes results to its own result_dir (defined in the config).
# After all runs, collect scores with:
#   python print_ablation_results.py

set -e
EXTRA_ARGS="$@"   # e.g. --emulator_ip 20.20.20.21

CONFIGS=(
    # ── Origin ablation ────────────────────────────────────────────────
    "experiment_configs/origin_script_gpt5.json"
    "experiment_configs/origin_noscript_gpt5.json"

    # ── GUI ablation ────────────────────────────────────────────────────
    "experiment_configs/gui_oss_gpt5.json"
    "experiment_configs/gui_a11y_gpt5.json"
    "experiment_configs/gui_mixed_gpt5.json"
    "experiment_configs/gui_omni_gpt5.json"

    # ── Code ablation ───────────────────────────────────────────────────
    "experiment_configs/code_retries3_gpt5.json"
    "experiment_configs/code_retries1_gpt5.json"
)

for cfg in "${CONFIGS[@]}"; do
    echo "======================================================"
    echo "Starting: $cfg"
    echo "======================================================"
    python run.py --config "$cfg" $EXTRA_ARGS
    echo "Finished: $cfg"
done

echo ""
echo "All ablations done. Collecting results..."
python print_ablation_results.py
