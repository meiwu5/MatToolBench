# Origin 任务示例：FTIR 堆叠谱图

## 任务输入

```
Draw a stacked FTIR spectrum plot for the loaded data and save to:
C:\Users\Docker\Desktop\setup\output_result\origin\FTIR_stack.png
```

## 期望输出

`C:\Users\Docker\Desktop\setup\output_result\origin\FTIR_stack.png` — 一张堆叠 FTIR 谱图，包含峰位标注。

---

## Agent 执行轨迹

**Step 1** — 检查屏幕状态

Screen analysis: Code Builder 已打开（窗口标题含 "Code Builder"），工作表已加载，无需重新打开文件。

```decision
COMMAND
```
```python
computer.keyboard.press("ctrl+n")  # 新建 Python 文件
```

---

**Step 2** — 命名新文件

Screen analysis: 弹出文件名输入对话框。

```decision
COMMAND
```
```python
computer.keyboard.write("ftir.py")
computer.keyboard.press("enter")
```

---

**Step 3** — 粘贴模板脚本（修改 save_path）

Screen analysis: 新的 ftir.py 标签页已创建，编辑区为空。

```decision
COMMAND
```
```python
script = open("assets/origin_scripts/FTIR.py").read().replace(
    "save_path = os.path.join('..', 'output_result', 'ftir_stack.png')",
    r"save_path = r'C:\Users\Docker\Desktop\setup\output_result\origin\FTIR_stack.png'"
)
computer.mouse.move_abs(x=0.5, y=0.5)
computer.mouse.single_click()
computer.keyboard.press("ctrl+a")
computer.keyboard.press("delete")
computer.clipboard.copy_text(script)
computer.clipboard.paste()
```

---

**Step 4** — 运行脚本

Screen analysis: 脚本已粘贴，格式正确，无乱码。

```decision
COMMAND
```
```python
computer.keyboard.press("f5")
```

---

**Step 5** — 验证输出

Screen analysis: Python 控制台显示 "FTIR plot saved: ..."，无报错。

```decision
DONE
```

---

## 误差容忍

- 输出文件存在且可正常打开（PNG 格式）
- 谱图包含 ≥1 条曲线
- 文件路径与任务要求完全一致
