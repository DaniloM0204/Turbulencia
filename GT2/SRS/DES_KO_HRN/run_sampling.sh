 #!/bin/bas

#foamPostProcess -solver incompressibleFluid -func wallShearStress -noZero -noFunctionObjects


#mkdir 10/tmp
#mv "10/tmp<kOmegaSSTDES:G>" 10/tmp/
#mv "10/tmp<(CDES*delta)>" 10/tmp/


foamPostProcess -func  sampleDict -noZero

foamPostProcess -func  probesDict -noZero





#Old manipulation - Not needed anymore

#mv "10/tmp/kOmegaSSTDES:G" "10/expr(kOmegaSSTDES:G)"
#mv "10/tmp/(CDES*delta)"  "10/expr(CDES*delta)"
#rm -rf 10/tmp/

#sed -i '14 s/[()]/ /g' 10/expr\(CDES\*delta\)
#sed -i 's/CDES\*delta/expr(CDES*delta)/g' 10/expr\(CDES\*delta\)

#sed -i '14 s/[()]/ /g' 10/expr\(kOmegaSSTDES\:G\)
#sed -i 's/kOmegaSSTDES\:G/expr(kOmegaSSTDES:G)/g' 10/expr\(kOmegaSSTDES\:G\)


