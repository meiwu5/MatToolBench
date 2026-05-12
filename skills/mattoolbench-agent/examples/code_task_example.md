# Code 任务示例：查询 Materials Project

## 任务输入

```
Query Materials Project for all binary Fe-O compounds and write their
material_id, formula, and band_gap to:
C:\Users\Docker\Desktop\setup\output_result\mp\fe_o_compounds.txt
```

## 期望输出

`fe_o_compounds.txt` — 包含所有二元 Fe-O 化合物的列表，每行格式：`material_id | formula | band_gap`

---

## Agent 输出代码

```python
from mp_api.client import MPRester

MP_API_KEY = "your_api_key_here"
OUTPUT_PATH = r"C:\Users\Docker\Desktop\setup\output_result\mp\fe_o_compounds.txt"

try:
    with MPRester(MP_API_KEY) as mpr:
        results = mpr.materials.summary.search(
            elements=["Fe", "O"],
            num_elements=2,
            fields=["material_id", "formula_pretty", "band_gap"]
        )

    lines = ["material_id | formula | band_gap"]
    for r in results:
        lines.append(f"{r.material_id} | {r.formula_pretty} | {r.band_gap:.4f}")

    import os
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Written {len(results)} entries to {OUTPUT_PATH}")

except Exception as e:
    import os
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(f"Error: {e}")
    raise
```

---

## 误差容忍

- 输出文件存在
- 包含 `material_id` 列
- 条目数 ≥ 1
