import os
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_2.txt")

with MPRester(api_key) as mpr:
    bandstructure = mpr.materials.electronic_structure_bandstructure.get_bandstructure_from_material_id(
        "mp-1434"
    )
labels = []
if bandstructure and getattr(bandstructure, "labels_dict", None):
    labels = sorted(list(bandstructure.labels_dict.keys()))

with open(output_path, "w") as f:
    f.write("\n".join(labels))

print("mp_task_2.txt 已生成")
