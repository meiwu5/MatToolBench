#!/bin/bash
VASP="mpirun -np 4 /mnt/d/ChemLLM/tools_download/qvasp-v2.25/exefile/vasp_test/vasp_std"

# 创建DOS计算目录
mkdir -p DOS_calc
cd DOS_calc

# 复制结构文件
cp ../POSCAR_BN_DOS ./POSCAR

# 生成基础输入文件
qvasp -pbe B N        # 根据BN材料生成POTCAR
qvasp -k 0.03         # 生成KPOINTS
qvasp -scf            # 生成SCF计算的INCAR

# 修改INCAR为DOS计算参数
sed -i "s/^ISMEAR.*/ISMEAR = -5/" INCAR
echo -e "LORBIT = 11" >> INCAR
echo -e "NEDOS = 2000" >> INCAR
echo -e "IBRION = -1" >> INCAR
echo -e "NSW = 0" >> INCAR

# 运行VASP
$VASP > vasp.log

cd ..