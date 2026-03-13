import os
from optimade.client import OptimadeClient
from pymatgen.core import Structure

def get_silicon_final_brute():
    query = 'nelements=1 AND elements HAS "Si"'
    client = OptimadeClient(base_urls=["https://optimade.materialsproject.org"])
    
    print(f"执行查询: {query}")

    try:
        results = client.get(filter=query)
        
        # 深度扫描函数：递归寻找包含特定 Key 的列表
        def find_entries(d):
            if isinstance(d, dict):
                # 尝试标准路径
                if 'data' in d and isinstance(d['data'], list):
                    return d['data']
                # 否则遍历字典的所有值继续找
                for v in d.values():
                    res = find_entries(v)
                    if res: return res
            elif isinstance(d, list) and len(d) > 0:
                # 检查列表项是否像是一个 OPTIMADE entry
                if isinstance(d[0], dict) and 'attributes' in d[0]:
                    return d
            return None

        # 开始在 results 字典中地毯式搜索
        entries = find_entries(results)

        if not entries:
            print(f"❌ 依旧无法定位数据。当前字典的所有键: {list(results.keys())}")
            # 打印第一层的结构，看看数据到底藏在哪个怪异的 Key 下
            first_key = list(results.keys())[0]
            print(f"Key '{first_key}' 的内容类型是: {type(results[first_key])}")
            return

        print(f"✅ 成功锁定数据！找到 {len(entries)} 个条目。")

        # 提取并构建第一个 Si 结构
        entry = entries[0]
        attr = entry.get('attributes', {})
        
        struct = Structure(
            lattice=attr['lattice_vectors'],
            species=attr['species_at_sites'],
            coords=attr['cartesian_site_positions'],
            coords_are_cartesian=True
        )
        
        # 导出文件
        out_name = "Si_FINAL_FIXED.vasp"
        struct.to(fmt="poscar", filename=out_name)
        
        print(f"🎉 成功导出: {os.path.abspath(out_name)}")
        print(f"化学式: {struct.composition.reduced_formula}")

    except Exception as e:
        print(f"💥 运行异常: {e}")

if __name__ == "__main__":
    get_silicon_final_brute()