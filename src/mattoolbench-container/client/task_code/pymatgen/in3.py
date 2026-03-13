from pymatgen.core import Molecule
import os

# 创建 C-C 分子片段
coords = [[0.0, 0.0, 0.0], [1.54, 0.0, 0.0]]
species = ["C", "C"]
cc_mol = Molecule(species, coords)

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task3.txt")
with open(output_path, "w") as f:
	f.write(f"{len(coords)}\n")
	f.write("C-C molecular fragment\n")
	for sp, (x, y, z) in zip(species, coords):
		f.write(f"{sp} {x:.6f} {y:.6f} {z:.6f}\n")

print("task3.txt 已成功生成（XYZ 格式）")
print(cc_mol)