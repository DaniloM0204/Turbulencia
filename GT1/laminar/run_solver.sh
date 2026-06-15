 #!/bin/bash

nprocs=4
foamDictionary system/decomposeParDict -entry numberOfSubdomains -set $nprocs

#decomposePar
#mpirun -np $nprocs foamRun -parallel | tee log.solver

foamRun | tee log.solver

#simpleFoam -postProcess -func wallShearStress -noZero -noFunctionObjects -latestTime
foamPostProcess -solver incompressibleFluid -func wallShearStress -noZero -noFunctionObjects -latestTime

foamPostProcess -func sampleDict0 -latestTime -noZero

