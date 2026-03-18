
<div align="center">

# MatToolBench

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)

</div>

**MatToolBench** is a desktop agent benchmark for materials science, evaluating AI agents on real-world tasks across professional materials characterization and analysis software. It covers three task categories 鈥?**Origin** (script-based data analysis), **GUI** (visual interaction with materials-science tools), and **Code** (programmatic database queries) 鈥?and is built on top of a Windows 11 virtual machine environment running inside Docker.

---

## 馃摎 Task Categories

| Category | Domains | Tasks | Agent Type | Description |
|----------|---------|-------|------------|-------------|
| **Origin** | XRD, XPS, Raman, Cycle, Step, CE | ~16 | OriginAgent | Writes OriginPro scripts to analyze experimental data and generate plots |
| **GUI** | Jade, Avantage, VESTA, DM, MS | ~100 | GUIAgent | Visually navigates materials software GUIs to complete analysis tasks |
| **Code** | MP, OQMD, PyMatgen, OPTIMADE | ~70 | CodeAgent | Generates Python code to query materials databases and retrieve properties |
---

## 馃椇锔?System Overview

```
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹?                    Input (Task Config)                      鈹?
鈹?             experiment_configs/*.json                       鈹?
鈹?        { task_id, agent_type, model, ... }                 鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                        鈹?
          鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
          鈹?                          鈹?
    run-local.sh                 run_azure.py
          鈹?                          鈹?
    Local Docker               Azure ML Job
    (single machine)           (parallel VMs)
          鈹?                          鈹?
          鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                        鈹?
                     run.py
                        鈹?
          鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹尖攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
          鈹?            鈹?            鈹?
     GUI Agent    Origin Agent   Code Agent
          鈹?            鈹?            鈹?
    screenshot 鈫?   LLM writes     LLM writes
    plan 鈫?act      .py script     query code
          鈹?            鈹?            鈹?
   Windows VM      OriginPro      Database API
  (QEMU/Docker)    (in VM)        (HTTP)
   Jade/VESTA/
   Avantage/DM/
   MatStudio
          鈹?            鈹?            鈹?
          鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                        鈹?
                   evaluators/
                (getters + metrics)
                        鈹?
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹?                       Output                               鈹?
鈹?   output_result/  +  results/logs/  +  screenshot traces   鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
```

**Local vs. Azure at a glance:**

| | Local | Azure |
|---|---|---|
| Entry point | `scripts/run-local.sh` | `scripts/run_azure.py` |
| Storage | Local disk (`vm/storage/`) | Azure Blob Storage |
| Concurrency | Serial, single machine | Parallel ML Jobs (`num_workers`) |
| Docker image | `mattoolbench:latest` (built locally) | `mattoolbench/mattoolbench:latest` (pulled from registry) |
| VM image | Persisted in `vm/storage/` | Uploaded to Azure datastore |

---

## 馃梻锔?Project Structure

