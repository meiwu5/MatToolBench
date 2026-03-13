#!/bin/bash
#vasp bat

job=$@
job=`echo $job|cut -d " " -f2-`
for i in $job
do
 cd $i
  cp $qvasppath/exefile/vasp* vasp.script
  qsub vasp.script
 cd - > /dev/null
done
