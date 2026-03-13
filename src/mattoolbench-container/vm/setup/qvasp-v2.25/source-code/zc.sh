#!/bin/bash

#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2014.06.20
#Write it to analysis the frequence and correct it

if [ "$1" = "-zc" ];then
  if [ -f OUTCAR ]; then
     a=`grep "f/i" OUTCAR|wc -l`
     if [ $a -ge 1 ];then
     $qvasppath/exefile/POSCAR/ZPE-corection.x
     else 
     echo " "
     echo -e "This POSCAR needn't to be corrected just because this is a stable body\n"
     fi
   else 
     echo " "
     echo -e "Please confire that there exits OUTCAR in current folder\n"
  fi

else
echo "please check qvasp and zep.sh in $qvasppath"
fi
