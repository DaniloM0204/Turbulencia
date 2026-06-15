 #!/bin/bash

nprocs=4
foamDictionary system/decomposeParDict -entry numberOfSubdomains -set $nprocs

decomposePar 
mpirun -np $nprocs foamRun -parallel | tee log.solver
reconstructPar 

#postProcess -func 'grad(U)' -latestTime -noZero
#postProcess -func sampleDict -latestTime -noZero
#postProcess -func surfacesDict -latestTime -noZero

foamPostProcess -solver incompressibleFluid -func wallShearStress -noZero -noFunctionObjects

#postProcess -func 'grad(U)' -noZero
#postProcess -func sampleDict -noZero
#postProcess -func surfacesDict -noZero

foamPostProcess -func 'grad(U)' -noZero
foamPostProcess -func sampleDict -latestTime
foamPostProcess -func surfacesDict -latestTime
