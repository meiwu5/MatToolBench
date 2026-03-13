#!/bin/bash
#vasp bat

job=$@
job=`echo $job|cut -d " " -f2-`
qdel $job
echo ''
echo "$job have beed deleted."
echo ''
