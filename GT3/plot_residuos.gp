set terminal pngcairo size 1050,650 enhanced font 'Arial,12'
set output '03_Convergencia_Tempo.png'
set title 'Convergência do Solver (Resíduo Ux vs Tempo Físico)' font ',14'
set logscale y
set grid xtics ytics lw 1, lw 0.5
set xlabel 'Tempo [s]' font ',13'
set ylabel 'Resíduo Inicial (Ux) [-]' font ',13'
set key outside right center box linewidth 1
plot '/home/danilom/OpenFOAM/danilom-12/run/GT3/RANS-kklo/residuos_Ux_tempo.dat' w l lw 2 title 'RANS-kklo', '/home/danilom/OpenFOAM/danilom-12/run/GT3/RANS-kOmegaSSTLM/residuos_Ux_tempo.dat' w l lw 2 title 'RANS-kOmegaSSTLM', '/home/danilom/OpenFOAM/danilom-12/run/GT3/setup_TM/RANS-koSSTv2/residuos_Ux_tempo.dat' w l lw 2 title 'setup_TM/RANS-koSSTv2', '/home/danilom/OpenFOAM/danilom-12/run/GT3/setup_TM/RANS-launderSharmaKE/residuos_Ux_tempo.dat' w l lw 2 title 'setup_TM/RANS-launderSharmaKE'
