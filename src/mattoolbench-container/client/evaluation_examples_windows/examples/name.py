import os
import json
import re
from pathlib import Path

def replace_double_slash_in_json_files(root_dir):
    """
    遍历 root_dir 及其所有子目录，
    找到所有 .json 文件，把文件内容中的 "//" 替换成 "\\"
    """
    root_path = Path(root_dir).resolve()
    print(f"开始处理目录: {root_path}")
    
    modified_count = 0
    file_count = 0
    
    # 遍历所有文件
    for file_path in root_path.rglob("*.json"):
        file_count += 1
        original_content = None
        
        try:
            # 读取文件原始内容（以文本模式）
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 只替换非字符串中的 // （简单版：直接全局替换）
            # 如果你需要更精确（只替换路径部分），可以后续再优化正则
            new_content = original_content.replace("//", "\\\\")
            
            # 如果内容有变化才写入
            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                modified_count += 1
                print(f"已修改: {file_path}")
            # else:
            #     print(f"无变化: {file_path}")
                
        except Exception as e:
            print(f"处理文件出错 {file_path}: {e}")
    
    print("\n处理完成！")
    print(f"总共扫描 json 文件: {file_count} 个")
    print(f"实际修改的文件: {modified_count} 个")


# ─────────────── 使用方式 ───────────────
if __name__ == "__main__":
    # 修改成你实际的文件夹路径
    folder_path = r"/mnt/d/ChemLLM/MatToolBench/src/mattoolbench-container/client/evaluation_examples_windows/examples"          # ← 这里改成你的路径
    # folder_path = "./my_project"                    # 相对路径也行
    
    replace_double_slash_in_json_files(folder_path)