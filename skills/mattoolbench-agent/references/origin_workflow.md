# Origin Agent 完整工作流

本文档是 Origin Agent 的详细操作手册，涵盖从数据导入到脚本运行的全流程。

---

## 可用 Python 包

以下包已安装在环境中，**只能使用这些包**，不得导入其他包：

```
originpro, numpy, pandas, matplotlib, scipy, re, os, math
```

---

## 标准工作流（7步）

### 第 0 步：检查当前屏幕状态

**在操作前，先判断起点：**

- **活动窗口标题包含 "Code Builder"**：数据文件已加载到 Origin 工作表中。跳过步骤 1-2，直接从步骤 3 开始（若已有 `.py` 标签页，则从步骤 4 开始）。
- **活动窗口是 Origin 主窗口**（无 Code Builder）：从步骤 1 开始。

---

### 步骤 1：导入数据文件

在 Origin **主窗口**（非 Code Builder）中按 Ctrl+O，打开文件对话框。

- 在 **Open 对话框**中输入任务目标里的精确文件路径，按 Enter。
- **不要**在 Code Builder 里输入文件路径。
- 确认工作表已加载并可见后再继续。
- 如果出现警告或导入对话框，先处理（点 OK/Next/Finish）。

---

### 步骤 2：打开 Code Builder

按 Alt+4。确认窗口标题已变化。

- 如果出现 "保存更改？" 对话框，先处理。

---

### 步骤 3：新建 Python 文件

按 Ctrl+N。

当提示输入文件名时，输入与绘图类型对应的文件名：

| 绘图类型 | 文件名 |
|---|---|
| Raman 光谱 | `raman.py` |
| FTIR 光谱 | `ftir.py` |
| XRD 衍射 | `xrd.py` |
| XPS 能谱 | `xps.py` |
| 能带结构 | `bs.py` |
| 电池循环 | `cycle.py` |
| 库仑效率 | `ce.py` |
| 自由能台阶 | `step.py` |

确认新文件标签页可见后，再进入代码输入步骤。

---

### 步骤 4：输入代码

点击编辑区确保焦点，然后通过**剪贴板**粘贴：

```python
computer.clipboard.copy_text("...完整的 Python 脚本...")
computer.clipboard.paste()
```

> **绝对不要使用 `computer.keyboard.write()` 输入脚本**——它只支持 ASCII，会损坏 Unicode 字符，导致 IndentationError 或乱码。

---

### 步骤 5：运行脚本

按 F5。观察错误对话框或 Python 控制台输出。

---

### 步骤 6：验证输出

确认输出文件存在于正确路径。

---

### 步骤 7：标记完成

只有在**视觉确认结果正确**后才标记 DONE。

---

## 数据访问规则

数据通过步骤 1 的 Open 对话框加载。在脚本中这样访问：

```python
wks = op.find_sheet()   # 获取当前工作表
df = wks.to_df()        # 转换为 DataFrame
```

**不要**在脚本中使用 `op.open()`，**不要**添加 `try/except` 数据加载块。

**如果输入文件扩展名为 `.ogwu`**：通过 File → Open 打开，然后用 `op.find_sheet()` 访问工作表。

**如果打开了多个工作表**：在运行脚本前先点击正确的 sheet 标签页。

---

## 脚本修改规则

使用模板脚本时，**只允许修改 `save_path` 参数**：

```python
save_path = r'C:\Users\Docker\Desktop\setup\output_result\origin\<filename>.png'
```

**不得修改**颜色、标签、模式或其他任何参数。

---

## step / free_energy 任务特殊处理

模板中的 `REACTION_STEPS` 和 `GIBBS_ENERGY` 是**占位示例值**。

运行前必须：
1. 从任务说明或工作表读取真实的步骤标签和吉布斯能量值
2. 将 `REACTION_STEPS` 和 `GIBBS_ENERGY` 替换为实际数值
3. 如果任务说明和工作表都没有数据，先用 Ctrl+O 打开文件，从工作表中读取

---

## 脚本错误处理

1. 读取错误信息
2. 修正脚本
3. 按 Ctrl+A → Delete 清空编辑器
4. 重新粘贴修正后的脚本
5. 按 F5 重新运行

---

## 快捷键速查

| 快捷键 | 功能 |
|---|---|
| Ctrl+O | 打开文件对话框 |
| Alt+4 | 打开/切换到 Code Builder |
| Ctrl+N | 在 Code Builder 中新建 Python 文件 |
| F5 | 运行当前脚本 |
| Ctrl+A | 全选（用于清空编辑器） |
