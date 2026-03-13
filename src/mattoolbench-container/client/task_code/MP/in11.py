import os
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_11.txt")

with MPRester(api_key) as mpr:
    docs = mpr.materials.insertion_electrodes.search(
        elements=["Li", "Fe", "P", "O"],
        num_elements=(4, 4),
        fields=["material_ids", "average_voltage"],
        all_fields=False,
    )

lines = []
for doc in docs:
    for mid in doc.material_ids or []:
        lines.append(f"{mid}: {doc.average_voltage}")

with open(output_path, "w") as f:
    f.write("\n".join(lines))

print("mp_task_11.txt 已生成")
