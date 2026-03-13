#!/bin/bash
#Author:Wencai Yi
#Goal: Transfer cif file to POSCAR

echo " "
if [ $# = 0 ]; then
 file=`ls *.cif 2> /dev/null`
else
 file=$@
 file=`echo $file|cut -d " " -f2-`
fi

for i in $file
do
 # check $i
 if [ -s $i ];then 
 $qvasppath/exefile/POSCAR/cif2pos $i
 # rename by cp
 filea=`echo $i|cut -c1-$((${#i}-4))`
 echo "Transfer done of " $i "!"
 cp POSCAR $filea.vasp  
 else
  echo "Please check the file of " $i " !"
 fi
done
echo " "
