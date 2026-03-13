"""
Task 6: Query OQMD to count all binary compounds containing Al (element_set=Al AND ntypes=2), and save the total count to 'oqmd_task_6.txt'.
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
    data  = oqmd_get("element_set=Al AND ntypes=2", limit=1)
    total = data.get("meta", {}).get("data_available", "N/A")
    save("oqmd_task_6.txt", "Total Al binary compounds in OQMD: " + str(total))

if __name__ == "__main__":
    main()
