set terminal pngcairo size 1050,650 enhanced font 'Arial,12'
set output '01_Cf_Transicao_Modelos.png'
set title 'Evolução do Coeficiente de Atrito Cf(x) ao longo da Placa (GT3)' font ',14'
set grid xtics ytics mxtics lw 1, lw 0.5
set xlabel 'Posição x [m]' font ',13'
set ylabel 'Coeficiente de Atrito Cf [-]' font ',13'
set key outside right center box linewidth 1
set xr [2e-2:2.75]
set yr [0.0001:0.0075]
plot '/home/danilom/OpenFOAM/danilom-12/run/GT3/RANS-kklo/postProcessing/sampleDict/3000/y01.xy' u 1:($2/14.580000000000002) w l lw 3 lc rgb '#0060ad' title 'k-kl-omega', '/home/danilom/OpenFOAM/danilom-12/run/GT3/RANS-kOmegaSSTLM/postProcessing/sampleDict/3000/y01.xy' u 1:($2/14.580000000000002) w l lw 3 lc rgb '#dd181f' title 'SST-LM', '/home/danilom/OpenFOAM/danilom-12/run/GT3/setup_TM/RANS-koSSTv2/postProcessing/sampleDict/3000/y01.xy' u 1:($2/14.580000000000002) w l lw 3 lc rgb '#00a000' title 'SST v2', '/home/danilom/OpenFOAM/danilom-12/run/GT3/setup_TM/RANS-launderSharmaKE/postProcessing/sampleDict/3000/y01.xy' u 1:($2/14.580000000000002) w l lw 3 lc rgb '#ffa500' title 'Launder-Sh'
