#!/bin/bash
source /Volumes/OpenFOAM/OpenFOAM-12/etc/bashrc

nprocs=4
foamDictionary system/decomposeParDict -entry numberOfSubdomains -set $nprocs

#decomposePar
#mpirun -np $nprocs foamRun -parallel | tee log.solver

foamRun | tee log.solver

foamPostProcess -solver incompressibleFluid -func wallShearStress -noZero -noFunctionObjects

#foamPostProcess -solver incompressibleFluid -func yPlus

foamPostProcess -func sampleDict -noZero

foamPostProcess -func probesDict -noZero
