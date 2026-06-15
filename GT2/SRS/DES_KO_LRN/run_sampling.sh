 #!/bin/bash

#foamPostProcess -solver incompressibleFluid -func wallShearStress -noZero -noFunctionObjects

foamPostProcess -func  sampleDict -noZero

foamPostProcess -func  probesDict -noZero


