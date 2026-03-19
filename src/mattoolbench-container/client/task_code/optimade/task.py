import os
from pathlib import Path
from optimade.client import OptimadeClient
from mp_api.client import MPRester

# ================= 配置区域 =================
API_KEY = "oUXXrSHjpKWSbjmHP1HT5YNVZCi21rbP"
DESKTOP = Path(os.path.join(os.path.expanduser("~"), "Desktop"))

# 初始化客户端 - 调高单次获取上限
opt_client = OptimadeClient(
    base_urls=["https://optimade.materialsproject.org"],
    silent=True
)

def get_data_safely(client, filter_str):
    """通用工具：处理 OPTIMADE 返回的 对象 或 字典"""
    response = client.get(filter=filter_str)
    # 处理结果
    if isinstance(response, dict):
        return response
    return response.data

# ===========================================

def run_all_tasks():
    print("🚀 开始执行综合任务...")

    # --- Task 1: IV 族单质与二元 ---
    res1 = get_data_safely(opt_client, 'elements HAS ANY "C","Si","Ge","Sn","Pb" AND nelements<=2')
    total1 = sum(len(d) for d in res1.values())
    (DESKTOP / "opt_task_1.txt").write_text(f"Total: {total1}")
    print("✅ Task 1 完成")
if __name__ == "__main__":
    run_all_tasks()