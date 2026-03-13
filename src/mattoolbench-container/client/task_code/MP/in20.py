import os
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

precious = {"Pt", "Au", "Pd", "Ag", "Ir", "Ru", "Rh"}

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_20.txt")

with MPRester(api_key) as mpr:
    docs = mpr.materials.summary.search(
        band_gap=(2.0, 3.0),
        fields=["elements"],
    )

filtered = [d for d in docs if not precious.intersection(set(d.elements or []))]

with open(output_path, "w") as f:
    f.write(f"count: {len(filtered)}")

print("mp_task_20.txt 已生成")
