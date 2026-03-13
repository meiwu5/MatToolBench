import os
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_8.txt")

with MPRester(api_key) as mpr:
    summary = mpr.materials.summary.search(
        material_ids=["mp-19005"],
        fields=["band_gap", "task_ids"],
    )[0]
    task_ids = summary.task_ids or []
    tasks = []
    if task_ids:
        tasks = mpr.materials.tasks.search(
            task_ids=task_ids,
            fields=["input"],
            all_fields=False,
        )

is_hubbard = False
for t in tasks:
    incar = None
    if isinstance(t.input, dict):
        incar = t.input.get("incar") if isinstance(t.input.get("incar"), dict) else None
    if incar:
        if incar.get("LDAU") or incar.get("LDAUU"):
            is_hubbard = True
            break

out = f"band_gap: {summary.band_gap}; is_hubbard: {str(is_hubbard).lower()}"

with open(output_path, "w") as f:
    f.write(out)

print("mp_task_8.txt 已生成")
