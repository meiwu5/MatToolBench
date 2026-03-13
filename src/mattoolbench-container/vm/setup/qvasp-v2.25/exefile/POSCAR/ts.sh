#!/bin/bash

#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2014.06.20
#Write it to produce POSCAR , INCAR , KPOINTS , POTCAR for TS in VASP


####### INCAR and KPOINTS ########
if [ "$1" = "-t" ]; then
  IMAGES=$2
  echo $IMAGES >> INCAR
elif [ "$1" = "-t2" ]; then
  IMAGE=`grep -c "PBC" POSCAR2`
  IMAGES=`echo $IMAGE - 3|bc`
  echo $IMAGES >> INCAR
else
  echo "Please check the ts.sh and qvasp in $qvasppath"
fi

if [ "$1" = "-t" ]; then
 if [ -s $qvasppath/exefile/Tools/USERTooLs/vtstscripts/nebmake.pl ]; then
  if [ -f P -a -f R ];then
    echo "Insert transition states by vtstscripts (http://theory.cm.utexas.edu/vtsttools/download.html)"
    $qvasppath/exefile/Tools/USERTooLs/vtstscripts/nebmake.pl R P $2
    echo "Insert points for TS calculations successfully"
  fi
 else
 echo ''
 echo "Please download vtstscripts.tgz from http://theory.cm.utexas.edu/vtsttools/download.html"
 echo "And then use 'tar -zxvf vtstscripts.tgz to exact it' at $qvasppath/exefile/Tools/USERTooLs/"
 echo "Finally use 'mv vtstscripts* vtstscripts' to rename it, Good Luck!"
 echo ''
fi
elif [ "$1" = "-t2" ]; then
     if [ -f POSCAR2 ];then
        if [ -f POSCAR1 ];then
            all=0
            singlenum=`sed -n 7p POSCAR1 | awk '{sub(/\r$/,"");print}'`
              for  i in $singlenum
               do
                all=`echo $[$all+$i]`
               done

            echo $all > num
            grep -c "PBC" POSCAR2 >> num

            rm -rf ./tstem 2> /dev/null

            $qvasppath/exefile/POSCAR/ts2.x
            rm -f num
           else
           echo ""
           echo -e "Please there exits POSCAR1 !\n"
           fi
        echo "Insert points for TS calculations successfully"
     else
     echo " "
     echo -e "Please confire that there exits POSCAR1 and POSCAR2 in current folder\n"
     fi
else
echo "Please check the ts.sh and qvasp in $qvasppath/exefile/Tools/"
fi
