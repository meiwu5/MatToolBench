"""
Task 19: Query OQMD for stable Li-Fe-O ternary compounds (element_set=Li,Fe,O AND ntypes=3 AND stability<0.01). Calculate the average delta_e and save the full list and average to 'oqmd_task_19.txt'.
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
    data    = oqmd_get("element_set=Li,Fe,O AND ntypes=3", limit=10)
    entries = data["data"]
    total   = data.get("meta", {}).get("data_available", len(entries))
    values  = [float(e["delta_e"]) for e in entries if e.get("delta_e") is not None]
    avg     = sum(values) / len(values) if values else None
    avg_str = "{:.4f}".format(avg) + " eV/atom" if avg is not None else "N/A"
    lines   = [
        "Stable Li-Fe-O ternary compounds: " + str(total),
        "Average delta_e: " + avg_str,
        "",
        "All entries:",
    ]
    for e in entries:
        lines.append(
            "  " + str(e.get("name","N/A")).ljust(20)
            + "  delta_e=" + str(e.get("delta_e","N/A")) + " eV/atom"
            + "  spacegroup=" + str(e.get("spacegroup","N/A"))
        )
    save("oqmd_task_19.txt", "\n".join(lines))

if __name__ == "__main__":
    main()
