#!/bin/bash
echo ""
echo "This script clear all file but POSCAR INCAR KPOINTS POTCAR and executable file"

list="POSCAR POTCAR INCAR KPOINTS vdw_kernel.bindat ""$@"

for i in `ls -1`
do
    for j in $list
    do
        if [[ $i =~ ${j}$ ]];then
            continue 2
        elif [ -x $i ];then
            continue 2
        fi
    done
    rm $i
done
echo "           ---------- Clean Done ----------"
echo ""
