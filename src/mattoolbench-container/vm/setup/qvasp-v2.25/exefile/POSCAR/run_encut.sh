#!/bin/bash

# ===== fcc Cu ENCUT 收敛性测试 - 纯输入文件准备版 =====

ORIGINAL_POSCAR="./POSCAR_Cu_ENCUT"

# 检查原始 POSCAR 是否存在
if [ ! -f "$ORIGINAL_POSCAR" ]; then
    echo "错误：找不到原始 POSCAR 文件！"
    echo "请确认路径：$ORIGINAL_POSCAR"
    exit 1
fi

echo "=================================================="
echo "开始准备 fcc Cu ENCUT 收敛测试输入文件"
echo "原始结构：$ORIGINAL_POSCAR"
echo "ENCUT 测试值：400 450 500 550 600 650 700 750 800 eV"
echo "=================================================="

# 创建状态记录文件
> encut_status.txt
echo "# ENCUT(eV)    状态" >> encut_status.txt
echo "# $(date)" >> encut_status.txt

for encut in 400 450 500 550 600 650 700 750 800
do
    dir="ENCUT_$encut"
    echo "正在准备 $dir ..."

    mkdir -p $dir
    cd $dir

    # 复制原始文件为 POSCAR
    cp "$ORIGINAL_POSCAR" ./POSCAR

    # 生成 POTCAR、KPOINTS、INCAR
    qvasp -pbe Cu
    qvasp -k 0.03
    qvasp -scf

    # 设置 ENCUT
    sed -i '/ENCUT/d' INCAR 2>/dev/null || true
    echo "ENCUT = $encut" >> INCAR

    # 金属推荐参数
    grep -q "^ISMEAR" INCAR || echo "ISMEAR = 1" >> INCAR
    grep -q "^SIGMA" INCAR || echo "SIGMA = 0.1" >> INCAR
    grep -q "^PREC" INCAR || echo "PREC = Accurate" >> INCAR
    grep -q "^EDIFF" INCAR || echo "EDIFF = 1E-6" >> INCAR

    echo "  → $dir 准备完成！"
    echo "$encut       成功准备" >> ../encut_status.txt

    cd ..
done

echo ""
echo "=================================================="
echo "大功告成！所有 9 个 ENCUT 目录已准备好"
echo "当前路径：$(pwd)"
echo ""
echo "请检查一个目录确认："
echo "   ls ENCUT_550/"
echo "   cat ENCUT_550/INCAR | grep ENCUT"
echo ""
echo "后续步骤："
echo "1. 获取 VASP 可执行文件（vasp_std 等）"
echo "2. 进入每个目录运行： /你的/vasp_std 路径 > log &"
echo "3. 计算完后汇总能量："
echo "   grep 'ENCUT =' ENCUT_*/INCAR"
echo "   grep 'free energy' ENCUT_*/OUTCAR"
echo "=================================================="