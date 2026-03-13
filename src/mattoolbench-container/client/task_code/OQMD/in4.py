"""
Task 4: Query OQMD for the most stable SiO2 compound (element_set=Si,O AND ntypes=2 AND stability<0.01), sorted by delta_e, and save the first result to 'oqmd_task_4.txt'.
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
    resp = requests.get(OQMD_API, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def save(filename, content):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {path}")

def main():
    data  = oqmd_get("element_set=Si,O AND ntypes=2", limit=1)
    entry = data["data"][0] if data["data"] else {}
    lines   = [
        "name:        " + str(entry.get("name", "N/A")),
        "entry_id:    " + str(entry.get("entry_id", "N/A")),
        "composition: " + str(entry.get("composition", "N/A")),
        "delta_e:     " + str(entry.get("delta_e", "N/A")) + " eV/atom",
        "stability:   " + str(entry.get("stability", "N/A")) + " eV/atom",
        "spacegroup:  " + str(entry.get("spacegroup", "N/A")),
    ]
    save("oqmd_task_4.txt", "\n".join(lines))

if __name__ == "__main__":
    main()
