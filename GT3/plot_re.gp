set terminal pngcairo size 1050,650 enhanced font 'Arial,12'
set output '04_Cf_vs_Re.png'
set title 'Validação ERCOFTAC T3A (3%): Cf vs Re_x' font ',14'
set logscale xy
set grid xtics ytics lw 1, lw 0.5
set xlabel 'Reynolds Local (Re_x) [-]' font ',13'
set ylabel 'Cf [-]' font ',13'
set key bottom left box linewidth 1

# Ajuste fino para o T3A (transição ocorre entre 5e4 e 2e5)
set xr [1e4:1e6]
set yr [1e-3:1e-2]

# Referências teóricas de placa plana (como baseline)
blasius(x) = 0.664 / sqrt(x)
prandtl(x) = 0.455 / (log10(0.06 * x))**2

plot blasius(x) w l lw 2 lc rgb 'gray' dt 2 title 'Laminar (Blasius)',      prandtl(x) w l lw 2 lc rgb 'black' dt 2 title 'Turbulento (Prandtl)' , '/home/danilom/OpenFOAM/danilom-12/run/GT3/RANS-kklo/postProcessing/sampleDict/3000/y01.xy' u ($1*5.4/1.5e-05):($2/14.580000000000002) w l lw 2 lc rgb '#0060ad' title 'RANS-kklo', '/home/danilom/OpenFOAM/danilom-12/run/GT3/RANS-kOmegaSSTLM/postProcessing/sampleDict/3000/y01.xy' u ($1*5.4/1.5e-05):($2/14.580000000000002) w l lw 2 lc rgb '#dd181f' title 'RANS-kOmegaSSTLM', '/home/danilom/OpenFOAM/danilom-12/run/GT3/setup_TM/RANS-koSSTv2/postProcessing/sampleDict/3000/y01.xy' u ($1*5.4/1.5e-05):($2/14.580000000000002) w l lw 2 lc rgb '#00a000' title 'setup_TM/RANS-koSSTv2', '/home/danilom/OpenFOAM/danilom-12/run/GT3/setup_TM/RANS-launderSharmaKE/postProcessing/sampleDict/3000/y01.xy' u ($1*5.4/1.5e-05):($2/14.580000000000002) w l lw 2 lc rgb '#ffa500' title 'setup_TM/RANS-launderSharmaKE'
