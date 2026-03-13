#!/bin/bash
#Author: Wencai Yi
#Email: yi.wencai@163.com
#Date:2018.06.20
#Goal: deal the magnetic moment data of MD simulation, from OSZICAR

  echo " "
  echo "Data dealing,keep waiting ..."

if [ ! -s  OSZICAR ];then
  echo -e "Data dealing failed, please check the OSZICAR!\n"
  exit;
fi
if [ ! -s  OUTCAR ];then
  echo -e "Data dealing failed, please check the OUTCAR!\n"
  exit;
fi


ispin=`grep "ISPIN" OUTCAR|awk '{print $3}'|head -n 1` 
if [ $ispin"x" != "2x" ];then
  echo -e "Data dealing failed, please set ISPIN = 2 in INCAR and then run vasp\n"
  exit;
fi

  echo "Time(ps)"   "Magnetic-moment(uB)"  "Temperature(K)" > mdm.dat
grep "T=" OSZICAR > .tmp
tstep=`cat .tmp |wc -l`
timefs=`grep "POTIM" OUTCAR|tail -n 1|awk '{print $3}'` 
for i in $(seq 1 $tstep)
do
  keywords=`cat .tmp |sed -n "${i}p"`
  timestep=`echo $keywords | awk '{print $1}'`
  if [ -z $timestep ];then
    break;
  fi
  timeps=`echo "scale=8;$timestep * $timefs / 1000" |bc`
  energy0=`echo $keywords | awk '{print $17}'`
  temp=`echo $keywords | awk '{print $3}'`
  echo $timeps  $energy0 $temp >> mdm.dat
done
rm -f .tmp > /dev/null 2> /dev/null

######## check ##########
checknu=`cat mdm.dat |wc -l`
checknu=`echo $checknu - 1 |bc`
if [ $tstep"x" = $checknu"x" ];then
  echo -e "Got it,the results were in mdm.dat\n"
else
  echo -e "Data dealing failed, please check the OSZICAR!\n"
fi