```
MatToolBench/
鈹溾攢鈹€ config.json                        # API keys, Azure credentials
鈹溾攢鈹€ requirements.txt                   # Host-side deps (azure-ai-ml, etc.)
鈹?
鈹溾攢鈹€ docs/                              # Extended development guides
鈹?  鈹溾攢鈹€ Develop-Agent.md
鈹?  鈹溾攢鈹€ Develop-Tasks.md
鈹?  鈹斺攢鈹€ Development-Tips.md
鈹?
鈹溾攢鈹€ scripts/
鈹?  鈹溾攢鈹€ build-container-image.sh       # Build Docker image
鈹?  鈹溾攢鈹€ run-local.sh                   # Local benchmark runner
鈹?  鈹溾攢鈹€ run_azure.py                   # Azure ML runner (full cloud mode)
鈹?  鈹溾攢鈹€ run_local_agent.py             # Run agent locally against Azure-hosted VM
鈹?  鈹溾攢鈹€ show_azure.py                  # Aggregate results from Azure runs
鈹?  鈹溾攢鈹€ experiments.json               # Azure experiment config
鈹?  鈹斺攢鈹€ azure_files/                   # Azure startup scripts
鈹?      鈹溾攢鈹€ run_entry.py               # Job entry point executed on each Azure VM
鈹?      鈹斺攢鈹€ compute-instance-startup.sh
鈹?
鈹斺攢鈹€ src/mattoolbench-container/
    鈹溾攢鈹€ Dockerfile-MatToolBench-Base   # Layer 1: Python / CUDA / model weights
    鈹溾攢鈹€ Dockerfile-MatToolBench        # Layer 2: client code + VM files
    鈹溾攢鈹€ entry.sh / start_vm.sh / start_client.sh
    鈹?
    鈹溾攢鈹€ vm/
    鈹?  鈹溾攢鈹€ image/setup.iso            # Windows 11 ISO
    鈹?  鈹溾攢鈹€ storage/                   # VM disk snapshots (windows.base, etc.)
    鈹?  鈹溾攢鈹€ unattend-files/            # Automated install answer files
    鈹?  鈹斺攢鈹€ setup/                     # PowerShell setup scripts + tools
    鈹?      鈹斺攢鈹€ [Avantage / VESTA / DigitalMicrograph / Materials Studio / ...]
    鈹?
    鈹斺攢鈹€ client/                        # Python client (runs inside container)
        鈹溾攢鈹€ run.py                     # Main execution entry point
        鈹溾攢鈹€ experiment_configs/        # JSON configs for each experiment
        鈹?  鈹溾攢鈹€ main_gpt_5.json
        鈹?  鈹溾攢鈹€ main_claude_sonnet_4_6.json
        鈹?  鈹溾攢鈹€ main_gemini_1.5_pro.json
        鈹?  鈹溾攢鈹€ ablation_gui_som_*.json
        鈹?  鈹斺攢鈹€ ...
        鈹溾攢鈹€ desktop_env/
        鈹?  鈹溾攢鈹€ envs/desktop_env.py    # Core VM environment class
        鈹?  鈹溾攢鈹€ controllers/           # VM / Python / setup controllers
        鈹?  鈹斺攢鈹€ evaluators/
        鈹?      鈹溾攢鈹€ getters/           # Read state from each tool (jade, vesta, ...)
        鈹?      鈹斺攢鈹€ metrics/           # Scoring functions
        鈹溾攢鈹€ mm_agents/
        鈹?  鈹溾攢鈹€ gui_agent.py
        鈹?  鈹溾攢鈹€ origin_agent.py
        鈹?  鈹溾攢鈹€ code_agent.py
        鈹?  鈹斺攢鈹€ navi/                  # NaviAgent: screen parsing + LLM planner
        鈹?      鈹溾攢鈹€ screenparsing_oss/ # GroundingDINO, OmniParser, OCR
        鈹?      鈹溾攢鈹€ gpt/               # GPT-4V / Phi-3 vision planners
        鈹?      鈹斺攢鈹€ llm/               # Text-only LLM planners
        鈹溾攢鈹€ task_code/                 # Reference code per database (MP, OQMD, ...)
        鈹溾攢鈹€ evaluation_examples_windows/  # Task definitions (JSON)
        鈹斺攢鈹€ output_result/             # Experiment outputs
```

---

## 鈽濓笍 Pre-requisites

