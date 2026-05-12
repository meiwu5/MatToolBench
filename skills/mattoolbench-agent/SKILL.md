---
name: mattoolbench-materials-agent
description: 控制材料科学软件（OriginLab、Jade、VESTA、Avantage、Materials Studio、DigitalMicrograph）及材料数据库API（Materials Project、OQMD、OPTIMADE、pymatgen）完成自动化分析任务的AI智能体工作流，涵盖GUI Agent、Origin Agent、Code Agent三类完整操作流程
---

# MatToolBench Materials Agent

## 概述

本 Skill 封装了 MatToolBench 基准测试中三类智能体的完整操作流程：

| Agent 类型 | 适用领域 | 工作方式 |
|---|---|---|
| **GUI Agent** | avantage / dm / jade / vesta / ms | 视觉截图 + 元素 ID 交互 |
| **Origin Agent** | origin | 视觉截图 + Code Builder 脚本注入 |
| **Code Agent** | mp / oqmd / pymatgen / optimade | 纯代码生成，无 GUI |

---

## 启动 Skill

### 命令行启动

```bash
# 启用 Skill（传入 skill 目录路径）
python run.py --agent_name auto --domain origin --model gpt-4o \
              --skill_path /path/to/skills/mattoolbench-agent

# 通过 start_client.sh 启动
bash start_client.sh --agent auto --model gpt-4o \
                     --skill-path /path/to/skills/mattoolbench-agent
```

### 云端 / experiment config JSON 启动

在 `experiment_configs/` 下的 JSON 配置文件中添加 `skill_path` 字段：

```json
{
  "agent_name": "auto",
  "model": "gpt-4o",
  "skill_path": "/client/skills/mattoolbench-agent",
  "origin_mode": "script",
  "origin_hint_mode": "hint",
  "result_dir": "./results/skill_run",
  "trial_id": "skill_v1"
}
```

启动：
```bash
python run.py --config experiment_configs/skill_gpt4o.json --emulator_ip 20.20.20.21
```

---

## 第一步：根据 domain 选择 Agent

```
domain ∈ {avantage, dm, jade, vesta, ms}  → GUI Agent
domain ∈ {mp, oqmd, pymatgen, optimade}   → Code Agent
domain == origin                            → Origin Agent
domain 未知                                → GUI Agent（默认）
```

---

## 第二步：执行循环（所有 Agent 通用）

每步输出固定格式：

```
1. Screen analysis   — 当前屏幕与任务目标关系
2. Multi-step plan   — 后续步骤和当前进度
3. Next step rationale — 本步操作理由
4. Decision:
   ```decision
   COMMAND  # 或 DONE / FAIL / WAIT
   ```
5. Action code:
   ```python
   # 一个操作
   ```
6. Memory:
   ```memory
   # 跨步骤信息
   ```
```

**关键约束**：每步只执行一个操作；连续 2 步无变化立即换策略。

---

## GUI Agent

**适用软件**：Jade、Avantage、VESTA、DigitalMicrograph、Materials Studio

### 完整输出规范和示例
→ `references/gui_agent_messages.md`

### computer 模块 API 速查

```python
# 鼠标（优先用 ID，无 ID 时用坐标）
computer.mouse.move_id(id=78)
computer.mouse.move_abs(x=0.22, y=0.75)   # 归一化坐标 0-1
computer.mouse.single_click()
computer.mouse.double_click()
computer.mouse.right_click()
computer.mouse.scroll(dir="down")          # "up"/"down"
computer.mouse.drag(x=0.35, y=0.48)

# 键盘
computer.keyboard.write("text")            # 仅 ASCII，不用于脚本输入
computer.keyboard.press("enter")           # 单键或组合键 "ctrl+a"

# 剪贴板（粘贴脚本必须用此方式）
computer.clipboard.copy_text("text")
computer.clipboard.copy_image(id=19, description="描述")
computer.clipboard.paste()

# 程序与窗口
computer.os.open_program("msedge")
computer.window_manager.switch_to_application("window_name")
```

完整 API → `references/computer_api.md`

### 各软件启动状态和快捷键
→ `references/software_hints.md`

---

## Origin Agent

**适用任务**：XRD、XPS、FTIR、Raman、能带结构、电池循环、库仑效率、自由能台阶

### 工作流（7步）
→ `references/origin_workflow.md`

### 任务类别 → 模板脚本

| 类别关键词 | 脚本文件 |
|---|---|
| `bs` / `band_structure` | `assets/origin_scripts/BS.py` |
| `xrd` / `xrd_match` | `assets/origin_scripts/XRD_match.py` |
| `xps` | `assets/origin_scripts/XPS.py` |
| `ftir` | `assets/origin_scripts/FTIR.py` |
| `raman` / `roman` | `assets/origin_scripts/roman.py` |
| `cycle` | `assets/origin_scripts/cycle.py` |
| `ce` / `coulombic` | `assets/origin_scripts/CE.py` |
| `step` / `free_energy` | `assets/origin_scripts/step.py` |
| 未知类别 | `assets/origin_scripts/base.py` |

### 脚本使用规则（CRITICAL）

1. **只修改 `save_path`**，其余参数不得修改：
   ```python
   save_path = r'C:\Users\Docker\Desktop\setup\output_result\origin\<filename>.png'
   ```
2. **通过剪贴板输入脚本**，不用 `keyboard.write()`
3. **`step`/`free_energy` 任务**：运行前必须用实际数值替换 `REACTION_STEPS` 和 `GIBBS_ENERGY`

---

## Code Agent

**适用任务**：Materials Project、OQMD、OPTIMADE、pymatgen

### 输出格式
仅输出单个 Python 代码块（无其他文字）：

```python
# 完整、自包含脚本
# 1. 查询 API
# 2. 处理结果
# 3. 写入输出文件（精确路径）
```

### 环境约束
- Python **3.10**（不用 3.11+ 语法）
- mp-api **0.39.5** / emmet-core **0.78.7**
- 不打开 GUI 窗口；UTF-8 写出文件
- 错误处理：即使数据不完整也写出结果文件

### API 代码示例
→ `references/code_api_hints.md`

---

## 常见边缘情况

### GUI
- **Jade 启动**：第一步必须关闭 "Read Pattern Files" 对话框
- **Materials Studio**：第一步必须确认窗口已最大化
- **意外对话框**：先处理，再继续
- **预触发对话框消失**：用快捷键重触发

### Origin
- **无 `.py` 标签页**：先 Ctrl+N 新建
- **粘贴乱码**：Ctrl+A → Delete，拆成 2-3 段分别粘贴
- **脚本报错**：修正后 Ctrl+A → Delete → 重新粘贴 → F5

### Code
- **OQMD 超时**：5次重试 + 指数退避
- **OPTIMADE**：用 `requests`，不用 `OptimadeClient`
- **Materials Project**：`MP_API_KEY` 直接赋值，不用 `os.getenv()`
