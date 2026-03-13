import os
import json
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_3.txt")

with MPRester(api_key) as mpr:
    doc = mpr.materials.summary.search(
        material_ids=["mp-19005"],
        fields=["formation_energy_per_atom", "decomposes_to"],
    )[0]

out = {
    "formation_energy_per_atom": doc.formation_energy_per_atom,
    "decomposes_to": doc.decomposes_to,
}

with open(output_path, "w") as f:
    f.write(json.dumps(out, ensure_ascii=False))

print("mp_task_3.txt 已生成")
