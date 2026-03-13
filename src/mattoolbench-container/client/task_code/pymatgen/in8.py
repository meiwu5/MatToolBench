from pymatgen.core import Molecule
import json
import os

lio = Molecule(["Li", "O"], [[0,0,0], [1.8,0,0]])  # 合理 Li-O 距离约1.8Å

dict_data = lio.as_dict()

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "task8.txt")
with open(output_path, "w") as f:
    json.dump(dict_data, f, indent=2)

print("task8.txt 已生成")