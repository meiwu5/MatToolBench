#!/bin/bash
VASP="mpirun -np 4 /mnt/d/ChemLLM/tools_download/qvasp-v2.25/exefile/vasp_test/vasp_std"
for e in $(seq 400 50 800); do
    mkdir -p ENCUT_$e; cd ENCUT_$e
    cp ../POSCAR_Cu_ENCUT ./POSCAR
    qvasp -pbe Cu; qvasp -k 0.03; qvasp -scf
    sed -i "s/^ENCUT.*/ENCUT = $e/" INCAR
    echo -e "IBRION = -1\nNSW = 0" >> INCAR
    $VASP > vasp.log; cd ..
done