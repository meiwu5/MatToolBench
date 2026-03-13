#!/bin/bash

#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2014.06.20
#Write it to analysis the frequence and correct it

if [ "$1" = "-z" ]; then
  if [ -f OUTCAR ]; then
   inp="OUTCAR"

     line1=`grep  -E "[0-9]+ f" $inp |grep -v "DFIELD  =" |grep -v "WRT_POTENTIAL=" |wc -l`
     line2=`grep  -E "f/i" $inp|wc -l`
     line=`echo $line1 - $line2 |bc`
 
      if [ $line2 == 0 ];then
      echo ;
      echo "This is a stable body"
      elif [ $line2 == 1 ];then
      echo ;
      echo "This is a transition state"
      else
      echo ;
      echo "The results are meaningless,baceuse there is too many imaginary frequencies"
      fi

      sum=0
      constant=2000

      for i in $(seq 1 $line)
        do
        energ=`grep  -E "[0-9]+ f" $inp |grep -v "DFIELD  =" |grep -v "WRT_POTENTIAL=" |awk '{print $10}'|sed -n "${i}p"`
        sum=`echo $sum + $energ |bc `
        done
        averg=`echo "scale=6;$sum/2000"|bc `
        echo ;
        echo "Zero point energy is :  $averg  eV"
        echo ;
       grep  -E "f/i" $inp
       echo ""
     else
       echo ;
        echo -e "\033[1m\033[33mThere is no OUTCAR in current folder,please check it\033[0m\n"
        echo ;
    fi
else
echo "please check qvasp and zep.sh in $qvasppath"
fi
