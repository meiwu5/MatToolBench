from pymatgen.core import Lattice
import numpy as np
import os

# 创建六方晶格 a=4.0, c=6.0
lattice = Lattice.hexagonal(a=4.0, c=6.0)

# 保存晶格矩阵
matrix = lattice.matrix
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task1.txt")
np.savetxt(output_path, matrix, fmt="%.6f", header="Hexagonal lattice matrix (a=4.0, c=6.0)")
print("task1.txt 已生成")
print(matrix)