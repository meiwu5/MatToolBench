#!/bin/bash


if [ "$user"x != "root"x ];then
  echo -n "Do you wish to remove qvasp to your machine ? (yes or no):"
  read guess
  while true;
  do
   if [ "$guess"x == "yes"x ];then
    echo "Please use command: chmod -R 777 $qvasppath ; rm -rf $qvasppath; to remove qvasp folder manually!"
    echo "Please remove the follow words in $HOME/.bashrc or /etc/profile:
    ######### qvasp #############
    export qvasppath=$qvasppath
    export PATH=$qvasppath:\$PATH
    export PATH=$qvasppath/exefile/Tools/USERTooLs/vtstscripts:\$PATH
    ########### end #############"
    break
   elif  [ "$guess"x == "quit"x ];then
    break
   else
     echo -n "Plese reinput valid word of (yes|no|quit):" 
     read guess
  fi
  done
fi

echo " "

