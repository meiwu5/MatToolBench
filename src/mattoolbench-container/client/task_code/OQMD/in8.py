"""
Task 8: Query OQMD for the top 5 most stable Ti-O compounds (element_set=Ti,O AND stability<0), sorted by delta_e ascending, and save their names/delta_e/stability to 'oqmd_task_8.txt'.
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
    data    = oqmd_get("element_set=Ti,O", limit=10)
    entries = data["data"]
    entries.sort(key=lambda e: float(e.get("delta_e") or 0))
    lines   = ["Top 5 stable Ti-O compounds:"]
    for e in entries[:5]:
        lines.append(
            "  " + str(e.get("name","N/A")).ljust(15)
            + "  delta_e=" + str(e.get("delta_e","N/A")) + " eV/atom"
            + "  stability=" + str(e.get("stability","N/A")) + " eV/atom"
        )
    save("oqmd_task_8.txt", "\n".join(lines))

if __name__ == "__main__":
    main()
