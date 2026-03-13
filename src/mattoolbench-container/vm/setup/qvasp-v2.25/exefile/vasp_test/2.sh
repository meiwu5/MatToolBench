#!/bin/bash
VASP="mpirun -np 4 /mnt/d/ChemLLM/tools_download/qvasp-v2.25/exefile/vasp_test/vasp_std"
for k in $(seq 4 2 12); do
    mkdir -p K$k; cd K$k
    cp ../POSCAR_MgO_kmesh ./POSCAR
    qvasp -pbe Mg O; qvasp -scf
    echo -e "K-Points\n0\nMonkhorst\n$k $k $k\n0 0 0" > KPOINTS
    $VASP > vasp.log; cd ..
done