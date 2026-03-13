from pymatgen.core import Lattice, Structure
from pymatgen.io.vasp.inputs import Poscar
import os

a = 5.43  # 金刚石 Si
lattice = Lattice.cubic(a)
si = Structure.from_spacegroup("Fd-3m", lattice, ["Si"], [[0, 0, 0]])

poscar = Poscar(si)
poscar_str = poscar.get_str()

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task12.txt")
with open(output_path, "w") as f:
    f.write(poscar_str)

print("task12.txt 已生成")
print(poscar_str)