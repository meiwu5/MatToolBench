import numpy as np
from pymatgen.io.vasp import Vasprun
import os

dep_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dependencies", "VASP"))
xml_path = os.path.join(dep_dir, "vasprun.xml")
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task17.txt")

run = Vasprun(xml_path, parse_dos=True)
last_step = run.ionic_steps[-1]
stress_tensor = np.array(last_step.get("stress"))

np.savetxt(output_path, stress_tensor, fmt="%.6f")

print("task17.txt 已生成，stress tensor =")
print(stress_tensor)