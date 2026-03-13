import os
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_19.txt")

with MPRester(api_key) as mpr:
    doc = mpr.materials.phonon.search(
        material_ids=["mp-2490"],
        fields=["born"],
        all_fields=False,
    )[0]

with open(output_path, "w") as f:
    f.write(str(doc.born))

print("mp_task_19.txt 已生成")
