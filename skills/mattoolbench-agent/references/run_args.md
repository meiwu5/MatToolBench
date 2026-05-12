# run.py 完整参数说明

## 基础用法

```bash
cd src/mattoolbench-container/client
python run.py [参数...]
```

---

## 核心参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--agent_name` | `auto` | Agent 类型：`auto`（按 domain 自动选择）、`gui`、`code`、`origin`、`navi` |
| `--domain` | `all` | 评测领域：`avantage`/`dm`/`jade`/`vesta`/`ms`/`mp`/`oqmd`/`pymatgen`/`optimade`/`origin` |
| `--model` | `gpt-5.4` | LLM 模型标识符（如 `gpt-4o`、`gpt-4o-mini`） |
| `--result_dir` | `./results` | 结果输出目录 |
| `--trial_id` | `0` | 实验编号（用于区分多次运行） |

## 环境参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--emulator_ip` | `20.20.20.21` | VM 桌面环境 IP |
| `--screen_width` | `1920` | 屏幕宽度 |
| `--screen_height` | `1080` | 屏幕高度 |
| `--max_steps` | `50` | 每个任务最大步数 |
| `--sleep_after_execution` | `3.0` | 执行动作后等待秒数 |
| `--observation_type` | `screenshot` | 观察类型：`screenshot`/`som` |
| `--som_origin` | `oss` | 屏幕元素来源：`oss`/`omni`/`no_omni` |

## 消融实验参数

| 参数 | 选项 | 说明 |
|---|---|---|
| `--origin_mode` | `script`（默认）/ `no_script` | Origin：是否注入模板脚本 |
| `--origin_hint_mode` | `hint`（默认）/ `no_hint` | Origin：是否包含工作流提示 |
| `--code_hint_mode` | `hint`（默认）/ `no_hint` | Code：是否包含 API 示例代码 |
| `--gui_hint_mode` | `hint`（默认）/ `no_hint` | GUI：是否包含软件快捷键提示 |

## Origin 专用参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--origin_category` | `auto` | 模板脚本类别：`auto`/`xrd`/`xps`/`ftir`/`raman`/`cycle`/`bs`/`step`/`ce` |
| `--origin_max_tokens` | `8000` | Origin Agent 最大输出 token 数 |

## LLM 参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--temperature` | `1.0` | 采样温度 |
| `--max_tokens` | `2048` | GUI/Code Agent 最大输出 token |

## 多进程参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--worker_id` | `0` | 当前 worker ID |
| `--num_workers` | `1` | 总 worker 数 |

---

## 常用命令示例

```bash
# 运行全部 origin 任务，自动选择模板脚本
python run.py --agent_name auto --domain origin --model gpt-4o \
              --result_dir ./results/origin_run1 --trial_id 1

# 只运行 FTIR 类任务
python run.py --domain origin --origin_category ftir \
              --test_all_meta_path evaluation_examples_windows/origin.json

# 消融：Origin 不注入模板脚本
python run.py --domain origin --origin_mode no_script --trial_id ablation_noscript

# 消融：Origin 不注入任何提示（最强基线）
python run.py --domain origin --origin_hint_mode no_hint --trial_id ablation_nohint

# 运行 GUI 任务（Jade + VESTA + Avantage）
python run.py --domain jade --agent_name gui --model gpt-4o

# 运行代码任务（Materials Project）
python run.py --domain mp --agent_name code --model gpt-4o

# 并行运行（2个 worker）
python run.py --worker_id 0 --num_workers 2 &
python run.py --worker_id 1 --num_workers 2 &
```
