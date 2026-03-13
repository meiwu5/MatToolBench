#!/bin/bash

#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2014.06.20
#Write it to show status of our job

squeue -u yiwc19 > .tmp

  JOBNUM=`cat .tmp | wc -l`
  if [ "$JOBNUM"x == "0"x ]; then
    JOBNUM=0
      echo ""
      echo -e "There is no job runing!\n"
      exit 1;
  else
    for i in $(seq 2 $JOBNUM)
      do
        JOBID=`cat .tmp | sed -n "${i}p" | awk '{print $1}' | cut -f1 -d.`
        PROG=`cat .tmp | sed -n "${i}p" | awk '{print $3}'`
        STATE=`cat .tmp | sed -n "${i}p" | awk '{print $5}'`
        jobpsd=`scontrol show job $JOBID|grep WorkDir`
        jobpsd=`echo ${jobpsd##*=}|sed -r 's/\,//'`
       # nodes=`qstat -f -e $JOBID|grep exec_host`
       # nodes=`echo ${nodes##*+}|sed -r 's/\///'`
        nodes=' '

echo " -------------------------------------------------------------------------------------------------------"
         printf "    %-6s      %-9s      %-4s %-4s     %-55s   \n"  "$JOBID" "$PROG" "$STATE" "$nodes" "$jobpsd"
done

fi
echo " -------------------------------------------------------------------------------------------------------"

rm .tmp
