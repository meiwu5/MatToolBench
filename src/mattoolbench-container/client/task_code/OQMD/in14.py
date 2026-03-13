"""
Task 14: Query OQMD for Al-O compounds with volume between 8 and 12 A^3/atom (element_set=Al,O AND volume>8 AND volume<12). Save the count and first result to 'oqmd_task_14.txt'.
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
    data  = oqmd_get("element_set=Al,O AND volume>8 AND volume<12", limit=1)
    total = data.get("meta", {}).get("data_available", "N/A")
    entry = data["data"][0] if data["data"] else {}
    lines = [
        "Al-O compounds with volume 8-12 A^3/atom: " + str(total),
        "First result:",
        "  entry_id:   " + str(entry.get("entry_id","N/A")),
        "  name:       " + str(entry.get("name","N/A")),
        "  volume:     " + str(entry.get("volume","N/A")) + " A^3/atom",
        "  delta_e:    " + str(entry.get("delta_e","N/A")) + " eV/atom",
        "  stability:  " + str(entry.get("stability","N/A")) + " eV/atom",
        "  spacegroup: " + str(entry.get("spacegroup","N/A")),
    ]
    save("oqmd_task_14.txt", "\n".join(lines))

if __name__ == "__main__":
    main()
