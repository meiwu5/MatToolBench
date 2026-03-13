from pymatgen.core import Lattice, Structure
import os

lattice = Lattice.hexagonal(a=4.0, c=6.0)
structure = Structure(lattice, ["Ti"], [[0, 0, 0]])
volume = structure.volume

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task11.txt")
with open(output_path, "w") as f:
    f.write(f"{volume:.4f}")  # 约83.1384

print("task11.txt 已生成，volume =", volume)