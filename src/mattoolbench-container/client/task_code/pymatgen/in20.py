from pymatgen.io.vasp.outputs import Eigenval
import os

dep_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dependencies", "VASP"))
eigenval_path = os.path.join(dep_dir, "EIGENVAL")
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task20.txt")

eigenval = Eigenval(eigenval_path)
bandgap, cbm, vbm, is_direct = eigenval.eigenvalue_band_properties
in_range = 1.0 <= bandgap <= 1.5

with open(output_path, "w") as f:
    f.write(f"bandgap: {bandgap:.6f}; in_range: {str(in_range).lower()}")

print("task20.txt 已生成，bandgap =", bandgap, ", in_range =", in_range)
