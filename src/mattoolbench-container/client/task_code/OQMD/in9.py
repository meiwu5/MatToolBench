"""
Task 9: Query OQMD for all Li ternary compounds (element_set=Li AND ntypes=3). Count total entries and how many have stability<0.01. Save both counts to 'oqmd_task_9.txt'.
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
    d_all    = oqmd_get("element_set=Li AND ntypes=3", limit=1)
    total    = d_all.get("meta", {}).get("data_available", "N/A")
    d_stable = oqmd_get("element_set=Li AND ntypes=3", limit=1)
    stable   = d_stable.get("meta", {}).get("data_available", "N/A")
    lines    = [
        "Total Li ternary compounds:  " + str(total),
        "Stable Li ternary compounds: " + str(stable),
    ]
    save("oqmd_task_9.txt","\n".join(lines))

if __name__ == "__main__":
    main()
