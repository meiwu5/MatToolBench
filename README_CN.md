<div align="center">

# MatToolBench

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9-blue.svg)](https://www.python.org/)

</div>

**MatToolBench** 是一个面向材料科学的桌面 AI 智能体评测基准。它在真实的 Windows 11 虚拟机环境中，对 AI 智能体在专业材料表征软件、计算数据库和脚本数据分析等端到端任务上的能力进行评估，涵盖三类任务——**Origin**（脚本数据分析）、**GUI**（材料软件视觉交互）、**Code**（数据库程序化查询）。

---

## 📚 任务类别

| 类别 | 领域 | 任务数量 | 智能体类型 | 说明 |
|------|------|----------|------------|------|
| **Origin** | XRD、XPS、Raman、Cycle、Step、CE | ~96 | OriginAgent | 编写 OriginPro 脚本分析实验数据并生成图表 |
| **GUI** | Jade、Avantage、VESTA、DM、MS | ~65 | GUIAgent | 视觉交互，操作材料软件 GUI 完成分析任务 |
| **Code** | MP、OQMD、PyMatgen、OPTIMADE | ~92 | CodeAgent | 生成 Python 代码查询材料数据库，获取材料属性 |

---

## 🗺️ 系统总览

```
┌─────────────────────────────────────────────────────────────┐
│                       输入（任务配置）                        │
│              experiment_configs/*.json                       │
│         { task_id, agent_type, model, ... }                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
          ┌─────────────┴─────────────┐
          │                           │
    run-local.sh                 run_azure.py
          │                           │
    本地 Docker 容器            Azure ML Job
    （单机运行）               （多 VM 并行）
          │                           │
          └─────────────┬─────────────┘
                        │
                     run.py
                        │
          ┌─────────────┼─────────────┐
          │             │             │
     GUI Agent    Origin Agent   Code Agent
          │             │             │
    截图 → 规划      LLM 编写        LLM 编写
    → 鼠标/键盘      .py 脚本        查询代码
          │             │             │
   Windows VM      OriginPro      数据库 API
  （QEMU/Docker）  （VM 内）       （HTTP 请求）
   Jade / VESTA /
   Avantage / DM /
   Materials Studio
          │             │             │
          └─────────────┴─────────────┘
                        │
                   evaluators/
               （getters + metrics）
                        │
┌─────────────────────────────────────────────────────────────┐
│                          输出                                │
│    output_result/  +  results/logs/  +  截图轨迹             │
└─────────────────────────────────────────────────────────────┘
```

**本地与 Azure 对比：**

| | 本地 | Azure |
|---|---|---|
| 入口 | `scripts/run-local.sh` | `scripts/run_azure.py` |
| 存储 | 本地磁盘（`vm/storage/`）| Azure Blob Storage |
| 并发 | 单机串行 | 多 Job 并行（`num_workers`）|
| Docker 镜像 | 本地构建 `mattoolbench:latest` | 拉取 `meiwu/mattoolbench:latest` |
| VM 镜像 | 持久化于 `vm/storage/` | 上传至 Azure datastore |

---

## 🗂️ 项目结构

```
MatToolBench/
├── config.json                        # API Key、Azure 凭证
├── requirements.txt                   # 宿主机依赖（azure-ai-ml 等）
│
├── docs/                              # 开发指南
│   ├── Develop-Agent.md               # 智能体开发指南
│   ├── Develop-Tasks.md               # 任务开发指南
│   └── Development-Tips.md            # 调试与开发技巧
│
├── scripts/
│   ├── build-container-image.sh       # Docker 镜像构建入口
│   ├── run-local.sh                   # 本地运行脚本
│   ├── run_azure.py                   # Azure ML 运行脚本（全云模式）
│   ├── run_local_agent.py             # 本地智能体对接 Azure 云端虚拟机
│   ├── show_azure.py                  # 汇总 Azure 运行结果
│   ├── experiments.json               # Azure 实验配置
│   └── azure_files/                   # Azure 启动脚本
│       ├── run_entry.py               # 每台 Azure VM 上的 Job 入口
│       └── compute-instance-startup.sh
│
└── src/mattoolbench-container/
    ├── Dockerfile-MatToolBench-Base   # 镜像层1：Python / CUDA / 模型权重
    ├── Dockerfile-MatToolBench        # 镜像层2：客户端代码 + VM 文件
    ├── entry.sh / start_vm.sh / start_client.sh
    │
    ├── vm/
    │   ├── image/setup.iso            # Windows 11 安装镜像
    │   ├── storage/                   # VM 磁盘快照（windows.base 等）
    │   ├── unattend-files/            # 自动安装应答文件
    │   └── setup/                     # Windows 内部安装脚本 + 工具包
    │       └── [Avantage / VESTA / DigitalMicrograph / Materials Studio / ...]
    │
    └── client/                        # Python 客户端（运行于容器内）
        ├── run.py                     # 主执行入口
        ├── experiment_configs/        # 各实验的 JSON 配置文件
        │   ├── main_gpt_5.json
        │   ├── main_claude_sonnet_4_6.json
        │   ├── main_gemini_1.5_pro.json
        │   ├── ablation_gui_som_*.json
        │   └── ...
        ├── desktop_env/
        │   ├── envs/desktop_env.py    # 核心环境类
        │   ├── controllers/           # VM / Python / 安装控制器
        │   └── evaluators/
        │       ├── getters/           # 各软件状态读取（jade、vesta 等）
        │       └── metrics/           # 评分函数
        ├── mm_agents/
        │   ├── gui_agent.py           # GUI 智能体
        │   ├── origin_agent.py        # Origin 智能体
        │   ├── code_agent.py          # Code 智能体
        │   └── navi/                  # NaviAgent 框架
        │       ├── screenparsing_oss/ # GroundingDINO、OmniParser、OCR
        │       ├── gpt/               # GPT-4V / Phi-3 视觉规划器
        │       └── llm/               # 纯文本 LLM 规划器
        ├── task_code/                 # 各数据库任务参考代码（MP、OQMD 等）
        ├── evaluation_examples_windows/  # 任务定义（JSON）
        └── output_result/             # 实验输出结果
```

---

## ☝️ 环境依赖

- Docker 已安装并运行。Windows 用户推荐使用 [Docker + WSL 2](https://docs.docker.com/desktop/wsl/)
- [OpenAI](https://platform.openai.com/docs/introduction) 或 [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) API Key
- Python 3.9，推荐使用 [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html)：
  ```bash
  conda create -n mattoolbench python=3.9
  conda activate mattoolbench
  ```

克隆并安装依赖：
```bash
git clone https://github.com/<your-org>/MatToolBench.git
cd MatToolBench
pip install -r requirements.txt
```

---

## 💻 本地部署（WSL 或 Linux）

### 1. 配置

在项目根目录创建 `config.json`：
```json
{
    "OPENAI_API_KEY": "<your-openai-key>",
    "OPENAI_ENDPOINT": "https://api.openai.com/v1",
    "AZURE_API_KEY": "<your-azure-openai-key>",
    "AZURE_ENDPOINT": "https://yourendpoint.openai.azure.com/"
}
```

> OpenAI 和 Azure OpenAI 二选一即可，脚本会自动检测。两者均未填写时会报错退出。

### 2. 构建 Docker 镜像

首次构建（包含 base 镜像）：
```bash
cd scripts
./build-container-image.sh --build-base-image true
```

> Base 镜像阶段会安装 Python 依赖、CUDA 库并下载模型权重（GroundingDINO、OmniParser），耗时约 **30–60 分钟**，具体取决于网络速度。国内用户建议配置 pip 镜像源加速。

base 镜像已构建且未变更时，可跳过该步骤：
```bash
./build-container-image.sh   # --build-base-image 默认为 false
```

### 3. 准备 Windows 11 虚拟机

#### 3.1 下载 Windows 11 ISO

前往 [Microsoft Evaluation Center](https://info.microsoft.com/ww-landing-windows-11-enterprise.html)，下载 **Windows 11 Enterprise Evaluation（90 天试用版，英文，美国）**（约 6 GB），将文件重命名为 `setup.iso`，放至：
```
src/mattoolbench-container/vm/image/setup.iso
```

#### 3.2 构建黄金镜像

有两种方式获取黄金镜像，推荐直接下载我们预构建的 VM 快照。

---

##### 方式 A：使用预构建 VM 快照（推荐）

直接下载我们已配置好的 VM 快照，所有材料科学软件均已安装完毕，无需手动操作。

**下载地址：** [MatToolBench VM Snapshot](TODO)  <!-- 替换为实际下载链接 -->

解压后将文件放至：
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

完成后直接跳至 [§ 4 运行基准测试](#4-运行基准测试)。

---

##### 方式 B：从头构建

自动脚本负责 Windows 11 的安装，专业材料科学软件需通过共享文件夹手动安装。

**B-1 — 下载软件安装包**

将各软件安装包下载后，放入 `src/mattoolbench-container/vm/setup/` 下对应的子目录：

| 软件 | 用途 | 版本 | 安装包路径 | 下载 |
|------|------|------|-----------|------|
| **OriginPro** | 数据分析与绘图 | 2024 | `vm/setup/OriginSetup.exe` | [下载](TODO) |
| **Jade** | XRD 物相分析 | 9.0 | `vm/setup/Jade_setup.exe` | [下载](TODO) |
| **Avantage** | XPS 分析 | 6.6.0 | `vm/setup/Avantage 6.6.0/Setup.exe` | [下载](TODO) |
| **VESTA** | 晶体结构可视化 | 3.90.1 | `vm/setup/VESTA-win64/` | [下载](https://jp-minerals.org/vesta/en/download.html) |
| **Digital Micrograph (GMS)** | TEM/EELS 分析 | 3.5 | `vm/setup/DigitalMicrograph/setup.exe` | [下载](TODO) |
| **Materials Studio** | 分子模拟 | 2023 (64位) | `vm/setup/Materials Studio 2023(64bit)/` | [下载](TODO) |

> VESTA 为开源软件，可从官网直接下载。其余均为商业软件，请联系相应厂商或通过机构授权获取。

**B-2 — 启动 Windows 11 自动安装**

```bash
cd scripts
./run-local.sh --mode dev --prepare-image true
```

在浏览器打开 `http://localhost:8006` 可观察 VM 启动和自动配置过程（Windows 安装 + 基础工具配置约需 **20 分钟**）。

**B-3 — 在 VM 内手动安装材料科学软件**

自动配置完成、Windows 桌面出现在 `http://localhost:8006` 后：

1. 在 VM 内打开**文件资源管理器**，导航到 `\\host.lan\Data`——这是宿主机 `src/mattoolbench-container/vm/setup/` 目录的共享映射。
2. 按以下顺序依次运行安装包：

```
\\host.lan\Data\OriginSetup.exe                        → 按向导完成安装
\\host.lan\Data\Jade_setup.exe                         → 按向导完成安装
\\host.lan\Data\Avantage 6.6.0\Setup.exe               → 按向导完成安装
\\host.lan\Data\VESTA-win64\VESTA_Setup.exe             → 按向导完成安装
\\host.lan\Data\DigitalMicrograph\setup.exe             → 按向导完成安装
\\host.lan\Data\Materials Studio 2023(64bit)\Setup.exe  → 按向导完成安装
```

3. 所有软件安装完成后，在 Windows 内正常关机（开始菜单 → 关机）。`vm/storage/` 中的磁盘快照会自动更新。

> **提示：** 也可通过 RDP 连接到 `localhost:3390`（用户名：`Docker`）以获得更流畅的安装体验。

#### 3.3 保存与复用 VM 快照

方式 B 构建完成后，备份整个 `vm/storage/` 目录，下次使用时无需重新安装：

```
vm/storage/
├── windows.base     ← VM 主磁盘镜像
├── windows.boot
├── windows.mac
├── windows.rom
├── windows.vars
├── windows.ver
└── data.img
```

将该目录复制到安全位置保存。需要恢复时，在运行 `./run-local.sh` 前将其放回原路径即可。

### 4. 运行基准测试

#### 4.1 快速启动
```bash
cd scripts
./run-local.sh
```

#### 4.2 使用实验配置文件

所有实验参数以 JSON 文件定义在 `experiment_configs/` 目录下：

```bash
cd src/mattoolbench-container/client
python run.py --config experiment_configs/main_gpt_5.json

# 运行时覆盖单个参数：
python run.py --config experiment_configs/main_gpt_5.json --trial_id 1
```

可用主实验配置：

| 配置文件 | 模型 |
|---|---|
| `main_gpt_5.json` | GPT-5（OpenAI）|
| `main_gpt_5_mini.json` | GPT-5-mini |
| `main_claude_sonnet_4_6.json` | Claude Sonnet 4.6 |
| `main_gemini_1.5_pro.json` | Gemini 1.5 Pro |
| `main_qwen_max.json` | Qwen-Max |

#### 4.3 调试 / 交互模式

以交互模式启动容器（不自动启动 VM 和客户端）：
```bash
./run-local.sh --interactive true
# 进入容器后手动启动各进程：
./start_vm.sh
./start_client.sh
```

测试 Windows VM 是否可访问：
```bash
./run-local.sh --connect true
# 在容器内执行：
curl -X GET http://20.20.20.21:5000/screenshot  # 返回 HTTP 200 则正常
```

#### 4.4 查看结果
```bash
cd src/mattoolbench-container/client
python show_result.py --result_dir results/main_gpt_5
python print_ablation_results.py   # 打印所有消融实验对比表格
```

日志位置：
- PowerShell 安装日志：`vm/setup/ps_script_log.txt`
- Windows 服务端日志：`vm/setup/server/server.log`

---

## ☁️ Azure 云端部署

Azure 部署通过 Azure ML Compute Instance 在多台云服务器上并行运行实验——每台服务器独立运行一个 Windows 11 虚拟机，所有 Worker 同时工作，大幅提升评测吞吐量。

### 部署架构

```
本地机器
  └── run_azure.py
        │
        ├── 并行创建 N 个 Compute Instance
        │     w0<exp>、w1<exp>、...、w{N-1}<exp>
        │
        └── 并行提交 N 个 ML Job
              每个 Job 在各自的 Compute Instance 上：
                ├── 拉取 Docker 镜像
                ├── 从 Azure Blob 复制 VM 快照
                ├── 启动 Windows 11 虚拟机（QEMU）
                └── 运行 Python 智能体（run.py）
```

Azure 部署支持**两种模式**：

| 模式 | 适用场景 | 方式 |
|------|----------|------|
| **全云模式** | 智能体在 Azure VM 内运行，全程自动化 | `vm_only: false` |
| **VM-only + 本地智能体** | Windows VM 在 Azure，智能体代码在本地运行 | `vm_only: true` + `run_local_agent.py` |

---

### 第一步 — Azure 环境准备

需要具备：
- 拥有足够配额的 **Azure 订阅**（例如 `Standard_D8_V3` 每个 Worker 需要 8 个 vCPU 核心）
- 一个 **Azure ML 工作区**（在 [ml.azure.com](https://ml.azure.com) 创建）
- 工作区中注册的 **Azure Blob Storage 数据存储**（默认使用 `workspaceblobstore`）
- 已登录 **Azure CLI**，或配置好 `DefaultAzureCredential` 所需的凭证

如需申请配额提升：
> Azure ML 门户 → 工作区 → 计算 → 配额 → 申请提升

---

### 第二步 — 在 `config.json` 中添加 Azure 凭证

在项目根目录的 `config.json` 中追加 Azure ML 相关凭证：

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

`AZURE_INSTANCE_IPS` 仅在 VM-only 模式下使用（见第六步），全云模式填空列表即可。

---

### 第三步 — 上传 VM 快照至 Azure Blob

Windows 11 黄金镜像必须提前上传到 Azure Blob Storage，各 Worker 启动时会从此处下载。

1. 先在本地构建黄金镜像（参见[本地部署 § 3.2](#32-构建黄金镜像)），或使用已有快照。
2. 将整个 `vm/storage/` 目录上传至 Azure 数据存储：

```bash
# 使用 Azure CLI 批量上传
az storage blob upload-batch \
    --account-name <your-storage-account> \
    --destination storage \
    --source src/mattoolbench-container/vm/storage/
```

也可使用 [Azure Storage Explorer](https://azure.microsoft.com/en-us/products/storage/storage-explorer) 将 `vm/storage/` 文件夹拖拽上传至名为 `storage` 的容器（与 `datastore_input_path` 默认值对应）。

上传后 Blob 中的预期目录结构：
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

### 第四步 — 上传 Compute Instance 启动脚本

每台 Azure Compute Instance 创建时会执行一个启动脚本，需提前上传至 ML 工作区的文件存储：

```bash
azcopy copy scripts/azure_files/compute-instance-startup.sh \
    "https://<storage>.blob.core.windows.net/azureml/Users/<username>/compute-instance-startup.sh"
```

然后在 `experiments.json` 中将 `ci_startup_script_path` 更新为对应的 `Users/` 路径：
```json
"ci_startup_script_path": "Users/<your-username>/compute-instance-startup.sh"
```

---

### 第五步 — 配置 `scripts/experiments.json`

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

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `ci_startup_script_path` | 启动脚本在 ML 工作区文件存储中的路径 | — |
| `docker_img_name` | 各 VM 拉取的 Docker Hub 镜像 | `meiwu/mattoolbench:latest` |
| `datastore_input_path` | Azure Blob 中 VM 快照的路径 | `storage` |
| `exp_name` | 实验名称，同时作为 Azure ML Experiment 名称 | — |
| `vm_size` | 每台 Compute Instance 的 Azure VM 规格 | `Standard_D8_V3` |
| `num_workers` | 并行 Compute Instance（Worker）数量 | `1` |
| `agent` | 智能体路由（`auto`、`gui`、`code`、`origin`、`navi`）| `auto` |
| `model_name` | LLM 骨干模型（如 `gpt-5`、`claude-sonnet-4-6`）| — |
| `som_origin` | 屏幕解析方式（`oss`、`a11y`、`mixed-oss`、`omni`）| `oss` |
| `a11y_backend` | 无障碍后端（`uia`、`win32`）| `uia` |
| `origin_mode` | 模板脚本注入（`script`、`noscript`）| `script` |
| `json_name` | 容器内的任务列表 JSON | `evaluation_examples_windows/test_all.json` |
| `vm_only` | 若为 `true`，仅启动 VM；智能体通过 `run_local_agent.py` 在本地运行 | `false` |
| `use_managed_identity` | 使用 Azure 托管身份代替服务主体 | `false` |

---

### 第六步 — 启动实验

**全云模式**（智能体在 Azure 运行，全程自动化）：

```bash
cd scripts
python run_azure.py --experiments_json experiments.json
```

`run_azure.py` 执行流程：
1. **并行**创建（或启动）`N` 台 Compute Instance，命名规则为 `w0<exp_name>`、`w1<exp_name>`……
2. **并行**提交 `N` 个 ML Job——每个 Job 自动下载 VM 快照、启动 Windows 虚拟机、运行智能体。

在 [Azure ML Studio](https://ml.azure.com) 中可实时查看任务状态；也可通过以下命令汇总结果：

```bash
python show_azure.py \
    --result_dir <your-result-dir> \
    --json_config experiments.json \
    --output_file results_table.md
```

---

### 第七步（可选）— VM-Only 模式 + 本地智能体

当你希望 **Windows VM 运行在 Azure**、而**智能体代码在本地执行**时使用此模式——例如需要快速迭代智能体逻辑，而不希望每次都重新构建 Docker 镜像。

**7.1 — 仅启动 VM**

将 `experiments.json` 中的 `vm_only` 设为 `true`，然后提交任务：
```bash
python run_azure.py --experiments_json experiments.json
```

每个 Job 会启动 Windows 虚拟机后持续等待 SSH 隧道连接。VM 在容器内暴露两个端口：
- Windows API：**5000**
- QEMU QMP：**7200**

**7.2 — 获取各 Compute Instance 的公网 IP**

在 Azure ML 门户中查看：
> 计算 → Compute Instance → 选择实例 → SSH 端点

也可直接将 IP 列表写入 `config.json`（列表索引 = Worker ID）：
```json
"AZURE_INSTANCE_IPS": ["20.1.2.3", "20.1.2.4", "20.1.2.5"]
```

Azure ML Compute Instance 默认 SSH 端口为 **50000**。

**7.3 — 在本地运行智能体**

单个 Worker：
```bash
cd scripts
python run_local_agent.py --exp_name experiment_1 --worker_id 0
```

全部 Worker 并行（Worker 数量取自 `experiments.json` 中的 `num_workers`）：
```bash
python run_local_agent.py --exp_name experiment_1 --all_workers
```

`run_local_agent.py` 会自动完成：
- 为每台 Azure Compute Instance 建立 SSH 隧道
- 为每个 Worker 分配独立的本地回环地址（`127.0.0.1`、`127.0.0.2`……），避免端口 5000 冲突
- 等待 Windows VM 就绪（最长 10 分钟）
- 启动 Python 智能体，连接至对应的隧道端点

其他常用参数：
```
--instance_ip  <ip>    手动指定单个 Worker 的 IP（覆盖 config.json）
--ssh_port     <port>  SSH 端口（默认：50000）
--pem_path     <path>  SSH 私钥路径（.pem 文件）
--result_dir   <path>  本地结果保存目录（默认：./results）
```

---

### 第八步 — 收集结果

结果写入 `experiments.json` 中配置的 `result_dir`（位于 Azure Blob 输出数据集中）。下载至本地：

```bash
az storage blob download-batch \
    --account-name <your-storage-account> \
    --source agent_outputs/<exp_name> \
    --destination ./results/
```

汇总分析：
```bash
cd src/mattoolbench-container/client
python print_ablation_results.py
```

---

## 🤖 智能体详情

### GUIAgent（NaviAgent）

材料软件 GUI 视觉交互智能体，每步执行流程：
1. 对 Windows VM 截图
2. 运行 **ScreenParser（SoM）** 识别并标注 UI 元素（GroundingDINO + OCR，或 OmniParser / 无障碍树）
3. 将标注截图传入 **LLMPlanner**（GPT-4V 等）
4. 通过 VM 控制器执行规划动作（点击、输入、滚动、快捷键）

屏幕解析模式由 `som_origin` 参数控制：

| `som_origin` 值 | 屏幕解析方式 |
|---|---|
| `oss` | GroundingDINO + Tesseract OCR（默认）|
| `a11y` | 仅 Windows 无障碍树 |
| `mixed-oss` | 无障碍树 + OCR 融合 |
| `omni` | OmniParser |

### OriginAgent

继承自 NaviAgent，执行流程：
1. 在 OriginPro 中打开数据文件（Ctrl+O）
2. 打开 Code Builder（Alt+4）
3. 编写或调整 OriginPro Python 脚本（可选：参考 `origin_draw/` 中的领域模板）
4. 运行脚本（F5）生成输出图表

模板脚本覆盖：XRD 物相匹配、XPS 峰拟合、拉曼光谱、电化学循环、阶跃分析、库仑效率等。

`origin_mode` 参数：
- `script` — LLM 以领域模板脚本为上下文进行调整
- `noscript` — LLM 从零编写脚本

### CodeAgent

纯文本智能体，执行流程：
1. LLM 生成 Python 代码，查询材料数据库（MP、OQMD、PyMatgen、OPTIMADE）
2. 执行代码；失败时将错误回溯反馈给 LLM 进行自我纠错
3. 最多重试 `code_retries` 次

---

## 🔬 消融实验设计

所有消融实验均以 **GPT-5 为骨干模型**，设置 `temperature: 0.0` 确保结果可复现。一键运行全部消融实验：

```bash
bash scripts/run_ablations.sh
```

### 维度一 — Origin：模板脚本注入

验证向 OriginAgent 系统提示词中注入预编写的领域模板脚本，是否能提升 Origin 绘图任务的成功率。

| 配置文件 | `origin_mode` | 说明 |
|---|---|---|
| `ablation_origin_script.json` | `script` | OriginAgent 接收领域模板脚本作为上下文 |
| `ablation_origin_noscript.json` | `no_script` | OriginAgent 从零编写脚本（基准线）|

**研究问题：** 为 LLM 提供特定任务的 OriginPro 脚本模板，相比从零生成是否有显著帮助？

### 维度二 — GUI：屏幕解析方式（SoM 模式）

对比四种不同的屏幕解析策略在材料科学 GUI 任务上的效果。

| 配置文件 | `som_origin` | 解析方式 | 说明 |
|---|---|---|---|
| `ablation_gui_som_oss.json` | `oss` | GroundingDINO + Tesseract OCR | 仅 OCR，无结构信息（基准线）|
| `ablation_gui_som_a11y.json` | `a11y` | Windows 无障碍树 | 纯结构信息，无视觉输入 |
| `ablation_gui_som_mixed.json` | `mixed-oss` | 无障碍树 + OCR 融合 | 多模态融合 |
| `ablation_gui_som_omni.json` | `omni` | OmniParser 视觉定位 | 端到端视觉解析 |

**研究问题：** 对于预训练时未见过的专业材料软件（Jade、VESTA 等），视觉定位是否优于结构化无障碍信息？

### 主实验 — LLM 模型对比

在完整 MatToolBench（全任务类型）上对比多个 LLM 骨干模型。运行命令：

```bash
bash scripts/run_main.sh
```

| 配置文件 | 模型 | 测试任务集 |
|---|---|---|
| `main_gpt_5.json` | GPT-5 | 全部（GUI + Origin + Code）|
| `main_gpt_5_mini.json` | GPT-5-mini | 全部 |
| `main_claude_sonnet_4_6.json` | Claude Sonnet 4.6 | 全部 |
| `main_qwen_max.json` | Qwen-Max | 全部 |
| `main_gemini_1.5_pro.json` | Gemini 1.5 Pro | 全部 |

### 关键配置参数

| 参数 | 说明 | 可选值 |
|---|---|---|
| `som_origin` | GUI/Origin 智能体的屏幕解析方式 | `oss`, `a11y`, `mixed-oss`, `omni` |
| `origin_mode` | 是否向 OriginAgent 注入领域模板脚本 | `script`, `no_script` |
| `model` | LLM 骨干模型 | `gpt-5`, `claude-sonnet-4-6`, `qwen-max`, ... |
| `max_steps` | 每任务最大步数（同时控制 CodeAgent 重试次数）| 整数（默认 `15`，Origin 任务用 `8`）|
| `temperature` | LLM 采样温度 | 主实验/消融用 `0.0`，探索性实验用 `0.5` |
| `diff_lvl` | 任务难度过滤 | `normal`, `hard` |

---

## 📊 实验结果

每个任务完成后，得分会追加写入结果目录下的 `scores_summary.csv`。汇总所有消融实验：

```bash
cd src/mattoolbench-container/client
python print_ablation_results.py
```

---

## 👏 致谢

- [Windows Agent Arena](https://github.com/microsoft/WindowsAgentArena) — Windows 虚拟机基准测试基础设施
- [OS World](https://github.com/xlang-ai/OSWorld) — 基准任务框架
- [OmniParser](https://github.com/microsoft/OmniParser) — 屏幕理解模型
- [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO) — 目标检测模块

## 📖 引用

```bibtex
@article{mattoolbench2024,
  title   = {MatToolBench: Benchmarking Desktop AI Agents for Materials Science},
  year    = {2024},
}
```

## 开源协议

MIT License，详见 [LICENSE](LICENSE)。
