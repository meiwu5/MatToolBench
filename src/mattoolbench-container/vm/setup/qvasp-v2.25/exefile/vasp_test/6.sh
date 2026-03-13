#!/bin/bash
VASP="mpirun -np 4 /mnt/d/ChemLLM/tools_download/qvasp-v2.25/exefile/vasp_test/vasp_std"

# 创建自旋极化计算目录
mkdir -p SCF_Ni_spin
cd SCF_Ni_spin

# 复制结构文件
cp ../POSCAR_Ni_spin ./POSCAR

# 生成基础输入文件
qvasp -pbe Ni         # 生成Ni的POTCAR
qvasp -k 0.03         # 生成KPOINTS
qvasp -scf            # 生成SCF计算的INCAR

# 修改INCAR为自旋极化参数
sed -i "s/^ISPIN.*/ISPIN = 2/" INCAR
echo -e "MAGMOM = 4*1.0" >> INCAR
echo -e "IBRION = -1" >> INCAR
echo -e "NSW = 0" >> INCAR

# 运行VASP
$VASP > vasp.log

cd ..