#!/bin/bash

  echo ''
if [ -s DOSCAR ]; then
 if [ -s $qvasppath/exefile/Tools/USERTooLs/vtstscripts/split_dos ]; then
  $qvasppath/exefile/Tools/USERTooLs/vtstscripts/split_dos > /dev/null
  filename=`ls DOS[0-9]*`
  for i in $filename
   do
     mv $i $i.dat
   done
  echo "Got it, please check DOS*.dat"
 else
  $qvasppath/exefile/Tools/vdos > /dev/null
  echo "Got it, please check *.dat"
 fi
else
  echo "Please there exit DOSCAR in current folder and DOSCAR is not empty!"
fi
 echo ''
