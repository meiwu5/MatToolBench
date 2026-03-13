from pymatgen.core import Structure, Lattice
import numpy as np
import os

a = 5.43
lattice = Lattice.cubic(a)
si = Structure.from_spacegroup("Fd-3m", lattice, ["Si"], [[0, 0, 0]])

# 避免特殊字符 Å
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task10.txt")
np.savetxt(output_path, si.frac_coords, fmt="%.6f", 
           header="Si diamond fractional coordinates (a=5.43 Angstrom)\n8 sites in conventional cell")

print("task10.txt 已成功生成")