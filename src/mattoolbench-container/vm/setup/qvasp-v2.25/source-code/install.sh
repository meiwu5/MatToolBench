#!/bin/bash

echo " "

path=`cd $(dirname $0); pwd -P`
#echo $path
#path=`pwd`
#path=$HOME/bin

user=`echo $USER`

if [ "$user"x != "root"x ];then
  echo -n "do you wish the installer to prepend the qvasp location to PATH in $HOME/.bashrc ? (yes or no):"
  read guess
  while true;
  do
   if [ "$guess"x == "yes"x ];then
    echo "######### qvasp #############
     export qvasppath=$path
     export PATH=$path:\$PATH
     export PATH=$path/exefile/vtstscripts:\$PATH" >> $HOME/.bashrc
    source $HOME/.bashrc
    echo -e "you have install it successfully\n"
    break
   elif  [ "$guess"x == "no"x ];then
    echo "Please add the follow words in $HOME/.bashrc:
    ######### qvasp #############
    export qvasppath=$path
    export PATH=$path:\$PATH
    export PATH=$path/exefile/vtstscripts:\$PATH
    ########### end #############
and then source $HOME/.bashrc"
    break
   elif  [ "$guess"x == "quit"x ];then
    echo "Please add the follow words in $HOME/.bashrc:
    ######### qvasp #############
    export qvasppath=$path
    export PATH=$path:\$PATH
    export PATH=$path/exefile/vtstscripts:\$PATH
    ########### end #############
and then source $HOME/.bashrc"
    break
   else
     echo -n "Plese reinput valid word of (yes|no|quit):" 
     read guess
  fi
  done
else
  echo -n "do you wish the installer to prepend the qvasp location to PATH in /etc/profile ? (yes or no):"
  read guess
  while true;
  do
   if [ "$guess"x == "yes"x ];then
    echo "######### qvasp #############
 export qvasppath=$path
 export PATH=$path:\$PATH
 export PATH=$path/exefile/vtstscripts:\$PATH" >> /etc/profile
    source /etc/profile
    break
   elif  [ "$guess"x == "no"x ];then
    echo "Please add the follow words in /etc/profile:
    ######### qvasp #############
    export qvasppath=$path
    export PATH=$path:\$PATH
    export PATH=$path/exefile/vtstscripts:\$PATH
    ########### end #############
and then source $HOME/.bashrc"
    break
   elif  [ "$guess"x == "quit"x ];then
    echo "Please add the follow words in /etc/profile:
    ######### qvasp #############
    export qvasppath=$path
    export PATH=$path:\$PATH
    export PATH=$path/exefile/vtstscripts:\$PATH
    ########### end #############
and then source $HOME/.bashrc"
    break
   else
     echo -n "Plese reinput valid word of (yes|no|quit):" 
     read guess
  fi
  done
fi

echo " "
