"""
Task 18: Query OQMD for Ce-O binary compounds with band_gap > 0 (element_set=Ce,O AND ntypes=2 AND band_gap>0). Find the largest band gap entry and save to 'oqmd_task_18.txt'.
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
    data    = oqmd_get("element_set=Ce,O AND ntypes=2 AND band_gap>0", limit=10)
    entries = data["data"]
    entries.sort(key=lambda e: float(e.get("band_gap") or 0), reverse=True)
    total   = data.get("meta", {}).get("data_available", "N/A")
    entry   = entries[0] if entries else {}
    lines   = [
        "Total Ce-O binary compounds with band_gap>0: " + str(total),
        "=== Largest band gap entry ===",
        "entry_id:   " + str(entry.get("entry_id","N/A")),
        "name:       " + str(entry.get("name","N/A")),
        "band_gap:   " + str(entry.get("band_gap","N/A")) + " eV",
        "delta_e:    " + str(entry.get("delta_e","N/A")) + " eV/atom",
        "stability:  " + str(entry.get("stability","N/A")) + " eV/atom",
        "spacegroup: " + str(entry.get("spacegroup","N/A")),
    ]
    save("oqmd_task_18.txt","\n".join(lines))

if __name__ == "__main__":
    main()
