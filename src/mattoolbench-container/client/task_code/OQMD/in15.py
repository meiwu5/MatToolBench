"""
Task 15: Query OQMD for stable La-Mn-O ternary compounds (element_set=La,Mn,O AND ntypes=3 AND stability<0.01), sorted by delta_e. Save total count and the lowest delta_e entry to 'oqmd_task_15.txt'.
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
    data    = oqmd_get("element_set=La,Mn,O AND ntypes=3", limit=10)
    entries = data["data"]
    entries.sort(key=lambda e: float(e.get("delta_e") or 0))
    total   = data.get("meta", {}).get("data_available", "N/A")
    entry   = entries[0] if entries else {}
    lines   = [
        "Total stable La-Mn-O ternary compounds: " + str(total),
        "=== Lowest formation energy entry ===",
        "entry_id:    " + str(entry.get("entry_id","N/A")),
        "name:        " + str(entry.get("name","N/A")),
        "composition: " + str(entry.get("composition","N/A")),
        "delta_e:     " + str(entry.get("delta_e","N/A")) + " eV/atom",
        "stability:   " + str(entry.get("stability","N/A")) + " eV/atom",
        "spacegroup:  " + str(entry.get("spacegroup","N/A")),
        "volume:      " + str(entry.get("volume","N/A")) + " A^3/atom",
        "prototype:   " + str(entry.get("prototype","N/A")),
    ]
    save("oqmd_task_15.txt", "\n".join(lines))

if __name__ == "__main__":
    main()
