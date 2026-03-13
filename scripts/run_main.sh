#!/bin/bash
# =============================================================================
# Main benchmark experiment: evaluate multiple LLMs on the full MatToolBench.
#
# Usage (from the repo root):
#   bash scripts/run_main.sh [--emulator_ip <ip>] [--models <m1,m2,...>]
#
# The --models flag (optional) runs only the listed models (comma-separated):
#   bash scripts/run_main.sh --models gpt-5,qwen-max
#
# Each model writes results to client/results/main_<model_name>/
# After all runs, collect scores with:
#   python scripts/print_results.py --prefix main_
# =============================================================================

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLIENT_DIR="$SCRIPT_DIR/../src/mattoolbench-container/client"

EMULATOR_ARGS=""
MODELS_FILTER=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --emulator_ip) EMULATOR_ARGS="--emulator_ip $2"; shift 2;;
        --models)      MODELS_FILTER="$2"; shift 2;;
        *) shift;;
    esac
done

ALL_CONFIGS=(
    "experiment_configs/main_gpt_5.json"
    "experiment_configs/main_gpt_5_mini.json"
    "experiment_configs/main_claude_sonnet_4_6.json"
    "experiment_configs/main_qwen_max.json"
    "experiment_configs/main_gemini_1.5_pro.json"
)

cd "$CLIENT_DIR"

for cfg in "${ALL_CONFIGS[@]}"; do
    if [[ -n "$MODELS_FILTER" ]]; then
        matched=0
        IFS=',' read -ra filter_list <<< "$MODELS_FILTER"
        for m in "${filter_list[@]}"; do
            safe_m="${m//-/_}"
            if [[ "$cfg" == *"$safe_m"* ]]; then matched=1; break; fi
        done
        [[ $matched -eq 0 ]] && continue
    fi

    echo "======================================================"
    echo "Starting main experiment: $cfg"
    echo "======================================================"
    python run.py --config "$cfg" $EMULATOR_ARGS
    echo "Finished: $cfg"
    echo ""
done

echo "======================================================"
echo "All main experiments done."
echo "Collect results: python scripts/print_results.py --prefix main_"
echo "======================================================"
