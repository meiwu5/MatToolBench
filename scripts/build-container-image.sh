#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

source ./shared.sh

mode=azure
build_base_image=false
hf_endpoint=""      # empty = use Dockerfile default (hf-mirror.com)
http_proxy=""
https_proxy=""

# Parse the command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            mode=$2
            shift 2
            ;;
        --build-base-image)
            build_base_image=$2
            shift 2
            ;;
        --hf-endpoint)
            hf_endpoint=$2
            shift 2
            ;;
        --http-proxy)
            http_proxy=$2
            shift 2
            ;;
        --https-proxy)
            https_proxy=$2
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --mode <dev/azure>            : Mode (default: azure)"
            echo "  --build-base-image <true/false>: Whether to build the mattoolbench-base image (default: false)"
            echo "  --hf-endpoint <url>            : HuggingFace endpoint (default: https://hf-mirror.com)"
            echo "                                   Use https://huggingface.co if you have direct access"
            echo "  --http-proxy  <url>            : HTTP proxy for wget/pip inside Docker build"
            echo "                                   Example: http://host.docker.internal:7890"
            echo "  --https-proxy <url>            : HTTPS proxy for wget/pip inside Docker build"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            log_error_exit "Unknown option: $1"
            ;;
    esac
done

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "$SCRIPT_DIR/../"

# Build --build-arg flags for base image (only non-empty values are passed)
base_extra_args=()
[[ -n "$hf_endpoint"  ]] && base_extra_args+=(--build-arg "HF_ENDPOINT=${hf_endpoint}")
[[ -n "$http_proxy"   ]] && base_extra_args+=(--build-arg "HTTP_PROXY=${http_proxy}")
[[ -n "$https_proxy"  ]] && base_extra_args+=(--build-arg "HTTPS_PROXY=${https_proxy}")

if [ "$build_base_image" = true ]; then
  echo "Building mattoolbench-base image"
  docker build --build-arg PROFILE_MODE=false \
    "${base_extra_args[@]}" \
    -f $SCRIPT_DIR/../src/mattoolbench-container/Dockerfile-MatToolBench-Base \
    -t mattoolbench-base:latest \
    $SCRIPT_DIR/../
else
  echo "Skipping mattoolbench-base image build"
fi

if [ "$mode" = "dev" ]; then # Only for dev mode
  mattoolbench_image_name="mattoolbench-$mode"
else
  mattoolbench_image_name="mattoolbench"
fi

docker build --build-arg DEPLOY_MODE=$mode \
  -f $SCRIPT_DIR/../src/mattoolbench-container/Dockerfile-MatToolBench \
  -t $mattoolbench_image_name:latest \
  $SCRIPT_DIR/../

docker tag $mattoolbench_image_name:latest mattoolbench/$mattoolbench_image_name:latest