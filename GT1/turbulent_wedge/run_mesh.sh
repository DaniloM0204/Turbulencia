#!/bin/bash


foamCleanTutorials

blockMesh

#For axial symmetry - Wedge
#If you have many cells in the radial direction increase the writing precision
extrudeMesh | tee log.extrudeMesh

#To clean empty patches.  Patch bottom is left empty after extrudeMesh
createPatch -overwrite | tee log.createPatch

#sed -i 's/empty/wedge/g' constant/polyMesh/boundary

checkMesh | tee log.checkMesh
