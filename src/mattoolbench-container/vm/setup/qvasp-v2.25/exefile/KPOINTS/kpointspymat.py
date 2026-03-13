#!/bin/env python
from pymatgen.io.vasp.inputs import Kpoints
from pymatgen.core import Structure
from pymatgen.symmetry.bandstructure import HighSymmKpath

struct = Structure.from_file("POSCAR")
kpath = HighSymmKpath(struct)
kpts = Kpoints.automatic_linemode(divisions=25,ibz=kpath)
kpts.write_file(".kpoints-tmp")


## need to install pymatgen by "conda install --channel conda-forge pymatgen"