- Docker daemon installed and running. On Windows, use [Docker with WSL 2](https://docs.docker.com/desktop/wsl/).
- An [OpenAI](https://platform.openai.com/docs/introduction) or [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) API Key.
- Python 3.12 鈥?recommended via [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html):
  ```bash
  conda create -n mattoolbench python=3.12
  conda activate mattoolbench
  ```

Clone and install:
```bash
git clone https://github.com/<your-org>/MatToolBench.git
cd MatToolBench
pip install -r requirements.txt
```

---

## 馃捇 Local Deployment (WSL or Linux)

### 1. Configuration

Create `config.json` at the project root:
```json
{
    "OPENAI_API_KEY": "<your-openai-key>",
    "OPENAI_ENDPOINT": "https://api.openai.com/v1",
    "AZURE_API_KEY": "<your-azure-openai-key>",
    "AZURE_ENDPOINT": "https://yourendpoint.openai.azure.com/"
}
```

> You only need **one** of the two blocks (OpenAI or Azure OpenAI). The script checks both and raises an error if neither is provided.

### 2. Build the Docker Image

Build base image and final image in one step:
```bash
cd scripts
./build-container-image.sh --build-base-image true
```

> The build installs Python dependencies, CUDA libraries, and downloads model weights (GroundingDINO, OmniParser). This can take **30鈥?0 minutes** depending on network speed.

If the base image (`mattoolbench-base:latest`) is already built and unchanged, skip it:
```bash
./build-container-image.sh   # --build-base-image defaults to false
```

### 3. Prepare the Windows 11 VM

#### 3.1 Download Windows 11 ISO
Visit [Microsoft Evaluation Center](https://info.microsoft.com/ww-landing-windows-11-enterprise.html), download **Windows 11 Enterprise Evaluation (90-day trial, English, United States)** (~6 GB), rename it to `setup.iso`, and place it at:
```
src/mattoolbench-container/vm/image/setup.iso
```

#### 3.2 Build the Golden Image

You have two options 鈥?use our pre-built snapshot (recommended) or build from scratch.

---

##### Option A: Use Our Pre-built VM Snapshot (Recommended)

Skip the entire installation process by downloading our ready-to-use snapshot. All materials science software is already installed and configured.

**Download:** [MatToolBench VM Snapshot](TODO)  <!-- replace with actual link -->

Extract and place the files at:
```
src/mattoolbench-container/vm/storage/
鈹溾攢鈹€ windows.base
鈹溾攢鈹€ windows.boot
鈹溾攢鈹€ windows.mac
鈹溾攢鈹€ windows.rom
鈹溾攢鈹€ windows.vars
鈹溾攢鈹€ windows.ver
鈹斺攢鈹€ data.img
```

Then skip to [搂 4 Running the Benchmark](#4-running-the-benchmark) directly.

---

##### Option B: Build from Scratch

The automated script handles Windows 11 installation. Specialty materials science software must be installed manually via the shared folder.

**Step B-1 鈥?Download the software installers**

Download each installer and place it in the corresponding subdirectory under `src/mattoolbench-container/vm/setup/`:

| Software | Purpose | Version | Installer path | Download |
|----------|---------|---------|----------------|----------|
| **OriginPro** | Data analysis & plotting | 2024 | `vm/setup/OriginSetup.exe` | [Download](TODO) |
| **Jade** | XRD phase analysis | 9.0 | `vm/setup/Jade_setup.exe` | [Download](TODO) |
| **Avantage** | XPS analysis | 6.6.0 | `vm/setup/Avantage 6.6.0/Setup.exe` | [Download](TODO) |
| **VESTA** | Crystal structure visualization | 3.90.1 | `vm/setup/VESTA-win64/` | [Download](https://jp-minerals.org/vesta/en/download.html) |
| **Digital Micrograph (GMS)** | TEM/EELS analysis | 3.5 | `vm/setup/DigitalMicrograph/setup.exe` | [Download](TODO) |
| **Materials Studio** | Molecular simulation | 2023 (64-bit) | `vm/setup/Materials Studio 2023(64bit)/` | [Download](TODO) |

> VESTA is open-source and can be downloaded from its official website. The other tools are commercial software; contact the respective vendors or use your institution's license.

**Step B-2 鈥?Start the automated Windows 11 installation**

```bash
cd scripts
./run-local.sh --mode dev --prepare-image true
```

Open `http://localhost:8006` in your browser to watch the VM boot and the automated setup progress (~20 minutes for Windows install + basic tools).

**Step B-3 鈥?Install materials science software inside the VM**

Once the automated setup finishes and the Windows desktop is visible at `http://localhost:8006`:

1. Open **File Explorer** inside the VM and navigate to `\\host.lan\Data` 鈥?this is the shared folder that maps directly to `src/mattoolbench-container/vm/setup/` on your host.
2. Run each installer from this shared folder in the following order:

```
\\host.lan\Data\OriginSetup.exe              鈫?follow the installer wizard
\\host.lan\Data\Jade_setup.exe               鈫?follow the installer wizard
\\host.lan\Data\Avantage 6.6.0\Setup.exe     鈫?follow the installer wizard
\\host.lan\Data\VESTA-win64\VESTA_Setup.exe  鈫?follow the installer wizard
\\host.lan\Data\DigitalMicrograph\setup.exe  鈫?follow the installer wizard
\\host.lan\Data\Materials Studio 2023(64bit)\Setup.exe 鈫?follow the installer wizard
```

3. After all software is installed, shut down the VM gracefully from inside Windows (Start 鈫?Shut down). The disk snapshot in `vm/storage/` is updated automatically.

> **Tip:** You can also use RDP to connect to the VM at `localhost:3390` (username: `Docker`, password: see `vm/setup/`) for a more comfortable installation experience.

#### 3.3 Saving and Reusing a VM Snapshot

After building the golden image (Option B above), back up the entire `vm/storage/` directory to avoid repeating installation next time:

```
vm/storage/
鈹溾攢鈹€ windows.base     鈫?main VM disk image
鈹溾攢鈹€ windows.boot
鈹溾攢鈹€ windows.mac
鈹溾攢鈹€ windows.rom
鈹溾攢鈹€ windows.vars
鈹溾攢鈹€ windows.ver
鈹斺攢鈹€ data.img
```

Copy this directory to a safe location. To restore, simply copy it back before running `./run-local.sh`.

### 4. Running the Benchmark

#### 4.1 Quick Start
```bash
cd scripts
./run-local.sh
```

#### 4.2 Using Experiment Config Files

All experiment parameters are captured in JSON files under `src/mattoolbench-container/client/experiment_configs/`:

```bash
cd src/mattoolbench-container/client
python run.py --config experiment_configs/main_gpt_5.json

# Override individual parameters at runtime:
python run.py --config experiment_configs/main_gpt_5.json --trial_id 1
```

Available main configs:

| Config file | Model |
|---|---|
| `main_gpt_5.json` | GPT-5 (OpenAI) |
| `main_gpt_5_mini.json` | GPT-5-mini |
| `main_claude_sonnet_4_6.json` | Claude Sonnet 4.6 |
| `main_gemini_1.5_pro.json` | Gemini 1.5 Pro |
| `main_qwen_max.json` | Qwen-Max |

#### 4.3 Interactive / Debug Mode

Start the container without launching VM and client automatically:
```bash
./run-local.sh --interactive true
# Then inside the container:
./start_vm.sh
./start_client.sh
```

Test that the Windows VM is reachable:
```bash
./run-local.sh --connect true
# Inside the container:
curl -X GET http://20.20.20.21:5000/screenshot  # should return HTTP 200
```

#### 4.4 Viewing Results
```bash
cd src/mattoolbench-container/client
python show_result.py --result_dir results/main_gpt_5
python print_ablation_results.py
```

Logs:
- PowerShell setup log: `vm/setup/ps_script_log.txt`
- Windows server log: `vm/setup/server/server.log`

---

## 鈽侊笍 Azure Cloud Deployment

Azure deployment runs the benchmark in parallel across multiple Azure ML Compute Instances 鈥?each instance hosts an independent Windows 11 VM, and all workers run simultaneously to maximize throughput.

### Architecture

```
Your Machine
  鈹斺攢鈹€ run_azure.py
        鈹?
        鈹溾攢鈹€ Creates N Compute Instances (parallel)
        鈹?    w0<exp>, w1<exp>, ..., w{N-1}<exp>
        鈹?
        鈹斺攢鈹€ Submits N ML Jobs (parallel)
              Each job on its Compute Instance:
                鈹溾攢鈹€ Pulls Docker image from registry
                鈹溾攢鈹€ Copies VM snapshot from Azure Blob
                鈹溾攢鈹€ Boots Windows 11 VM (QEMU)
                鈹斺攢鈹€ Runs Python agent (run.py)
```

There are **two deployment modes** on Azure:

| Mode | When to use | How |
|------|-------------|-----|
| **Full cloud** | Agent runs inside the Azure VM, fully automated | `vm_only: false` in experiments.json |
| **VM-only + local agent** | Windows VM on Azure, agent code runs on your local machine | `vm_only: true` + `run_local_agent.py` |

---

### Step 1 鈥?Azure Prerequisites

You need:
- An **Azure subscription** with sufficient quota for the chosen VM SKU (e.g., `Standard_D8_V3` requires 8 vCPU cores per worker)
- An **Azure ML Workspace** (create one at [ml.azure.com](https://ml.azure.com))
- An **Azure Blob Storage datastore** registered in the workspace (the default `workspaceblobstore` is used)
- The **Azure CLI** logged in, or credentials configured for `DefaultAzureCredential`

Request quota increases if needed:
> Azure ML portal 鈫?your workspace 鈫?Compute 鈫?Quotas 鈫?Request increase

---

### Step 2 鈥?Add Azure Credentials to `config.json`

Extend your `config.json` with Azure ML credentials:

```json
{
    "OPENAI_API_KEY": "<your-openai-key>",
    "OPENAI_ENDPOINT": "https://api.openai.com/v1",
    "AZURE_API_KEY": "<your-azure-openai-key>",
    "AZURE_ENDPOINT": "https://yourendpoint.openai.azure.com/",

    "AZURE_SUBSCRIPTION_ID": "<your-subscription-id>",
    "AZURE_ML_RESOURCE_GROUP": "<your-resource-group>",
    "AZURE_ML_WORKSPACE_NAME": "<your-workspace-name>",

    "AZURE_INSTANCE_IPS": []
}
```

`AZURE_INSTANCE_IPS` is used in VM-only mode (see Step 6). Leave it as an empty list for full-cloud mode.

---

### Step 3 鈥?Upload the VM Snapshot to Azure Blob

The Windows 11 golden image must be available on Azure Blob Storage so each worker can download it at startup.

1. Build the golden image locally (see [Local 搂 3.2](#32-build-the-golden-image)) or obtain a pre-built snapshot.
2. Upload the entire `vm/storage/` directory to your Azure datastore:

```bash
# Using Azure CLI 鈥?upload the snapshot directory
az storage blob upload-batch \
    --account-name <your-storage-account> \
    --destination storage \
    --source src/mattoolbench-container/vm/storage/
```

Or use [Azure Storage Explorer](https://azure.microsoft.com/en-us/products/storage/storage-explorer) to drag-and-drop the `vm/storage/` folder into a container named `storage` (matching the default `datastore_input_path`).

The expected layout on Blob after upload:
```
storage/
鈹溾攢鈹€ windows.base
鈹溾攢鈹€ windows.boot
鈹溾攢鈹€ windows.mac
鈹溾攢鈹€ windows.rom
鈹溾攢鈹€ windows.vars
鈹溾攢鈹€ windows.ver
鈹斺攢鈹€ data.img
```

---

### Step 4 鈥?Upload the Compute Instance Startup Script

Each Azure Compute Instance runs a startup script on creation. Upload it to your Azure ML workspace filestore:

```bash
az ml workspace show --name <workspace> --resource-group <rg>
# Navigate to Files in the ML Studio, or use azcopy:
azcopy copy scripts/azure_files/compute-instance-startup.sh \
    "https://<storage>.blob.core.windows.net/azureml/Users/<username>/compute-instance-startup.sh"
```

Update `ci_startup_script_path` in `experiments.json` to match the path under `Users/`:
```json
"ci_startup_script_path": "Users/<your-username>/compute-instance-startup.sh"
```

---

### Step 5 鈥?Configure `scripts/experiments.json`

```json
{
  "experiment_1": {
    "ci_startup_script_path": "Users/<your-username>/compute-instance-startup.sh",
    "docker_img_name":        "meiwu/mattoolbench:latest",
    "datastore_input_path":   "storage",
    "exp_name":               "Experiment1",
    "vm_size":                "Standard_D8_V3",
    "num_workers":            10,
    "agent":                  "auto",
    "model_name":             "gpt-5",
    "som_origin":             "oss",
    "a11y_backend":           "uia",
    "origin_mode":            "script",
    "json_name":              "evaluation_examples_windows/test_all.json",
    "vm_only":                false
  }
}
```

**Parameter reference:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ci_startup_script_path` | Path to the startup script in the ML workspace filestore | 鈥?|
| `docker_img_name` | Docker Hub image pulled on each VM | `meiwu/mattoolbench:latest` |
| `datastore_input_path` | Azure Blob path containing the VM snapshot | `storage` |
| `exp_name` | Experiment name; also used as the Azure ML Experiment name | 鈥?|
| `vm_size` | Azure VM SKU for each Compute Instance | `Standard_D8_V3` |
| `num_workers` | Number of parallel Compute Instances / ML Jobs | `1` |
| `agent` | Agent routing (`auto`, `gui`, `code`, `origin`, `navi`) | `auto` |
| `model_name` | LLM backbone (e.g., `gpt-5`, `claude-sonnet-4-6`) | 鈥?|
| `som_origin` | Screen-parsing method (`oss`, `a11y`, `mixed-oss`, `omni`, `mixed-omni`, `no_omni`) | `oss` |
| `a11y_backend` | Accessibility backend (`uia`, `win32`) | `uia` |
| `origin_mode` | Template script injection (`script`, `no_script`) | `script` |
| `json_name` | Task list JSON inside the container | `evaluation_examples_windows/test_all.json` |
| `vm_only` | If `true`, start VM only; agent runs locally via `run_local_agent.py` | `false` |
| `use_managed_identity` | Use Azure Managed Identity instead of service principal | `false` |

---

### Step 6 鈥?Launch the Experiment

**Full cloud mode** (agent runs on Azure, fully automated):

```bash
cd scripts
python run_azure.py --experiments_json experiments.json
```

`run_azure.py` will:
1. Create (or start) `N` Compute Instances in parallel, named `w0<exp_name>`, `w1<exp_name>`, 鈥?
2. Submit `N` ML Jobs in parallel 鈥?each job downloads the VM snapshot, boots the Windows VM, and runs the agent.

Monitor job status in the [Azure ML Studio](https://ml.azure.com) or via:
```bash
python show_azure.py --result_dir <your-result-dir> \
                     --json_config experiments.json \
                     --output_file results_table.md
```

---

### Step 7 (Optional) 鈥?VM-Only Mode + Local Agent

Use this mode when you want the **Windows VMs on Azure** but the **agent code running on your local machine** (e.g., for faster iteration on agent logic without rebuilding the Docker image).

**Step 7.1 鈥?Start VMs only**

Set `vm_only: true` in `experiments.json` and launch:
```bash
python run_azure.py --experiments_json experiments.json
```

Each job will boot the Windows VM and then wait indefinitely for an incoming SSH tunnel connection. The Windows API is exposed on port 5000 inside the VM, and QEMU QMP on port 7200.

**Step 7.2 鈥?Get the public IP of each Compute Instance**

Find the SSH endpoint in the Azure ML portal:
> Compute 鈫?Compute Instances 鈫?select instance 鈫?SSH endpoint

Or add the IPs directly to `config.json` (index = worker ID):
```json
"AZURE_INSTANCE_IPS": ["20.1.2.3", "20.1.2.4", "20.1.2.5"]
```

The default SSH port for Azure ML Compute Instances is **50000**.

**Step 7.3 鈥?Run the local agent**

Single worker:
```bash
cd scripts
python run_local_agent.py --exp_name experiment_1 --worker_id 0
```

All workers in parallel (uses `num_workers` from `experiments.json`):
```bash
python run_local_agent.py --exp_name experiment_1 --all_workers
```

`run_local_agent.py` automatically:
- Opens an SSH tunnel from your local machine to each Azure Compute Instance
- Assigns each worker a unique loopback address (`127.0.0.1`, `127.0.0.2`, 鈥? to avoid port conflicts
- Waits for the Windows VM to be ready (up to 10 minutes)
- Launches the Python agent pointing at the tunnel endpoint

Additional options:
```
--instance_ip  <ip>     Override the IP for a single worker
--ssh_port     <port>   SSH port (default: 50000)
--pem_path     <path>   Path to SSH private key (.pem)
--result_dir   <path>   Local directory to save results (default: ./results)
```

---

### Step 8 鈥?Collect Results

Results are written to the `result_dir` configured in `experiments.json` (inside the Azure Blob output dataset). Download them:

```bash
az storage blob download-batch \
    --account-name <your-storage-account> \
    --source agent_outputs/<exp_name> \
    --destination ./results/
```

Then summarize:
```bash
cd src/mattoolbench-container/client
python print_ablation_results.py
```

---

## 馃 Agent Architecture

### Agent Routing (`--agent_name`)

| Value | Agent class | Domains |
|---|---|---|
| `auto` *(default)* | Auto-routed by domain | All |
| `gui` | `GUIAgent` | avantage, dm, jade, vesta, ms |
| `code` | `CodeAgent` | mp, oqmd, pymatgen, optimade |
| `origin` | `OriginAgent` | origin |
| `navi` | `NaviAgent` | Legacy visual agent (all domains) |

### GUIAgent (NaviAgent)

Visual agent for materials software GUIs. Each step:
1. Takes a screenshot of the Windows VM
2. Runs **ScreenParser** (SoM) to identify and label UI elements
3. Passes the annotated screenshot to the **LLMPlanner** (any OpenAI-compatible model)
4. Executes the planned action (click, type, scroll, hotkey) via the VM controller

#### Screen Parsing Mode (`--som_origin`)

| `som_origin` | Method | Speed | Requires a11y tree | Local model |
|---|---|---|---|---|
| `oss` *(default)* | Tesseract OCR only | Fast | No | No |
| `a11y` | Windows Accessibility tree (UIA/Win32) | Medium | **Yes** | No |
| `mixed-oss` | Accessibility tree + Tesseract OCR merged | Slow | **Yes** | No |
| `mixed` | Accessibility tree + GroundingDINO | Slow | **Yes** | Yes |
| `omni` | OmniParser (YOLO + Florence) | Slow | No | Yes |
| `mixed-omni` | Accessibility tree + OmniParser | Slowest | **Yes** | Yes |
| `no_omni` | Raw screenshots only (no SoM / no IDs) | Fastest | No | No |

#### Observation Type (`--observation_type`)

Controls which data is collected from the VM on every step. **Must match `som_origin`.**

| `observation_type` | Collects a11y tree | Use with |
|---|---|---|
| `screenshot` *(default)* | No | `oss`, `omni`, `no_omni` |
| `a11y_tree` | **Yes** | `a11y`, `mixed-oss`, `mixed`, `mixed-omni` |
| `screenshot_a11y_tree` | **Yes** | Same as `a11y_tree` |

> **Important:** When `som_origin=oss` or `som_origin=no_omni`, the accessibility tree is never used. Collecting it anyway (`observation_type=a11y_tree`) wastes 5-10 seconds per step on a slow Windows UIA API call. Always keep `observation_type=screenshot` unless you are using an a11y-based SoM mode.

### OriginAgent

Extends NaviAgent. Given a task:
1. Opens the data file in OriginPro (Ctrl+O)
2. Opens the Code Builder (Alt+4)
3. Writes or adapts an OriginPro Python script (optionally seeded by a template from `origin_draw/`)
4. Runs the script (F5) to produce the output figure

Controlled by `--origin_mode`:
- `script` *(default)* 鈥?LLM is given a task-specific template script as context
- `no_script` 鈥?LLM writes the script from scratch (ablation baseline)

Template script categories (`--origin_category`):

| Category | Script | Analysis type |
|---|---|---|
| `xrd` | `XRD_match.py` | XRD phase matching |
| `xps` | `XPS.py` | XPS peak fitting |
| `ftir` | `FTIR.py` | FTIR spectroscopy |
| `raman` | `roman.py` | Raman spectroscopy |
| `cycle` | `cycle.py` | Electrochemical cycling |
| `bs` | `BS.py` | Band structure |
| `step` | `step.py` | Free energy step |
| `ce` | `CE.py` | Coulombic efficiency |
| `auto` *(default)* | 鈥?| Read from each task's JSON config |

### CodeAgent

Text-only agent. Given a task:
1. LLM generates Python code to query a materials database (MP, OQMD, PyMatgen, OPTIMADE)
2. Code is executed inside the VM using the correct virtual environment
3. On failure, stdout/stderr are fed back for self-correction
4. Repeats up to `--code_retries` times (default: 3)

---

## 馃敩 Ablation Experiments

All ablation runs use **GPT-5 as the backbone** with `temperature: 0.0` for reproducibility. Run all ablations at once:

```bash
bash scripts/run_ablations.sh
```

### Dimension 1 鈥?Origin: Template Script Injection

Tests whether injecting a pre-written domain-specific script into the OriginAgent system prompt improves task success on Origin plotting tasks.

| Config file | `origin_mode` | Description |
|---|---|---|
| `ablation_origin_script.json` | `script` | OriginAgent receives a domain template script as context |
| `ablation_origin_noscript.json` | `no_script` | OriginAgent writes the script from scratch (baseline) |

**Research question:** Does providing a task-specific OriginPro script template help the LLM adapt rather than generate from scratch?

### Dimension 2 鈥?GUI: Screen Parser (SoM Mode)

Tests which screen-parsing strategy works best for materials-science GUI tasks across four modalities.

| Config file | `som_origin` | `observation_type` | Screen parsing method | Description |
|---|---|---|---|---|
| `ablation_gui_som_oss.json` | `oss` | `screenshot` | Tesseract OCR only | OCR-only, no structural info (baseline) |
| `ablation_gui_som_a11y.json` | `a11y` | `a11y_tree` | Windows Accessibility tree | Pure structural info, no vision |
| `ablation_gui_som_mixed.json` | `mixed-oss` | `a11y_tree` | A11y tree + OCR merged | Combined modality |
| `ablation_gui_som_omni.json` | `omni` | `screenshot` | OmniParser (YOLO + Florence) | End-to-end visual parsing |
| `ablation_gui_som_no_omni.json` | `no_omni` | `screenshot` | Raw screenshots only | No parser, direct coordinate clicks |

**Research question:** For specialist materials GUI tools (Jade, VESTA, etc.) not seen in general pretraining, does visual grounding outperform structural accessibility?

### Main Experiment 鈥?LLM Comparison

Tests multiple LLM backbones across the full MatToolBench (all task types). Run with:

```bash
bash scripts/run_main.sh
```

| Config file | Model | Task set |
|---|---|---|
| `main_gpt_5.json` | GPT-5 | All (GUI + Origin + Code) |
| `main_gpt_5_mini.json` | GPT-5-mini | All |
| `main_claude_sonnet_4_6.json` | Claude Sonnet 4.6 | All |
| `main_qwen_max.json` | Qwen-Max | All |
| `main_gemini_1.5_pro.json` | Gemini 1.5 Pro | All |

### Key Config Parameters

| Parameter | Description | Values / Default |
|---|---|---|
| `agent_name` | Agent type | `auto` *(default)*, `gui`, `code`, `origin`, `navi` |
| `som_origin` | Screen parsing method (GUI/Origin agents) | `oss` *(default)*, `a11y`, `mixed-oss`, `mixed`, `omni`, `mixed-omni`, `no_omni` |
| `observation_type` | VM observation to collect each step | `screenshot` *(default)*, `a11y_tree` |
| `origin_mode` | Template script injection for OriginAgent | `script` *(default)*, `no_script` |
| `origin_category` | Template script category for OriginAgent | `auto` *(default)*, `xrd`, `xps`, `ftir`, `raman`, `cycle`, `bs`, `step`, `ce` |
| `model` | LLM backbone | `gpt-5`, `claude-sonnet-4-6`, `qwen-max`, 鈥?|
| `temperature` | LLM sampling temperature | `0.0` for main/ablation, `1.0` default |
| `max_steps` | Max agent steps per task | `50` *(default)* |
| `sleep_after_execution` | Seconds to wait after each action | `3` *(default)* |
| `code_retries` | Max self-correction retries for CodeAgent | `3` *(default)* |
| `a11y_backend` | Windows accessibility API backend | `uia` *(default)*, `win32` |
| `diff_lvl` | Task difficulty | `normal` *(default)*, `hard` |
| `num_workers` | Parallel workers (Azure multi-VM) | `1` *(default)* |

---

## 鈿?Performance Notes

Each agent step involves two potentially slow operations: **VM observation collection** and **LLM inference**. Follow these guidelines to avoid unnecessary latency.

### Observation collection

The accessibility tree (`observation_type=a11y_tree`) requires a Windows UIA API call that can take **5鈥?0 seconds per step** and returns large XML payloads. Collect it only when your SoM mode actually needs it:

| `som_origin` | Required `observation_type` | Notes |
|---|---|---|
| `oss` *(default)* | `screenshot` | No a11y tree needed |
| `omni` | `screenshot` | No a11y tree needed |
| `no_omni` | `screenshot` | Raw screenshots only; no SoM parsing |
| `a11y` | `a11y_tree` | A11y tree is the only input |
| `mixed-oss`, `mixed`, `mixed-omni` | `a11y_tree` | A11y tree used for masking |

The default `observation_type` is `screenshot`. Only change it when using an a11y-based SoM mode.

### LLM inference

Factors that increase LLM latency (tokens sent per step):

| Factor | Setting | Impact |
|---|---|---|
| Candidate element list | Automatically truncated at 4 000 chars | High |
| Previous action history | `n_prev=3` (last 3 steps) | Medium |
| Screenshot resolution | Resized to max 768 px | Medium |
| Max output tokens | `max_tokens=2048` (GUI), `1500` (Code) | Medium |

If using a **thinking model** (e.g. Qwen3-Thinking), each response includes a long `<think>鈥?/think>` block. Disable thinking mode via your API's `extra_body` parameter if reasoning is not required for the task.

---

## 馃搳 Results

Per-task scores are saved to `scores_summary.csv` in the result directory after each task. Aggregate across experiments:
```bash
cd src/mattoolbench-container/client
python print_ablation_results.py
```

---

## 馃憦 Acknowledgements

- [Windows Agent Arena](https://github.com/microsoft/WindowsAgentArena) for the Windows VM benchmark infrastructure.
- [OS World](https://github.com/xlang-ai/OSWorld) for the original benchmark task framework.
- [OmniParser](https://github.com/microsoft/OmniParser) for the screen understanding model.
- [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO) for the object detection module.

## 馃摉 Citation

```bibtex
@article{mattoolbench2024,
  title   = {MatToolBench: Benchmarking Desktop AI Agents for Materials Science},
  year    = {2024},
}
```

## License

MIT License 鈥?see [LICENSE](LICENSE).

