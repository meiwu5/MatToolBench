#!/bin/bash

################# POTCAR #################################
if [ -s POSCAR ];then
 if [ -s POTCAR ];then
    continue;
  else
  $qvasppath/exefile/POTCAR/potcar.sh -pbe $(sed -n '6p' POSCAR | awk '{sub(/\r$/,"");print}') 2> /dev/null
 fi
 if [ -s KPOINTS ];then
    continue;
  else
    qvasp -k
 fi
fi
############## script ###########################
cp $qvasppath/exefile/vasp* .

