#!/bin/bash
#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2014.06.20
#Write it to use the scripts by user themselves

##echo $@
     echo ""
if [ "$#" -eq "1" ];then
  key=`echo $1`
  key=`echo ${key#*\-}`
  if [ -x $qvasppath/exefile/Tools/USERTooLs/$key ];then
     $qvasppath/exefile/Tools/USERTooLs/$key
  else
     echo "No tool at " $qvasppath/exefile/Tools/USERTooLs/$key "was found!"
     echo "Or use chmod 755 " $qvasppath/exefile/Tools/USERTooLs/$key " to add executable rights!"
     echo "See qvasp help doc:"
     qvasp -help
  fi
elif [ "$#" -ge "2" ];then
  key=`echo $1`
  key=`echo ${key#*\-}`
  canshu=$@
  canshu=`echo $canshu|cut -d " " -f2-`
  if [ -x $qvasppath/exefile/Tools/USERTooLs/$key ];then
     $qvasppath/exefile/Tools/USERTooLs/$key $canshu
  else
     echo "No tool at " $qvasppath/exefile/Tools/USERTooLs/$key "was found!"
     echo "Or use chmod 755 " $qvasppath/exefile/Tools/USERTooLs/$key " to add executable rights!"
     echo "See qvasp help doc:"
     qvasp -help
  fi
else
  qvasp -help
fi

echo " "
