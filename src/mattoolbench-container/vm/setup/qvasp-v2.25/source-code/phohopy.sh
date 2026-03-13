#!/bin/bash

echo 'ATOM_NAME = Sc
DIM = 3 3 2
BAND=  0.000  0.000  0.000    0.000  0.000  0.500     -0.333  0.667  0.500    -0.333  0.667  0.000   0.000  0.000  0.000  0.000  0.500  0.000
FORCE_CONSTANTS = READ
## need modify as you want
' > band.conf

echo 'ATOM_NAME = Sc
DIM = 3 3 2
MP = 8 8 8
FORCE_CONSTANTS = READ
##PDOS = 1

## need modify as you want
'> mesh.conf
