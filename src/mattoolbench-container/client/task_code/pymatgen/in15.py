import os
from pymatgen.io.vasp import Vasprun

# 1. 设置路径
dep_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dependencies", "VASP"))
xml_path = os.path.join(dep_dir, "vasprun.xml")
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output_result", "pymatgen"))
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "task15.txt")

if os.path.exists(xml_path):
    # 2. 使用 pymatgen 解析 vasprun.xml
    # parse_dos=True 表示解析态密度相关信息（包含费米能）
    run = Vasprun(xml_path, parse_dos=True)
    
    # 3. 提取费米能级
    efermi = run.efermi
    # 4. 写入文件
    with open(output_file, "w") as f:
        f.write(f"{efermi}")
    
    print(f"✅ 成功！从 {xml_path} 提取 efermi = {efermi}")
    print(f"结果已存至: {output_file}")
else:
    print(f"❌ 错误：在当前目录找不到 {xml_path}")