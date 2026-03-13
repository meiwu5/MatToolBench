#!/bin/bash

echo 'ATOM_NAME = System
DIM =                       ## modify it
BAND=                     
FORCE_CONSTANTS = READ
## need modify as you want
' > band.conf

echo 'ATOM_NAME = System
DIM =                 ## modify it
MP = 11 11 11
FORCE_CONSTANTS = READ
##PDOS = 1

## need modify as you want
'> mesh.conf
