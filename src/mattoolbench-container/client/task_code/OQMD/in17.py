"""
Task 17: Query OQMD for all stable Cu-Au binary compounds (element_set=Cu,Au AND ntypes=2 AND stability<0.01), sorted by delta_e. Save each entry's name/composition/delta_e to 'oqmd_task_17.txt'.
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
    data    = oqmd_get("element_set=Cu,Au AND ntypes=2", limit=10)
    entries = data["data"]
    entries.sort(key=lambda e: float(e.get("delta_e") or 0))
    total   = data.get("meta", {}).get("data_available", len(entries))
    lines   = ["Stable Cu-Au binary compounds: " + str(total)]
    for e in entries:
        lines.append(
            "  entry_id=" + str(e.get("entry_id","N/A")).ljust(10)
            + "  name=" + str(e.get("name","N/A")).ljust(10)
            + "  composition=" + str(e.get("composition","N/A")).ljust(15)
            + "  delta_e=" + str(e.get("delta_e","N/A")) + " eV/atom"
        )
    save("oqmd_task_17.txt", "\n".join(lines))

if __name__ == "__main__":
    main()
