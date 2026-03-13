#!/bin/bash
# extract image and real parts of dielectric function from vasprun.xml

awk 'BEGIN{i=1} /imag/,\
                /\/imag/ \
                 {a[i]=$2 ; b[i]=$3 ; c[i]=$4; d[i]=$5 ; e[i]=$6 ; f[i]=$7; g[i]=$8; i=i+1} \
     END{for (j=12;j<i-3;j++) print a[j],b[j],c[j],d[j],e[j],f[j],g[j]}' vasprun.xml > IMAG.dat

awk 'BEGIN{i=1} /real/,\
                /\/real/ \
                 {a[i]=$2 ; b[i]=$3 ; c[i]=$4; d[i]=$5 ; e[i]=$6 ; f[i]=$7; g[i]=$8; i=i+1} \
     END{for (j=12;j<i-3;j++) print a[j],b[j],c[j],d[j],e[j],f[j],g[j]}' vasprun.xml > REAL.dat

$qvasppath/exefile/Tools/optics.x

echo ''
echo 'Please check IMAG.dat,REAL.dat,x,y,z, the unit of absorption coefficient is x10^5 cm^-1'
echo 'Ref and cite DOI: 10.1039/c7tc02287e'
echo ''
