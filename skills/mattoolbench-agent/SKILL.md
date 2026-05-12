---
name: mattoolbench-materials-agent
description: 控制材料科学软件（OriginLab、Jade、VESTA、Avantage、Materials Studio、DigitalMicrograph）及材料数据库API（Materials Project、OQMD、OPTIMADE、pymatgen）完成自动化分析任务的AI智能体工作流
---

# MatToolBench Materials Agent

## 概述

本 Skill 封装了 MatToolBench 基准测试中三类智能体的完整操作流程，用于驱动 AI 自动完成材料科学软件任务：

| Agent 类型 | 适用软件 / 任务 | 工作方式 |
|---|---|---|
| **GUI Agent** | Jade、Avantage、VESTA、DigitalMicrograph、Materials Studio | 视觉截图 + 元素 ID 点击 |
| **Origin Agent** | OriginLab 绘图与数据分析 | 视觉截图 + Python 脚本注入 Code Builder |
| **Code Agent** | Materials Project、OQMD、OPTIMADE、pymatgen | 纯代码生成，无 GUI |

---

## 第一步：判断任务类型

根据任务的 `domain` 字段选择 Agent：

```
domain ∈ {avantage, dm, jade, vesta, ms}  → GUI Agent
domain ∈ {mp, oqmd, pymatgen, optimade}   → Code Agent
domain == origin                            → Origin Agent
```

如果 `domain` 未知，默认使用 GUI Agent。

---

## 第二步：运行 benchmark

```bash
# 自动选择 Agent（推荐）
python run.py --agent_name auto --domain <domain> --model gpt-4o \
              --result_dir ./results --trial_id 0

# 指定单个任务
python run.py --agent_name auto --domain origin \
              --test_all_meta_path evaluation_examples_windows/origin.json \
              --origin_category xrd --model gpt-4o

# 消融实验（去掉提示）
python run.py --agent_name auto --domain origin --origin_hint_mode no_hint
python run.py --agent_name auto --domain jade   --gui_hint_mode no_hint
python run.py --agent_name auto --domain mp     --code_hint_mode no_hint
```

完整参数说明见 `references/run_args.md`。

---

## 第三步：Agent 执行循环

每个 Agent 在每个 step 中的输出格式如下：

```
1. Screen analysis   — 描述当前屏幕与任务目标的关系
2. Multi-step plan   — 列出后续步骤与当前进度
3. Next step rationale — 解释本步操作的原因
4. Decision block:
   ```decision
   COMMAND  # 或 DONE / FAIL / WAIT
   ```
5. Action code block:
   ```python
   # 使用 computer 模块执行一个操作
   ```
6. Memory update:
   ```memory
   # 存储跨步骤信息
   ```
```

### 决策规则
- **DONE**：任务已完成，输出文件已确认存在
- **FAIL**：任务无法完成（技术错误或目标不可达）
- **WAIT**：屏幕处于加载状态，等待下一帧
- **COMMAND**：执行 code block 中的操作

### 关键约束
- **每步只执行一个操作**，不要在一个 code block 里堆叠多个动作
- 如果连续 2 步屏幕无变化，**立即换策略**（换快捷键、换按钮、重新规划）
- 关闭对话框优先点文字按钮（"Close"、"Cancel"），而非小 X 图标

---

## GUI Agent 详细流程

详细的每个软件启动状态和快捷键见 → `references/software_hints.md`

### computer 模块 API

```python
# 鼠标操作
computer.mouse.move_id(id=78)              # 移动到元素 ID（优先使用）
computer.mouse.move_abs(x=0.22, y=0.75)   # 归一化坐标 (0-1, 左上为原点)
computer.mouse.single_click()
computer.mouse.double_click()
computer.mouse.right_click()
computer.mouse.scroll(dir="down")          # "up" 或 "down"
computer.mouse.drag(x=0.35, y=0.48)

# 键盘操作
computer.keyboard.write("hello")           # 写入文本（仅支持 ASCII）
computer.keyboard.press("enter")           # 按键（enter/escape/ctrl+a 等）

# 剪贴板操作（粘贴脚本必须用此方式，不能用 keyboard.write）
computer.clipboard.copy_text("text")
computer.clipboard.copy_image(id=19, description="图像描述")
computer.clipboard.paste()

# 程序与窗口
computer.os.open_program("msedge")        # 打开程序
computer.window_manager.switch_to_application("window_name")
```

完整 API 参考见 → `references/computer_api.md`

---

## Origin Agent 详细流程

完整工作流和脚本注入规则见 → `references/origin_workflow.md`

### 任务类别 → 模板脚本映射

| 任务类别 | 模板脚本 |
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

### 脚本修改规则（CRITICAL）
使用模板脚本时**只允许修改一个参数**：
```python
save_path = r'C:\Users\Docker\Desktop\setup\output_result\origin\<filename>.png'
```
不得修改颜色、标签、模式等其他任何参数。

### step/free_energy 任务特殊处理
`REACTION_STEPS` 和 `GIBBS_ENERGY` 是占位示例值，**运行前必须**：
1. 从任务说明或工作表读取真实的步骤标签和吉布斯能量值
2. 用实际数值替换模板中的占位值

---

## Code Agent 详细流程

完整的 API 代码示例见 → `references/code_api_hints.md`

### 输出格式
Code Agent 只输出一个 Python 代码块：
```python
# 完整、自包含的脚本
# 1. 查询数据库/API
# 2. 处理结果
# 3. 写入输出文件（使用任务中指定的精确路径）
```

### 关键约束
- Python 版本：**3.10**（不得使用 3.11+ 语法）
- mp-api 版本：**0.39.5** / emmet-core **0.78.7**
- 不得打开 GUI 窗口
- 输出文件使用 UTF-8 编码
- 错误处理：始终写出结果文件，即使数据不完整

---

## 常见边缘情况

### GUI Agent
- **对话框意外出现**：先处理（确认/取消/输入路径），再继续主任务
- **窗口未最大化**（Materials Studio）：第一步必须最大化，坐标点击依赖全屏
- **预触发的对话框消失**：用对应快捷键重新触发（见 `references/software_hints.md`）
- **Jade 启动**：第一步必须关闭 "Read Pattern Files" 数据库对话框

### Origin Agent
- **Code Builder 无编辑区 tab**：先按 Ctrl+N 创建新 Python 文件
- **粘贴后出现乱码或缩进错误**：按 Ctrl+A → Delete 清空，将脚本拆成 2-3 段分别粘贴
- **脚本报错**：读错误信息，修正脚本，Ctrl+A → Delete → 重新粘贴 → F5

### Code Agent
- **OQMD 响应慢**：使用 retry 逻辑（5次重试，指数退避）
- **OPTIMADE**：直接用 `requests` 调用 REST API，不用 `OptimadeClient`（未安装）
- **Materials Project**：通过 `MP_API_KEY` 环境变量传入密钥，不用 `os.getenv()`
