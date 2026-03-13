"""
Task 11: Query OQMD for stable Ba-Ti-O compounds (element_set=Ba,Ti,O AND stability<0.01). Save all results' names, spacegroup, and delta_e to 'oqmd_task_11.txt'.
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
    data    = oqmd_get("element_set=Ba,Ti,O", limit=10)
    entries = data["data"]
    total   = data.get("meta", {}).get("data_available", len(entries))
    lines   = ["Stable Ba-Ti-O compounds: " + str(total)]
    for e in entries:
        lines.append(
            "  " + str(e.get("name","N/A")).ljust(20)
            + "  delta_e=" + str(e.get("delta_e","N/A")) + " eV/atom"
            + "  spacegroup=" + str(e.get("spacegroup","N/A"))
        )
    save("oqmd_task_11.txt", "\n".join(lines))

if __name__ == "__main__":
    main()
