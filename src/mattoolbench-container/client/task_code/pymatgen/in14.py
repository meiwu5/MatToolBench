from pymatgen.io.vasp.inputs import Kpoints
import os

# 生成 8×8×8 Monkhorst-Pack 网格，移位为 (0,0,0)
kpts = Kpoints.monkhorst_automatic(kpts=(8, 8, 8), shift=(0, 0, 0))

# 正确获取字符串内容（适用于最新 pymatgen）
kpts_str = str(kpts)  # 推荐方式

# 保存到 output_result/task14.txt
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task14.txt")
with open(output_path, "w") as f:
    f.write(kpts_str)

print("task14.txt 已生成在 output_result")
print(kpts_str)