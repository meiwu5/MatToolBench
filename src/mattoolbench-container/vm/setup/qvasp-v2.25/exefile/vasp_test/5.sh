#!/bin/bash
VASP="mpirun -np 4 /mnt/d/ChemLLM/tools_download/qvasp-v2.25/exefile/vasp_test/vasp_std"

# 创建全弛豫计算目录
mkdir -p Relax_ZnO
cd Relax_ZnO

# 复制结构文件
cp ../POSCAR_ZnO_relax ./POSCAR

# 生成基础输入文件
qvasp -pbe Zn O       # 生成ZnO的POTCAR
qvasp -k 0.03         # 生成KPOINTS
qvasp -relax          # 生成弛豫计算的INCAR

# 修改INCAR为全弛豫参数
sed -i "s/^ISIF.*/ISIF = 3/" INCAR
sed -i "s/^IBRION.*/IBRION = 2/" INCAR
sed -i "s/^NSW.*/NSW = 100/" INCAR
sed -i "s/^EDIFFG.*/EDIFFG = -0.01/" INCAR

# 运行VASP
$VASP > vasp.log

cd ..