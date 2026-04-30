
<div align="center">

<h1><img src="docs/logo.png" height="55" alt="MatToolBench Logo">&nbsp;&nbsp;<span style="color:#2060a8">Mat</span><span style="color:#2e8b48">Tool</span><span style="color:#d07810">Bench</span></h1>

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-mattoolbench%2Fmattoolbench-blue?logo=docker)](https://hub.docker.com/r/mattoolbench/mattoolbench)
[![Website](https://img.shields.io/badge/Website-MatToolBench-green)](https://meiwu5.github.io/MatToolBench/)

</div>

**MatToolBench** is a desktop agent benchmark for materials science, evaluating AI agents on real-world tasks across professional materials characterization and analysis software. It covers three task categories — **Origin** (script-based data analysis), **GUI** (visual interaction with materials-science tools), and **Code** (programmatic database queries) — and is built on top of a Windows 11 virtual machine environment running inside Docker.

---

## 🎬 Demo Video

<p align="center">
  <a href="https://mattoolbench.github.io/demo/">
    <div style="position: relative; display: inline-block;">
      <img src="https://raw.githubusercontent.com/mattoolbench/demo/main/demo_cover.png" 
           width="720" 
           alt="MatToolBench Demo Video Cover"
           style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
      
      <!-- 播放三角图标 -->
      <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                  background: rgba(0,0,0,0.65); border-radius: 50%; width: 90px; height: 90px; 
                  display: flex; align-items: center; justify-content: center; 
                  box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <span style="color: white; font-size: 45px; margin-left: 8px;">▶</span>
      </div>
    </div>
  </a>
</p>

<p align="center">
  <strong>▶ Click the image above to play the demo</strong> &nbsp;·&nbsp; 
  <b><span style="color:#d07810">⚡ Sped up</span></b>
</p>

<p align="center">
  <a href="https://mattoolbench.github.io/demo/demo.mp4" target="_blank">
    ⬇ Download Video (47MB)
  </a>
</p>

## 📊 Main Results

**Sc.** = normalized task score (0–100); **SR** = success rate (%, all sub-criteria satisfied). <b style="color:#c96800">Orange bold</b>: best per domain; <u>underline</u>: second best; <b style="color:#c0392b"><i>Red bold italic</i></b>: best model overall.

<table>
<thead>
<tr bgcolor="#1a3a6e">
<th align="left"><span style="color:white">Cat.</span></th>
<th align="left"><span style="color:white">Domain</span></th>
<th colspan="2" align="center"><span style="color:white">Doubao<br>seed-1-8</span></th>
<th colspan="2" align="center"><span style="color:white">Kimi<br>k2.5</span></th>
<th colspan="2" align="center"><span style="color:white">Claude<br>sonnet-4.6</span></th>
<th colspan="2" align="center"><b><i><span style="color:#ffd060">GPT<br>5.4</span></i></b></th>
<th colspan="2" align="center"><span style="color:white">Qwen3-VL<br>235B</span></th>
<th colspan="2" align="center"><span style="color:white">Qwen3-VL<br>32B</span></th>
<th colspan="2" align="center"><span style="color:white">Qwen3-VL<br>8B</span></th>
</tr>
<tr bgcolor="#2d5580">
<th></th><th></th>
<th align="center"><span style="color:#b8d4f8">Sc.</span></th><th align="center"><span style="color:#b8d4f8">SR</span></th>
<th align="center"><span style="color:#b8d4f8">Sc.</span></th><th align="center"><span style="color:#b8d4f8">SR</span></th>
<th align="center"><span style="color:#b8d4f8">Sc.</span></th><th align="center"><span style="color:#b8d4f8">SR</span></th>
<th align="center"><span style="color:#b8d4f8">Sc.</span></th><th align="center"><span style="color:#b8d4f8">SR</span></th>
<th align="center"><span style="color:#b8d4f8">Sc.</span></th><th align="center"><span style="color:#b8d4f8">SR</span></th>
<th align="center"><span style="color:#b8d4f8">Sc.</span></th><th align="center"><span style="color:#b8d4f8">SR</span></th>
<th align="center"><span style="color:#b8d4f8">Sc.</span></th><th align="center"><span style="color:#b8d4f8">SR</span></th>
</tr>
</thead>
<tbody>
<tr bgcolor="#f0f5ff">
<td rowspan="6" bgcolor="#2060a8" align="center"><b><span style="color:white">GUI</span></b></td>
<td>Avantage</td>
<td><b style="color:#c96800">44.6</b></td><td><b style="color:#c96800">35.0</b></td>
<td>32.3</td><td><u>20.0</u></td>
<td><u>41.3</u></td><td><b style="color:#c96800">35.0</b></td>
<td>32.3</td><td>15.0</td>
<td>30.8</td><td>10.0</td>
<td>26.2</td><td>15.0</td>
<td>18.5</td><td>15.0</td>
</tr>
<tr bgcolor="#f0f5ff">
<td>JADE</td>
<td><u>54.2</u></td><td><b style="color:#c96800">25.0</b></td>
<td>50.8</td><td><b style="color:#c96800">25.0</b></td>
<td><b style="color:#c96800">57.6</b></td><td><b style="color:#c96800">25.0</b></td>
<td>50.8</td><td><u>20.0</u></td>
<td>45.8</td><td>10.0</td>
<td>37.3</td><td>10.0</td>
<td>37.3</td><td>5.0</td>
</tr>
<tr bgcolor="#f0f5ff">
<td>DM</td>
<td><b style="color:#c96800">56.7</b></td><td><b style="color:#c96800">20.0</b></td>
<td><u>52.2</u></td><td><b style="color:#c96800">20.0</b></td>
<td>40.3</td><td><b style="color:#c96800">20.0</b></td>
<td>50.7</td><td><b style="color:#c96800">20.0</b></td>
<td><u>52.2</u></td><td><u>10.0</u></td>
<td>6.0</td><td>0.0</td>
<td>38.8</td><td><u>10.0</u></td>
</tr>
<tr bgcolor="#f0f5ff">
<td>MS</td>
<td>47.6</td><td>15.0</td>
<td>35.4</td><td>10.0</td>
<td><u>52.4</u></td><td><u>20.0</u></td>
<td><b style="color:#c96800">56.1</b></td><td><b style="color:#c96800">30.0</b></td>
<td>43.9</td><td>0.0</td>
<td>26.8</td><td>0.0</td>
<td>20.7</td><td>0.0</td>
</tr>
<tr bgcolor="#f0f5ff">
<td>VESTA</td>
<td>52.2</td><td><u>20.0</u></td>
<td><u>59.4</u></td><td><b style="color:#c96800">25.0</b></td>
<td>58.0</td><td><b style="color:#c96800">25.0</b></td>
<td><b style="color:#c96800">65.2</b></td><td><u>20.0</u></td>
<td>52.2</td><td>10.0</td>
<td>29.0</td><td>10.0</td>
<td>30.4</td><td>10.0</td>
</tr>
<tr bgcolor="#dce8ff">
<td><i>Avg.</i></td>
<td><b style="color:#c96800">52.1</b></td><td><u>24.0</u></td>
<td>46.0</td><td>20.0</td>
<td>49.9</td><td><b style="color:#c96800">25.0</b></td>
<td><u>51.0</u></td><td>21.0</td>
<td>45.0</td><td>8.0</td>
<td>25.1</td><td>7.0</td>
<td>29.1</td><td>8.0</td>
</tr>
<tr bgcolor="#f0f8f3">
<td bgcolor="#2e8b48" align="center"><b><span style="color:white">Origin</span></b></td>
<td>OriginPro</td>
<td>11.7</td><td>12.5</td>
<td>22.5</td><td>25.0</td>
<td><u>53.1</u></td><td><u>56.3</u></td>
<td><b style="color:#c96800">63.8</b></td><td><b style="color:#c96800">68.8</b></td>
<td>6.3</td><td>6.3</td>
<td>5.3</td><td>6.3</td>
<td>0.0</td><td>0.0</td>
</tr>
<tr bgcolor="#fffbf0">
<td rowspan="5" bgcolor="#d07810" align="center"><b><span style="color:white">Code</span></b></td>
<td>Pymatgen</td>
<td>30.0</td><td>30.0</td>
<td>15.0</td><td>15.0</td>
<td>25.0</td><td>25.0</td>
<td><b style="color:#c96800">35.0</b></td><td><b style="color:#c96800">35.0</b></td>
<td><b style="color:#c96800">35.0</b></td><td><b style="color:#c96800">35.0</b></td>
<td><u>29.4</u></td><td><u>29.4</u></td>
<td>15.0</td><td>15.0</td>
</tr>
<tr bgcolor="#fffbf0">
<td>MP</td>
<td><b style="color:#c96800">25.0</b></td><td><b style="color:#c96800">25.0</b></td>
<td><u>22.5</u></td><td><u>20.0</u></td>
<td>21.9</td><td>15.0</td>
<td>17.5</td><td>15.0</td>
<td><b style="color:#c96800">25.0</b></td><td><b style="color:#c96800">25.0</b></td>
<td>10.0</td><td>10.0</td>
<td>10.0</td><td>10.0</td>
</tr>
<tr bgcolor="#fffbf0">
<td>OQMD</td>
<td>33.2</td><td>10.0</td>
<td>50.3</td><td>30.0</td>
<td><b style="color:#c96800">60.8</b></td><td><b style="color:#c96800">50.0</b></td>
<td><u>58.2</u></td><td><u>45.0</u></td>
<td>26.2</td><td>10.0</td>
<td>11.5</td><td>0.0</td>
<td>18.4</td><td>0.0</td>
</tr>
<tr bgcolor="#fffbf0">
<td>OPTIMADE</td>
<td>70.0</td><td>70.0</td>
<td><u>80.0</u></td><td><u>80.0</u></td>
<td>75.0</td><td>75.0</td>
<td><b style="color:#c96800">85.0</b></td><td><b style="color:#c96800">85.0</b></td>
<td>20.0</td><td>20.0</td>
<td>30.0</td><td>30.0</td>
<td>10.0</td><td>10.0</td>
</tr>
<tr bgcolor="#ffe8c0">
<td><i>Avg.</i></td>
<td>39.6</td><td>33.8</td>
<td>42.0</td><td>36.2</td>
<td><u>45.7</u></td><td><u>41.3</u></td>
<td><b style="color:#c96800">48.9</b></td><td><b style="color:#c96800">45.0</b></td>
<td>26.6</td><td>22.5</td>
<td>20.2</td><td>17.4</td>
<td>13.4</td><td>8.8</td>
</tr>
<tr bgcolor="#ede8f8">
<td colspan="2" bgcolor="#3a2a6e"><b><span style="color:white">Overall Avg.</span></b></td>
<td>42.5</td><td>26.3</td>
<td>42.0</td><td>27.0</td>
<td><u>48.5</u></td><td><u>34.6</u></td>
<td><b style="color:#c0392b"><i>51.5</i></b></td><td><b style="color:#c0392b"><i>35.4</i></b></td>
<td>33.7</td><td>13.6</td>
<td>21.2</td><td>11.1</td>
<td>19.9</td><td>7.5</td>
</tr>
</tbody>
</table>

---

## 📚 Task Categories

| Category | Domains | Tasks | Agent Type | Description |
|----------|---------|-------|------------|-------------|
| **Origin** | XRD, XPS, Raman, Cycle, Step, CE | ~16 | OriginAgent | Writes OriginPro scripts to analyze experimental data and generate plots |
| **GUI** | Jade, Avantage, VESTA, DM, MS | ~100 | GUIAgent | Visually navigates materials software GUIs to complete analysis tasks |
| **Code** | MP, OQMD, PyMatgen, OPTIMADE | ~70 | CodeAgent | Generates Python code to query materials databases and retrieve properties |
---

## 🗺️ System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Input (Task Config)                      │
│              experiment_configs/*.json                       │
│         { task_id, agent_type, model, ... }                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
          ┌─────────────┴─────────────┐
          │                           │
    run-local.sh                 run_azure.py
          │                           │
    Local Docker               Azure ML Job
    (single machine)           (parallel VMs)
          │                           │
          └─────────────┬─────────────┘
                        │
                     run.py
                        │
          ┌─────────────┼─────────────┐
          │             │             │
     GUI Agent    Origin Agent   Code Agent
          │             │             │
    screenshot →    LLM writes     LLM writes
    plan → act      .py script     query code
          │             │             │
   Windows VM      OriginPro      Database API
  (QEMU/Docker)    (in VM)        (HTTP)
   Jade/VESTA/
   Avantage/DM/
   MatStudio
          │             │             │
          └─────────────┴─────────────┘
                        │
                   evaluators/
                (getters + metrics)
                        │
┌─────────────────────────────────────────────────────────────┐
│                        Output                               │
│    output_result/  +  results/logs/  +  screenshot traces   │
└─────────────────────────────────────────────────────────────┘
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

## 🗂️ Project Structure

```
MatToolBench/
├── config.json                        # API keys, Azure credentials
├── requirements.txt                   # Host-side deps (azure-ai-ml, etc.)
│
├── scripts/
│   ├── build-container-image.sh       # Build Docker image
│   ├── run-local.sh                   # Local benchmark runner
│   ├── run_azure.py                   # Azure ML runner (full cloud mode)
│   ├── run_local_agent.py             # Run agent locally against Azure-hosted VM
│   ├── show_azure.py                  # Aggregate results from Azure runs
│   ├── sync_results.py                # Incrementally sync Azure results to local folder
│   ├── compute_efficiency.py          # Compute efficiency metrics from eval_detail.json
│   ├── experiments.json               # Azure experiment config
│   └── azure_files/                   # Azure startup scripts
│       ├── run_entry.py               # Job entry point executed on each Azure VM
│       └── compute-instance-startup.sh
│
└── src/mattoolbench-container/
    ├── Dockerfile-MatToolBench-Base   # Layer 1: Python / CUDA / model weights
    ├── Dockerfile-MatToolBench        # Layer 2: client code + VM files
    ├── entry.sh / start_vm.sh / start_client.sh
    │
    ├── vm/
    │   ├── image/setup.iso            # Windows 11 ISO
    │   ├── storage/                   # VM disk snapshots (windows.base, etc.)
    │   ├── unattend-files/            # Automated install answer files
    │   └── setup/                     # PowerShell setup scripts + tools
    │       └── [Avantage / VESTA / DigitalMicrograph / Materials Studio / ...]
    │
    └── client/                        # Python client (runs inside container)
        ├── run.py                     # Main execution entry point
        ├── experiment_configs/        # JSON configs for each experiment
        │   ├── main_gpt_5.json
        │   ├── main_claude_sonnet_4_6.json
        │   ├── main_gemini_1.5_pro.json
        │   ├── ablation_gui_som_*.json
        │   └── ...
        ├── desktop_env/
        │   ├── envs/desktop_env.py    # Core VM environment class
        │   ├── controllers/           # VM / Python / setup controllers
        │   └── evaluators/
        │       ├── getters/           # Read state from each tool (jade, vesta, ...)
        │       └── metrics/           # Scoring functions
        ├── mm_agents/
        │   ├── gui_agent.py
        │   ├── origin_agent.py
        │   ├── code_agent.py
        │   └── navi/                  # NaviAgent: screen parsing + LLM planner
        │       ├── screenparsing_oss/ # GroundingDINO, OmniParser, OCR
        │       ├── gpt/               # GPT-4V / Phi-3 vision planners
        │       └── llm/               # Text-only LLM planners
        ├── task_code/                 # Reference code per database (MP, OQMD, ...)
        ├── evaluation_examples_windows/  # Task definitions (JSON)
        └── output_result/             # Experiment outputs
```

---

## 🚀 Quick Start (WSL / Linux)

The fastest way to run MatToolBench locally — no build required.

### Prerequisites

- [Docker](https://docs.docker.com/desktop/wsl/) installed and running (WSL 2 recommended on Windows)
- An [OpenAI](https://platform.openai.com/docs/introduction) or [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) API key
- Python 3.12 ([Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html) recommended)

Clone the repo and install host-side dependencies:
```bash
git clone https://github.com/meiwu5/MatToolBench.git
cd MatToolBench
conda create -n mattoolbench python=3.12
conda activate mattoolbench
pip install -r requirements.txt
```

### Step 1 — Pull the Docker image

```bash
docker pull mattoolbench/mattoolbench:latest
```

> The image (~27 GB) includes the full Python environment, model weights (GroundingDINO, OmniParser), and the benchmark client. Pull time depends on network speed.

### Step 2 — Download the VM snapshot

Download the pre-built Windows 11 VM snapshot (with all materials science software pre-installed) from Google Drive and extract it into the repository:

**[Download VM snapshot from Google Drive](https://drive.google.com/drive/folders/1JEquB482BRsghgyJbWcwEBdZSXL_97e9?usp=drive_link)**

Place the extracted files at:
```
src/mattoolbench-container/vm/storage/
├── windows.base
├── windows.boot
├── windows.mac
├── windows.rom
├── windows.vars
├── windows.ver
└── data.img
```

### Step 3 — Configure API keys

Create `config.json` at the project root:
```json
{
    "OPENAI_API_KEY": "<your-openai-key>",
    "OPENAI_ENDPOINT": "https://api.openai.com/v1",
    "MP_API_KEY": "<your-materials-project-api-key>"
}
```

### Step 4 — Run

```bash
cd scripts
./run-local.sh
```

Open **http://localhost:8006** in your browser to watch the Windows 11 VM boot and the agent run tasks in real time.

---

## 💻 Local Deployment (WSL or Linux)

### 1. Configuration

Create `config.json` at the project root:
```json
{
    "OPENAI_API_KEY": "<your-openai-key>",
    "OPENAI_ENDPOINT": "https://api.openai.com/v1",
    "AZURE_API_KEY": "<your-azure-openai-key>",
    "AZURE_ENDPOINT": "https://yourendpoint.openai.azure.com/",

    "MP_API_KEY": "<your-materials-project-api-key>"
}
```

> You only need **one** of the two LLM blocks (OpenAI or Azure OpenAI). The script checks both and raises an error if neither is provided.

> **`MP_API_KEY`** is required for **Code tasks** that query the [Materials Project](https://materialsproject.org) database (`mp` and `optimade` domains). Get your key from [materialsproject.org/dashboard](https://materialsproject.org/dashboard). If omitted, those tasks will fail with an authentication error. `OQMD` and `pymatgen` tasks do not require a key.

### 2. Docker Image

#### Option A — Pull from Docker Hub (recommended)

```bash
docker pull mattoolbench/mattoolbench:latest
```

Both images are available on Docker Hub:

| Image | Size | Purpose |
|-------|------|---------|
| `mattoolbench/mattoolbench:latest` | ~27 GB | Complete ready-to-run image |
| `mattoolbench/mattoolbench-base:latest` | ~21 GB | Base layer (for custom builds) |

#### Option B — Build locally

Build base image and final image from source:
```bash
cd scripts
./build-container-image.sh --build-base-image true
```

> The build downloads Python dependencies, CUDA libraries, and model weights (GroundingDINO, OmniParser). This can take **30–60 minutes**.

If the base image is already built and unchanged:
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

You have two options — use our pre-built snapshot (recommended) or build from scratch.

---

##### Option A: Use Our Pre-built VM Snapshot (Recommended)

Skip the entire installation process by downloading our ready-to-use snapshot. All materials science software is already installed and configured.

**Download:** [MatToolBench VM Snapshot (Google Drive)](https://drive.google.com/drive/folders/1JEquB482BRsghgyJbWcwEBdZSXL_97e9?usp=drive_link)

Extract and place the files at:
```
src/mattoolbench-container/vm/storage/
├── windows.base
├── windows.boot
├── windows.mac
├── windows.rom
├── windows.vars
├── windows.ver
└── data.img
```

Then skip to [§ 4 Running the Benchmark](#4-running-the-benchmark) directly.

---

##### Option B: Build from Scratch

The automated script handles Windows 11 installation. Specialty materials science software must be installed manually via the shared folder.

**Step B-1 — Download the software installers**

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

The automated setup script also installs a Python server environment inside Windows (`vm/setup/server/requirements.txt`) that handles VM-side screenshot capture, action execution, and accessibility tree queries, as well as per-domain Python virtual environments for Code tasks (mp/oqmd/pymatgen/optimade). You do not need to install these manually — they are configured by the PowerShell setup scripts automatically.

**Step B-2 — Start the automated Windows 11 installation**

```bash
cd scripts
./run-local.sh --mode dev --prepare-image true
```

Open `http://localhost:8006` in your browser to watch the VM boot and the automated setup progress (~20 minutes for Windows install + basic tools).

**Step B-3 — Install materials science software inside the VM**

Once the automated setup finishes and the Windows desktop is visible at `http://localhost:8006`:

1. Open **File Explorer** inside the VM and navigate to `\\host.lan\Data` — this is the shared folder that maps directly to `src/mattoolbench-container/vm/setup/` on your host.
2. Run each installer from this shared folder in the following order:

```
\\host.lan\Data\OriginSetup.exe              → follow the installer wizard
\\host.lan\Data\Jade_setup.exe               → follow the installer wizard
\\host.lan\Data\Avantage 6.6.0\Setup.exe     → follow the installer wizard
\\host.lan\Data\VESTA-win64\VESTA_Setup.exe  → follow the installer wizard
\\host.lan\Data\DigitalMicrograph\setup.exe  → follow the installer wizard
\\host.lan\Data\Materials Studio 2023(64bit)\Setup.exe → follow the installer wizard
```

3. After all software is installed, shut down the VM gracefully from inside Windows (Start → Shut down). The disk snapshot in `vm/storage/` is updated automatically.


#### 3.3 Saving and Reusing a VM Snapshot

After building the golden image (Option B above), back up the entire `vm/storage/` directory to avoid repeating installation next time:

```
vm/storage/
├── windows.base     ← main VM disk image
├── windows.boot
├── windows.mac
├── windows.rom
├── windows.vars
├── windows.ver
└── data.img
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

## ☁️ Azure Cloud Deployment

Azure deployment runs the benchmark in parallel across multiple Azure ML Compute Instances — each instance hosts an independent Windows 11 VM, and all workers run simultaneously to maximize throughput.

### Architecture

```
Your Machine
  └── run_azure.py
        │
        ├── Creates N Compute Instances (parallel)
        │     w0<exp>, w1<exp>, ..., w{N-1}<exp>
        │
        └── Submits N ML Jobs (parallel)
              Each job on its Compute Instance:
                ├── Pulls Docker image from registry
                ├── Copies VM snapshot from Azure Blob
                ├── Boots Windows 11 VM (QEMU)
                └── Runs Python agent (run.py)
```

---

### Step 1 — Azure Prerequisites

You need:
- An **Azure subscription** with sufficient quota for the chosen VM SKU (e.g., `Standard_D8_V3` requires 8 vCPU cores per worker)
- An **Azure ML Workspace** (create one at [ml.azure.com](https://ml.azure.com))
- An **Azure Blob Storage datastore** registered in the workspace (the default `workspaceblobstore` is used)
- The **Azure CLI** logged in, or credentials configured for `DefaultAzureCredential`

Request quota increases if needed:
> Azure ML portal → your workspace → Compute → Quotas → Request increase

---

### Step 2 — Add Azure Credentials to `config.json`

Extend your `config.json` with Azure ML credentials:

```json
{
    "OPENAI_API_KEY": "<your-openai-key>",
    "OPENAI_ENDPOINT": "https://api.openai.com/v1",
    "AZURE_API_KEY": "<your-azure-openai-key>",
    "AZURE_ENDPOINT": "https://yourendpoint.openai.azure.com/",

    "MP_API_KEY": "<your-materials-project-api-key>",

    "AZURE_SUBSCRIPTION_ID": "<your-subscription-id>",
    "AZURE_ML_RESOURCE_GROUP": "<your-resource-group>",
    "AZURE_ML_WORKSPACE_NAME": "<your-workspace-name>",

    "AZURE_STORAGE_ACCOUNT": "<your-storage-account-name>",
    "AZURE_STORAGE_KEY": "<your-storage-account-key>",
    "AZURE_STORAGE_CONTAINER": "<your-blob-container-name>"
}
```

| Key | Required | Description |
|-----|----------|-------------|
| `OPENAI_API_KEY` + `OPENAI_ENDPOINT` | One of the two LLM blocks | OpenAI-compatible API key and base URL |
| `AZURE_API_KEY` + `AZURE_ENDPOINT` | One of the two LLM blocks | Azure OpenAI key and endpoint |
| `MP_API_KEY` | For `mp` / `optimade` Code tasks | [Materials Project](https://materialsproject.org/dashboard) API key. CodeAgent injects it into generated scripts at runtime. `oqmd` and `pymatgen` tasks do not need it. |
| `AZURE_SUBSCRIPTION_ID` / `AZURE_ML_RESOURCE_GROUP` / `AZURE_ML_WORKSPACE_NAME` | Azure cloud mode | Your Azure ML workspace identifiers |
| `AZURE_STORAGE_ACCOUNT` / `AZURE_STORAGE_KEY` / `AZURE_STORAGE_CONTAINER` | Azure cloud mode | Storage account credentials for `clear_agent_outputs.py` |

---

### Step 3 — Upload the VM Snapshot to Azure Blob

The Windows 11 golden image must be available on Azure Blob Storage so each worker can download it at startup.

1. Build the golden image locally (see [Local § 3.2](#32-build-the-golden-image)) or obtain a pre-built snapshot.
2. Upload the entire `vm/storage/` directory to your Azure datastore:

```bash
# Using Azure CLI — upload the snapshot directory
az storage account keys list --account-name <your-storage-account> --query "[0].value" -o tsv

az storage blob upload-batch \
    --account-name <your-storage-account> \
    --destination <your-blob-container>/storage \
    --source src/mattoolbench-container/vm/storage/ \
    --account-key "<your-account-key>"
```

Or use [Azure Storage Explorer](https://azure.microsoft.com/en-us/products/storage/storage-explorer) to drag-and-drop the `vm/storage/` folder into the `storage` path inside your blob container (matching the `datastore_input_path` in `experiments.json`).

The expected layout on Blob after upload:
```
storage/
├── windows.base
├── windows.boot
├── windows.mac
├── windows.rom
├── windows.vars
├── windows.ver
└── data.img
```

---

### Step 4 — Upload the Compute Instance Startup Script

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

### Step 5 — Configure `scripts/experiments.json`

```json
{
  "experiment_1": {
    "ci_startup_script_path": "Users/<your-username>/compute-instance-startup.sh",
    "docker_img_name":        "mattoolbench/mattoolbench:latest",
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
    "max_steps":              50,
    "max_tokens":             2048,
    "origin_max_tokens":      8000,
  }
}
```

**Parameter reference:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ci_startup_script_path` | Path to the startup script in the ML workspace filestore | — |
| `docker_img_name` | Docker Hub image pulled on each VM | `mattoolbench/mattoolbench:latest` |
| `datastore_input_path` | Azure Blob path containing the VM snapshot | `storage` |
| `exp_name` | Experiment name; also used as the Azure ML Experiment name | — |
| `vm_size` | Azure VM SKU for each Compute Instance | `Standard_D8_V3` |
| `num_workers` | Number of parallel Compute Instances / ML Jobs | `1` |
| `agent` | Agent routing (`auto`, `gui`, `code`, `origin`, `navi`) | `auto` |
| `model_name` | LLM backbone (e.g., `gpt-5`, `claude-sonnet-4-6`) | — |
| `som_origin` | Screen-parsing method (`oss`, `a11y`, `mixed-oss`, `omni`) | `oss` |
| `a11y_backend` | Accessibility backend (`uia`, `win32`) | `uia` |
| `origin_mode` | Template script injection for OriginAgent (`script`, `no_script`) | `script` |
| `gui_hint_mode` | Per-app startup hints for GUIAgent (`hint`, `no_hint`) | `hint` |
| `json_name` | Task list JSON inside the container | `evaluation_examples_windows/test_all.json` |
| `use_managed_identity` | Use Azure Managed Identity instead of service principal | `false` |

---

### Step 6 — Launch the Experiment

**Full cloud mode** (agent runs on Azure, fully automated):

```bash
cd scripts
python run_azure.py --experiments_json experiments.json
```

`run_azure.py` will:
1. Create (or start) `N` Compute Instances in parallel, named `w0<exp_name>`, `w1<exp_name>`, …
2. Submit `N` ML Jobs in parallel — each job downloads the VM snapshot, boots the Windows VM, and runs the agent.

Monitor job status in the [Azure ML Studio](https://ml.azure.com) or via:
```bash
python show_azure.py --result_dir <your-result-dir> \
                     --json_config experiments.json \
                     --output_file results_table.md
```

---

### Step 7 — Collect Results

Results are written to `agent_outputs/` in the `workspaceblobstore` (Azure Blob output dataset).

#### Option A: Real-time sync (recommended)

`scripts/sync_results.py` continuously pulls new or updated files from Azure Blob to a local folder using incremental sync (only downloads changed files):

```bash
# Install dependency (if not already present)
pip install azure-storage-blob

# Continuous sync every 30 seconds (default)
python scripts/sync_results.py --local_dir ./results_local

# Custom interval
python scripts/sync_results.py --local_dir ./results_local --interval 60

# Single sync and exit
python scripts/sync_results.py --local_dir ./results_local --once

# Filter by experiment name
python scripts/sync_results.py --local_dir ./results_local --exp_name Experiment1
```

Then summarize:
```bash
python scripts/show_azure.py \
    --result_dir ./results_local \
    --json_config scripts/experiments.json \
    --output_file results_table.md
```

#### Option B: One-shot download via Azure CLI

```bash
az storage blob download-batch \
    --account-name <your-storage-account> \
    --source <your-blob-container>/agent_outputs/<exp_name> \
    --destination ./results/ \
    --account-key "<your-account-key>"
```

---

## 🤖 Agent Architecture

### Agent Routing

The `--agent` flag (or the `agent` field in `experiments.json`) controls which agent handles each task. With the default `auto` setting, the agent is selected automatically based on the task domain.

| Value | Agent class | Domains |
|---|---|---|
| `auto` *(default)* | Routed by domain | All |
| `gui` | `GUIAgent` | avantage, dm, jade, vesta, ms |
| `code` | `CodeAgent` | mp, oqmd, pymatgen, optimade |
| `origin` | `OriginAgent` | origin |

### Observation Model

The default observation for all GUI and Origin tasks is a **raw screenshot** (`observation_type=screenshot`, `som_origin=no_omni`). The screenshot is passed directly to the LLM without any Set-of-Marks (SoM) bounding-box overlays. This is the configuration used in the main benchmark evaluation.

Six observation modes are available for ablation:

| `som_origin` | `observation_type` | Description |
|---|---|---|
| `no_omni` *(main eval)* | `screenshot` | Raw screenshot, no element markers |
| `oss` | `screenshot` | Screenshot + OCR-detected text regions overlaid |
| `omni` | `screenshot` | Screenshot + OmniParser (YOLO + Florence) element boxes |
| `a11y` | `a11y_tree` | Windows Accessibility tree only (no screenshot) |
| `mixed-oss` | `a11y_tree` | A11y tree + OCR merged |
| `mixed-omni` | `a11y_tree` | A11y tree + OmniParser merged |

> Modes that require `a11y_tree` trigger a Windows UIA API call that can take 5–60 seconds per step. Do not set `observation_type=a11y_tree` unless your `som_origin` actually uses the accessibility tree.

### Action Space

All agents generate Python code strings that are sent to the VM server via HTTP and executed with `exec()`. The VM server exposes a `Computer` object with five sub-modules:

| Module | Example methods |
|---|---|
| `computer.mouse` | `move(x, y)`, `click(x, y)`, `double_click(x, y)`, `scroll(x, y, dx, dy)` |
| `computer.keyboard` | `type(text)`, `hotkey(*keys)`, `key_down(key)`, `key_up(key)` |
| `computer.clipboard` | `get_text()`, `set_text(text)` |
| `computer.os` | `run(cmd)`, `get_pid(name)` |
| `computer.window` | `activate(pid)`, `maximize(pid)`, `get_rect(pid)` |

### GUIAgent

`GUIAgent` is a thin wrapper around `NaviAgent`. On each step it:
1. Takes a screenshot of the Windows VM
2. Optionally overlays SoM element markers (disabled by default — `no_omni`)
3. Sends the screenshot (and optional element list) to the LLM with a domain-specific system prompt
4. Parses the returned Python code block and executes it on the VM

The system prompt includes per-application startup guides for each materials-science tool (file open dialogs, non-standard first actions, critical key shortcuts). These hints can be toggled for ablation with `--gui_hint_mode hint/no_hint`.

### OriginAgent

`OriginAgent` inherits `NaviAgent` but targets OriginPro's Code Builder (Alt+4). Given a task:
1. Opens the data file in OriginPro (Ctrl+O)
2. Opens Code Builder (Alt+4)
3. Pastes a Python script via the clipboard and runs it with F5
4. The LLM adapts a domain-specific template script (from `client/origin_draw/`) rather than writing from scratch

Template script injection is controlled by `--origin_mode`:
- `script` *(default)* — LLM receives a domain template as context and adapts it
- `no_script` — LLM writes the full script from scratch (ablation baseline)

Available templates:

| Category | Script | Analysis type |
|---|---|---|
| `xrd` | `XRD_match.py` | XRD phase matching |
| `xps` | `XPS.py` | XPS peak fitting |
| `ftir` | `FTIR.py` | FTIR spectroscopy |
| `raman` | `roman.py` | Raman spectroscopy |
| `cycle` | `cycle.py` | Electrochemical cycling |
| `bs` | `BS.py` | Band structure |
| `step` | `step.py` | Free energy step diagram |
| `ce` | `CE.py` | Coulombic efficiency |

### CodeAgent

`CodeAgent` is a text-only (no screenshot) agent. Given a task:
1. LLM generates a Python code block to query the target materials database
2. The code is written to a temp file on the VM and executed inside the correct per-domain virtual environment (`oqmd`, `pymatgen`, or `optimade` venv under `C:\Users\Docker\`)
3. If the code fails, stdout/stderr are fed back to the LLM for self-correction
4. This generate-and-correct loop continues up to `max_steps` iterations; the episode ends immediately when code returns exit code 0

---

## 📊 Evaluation System

MatToolBench uses a **two-tier evaluation framework**: accuracy metrics and efficiency metrics, recorded independently in each task's `eval_detail.json`.

The complete evaluation dataset (task configs, ground-truth files, reference trajectories) is available at:

**[Evaluation Dataset on Google Drive](https://drive.google.com/drive/folders/12fmmf8sXYNRslch-7w7mYktyTfV0GNcc?usp=drive_link)**

### Accuracy Metrics

Each task's evaluator is defined in its JSON config under `"evaluator"`. Three evaluator types are used:

| Evaluator | Used by | Scoring |
|-----------|---------|---------|
| `detect_file_match` | PyMatgen tasks | Exact binary match of output file content (0.0 or 1.0) |
| `detect_kv_match` | MP, OQMD tasks | Fraction of gold key-value pairs matched (`matched / total_gold_keys`), numeric tolerance rtol=1e-3 |
| `exact_match` + `file_exists` | OPTIMADE tasks | 1.0 if output file exists, 0.0 otherwise |

#### Origin Task Evaluation

OriginPro tasks produce plots rather than structured key-value output, so they are evaluated by a vision LLM scoring the generated figure against a textual description of the expected result. Reference images (human-created plots for each task type) are stored in `origin_images/origin_images/` and are used as baselines for the LLM vs. human comparison study. The scoring script is `origin_images/score_origin_images.py`.

Each generated plot is rated on three dimensions (1.0–5.0 scale):

| Dimension | What it measures |
|-----------|-----------------|
| **C** — Visual Correctness | Plot type, axis labels/units, data accuracy, scale/range |
| **A** — Aesthetic Quality | Publication readiness: colors, fonts, spacing, legend placement |
| **T** — Task Completeness | Presence of all required elements (insets, annotations, panels, color bars) |

The per-category reference images cover: `xrd`, `xps`, `roman` (Raman), `ftir`, `cycle`, `step`, `ce`.

For OPTIMADE tasks, results are non-deterministic (vary by provider/time), so a **`score_by_attempts`** flag overrides the file-exists score with an attempt-efficiency score:

```
score_by_attempts = (max_steps − first_success_step + 1) / max_steps
```

This rewards generating working code on the first try, and degrades linearly with each failed attempt.

### Efficiency Metrics

Efficiency metrics are computed independently of accuracy and stored in `eval_detail.json`:

| Field | Formula | Applies to |
|-------|---------|------------|
| `steps_taken` | Total agent steps used | All tasks |
| `step_efficiency` | `1 − (steps_taken − 1) / (max_steps − 1)` | All tasks |
| `first_success_step` | First step where `returncode == 0` | Code tasks only |

`step_efficiency` ranges from 1.0 (task completed in step 1) to 0.0 (used all `max_steps`).

### Computing Efficiency Reports

```bash
# Single experiment
python scripts/compute_efficiency.py --result_dir ./results/Experiment1

# Compare multiple models
python scripts/compute_efficiency.py \
    --result_dir ./results/ModelA \
    --result_dir ./results/ModelB \
    --output_json efficiency_comparison.json
```

The report shows per-domain breakdowns:

```
Domain         N  StepEff  StepEff(ok)  CodeEff  N_code  N_ok
mp            20   0.72        0.81        N/A       0     14
oqmd          20   0.68        0.79       0.72      20     11
pymatgen      20   0.81        0.89       0.80      20     17
optimade      10   0.52        0.71       0.60      10      6
```

- **StepEff**: average step efficiency across all tasks in this domain
- **StepEff(ok)**: step efficiency for tasks that were solved (success_rate=1)
- **CodeEff**: code-attempt efficiency (first `returncode==0` step), Code tasks only

---

## 📂 Task Input Data

Each task in `evaluation_examples_windows/examples/<domain>/` references one or more input data files pre-placed on the VM at `C:\Users\Docker\Desktop\setup\dependencies\<software>\`. The source files are stored in the repository under `src/mattoolbench-container/vm/setup/dependencies/` and are copied into the VM by the PowerShell setup scripts.

### Input Data Files by Software

| Software | Format | Files |
|----------|--------|-------|
| **Avantage** (XPS) | `.VGD`, `.vgp` | `C1s Scan.VGD`, `O1s Scan.VGD`, `XPS Survey.VGD`, `Zn2p Scan.VGD`, `Zn.vgp` |
| **Digital Micrograph** (TEM) | `.dm3` | `dm1.dm3` – `dm10.dm3`, `5.dm3` |
| **Jade** (XRD) | `.jip`, `.xrdml`, `.txt` | `XRD1`–`XRD4` (`.jip` + `.xrdml`), `WRT-ZSX-5.jip/.txt` |
| **Materials Studio** | `.xsd` | `Al2O3.xsd`, `Fe.xsd`, `LiF.xsd`, `AIGH-mol.xsd`, `Novolac4.xsd`, `SuperSi.xsd`, `TMOS.xsd`, `urea.xsd` |
| **VASP** | `POSCAR` | Al (bulk/workfunc), Au (slab), BN (DOS), CoO (spin), Cu (ENCUT/slab), Fe (lattice/slab), Ge (band), graphene, MgO (k-mesh), Ni (spin), Pt (slab), Si (surface), SrTiO3, Ti, TiO2 (DFT+U), WS2 (HSE), ZnO (relax), `vasprun.xml` |
| **VESTA** (crystal) | `.cif` | Al₂O₃, MgO, Fe, Si, NaCl, GaAs, Cu, C (graphite), GaN, Au |
| **OriginPro** | `.ogwu`, `.opju`, `.txt` | XRD1–2 (`.txt`), XPS_1/XPS2 (`.ogwu`), Cycle1–2, CE1–2, Book2–3, book9, CPO1 (`.opju`), CPO2, step (`.opju`), PDF reference files |

---

## 📊 Results

Per-task scores are saved to `scores_summary.csv` in the result directory after each task. Each task also produces an `eval_detail.json` with full accuracy and efficiency fields.

Aggregate accuracy across experiments:
```bash
cd src/mattoolbench-container/client
python print_ablation_results.py
```

Compute efficiency metrics:
```bash
python scripts/compute_efficiency.py --result_dir ./results/Experiment1
```

---

## 🛠️ Troubleshooting

### Windows VM disk full — `setupact.log` growing unboundedly

**Symptom:** The Windows 11 VM runs out of disk space during a long experiment. The culprit is one or more `setupact.log` files growing to several GB:

```
C:\Windows\Panther\setupact.log
C:\Windows\Panther\UnattendGC\setupact.log
C:\Windows\System32\LogFiles\setupcln\setupact.log
```

**Why it happens:** The VM snapshot (`windows.base`) is captured from a sysprepped Windows image. On every cold boot from that snapshot, Windows re-enters the **Unattend specialization / generalization cleanup (UnattendGC)** phase and logs continuously to these files via the Panther setup engine. Over a long experiment or across multiple task runs the files can grow to tens of GB and fill the virtual disk.

**Fix — delete the logs from inside the VM (PowerShell as Administrator):**

```powershell
ri C:\Windows\Panther\setupact.log -Force
ri C:\Windows\Panther\UnattendGC\setupact.log -Force
ri C:\Windows\System32\LogFiles\setupcln\setupact.log -Force
```

Run these at the start of an experiment (e.g., in the VM startup PowerShell script) or whenever `df` inside the VM shows the C: drive near capacity.

---

## 👏 Acknowledgements

- [Windows Agent Arena](https://github.com/microsoft/WindowsAgentArena) for the Windows VM benchmark infrastructure.
- [OS World](https://github.com/xlang-ai/OSWorld) for the original benchmark task framework.
- [OmniParser](https://github.com/microsoft/OmniParser) for the screen understanding model.
- [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO) for the object detection module.

## 📖 Citation

```bibtex
@article{mattoolbench2025,
  title   = {MatToolBench: Revealing the Transfer Gap of Multimodal Agents in Professional Materials Science Workflows},
  year    = {2025},
}
```

## License

MIT License — see [LICENSE](LICENSE).
