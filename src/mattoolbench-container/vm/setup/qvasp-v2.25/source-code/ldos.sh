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

if [ ! -s $2 ] ; then
echo "Please check there exist file:$2"
exit 1;
fi
canshu=$@
canshu=`echo $canshu|cut -d " " -f2-`
filenu=$#
let filenu=$filenu-1
#$filenu--

line=`cat $2|wc -l`
rank=`awk '{print NF}' $2|sed -n 2p`

echo $rank > .tmp
echo $line >> .tmp
echo $filenu >> .tmp 
for file in $canshu
do
echo $file >> .tmp
done

$qvasppath/exefile/Tools/ldos.x

######### clean #######
rm .tmp

