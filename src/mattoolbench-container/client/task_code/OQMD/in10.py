"""
Task 10: Query OQMD for Ga-N compounds with band gap between 1.0 and 2.0 eV (element_set=Ga,N AND band_gap>1.0 AND band_gap<2.0). Save the total count and first result's details to 'oqmd_task_10.txt'.
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
    data  = oqmd_get("element_set=Ga,N AND band_gap>1.0 AND band_gap<2.0", limit=1)
    total = data.get("meta", {}).get("data_available", "N/A")
    entry = data["data"][0] if data["data"] else {}
    lines = [
        "Total GaN entries with band_gap 1-2 eV: " + str(total),
        "First result:",
        "  name:       " + str(entry.get("name","N/A")),
        "  entry_id:   " + str(entry.get("entry_id","N/A")),
        "  band_gap:   " + str(entry.get("band_gap","N/A")) + " eV",
        "  delta_e:    " + str(entry.get("delta_e","N/A")) + " eV/atom",
        "  stability:  " + str(entry.get("stability","N/A")) + " eV/atom",
        "  spacegroup: " + str(entry.get("spacegroup","N/A")),
    ]
    save("oqmd_task_10.txt", "\n".join(lines))

if __name__ == "__main__":
    main()
