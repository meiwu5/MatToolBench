#!/bin/bash

host=`hostname`
bjobs |grep $host > .tmp

  JOBNUM=`cat .tmp | wc -l`
  if [ "$JOBNUM"x == "0"x ]; then
    JOBNUM=0
      echo ""
      echo -e "There is no job runing!\n"
      exit 1;
  else
    for i in $(seq 1 $JOBNUM)
      do
        JOBID=`cat .tmp | sed -n "${i}p" | awk '{print $1}' | cut -f1 -d.`
        info=`bjobs -l $JOBID|tr -d '\n '`
        PROG=`cat .tmp | sed -n "${i}p" | awk '{print $4}'`
        STATE=`cat .tmp | sed -n "${i}p" | awk '{print $3}'`
        jobpsd=`echo ${info##*OutputFile<}`
        jobpsd=`echo ${jobpsd%\/output*}`
        if [ "$STATE"x == "RUN"x ];then
          nodes=`cat .tmp | sed -n "${i}p" | awk '{print $6}'`
        else
          nodes=' '
        fi

echo " -------------------------------------------------------------------------------------------------------"
         printf "    %-6s      %-9s      %-4s %-8s     %-55s   \n"  "$JOBID" "$PROG" "$STATE" "$nodes" "$jobpsd"
        rm -f .info
done

fi
echo " -------------------------------------------------------------------------------------------------------"

rm -f .tmp
