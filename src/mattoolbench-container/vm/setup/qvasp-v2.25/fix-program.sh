#!/bin/bash

#kpoints.x cif2pos supercell findsym findcell cleavesurface

FC=ifort  # gfortran
cd source-code
######## main program #####
echo "Recomile qvasp ..."
$FC qvasp.f90 -o qvasp
cp -f qvasp ../qvasp
######## POSCAR ##########
echo "Recomile fix-pos.x ..."
$FC fix-pos.f90 -o fix-pos.x
cp -f fix-pos.x ../exefile/POSCAR/fix-pos.x
######## Tools ############
echo "Recomile band.x ..."
$FC bandv2.f90 -o band.x
cp -f band.x ../exefile/Tools/band.x

echo "Recomile getcif.x ..."
$FC getcif.f90 -o getcif.x
cp -f getcif.x ../exefile/Tools/getcif.x

echo "Recomile ldos.x ..."
$FC ldos.f90 -o ldos.x
cp -f ldos.x ../exefile/Tools/ldos.x

echo "Recomile optics.x ..."
$FC optics.f90 -o optics.x
cp -f optics.x ../exefile/Tools/optics.x

echo "Recomile ts.x ..."
$FC ts.f90 -o ts.x
cp -f ts.x ../exefile/Tools/ts.x

echo "Recomile ZPE-corection.x ..."
$FC ZPE-corection.f90 -o ZPE-corection.x
cp -f ZPE-corection.x ../exefile/Tools/ZPE-corection.x

echo "Recomile nanotube ..."
$FC nanotube.f90 -o nanotube
cp -f nanotube ../exefile/Tools/USERTooLs/nanotube

echo "Recomile out2arc ..."
$FC tran-arc.f90 -o out2arc
cp -f out2arc ../exefile/Tools/USERTooLs/out2arc

echo "Recomile 3d-band ..."
$FC 3d-band.f90 -o 3d-band
cp -f 3d-band ../exefile/Tools/3d-band

echo "Recomile 3dkpoints ..."
$FC 3dkpoints.f90 -o 3dkpoints.f90
cp -f 3dkpoints.f90 ../exefile/Tools/USERTooLs/3dkpoints.f90
echo "Fix done."
