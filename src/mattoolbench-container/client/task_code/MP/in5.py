import os
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_5.txt")

with MPRester(api_key) as mpr:
    docs = mpr.materials.summary.search(
        chemsys="Al-O",
        energy_above_hull=0,
        fields=["material_id"],
    )

ids = sorted([d.material_id for d in docs])
with open(output_path, "w") as f:
    f.write("\n".join(ids))

print("mp_task_5.txt 已生成")
