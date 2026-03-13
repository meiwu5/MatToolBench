#!/bin/bash

echo " "
guess=`grep 'TOTAL ELASTIC MODULI' OUTCAR`
if [ "$guess" ];then
   grep -A 10 'TOTAL ELASTIC MODULI' OUTCAR
else
  echo "Please check your INCAR, which include IBRION=6;NFREE=4;NSW=1"
fi
echo " "
