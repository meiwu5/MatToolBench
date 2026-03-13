#!/bin/bash

folder=`ls -l |grep ^d |awk '{print $NF}'|tr '\n' ' '`
for i in $folder
do
 cd $i
  file=`ls *.Z`
  for j in $file
  do
    uncompress $j
    chmod 644 $j 
  done
  chmod o+r $i
  chmod o+x $i
 cd ..
done

