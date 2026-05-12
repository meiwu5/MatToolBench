#!/bin/bash
# MatToolBench 基准测试运行脚本
# 用法: bash scripts/run_benchmark.sh [domain] [model] [trial_id]
#
# 示例:
#   bash scripts/run_benchmark.sh origin gpt-5.4 1
#   bash scripts/run_benchmark.sh jade   gpt-5.4 1
#   bash scripts/run_benchmark.sh mp     gpt-5.4 1

set -e

DOMAIN="${1:-origin}"
MODEL="${2:-gpt-5.4}"
TRIAL="${3:-0}"
CLIENT_DIR="src/mattoolbench-container/client"
RESULT_DIR="results/${DOMAIN}_${MODEL}_trial${TRIAL}"

echo "====================================="
echo "  MatToolBench Benchmark Runner"
echo "  Domain:  $DOMAIN"
echo "  Model:   $MODEL"
echo "  Trial:   $TRIAL"
echo "  Results: $RESULT_DIR"
echo "====================================="

mkdir -p "$RESULT_DIR"

cd "$CLIENT_DIR"

python run.py \
    --agent_name auto \
    --domain "$DOMAIN" \
    --model "$MODEL" \
    --result_dir "../../$RESULT_DIR" \
    --trial_id "$TRIAL" \
    --max_steps 50 \
    --temperature 1.0

echo "Done. Results saved to $RESULT_DIR"
