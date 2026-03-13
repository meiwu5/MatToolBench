#!/bin/bash
#=============================================================================
# Filename: dos.sh
# Author: Yi,Wencai - yi.wencai@163.com
# Last modified: 2015-01-31 11:40
# Copy Right(C):Please contact me before you copy it to others!
# Description: I write this tools to produce LDOS dat
#============================================================================

if [ $# -le 1 ]; then
echo "Please use this process correctly by follow LDOS name!"
echo "Good Luck!"
exit 1;
fi

if [ ! -s DOS$2.dat ] ; then
echo "Please check there exist file:DOS$2.dat"
exit 1;
fi
canshu=$@
canshu=`echo $canshu|cut -d " " -f2-`
filenu=$#
let filenu=$filenu-1
#$filenu--

line=`cat DOS$2.dat|wc -l`
rank=`awk '{print NF}' DOS$2.dat|sed -n 2p`

echo $rank > .tmp
echo $line >> .tmp
echo $filenu >> .tmp
for file in $canshu
do
echo DOS$file.dat >> .tmp
done

ulimit -s unlimited   # be useful for multi-atoms
ulimit -m unlimited
#ulimit -c unlimited
ulimit -d unlimited
$qvasppath/exefile/Tools/ldos.x

echo ""
if [ -s LDOS.dat ];then
 echo "Finished the jobs,the results stored in LDOS.dat"
else
 echo "There is some error during execution"
fi
echo ""
######### clean #######
rm .tmp

