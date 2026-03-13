#!/bin/bash

#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2014.06.20
#Write it to produce POTCAR for VASP

if [ "$1" = "-pw91" ];then
 potcardir=$qvasppath/exefile/POTCAR/paw_pw91
  if [ -a $potcardir ];then
     if [ "$#" -ge "2" ];then
        if [ -a $potcardir/$2 ]; then
           cat $potcardir/$2/POTCAR > POTCAR
            if [ "$#" -eq "2" ];then
                 echo " "
                 echo -e " The POTCAR is produced successfully\n"
                echo -e " Lte's check it"
                grep "TITEL  = PAW_GGA" POTCAR
                echo ""
                exit 1;
            fi
         else 
         echo ""
         echo -e "please check there exits $potcardir/$2\n"
               exit 1;
        fi
          if [ "$#" -ge "3" ];then
           canshu=$@
           canshu=`echo $canshu|cut -d " " -f2-|cut -d " " -f2-`
           for i in $canshu
             do
               if [ -a $potcardir/$i ];then
                 cat $potcardir/$i/POTCAR >> POTCAR
               else
                  echo "please check there exits $potcardir/$i"
                  exit 1;
               fi
            done        
                echo " "
                 echo -e " The POTCAR is produced successfully\n"
                echo -e " Let's check it"
                grep "TITEL  = PAW_GGA" POTCAR
                echo ""
          fi
        else
          helpdoc
      fi
   else
     echo " ";
     echo -e "Please check there exits paw_gga folder in $HOME/bin\n"
  fi
elif [ "$1" = "-pbe" ];then
 potcardir=$qvasppath/exefile/POTCAR/paw_pbe
  if [ -a $potcardir ];then
     if [ "$#" -ge "2" ];then
        if [ -a $potcardir/$2 ]; then
           cat $potcardir/$2/POTCAR > POTCAR
            if [ "$#" -eq "2" ];then
                 echo " "
                 echo -e " The POTCAR is produced successfully\n"
                echo -e " Lte's check it"
                grep "TITEL  = PAW_PBE" POTCAR
                echo ""
                exit 1;
            fi
         else 
         echo ""
         echo -e "please check there exits $potcardir/$2\n"
               exit 1;
        fi
          if [ "$#" -ge "3" ];then
           canshu=$@
           canshu=`echo $canshu|cut -d " " -f2-|cut -d " " -f2-`
           for i in $canshu
             do
               if [ -a $potcardir/$i ];then
                 cat $potcardir/$i/POTCAR >> POTCAR
               else
                  echo "please check there exits $potcardir/$i"
                  exit 1;
               fi
            done        
                echo " "
                 echo -e " The POTCAR is produced successfully\n"
                echo -e " Let's check it"
                grep "TITEL  = PAW_PBE" POTCAR
                echo ""
          fi
        else
          helpdoc
      fi
   else
     echo " ";
     echo -e "Please check there exits paw_gga folder in $HOME/bin\n"
   fi
elif [ "$1" = "-lda" ];then
 potcardir=$qvasppath/exefile/POTCAR/paw_lda
  if [ -a $potcardir ];then
     if [ "$#" -ge "2" ];then
        if [ -a $potcardir/$2 ]; then
           cat $potcardir/$2/POTCAR > POTCAR
            if [ "$#" -eq "2" ];then
                 echo " "
                 echo -e " The POTCAR is produced successfully\n"
                echo -e " Lte's check it"
                grep "TITEL  = PAW" POTCAR
                echo ""
                exit 1;
            fi
         else
         echo ""
         echo -e "please check there exits $potcardir/$2\n"
               exit 1;
        fi
          if [ "$#" -ge "3" ];then
           canshu=$@
           canshu=`echo $canshu|cut -d " " -f2-|cut -d " " -f2-`
           for i in $canshu
             do
               if [ -a $potcardir/$i ];then
                 cat $potcardir/$i/POTCAR >> POTCAR
               else
                  echo "please check there exits $potcardir/$i"
                  exit 1;
               fi
            done
                echo " "
                 echo -e " The POTCAR is produced successfully\n"
                echo -e " Let's check it"
                grep "TITEL  = PAW" POTCAR
                echo ""
          fi
        else
          helpdoc
      fi
   else
     echo " ";
     echo -e "Please check there exits paw_gga folder in $HOME/bin\n"
   fi
elif [ "$1" = "-cp" ];then
   if [ -s POTCAR ];then
     echo ""
      grep "TITEL  = PAW" POTCAR
      echo ""
    else
      echo ""
      echo "Please confire there exits POTCAR or it is a empty file in current folder"
      echo ""
   fi
else
echo "please check qvasp or potcar.sh"
fi
