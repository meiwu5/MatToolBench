import os
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_6.txt")

with MPRester(api_key) as mpr:
    doc = mpr.materials.elasticity.search(
        material_ids=["mp-134"],
        fields=["bulk_modulus", "shear_modulus"],
    )[0]

bulk = doc.bulk_modulus
shear = doc.shear_modulus

def _vrh(val):
    if hasattr(val, "vrh"):
        return val.vrh
    if isinstance(val, dict):
        return val.get("vrh", val)
    return val

out = f"K_VRH: {_vrh(bulk)}; G_VRH: {_vrh(shear)}"

with open(output_path, "w") as f:
    f.write(out)

print("mp_task_6.txt 已生成")
