#!/bin/bash

#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2014.06.20
#Write it to show status of our job

 QSTAT=`squeue -u $USER |grep -v JOBID`

  if [ -z "$QSTAT" ]; then
    JOBNUM=0
      echo ""
      echo -e "There is no job runing!\n"
      exit 1;
  else
    JOBNUM=`echo "$QSTAT" | wc -l`
    #str=`qstat -u $USER |grep -n "\-\-\-\-\-\-"`
    #str=`echo ${str%:*}`
    #QSTAT=`qstat -u $USER| sed "1,${str}d"`
    JOBNUM=`echo "$QSTAT" | wc -l`

    for i in $(seq 1 $JOBNUM)
      do
        JOBID=`echo "$QSTAT" | sed -n "${i}p" | awk '{print $1}'`
        PROG=`echo "$QSTAT" | sed -n "${i}p" | awk '{print $3}'`
        STATE=`echo "$QSTAT" | sed -n "${i}p" | awk '{print $5}'`
        jobpsd=`scontrol show job -d $JOBID|grep WorkDir`
        jobpsd=`echo ${jobpsd#*WorkDir=}`
       # jobpsd=`echo ${jobpsd%%,*}`
        if [ "$jobpsd"x == "Q" ];then
         nodes=" "
        else
         nodes=`echo "$QSTAT" | sed -n "${i}p" | awk '{print $8}'`
        fi
echo " -------------------------------------------------------------------------------------------------------"
         printf "    %-6s      %-9s      %-4s %-4s     %-55s   \n"  "$JOBID" "$PROG" "$STATE" "$nodes" "$jobpsd"
done

fi
echo " -------------------------------------------------------------------------------------------------------"

