#!/bin/bash

#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2022.07.04
#Write it to read the energy from OUTCAR

#function lower_than() {
#    python -c "import sys; sys.exit(0) if $1 < $2 else sys.exit(1)"
#}
readeneirgy()
{
# check existence of input file
   if [ -n "$(grep  -a "enthalpy is  TOTEN" $inp)" ];then
    enthalpy=`grep -a "enthalpy is  TOTEN" $inp|tail -1|awk '{print $5}'`
    pv=`grep -a "enthalpy is  TOTEN" $inp|tail -1|awk '{print $NF}'`
    press=`grep PSTRESS $inp |tail -n 1|awk '{print $2}'`
    press=`echo $press / 10 | bc`
   else
     energy=`grep -a "energy(sigma->0)" $inp|tail -1|awk '{print $NF}'`
   fi
}

readcoverage()
{
  coveraged="NO"
  ibv=`grep -a "IBRION" $inp |tail -n 1 |awk '{print $3}'`   # force:EDIFFG
  if [ "$ibv"x == "1"x -o "$ibv"x == "2"x -o "$ibv"x == "3"x ];then   ## relax or others
   if [ -n "$(grep  -a "reached required accuracy" $inp)" ];then
       coveraged="YES"
   fi
  else ## scf: EDIFF
   if [ -n "$(grep  -a "because EDIFF is reached" $inp)" ];then
       Iteration=`grep -nr "Iteration" $inp |  gawk '{print $1}' FS=":"|tail -n 1`
       EDIFFre=`grep -nr "because EDIFF is reached" $inp |  gawk '{print $1}' FS=":"|tail -n 1`
       if [ $Iteration -lt $EDIFFre ];then    ## for last electron step
         coveraged="YES"
       fi
   fi
  fi
}
echo " "
if [ -f OUTCAR ]; then  # current folder 
 # get input file name
 inp="OUTCAR"

# check existence of input file
   readeneirgy;
   if [ "$energy""x""$enthalpy" == "x" ];then
      echo "Get Nothing from OUTCAR, Please check OUTCAR file! Good Luck!"
    echo; 
    exit;
   fi
   readcoverage;
        if [ $enthalpy ];then
         echo -e  "Pressure: \033[0m \033[1m\033[33m$press\033[0m GPa,Enthalpy:  \033[0m \033[1m\033[33m$enthalpy\033[0m eV, PV:  \033[0m \033[1m\033[33m$pv\033[0m "; 
        else
         echo -e  "Energy in this folder is:  \033[0m \033[1m\033[33m$energy\033[0m eV";
        fi
        echo -e "Get COVERAGED: \033[0m \033[1m\033[33m$coveraged\033[0m !" 
else


### for folder ##########
path="."
pstress="no"
#to read the actually number of file,which include OUTCAR
foldernum=`ls -l "$path" |grep -a "^d"|wc -l`   #all folder number
if [ $foldernum -gt 0 ];then
 foldernuma=0                            #available folder number
 availfolder=""
 for i in $(seq 1 $foldernum)
  do
    foldname=`ls -l $path |grep -a "^d"|awk '{print $NF}'|sed -n "${i}p"` #read the current  name of folder
    if [ -e $path/$foldname/OUTCAR ];then
       foldernuma=`expr $foldernuma + 1`
       availfolder="$availfolder $foldname"
       inp=$path/$foldname/OUTCAR
       if [ -n "$(grep  -a "enthalpy is  TOTEN" $inp)" ];then
           pstress="yes" 
       fi
    fi
  done
#echo $availfolder $pstress
  # there is single folder
   if [ $foldernuma -eq 1 ]; then # no sort
    foldname=`echo $availfolder` #read the current  name of folder
    inp=$path/$foldname/OUTCAR
    readeneirgy;
   if [ "$energy""x""$enthalpy" == "x" ];then
      echo "Get Nothing from $inp, Please check OUTCAR file! Good Luck!"
    echo; 
    exit;
   fi
   readcoverage;

     if [ $enthalpy ];then
         echo -e  "Folder: \033[0m \033[1m\033[33m$foldname\033[0m , Pressure: \033[0m \033[1m\033[33m$press\033[0m GPa,Enthalpy:  \033[0m \033[1m\033[33m$enthalpy\033[0m eV, PV:  \033[0m \033[1m\033[33m$pv\033[0m "; 
     else
         echo -e  "Energy in $foldname is:  \033[0m \033[1m\033[33m$energy\033[0m eV";
     fi
   # there is so many folder to read
   elif [ $foldernuma -gt 1 ];then
    if [ $pstress"x" == "yesx" ];then
        echo "------------------------------------------------------------------------------------------------------"
        for i in $availfolder
           do
             enthalpy=""
             inp=$path/$i/OUTCAR
             readeneirgy;

             readcoverage;
             if [ $enthalpy ];then
               printf "Folder:  %-11s, Pressure: %-4s GPa, Enthalpy:  %-12s eV, PV: %-12s, coveraged: %-4s   \n" "$i" "$press" "$enthalpy" "$pv" "$coveraged"
             else
              printf "Folder:  %-11s, Energy: %-12s eV,  coveraged:  %-4s   \n" "$i" "$energy" "$coveraged"
             fi
             echo "------------------------------------------------------------------------------------------------------"
           done
    else
        echo "|--------------------------------------------------------------"
        echo "|        foldername         |      energy       | convergence |"
        echo "|--------------------------------------------------------------"  
        for i in $availfolder
           do
                #foldname=`echo $i` #read the current  name 0f folder
                #if [ -e $path/$foldname/OUTCAR ];then
                   inp=$path/$i/OUTCAR
                   energy=`cat $inp|grep -a "energy(sigma->0)"|tail -1|awk '{print $NF}'`

                   readcoverage;
                   printf "|    %-18s     |    %-12s   |     %-4s    |\n" "$i" "$energy" "$coveraged"
                   echo "|--------------------------------------------------------------|"
                 #fi

                   a=$energy
                   if [ -z $b ];then  # init value of b, for energy compare
                     b=$a
                     y=$a
                     x=$i
                     z=$i

                   elif [ $(echo "$a>$b"|bc) -eq 1 ];then
                     b=$a
                     x=$i
               #choose the min energy
                   elif [ $(echo "$a<$y"|bc) -eq 1 ];then
                     y=$a
                     z=$i
                   fi
                #fi
     done
        echo
        echo "the max energy point is: " 
        echo -e "folder:  $x      energy:   $b\n"
        echo "the min energy point is: " 
        echo -e "folder:  $z      energy:   $y\n"
    fi

   else
   echo " ";
   echo -e "\033[1m\033[33mthere is no OUTCAR in every folder,please check it\033[0m\n"
   fi
 else
  echo " ";
  echo -e "\033[1m\033[33mthere is no OUTCAR or any folder,please check it\033[0m\n"
 fi
fi
echo " "
