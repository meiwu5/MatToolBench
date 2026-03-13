#!/bin/bash
VASP="mpirun -np 4 /mnt/d/ChemLLM/tools_download/qvasp-v2.25/exefile/vasp_test/vasp_std"
# Step 1: SCF
mkdir -p Ge_band; cd Ge_band
cp ../POSCAR_Ge_band ./POSCAR; qvasp -pbe Ge; qvasp -k 0.02; qvasp -scf
$VASP > vasp_scf.log
# Step 2: Band
cp OUTCAR CHGCAR  # 确保电荷密度读入
cat > KPOINTS << EOF
K-Path (G-X-M-G)
10
Line-mode
Reciprocal
0.0 0.0 0.0 !G
0.5 0.0 0.5 !X

0.5 0.0 0.5 !X
0.5 0.5 0.5 !M

0.5 0.5 0.5 !M
0.0 0.0 0.0 !G
EOF
sed -i "s/ICHARG.*/ICHARG = 11/" INCAR
$VASP > vasp_band.log; cd ..