# 材料数据库 API 参考

本文档包含 Code Agent 任务中各数据库/API 的具体调用示例。

---

## 环境约束

- Python 版本：**3.10**（不得使用 3.11+ 语法，如 `typing.NotRequired`、`tomllib`、复杂 `match` 语句）
- **mp-api 版本 0.39.5 / emmet-core 0.78.7**，只能使用这些版本提供的 API 接口
- OQMD：**使用 `requests` 直接调用 REST API**，不要用 `qmpy_rester`（未安装）
- OPTIMADE：**不要使用 `OptimadeClient`**（未安装），直接用 `requests`

---

## Materials Project（mp / pymatgen / mixed 任务）

```python
from mp_api.client import MPRester

MP_API_KEY = "your_api_key_here"  # 从任务环境变量获取，不用 os.getenv()

with MPRester(MP_API_KEY) as mpr:
    # 按 material_id 获取结构
    struct = mpr.materials.get_structure_by_material_id("mp-149")

    # 获取 DOS
    dos = mpr.materials.electronic_structure_dos.get_dos_from_material_id("mp-13")

    # 按元素搜索（指定返回字段）
    results = mpr.materials.summary.search(
        elements=["Fe", "O"],
        fields=["material_id", "band_gap", "formation_energy_per_atom"]
    )
```

---

## OQMD（oqmd 任务）

**必须使用 `requests` 直接调用 REST API，必须加重试逻辑（OQMD 从云环境访问可能很慢）：**

```python
import requests, time

OQMD_API = "https://oqmd.org/oqmdapi/formationenergy"

def oqmd_get(params, retries=5, timeout=60):
    for i in range(retries):
        try:
            resp = requests.get(OQMD_API, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if i < retries - 1:
                time.sleep(5 * (i + 1))
            else:
                raise

data = oqmd_get({
    "format": "json",
    "filter": "element_set=Fe,O AND ntypes=2",
    "limit": 10,
    "offset": 0
})["data"]

# 每条 entry 字段：name, entry_id, delta_e, stability,
#                  spacegroup, volume, unit_cell, site_atoms, ...
```

---

## OPTIMADE（optimade 任务）

**优先使用 `requests` 直接调用（最可靠）：**

```python
import requests

OPTIMADE_BASE = "https://optimade.materialsproject.org/v1"

def optimade_query(filter_str, page_limit=100):
    """查询 OPTIMADE REST API，自动翻页，返回所有条目"""
    entries = []
    url = f"{OPTIMADE_BASE}/structures"
    params = {
        "filter": filter_str,
        "page_limit": page_limit,
        "response_fields": "id,attributes"
    }
    while url:
        resp = requests.get(url, params=params, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        entries.extend(data.get("data", []))
        next_link = data.get("links", {}).get("next")
        url = next_link if next_link and next_link != url else None
        params = {}  # next link 已包含查询参数
    return entries

entries = optimade_query('nelements=2 AND elements HAS "Si"')
# 每条 entry 结构：
# {
#   "id": "...",
#   "attributes": {
#     "nelements": 2,
#     "elements": [...],
#     "chemical_formula_reduced": "...",
#     "nsites": N,
#     "lattice_vectors": [[...], [...], [...]],
#     "cartesian_site_positions": [...],
#     "species_at_sites": [...],
#     "_mp_bandgap": ...,
#     ...
#   }
# }
```

**备选方案** — 使用 `optimade` 基础包的 filter 解析器（不用 `OptimadeClient`）：

```python
from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import MongoTransformer

parser = LarkParser()
tree = parser.parse('nelements=2 AND elements HAS "Si"')
```

---

## pymatgen（纯 Python 任务，无外部 API）

```python
from pymatgen.core import Structure, Lattice, Element
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.io.vasp import Poscar

# 从文件读取结构
struct = Structure.from_file("POSCAR")

# 对称性分析
analyzer = SpacegroupAnalyzer(struct)
spacegroup = analyzer.get_space_group_symbol()

# 写出文件
struct.to(fmt="poscar", filename="output.vasp")
```

---

## 输出文件规则

- 使用任务说明中指定的**精确路径**，不得自行命名
- 使用 UTF-8 编码写出文本文件
- 错误处理（try/except）：即使数据不完整也要写出结果文件
- 不得打开任何 GUI 窗口
