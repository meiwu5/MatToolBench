"""
Task 16: Query OQMD for all Zn-O binary polymorphs (element_set=Zn,O AND ntypes=2), sorted by delta_e. Save total count, most stable and least stable entries to 'oqmd_task_16.txt'.
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
    data    = oqmd_get("element_set=Zn,O AND ntypes=2", limit=10)
    entries = data["data"]
    entries.sort(key=lambda e: float(e.get("delta_e") or 0))
    total   = data.get("meta", {}).get("data_available", len(entries))
    most    = entries[0]  if entries else {}
    least   = entries[-1] if entries else {}
    lines   = [
        "Total Zn-O binary polymorphs: " + str(total),
        "",
        "=== Most stable (lowest delta_e) ===",
        "entry_id:   " + str(most.get("entry_id","N/A")),
        "name:       " + str(most.get("name","N/A")),
        "delta_e:    " + str(most.get("delta_e","N/A")) + " eV/atom",
        "stability:  " + str(most.get("stability","N/A")) + " eV/atom",
        "spacegroup: " + str(most.get("spacegroup","N/A")),
        "",
        "=== Least stable (highest delta_e) ===",
        "entry_id:   " + str(least.get("entry_id","N/A")),
        "name:       " + str(least.get("name","N/A")),
        "delta_e:    " + str(least.get("delta_e","N/A")) + " eV/atom",
        "stability:  " + str(least.get("stability","N/A")) + " eV/atom",
        "spacegroup: " + str(least.get("spacegroup","N/A")),
    ]
    save("oqmd_task_16.txt","\n".join(lines))

if __name__ == "__main__":
    main()
