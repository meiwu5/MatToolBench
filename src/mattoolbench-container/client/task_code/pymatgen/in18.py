from pymatgen.io.vasp.inputs import Poscar
import os

dep_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dependencies", "VASP"))
poscar_path = os.path.join(dep_dir, "POSCAR")
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task18.txt")

structure = Poscar.from_file(poscar_path).structure
num_atoms = structure.num_sites

with open(output_path, "w") as f:
    f.write(str(num_atoms))

print("task18.txt 已生成，num_atoms =", num_atoms)
