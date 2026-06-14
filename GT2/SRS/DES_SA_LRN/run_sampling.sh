 #!/bin/bas

#foamPostProcess -solver incompressibleFluid -func wallShearStress -noZero -noFunctionObjects

foamPostProcess -func  sampleDict -noZero

foamPostProcess -func  probesDict -noZero





#Old manipulation - Not needed anymore

#cp "10/tmp/SpalartAllmarasIDDES:dTilda" "10/expr(SpalartAllmarasIDDES:dTilda)"
#rm -rf 10/tmp/

#sed -i '14 s/[()]/ /g' 10/expr\(SpalartAllmarasIDDES\:dTilda\)
#sed -i 's/SpalartAllmarasIDDES\:dTilda/expr(SpalartAllmarasIDDES:dTilda)/g' 10/expr\(SpalartAllmarasIDDES\:dTilda\)


