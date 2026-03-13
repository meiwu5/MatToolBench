from pymatgen.core import Structure
import os

lattice = [[4.2, 0, 0], [0, 4.2, 0], [0, 0, 4.2]]
cscl = Structure(lattice, ["Cs", "Cl"], [[0,0,0], [0.5,0.5,0.5]])

num_sites = cscl.num_sites

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task6.txt")
with open(output_path, "w") as f:
    f.write(str(num_sites))

print("task6.txt 已生成，num_sites =", num_sites)