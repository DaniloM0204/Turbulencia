#!/bin/bash


foamCleanTutorials

plot3dToFoam -noBlank -2D 1 ../nasa_grid/grid1

autoPatch 30 -overwrite

topoSet

createPatch -overwrite

cp system/boundary constant/polyMesh/

checkMesh | tee log.checkMesh
