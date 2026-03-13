#!/bin/bash

############### Modified by yours ##########################
source /share/apps/environment/intel2020
EXEC=/share/apps/vasp/vasp.6.3.1/vasp_std
NP=36 ## cores number

for i in 200 250 300 350 400 450 500 550 600 650 700 750
do
cat > INCAR <<!
 SYSTEM =  AlN-single
 Electronic strcutre
   PREC   = normal
   ENCUT  = $i eV;
   NELMIN = 2 ; NELMDL = -5
   LREAL  = .False.

#  NBANDS = 460

   GGA = PE

 Ionic Relaxation
   NSW    = 0    number of steps for IOM
   IBRION = -1
   ISIF   = 2
#   PSTRESS= 0

 DOS related values:
   ISMEAR =    -5  ; SIGMA = 0.01
   EMIN   =   -15 ;  EMAX = 15

LWAVE=F
LCHARG=F
!
echo "ENCUT= $i eV";
rm -f WAVECAR CHGCAR
mpirun -np $NP $EXEC    
#E=`grep "TOTEN" OUTCAR | tail -1 | awk '{printf "%12.6f\n",$5}'`
E=`grep "without entropy" OUTCAR |tail -n 1|awk '{printf $7}'`
cputime=`grep "CPU" OUTCAR |awk '{printf $6}'`
echo $i $E $cputime >> comment
done
