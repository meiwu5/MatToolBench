from pymatgen.core import Molecule
import os

coords = [[0, 0, 0], [1.54, 0, 0]]
cc_mol = Molecule(["C", "C"], coords)

distance = cc_mol.get_distance(0, 1)

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task4.txt")
with open(output_path, "w") as f:
    f.write(f"{distance:.4f}")

print("task4.txt 已生成，距离 =", distance)