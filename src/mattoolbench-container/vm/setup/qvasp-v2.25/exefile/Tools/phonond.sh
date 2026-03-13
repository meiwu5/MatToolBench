#!/bin/bash

phonopy --fc vasprun.xml

phonopy -p --factor=521.471  -c   POSCAR-unitcell   band.conf 

phonopy-bandplot --gnuplot >PhononBAND.dat
