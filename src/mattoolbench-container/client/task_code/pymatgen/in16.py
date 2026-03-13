from pymatgen.io.vasp import Vasprun
import os

dep_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dependencies", "VASP"))
xml_path = os.path.join(dep_dir, "vasprun.xml")
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task16.txt")

run = Vasprun(xml_path, parse_dos=True)
last_step = run.ionic_steps[-1]
final_energy = last_step.get("e_0_energy", last_step.get("e_fr_energy"))

with open(output_path, "w") as f:
    f.write(f"{final_energy}")

print("task16.txt 已生成，final_energy =", final_energy)