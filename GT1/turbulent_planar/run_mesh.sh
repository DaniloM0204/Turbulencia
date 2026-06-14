#!/bin/bash


foamCleanTutorials

blockMesh

#To clean empty patches.  Patch bottom is left empty after extrudeMesh
createPatch -overwrite | tee log.createPatch

#sed -i 's/empty/wedge/g' constant/polyMesh/boundary

checkMesh | tee log.checkMesh
