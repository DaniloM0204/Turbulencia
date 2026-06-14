 #!/bin/bash

foamRun | tee log.solver
 
foamPostProcess -func 'grad(U)' -latestTime

foamPostProcess -func sample1 -latestTime -noZero

foamPostProcess -func sample2 -latestTime -noZero

