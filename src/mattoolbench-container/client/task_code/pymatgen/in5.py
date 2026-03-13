from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
import os

# 立方晶格 a=4.2，空间群 225 (Fm-3m)
lattice = Lattice.cubic(4.2)
cscl = Structure.from_spacegroup(225, lattice, ["Cs", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
cscl = cscl.get_primitive_structure()

# 可选：使用 SpacegroupAnalyzer 确认空间群
analyzer = SpacegroupAnalyzer(cscl)
print("空间群:", analyzer.get_space_group_number())  # 应为 225

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task5.txt")
with open(output_path, "w") as f:
    f.write(str(cscl))

print("task5.txt 已生成")
print(cscl)