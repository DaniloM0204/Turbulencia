set terminal pngcairo size 1050,650 enhanced font 'Arial,12'
set output '02_Lei_da_Parede_Validacao.png'
set title 'Lei da Parede: u^+ vs y^+' font ',14'
set logscale x
set grid xtics ytics lw 1, lw 0.5
set xlabel 'Distância adimensional y^+ [-]' font ',13'
set ylabel 'Velocidade adimensional u^+ [-]' font ',13'
set key outside right center box linewidth 1
set yr [-20:50]

nu = 1.5e-05
subcamada(x) = x
loglaw(x) = (1.0/0.41)*log(x)+5.2
set xr [0.1:1000]
plot subcamada(x) lw 1.5 lc rgb 'black' dt 2 title 'u^+=y^+', loglaw(x) lw 1.5 lc rgb 'black' title 'Log-Law', '/home/danilom/OpenFOAM/danilom-12/run/GT3/RANS-kklo/postProcessing/sampleDict/3000/line0795.xy' u ($1*0.25/1.5e-05):($2/0.25) w l lw 3 title 'RANS-kklo', '/home/danilom/OpenFOAM/danilom-12/run/GT3/RANS-kOmegaSSTLM/postProcessing/sampleDict/3000/line0795.xy' u ($1*0.25/1.5e-05):($2/0.25) w l lw 3 title 'RANS-kOmegaSSTLM', '/home/danilom/OpenFOAM/danilom-12/run/GT3/setup_TM/RANS-koSSTv2/postProcessing/sampleDict/3000/line0795.xy' u ($1*0.25/1.5e-05):($2/0.25) w l lw 3 title 'setup_TM/RANS-koSSTv2', '/home/danilom/OpenFOAM/danilom-12/run/GT3/setup_TM/RANS-launderSharmaKE/postProcessing/sampleDict/3000/line0795.xy' u ($1*0.25/1.5e-05):($2/0.25) w l lw 3 title 'setup_TM/RANS-launderSharmaKE'
