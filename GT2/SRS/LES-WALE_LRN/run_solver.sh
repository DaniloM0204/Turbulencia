 #!/bin/bash

nprocs=4
foamDictionary system/decomposeParDict -entry numberOfSubdomains -set $nprocs

#decomposePar
#mpirun -np $nprocs foamRun -parallel | tee log.solver

foamRun | tee log.solver
 
#foamPostProcess -solver incompressibleFluid -func wallShearStress -noZero -noFunctionObjects

foamPostProcess -func  sampleDict -noZero

foamPostProcess -func  probesDict -noZero


