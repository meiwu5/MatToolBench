import os
import numpy as np
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_12.txt")

with MPRester(api_key) as mpr:
    docs = mpr.materials.piezoelectric.search(
        material_ids=["mp-2104"],
        fields=["total"],
        all_fields=False,
    )

max_idx = None
max_val = None
if docs:
    matrix = np.array(docs[0].total)
    max_idx = np.unravel_index(np.abs(matrix).argmax(), matrix.shape)
    max_val = matrix[max_idx]

with open(output_path, "w") as f:
    f.write(f"max_value: {max_val}; index: {max_idx}")

print("mp_task_12.txt 已生成")
