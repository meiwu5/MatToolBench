from pymatgen.core import Molecule
import json
import os

# 假设已保存 dict
lio = Molecule(["Li", "O"], [[0,0,0], [1.8,0,0]])
dict_data = lio.as_dict()

# 重建
reconstructed = Molecule.from_dict(dict_data)

formula, _ = reconstructed.composition.get_reduced_formula_and_factor()
if formula in ("Li2O2", "Li1O1"):
    formula = "LiO"

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task9.txt")
with open(output_path, "w") as f:
    f.write(f"dict: {dict_data}; formula: {formula}")

print("task9.txt 已生成，formula =", formula)  # LiO