from pymatgen.io.vasp.inputs import Incar
import os

incar = Incar({"NSW": 100, "EDIFF": 1e-6})
incar_str = incar.get_str()

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task13.txt")
with open(output_path, "w") as f:
    f.write(incar_str)

print("task13.txt 已生成")
print(incar_str)