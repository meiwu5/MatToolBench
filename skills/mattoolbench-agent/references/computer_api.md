# computer 模块完整 API 参考

本文档是 GUI Agent 和 Origin Agent 可用的所有 `computer` 模块函数。

---

## 鼠标操作

```python
# 移动到指定元素 ID（优先使用，比坐标更准确）
computer.mouse.move_id(id=78)

# 移动到归一化坐标 (x, y)，左上角 (0,0)，右下角 (1,1)
# 仅当没有元素 ID 时使用（如空白区域、表单输入框）
computer.mouse.move_abs(x=0.22, y=0.75)

# 单击（在 move_id 或 move_abs 之后）
computer.mouse.single_click()

# 双击（打开文件/文件夹，选择文本）
computer.mouse.double_click()

# 右键（打开上下文菜单）
computer.mouse.right_click()

# 滚动（"up" 或 "down"）
computer.mouse.scroll(dir="down")

# 拖拽到目标归一化坐标
computer.mouse.drag(x=0.35, y=0.48)
```

### 何时用 `move_id` vs `move_abs`

| 场景 | 使用 |
|---|---|
| 按钮、图标、菜单项 | `move_id` |
| 空白输入区域（邮件正文、空表单） | `move_abs` |
| 截图中可见但无 ID 的目标 | `move_abs` |
| raw 模式（no_omni）| 只能用 `move_abs` |

---

## 键盘操作

```python
# 写入文本字符串（仅支持 ASCII）
# 不要用于 Origin 脚本输入——使用剪贴板代替
computer.keyboard.write("hello world")

# 按单个键
computer.keyboard.press("enter")
computer.keyboard.press("escape")
computer.keyboard.press("delete")
computer.keyboard.press("tab")
computer.keyboard.press("f5")

# 组合键（使用 + 分隔）
computer.keyboard.press("ctrl+a")    # 全选
computer.keyboard.press("ctrl+c")    # 复制
computer.keyboard.press("ctrl+v")    # 粘贴
computer.keyboard.press("ctrl+s")    # 保存
computer.keyboard.press("ctrl+o")    # 打开文件
computer.keyboard.press("ctrl+n")    # 新建
computer.keyboard.press("ctrl+z")    # 撤销
computer.keyboard.press("alt+4")     # Origin: 打开 Code Builder
computer.keyboard.press("win+up")    # 最大化窗口
computer.keyboard.press("alt+f4")    # 关闭窗口
```

---

## 剪贴板操作

```python
# 复制文本到剪贴板（用于存储信息或粘贴脚本）
computer.clipboard.copy_text("text to copy")

# 复制图像元素到剪贴板（带描述）
computer.clipboard.copy_image(id=19, description="revenue projection plot")

# 粘贴当前剪贴板内容（先确保点击了目标位置）
computer.clipboard.paste()
```

### 粘贴脚本的标准流程（Origin/Code Builder）

```python
# Step 1: 确保编辑器有焦点
computer.mouse.move_abs(x=0.5, y=0.5)
computer.mouse.single_click()

# Step 2: 全选并清空
computer.keyboard.press("ctrl+a")
computer.keyboard.press("delete")

# Step 3: 复制并粘贴脚本
computer.clipboard.copy_text("""
import originpro as op
# ... 完整脚本 ...
""")
computer.clipboard.paste()
```

---

## 程序与窗口

```python
# 打开程序（推荐方式，比点击图标更可靠）
computer.os.open_program("msedge")       # Microsoft Edge
computer.os.open_program("notepad")      # 记事本
computer.os.open_program("outlook")      # Outlook
computer.os.open_program("winword")      # Word
computer.os.open_program("excel")        # Excel
computer.os.open_program("powerpnt")     # PowerPoint

# 切换到指定窗口（窗口名称需与 "All window names" 输入中完全一致）
computer.window_manager.switch_to_application("semester_review.pptx - PowerPoint")
computer.window_manager.switch_to_application("Code Builder - Origin 2026")
```

---

## raw 模式（no_omni / som_origin=no_omni）限制

在 raw 截图模式下，**不可用**的函数：
- `computer.mouse.move_id(...)` — 无元素 ID
- `computer.clipboard.copy_image(...)` — 无元素 ID

只能使用：
- `computer.mouse.move_abs(x=..., y=...)` + 单击/双击/右键
- `computer.keyboard.write()` / `computer.keyboard.press()`
- `computer.clipboard.copy_text()` / `computer.clipboard.paste()`
- `computer.os.open_program()` / `computer.window_manager.switch_to_application()`
