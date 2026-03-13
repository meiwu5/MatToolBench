#!/bin/env python
import MDAnalysis
import MDAnalysis.analysis.rdf
import matplotlib.pyplot as plt
import numpy


element1=input("Please input the first element:")
element2=input("Please input the second element:")

element1="type " + element1
element2="type " + element2
u = MDAnalysis.Universe('XDATCAR.pdb', permissive=True)
g1= u.select_atoms(element1)
g2= u.select_atoms(element2)
rdf = MDAnalysis.analysis.rdf.InterRDF(g1,g2,nbins=75, range=(0.0, min(u.dimensions[:3])/2.0))
           
rdf.run()

#for i in rdf.bins:
for i in range(1,74):
    print(rdf.bins[i],rdf.rdf[i])
#print 'ge'
#for i in rdf.rdf:
#    print i
fig = plt.figure(figsize=(5,4))
ax = fig.add_subplot(111)
ax.plot(rdf.bins, rdf.rdf, 'k-',  label="rdf")

ax.legend(loc="best")
ax.set_xlabel(r"Distance ($\AA$)")
ax.set_ylabel(r"RDF")
fig.savefig("RDF_all.png")
#plt.show()
