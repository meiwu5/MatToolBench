import os
from mp_api.client import MPRester
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))
from pymatgen.core.surface import SlabGenerator

api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY not set")

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "mp"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mp_task_10.txt")

with MPRester(api_key) as mpr:
    doc = mpr.materials.summary.search(
        material_ids=["mp-126"],
        fields=["structure"],
    )[0]

structure = doc.structure
slabgen = SlabGenerator(structure, (1, 1, 1), min_slab_size=5, min_vacuum_size=10, center_slab=True)
slab = slabgen.get_slab()
num_atoms = slab.num_sites

with open(output_path, "w") as f:
    f.write(str(num_atoms))

print("mp_task_10.txt 已生成")
