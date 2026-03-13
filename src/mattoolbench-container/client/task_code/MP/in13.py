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
output_path = os.path.join(output_dir, "mp_task_13.txt")

with MPRester(api_key) as mpr:
    docs = mpr.materials.phonon.search(
        material_ids=["mp-149"],
        fields=["phonon_method"],
        all_fields=False,
    )
    phonon_method = docs[0].phonon_method if docs else None
    bs = None
    if phonon_method:
        try:
            bs = mpr.materials.phonon.get_bandstructure_from_material_id("mp-149", phonon_method)
        except Exception:
            bs = None

max_freq = None
if bs is not None:
    max_freq = float(np.max(bs.bands))

with open(output_path, "w") as f:
    f.write(f"max_phonon_frequency: {max_freq}")

print("mp_task_13.txt 已生成")
