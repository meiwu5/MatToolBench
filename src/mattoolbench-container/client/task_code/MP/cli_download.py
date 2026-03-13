from mp_api.client import MPRester

# 你的API密钥
api_key = "oUXXrSHjpKWSbjmHP1HT5YNVZCi21rbP"

with MPRester(api_key) as mpr:
    # 下载指定10个材料ID的数据
    material_ids = ["mp-149", "mp-66", "mp-22862", "mp-804", "mp-1143", 
                    "mp-2534", "mp-1265", "mp-30", "mp-81", "mp-13"]
    
    docs = mpr.materials.summary.search(material_ids=material_ids)
    
    print(f"成功下载 {len(docs)} 个材料数据\n")
    
    for doc in docs:
        mp_id = doc.material_id
        formula = doc.formula_pretty
        structure = doc.structure
        
        print(f"材料ID: {mp_id}")
        print(f"化学式: {formula}")
        print(f"晶系: {doc.symmetry.crystal_system}")
        print(f"空间群: {doc.symmetry.symbol}")
        
        # 保存为CIF文件
        cif_filename = f"{mp_id}_{formula}.cif"
        structure.to(filename=cif_filename, fmt="cif")
        print(f"已保存CIF: {cif_filename}\n")
        print("-" * 50)