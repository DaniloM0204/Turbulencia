 #!/bin/bash

foamRun | tee log.simpleFoam
 
foamPostProcess -func 'grad(U)' -latestTime

foamPostProcess -func sampleDict -latestTime -noZero

foamPostProcess -func surfacesDict -latestTime -noZero

