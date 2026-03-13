import os
from mp_api.client import MPRester
from pymatgen.electronic_structure.core import Spin
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_4.txt")

with MPRester(api_key) as mpr:
    dos = mpr.materials.electronic_structure_dos.get_dos_from_material_id("mp-13")
up_max = None
down_max = None
if dos:
    if Spin.up in dos.densities:
        up_max = max(dos.densities[Spin.up])
    if Spin.down in dos.densities:
        down_max = max(dos.densities[Spin.down])

with open(output_path, "w") as f:
    f.write(f"Spin.Up max: {up_max}; Spin.Down max: {down_max}")

print("mp_task_4.txt 已生成")
