#!/bin/bash

#Modified for SLURM by Zhao,Hongsheng
#Original Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified to work with SLURM instead of PBS/Torque

# Check if user has any jobs
JOBS=`squeue -u $USER --noheader 2>/dev/null`

if [ -z "$JOBS" ]; then
    echo ""
    echo -e "There is no job running!\n"
    exit 1
else
    JOBNUM=`echo "$JOBS" | wc -l`
    
    echo " -------------------------------------------------------------------------------------------------------"
    printf "    %-10s %-15s %-10s %-10s %-8s %-12s %-20s %-30s\n" "JOBID" "PARTITION" "NAME" "USER" "STATE" "TIME" "NODES" "WORKDIR"
    echo " -------------------------------------------------------------------------------------------------------"
    
    echo "$JOBS" | while read line; do
        JOBID=`echo "$line" | awk '{print $1}'`
        PARTITION=`echo "$line" | awk '{print $2}'`
        NAME=`echo "$line" | awk '{print $3}'`
        USER=`echo "$line" | awk '{print $4}'`
        STATE=`echo "$line" | awk '{print $5}'`
        TIME=`echo "$line" | awk '{print $6}'`
        NODES=`echo "$line" | awk '{print $7}'`
        NODELIST=`echo "$line" | awk '{print $8}'`
        
        # Get working directory from scontrol
        WORKDIR=`scontrol show job $JOBID 2>/dev/null | grep -o 'WorkDir=[^[:space:]]*' | cut -d= -f2`
        if [ -z "$WORKDIR" ]; then
            WORKDIR="N/A"
        fi
        
        printf "    %-10s %-15s %-10s %-10s %-8s %-12s %-20s %-30s\n" "$JOBID" "$PARTITION" "$NAME" "$USER" "$STATE" "$TIME" "$NODELIST" "$WORKDIR"
    done
    
    echo " -------------------------------------------------------------------------------------------------------"
    echo "Total jobs: $JOBNUM"
fi
