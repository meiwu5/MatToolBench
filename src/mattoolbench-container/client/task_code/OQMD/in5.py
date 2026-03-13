"""
Task 5: Query OQMD for NaCl (element_set=Na,Cl AND ntypes=2), get the first entry, extract name/composition/spacegroup/volume/delta_e/stability, and save to 'oqmd_task_5.txt'.
"""

import os
import requests

OQMD_API   = "https://oqmd.org/oqmdapi/formationenergy"
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "oqmd"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


def oqmd_get(filter_str="", limit=100, **kwargs):
    params = {"format": "json", "limit": limit, "offset": 0}
    if filter_str:
        params["filter"] = filter_str
    params.update(kwargs)
    resp = requests.get(OQMD_API, params=params, timeout=120)
    resp.raise_for_status()
    return resp.json()


def save(filename, content):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {path}")

def main():
    data  = oqmd_get("element_set=Na,Cl AND ntypes=2", limit=1)
    entry = data["data"][0] if data["data"] else {}
    lines = [
        "name:        " + str(entry.get("name", "N/A")),
        "entry_id:    " + str(entry.get("entry_id", "N/A")),
        "composition: " + str(entry.get("composition", "N/A")),
        "spacegroup:  " + str(entry.get("spacegroup", "N/A")),
        "volume:      " + str(entry.get("volume", "N/A")) + " A^3/atom",
        "delta_e:     " + str(entry.get("delta_e", "N/A")) + " eV/atom",
        "stability:   " + str(entry.get("stability", "N/A")) + " eV/atom",
    ]
    save("oqmd_task_5.txt", "\n".join(lines))

if __name__ == "__main__":
    main()
