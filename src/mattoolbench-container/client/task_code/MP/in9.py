import os
from mp_api.client import MPRester
from mp_api.client.routes.materials.magnetism import Ordering
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_9.txt")

with MPRester(api_key) as mpr:
    ids = mpr.materials.summary.search(
        chemsys="Fe-O",
        fields=["material_id"],
    )
    material_ids = [d.material_id for d in ids]

    docs = mpr.materials.magnetism.search(
        material_ids=material_ids,
        ordering=Ordering.FM,
        fields=["material_id", "total_magnetization"],
        all_fields=False,
    )

lines = []
for doc in docs[:5]:
    lines.append(f"{doc.material_id}: {doc.total_magnetization}")

with open(output_path, "w") as f:
    f.write("\n".join(lines))

print("mp_task_9.txt 已生成")
