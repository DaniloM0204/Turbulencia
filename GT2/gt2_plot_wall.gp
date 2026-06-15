set terminal pngcairo size 1000,650 enhanced font 'Arial,12'
set output 'GT2_01_Lei_da_Parede.png'
set title 'Perfil Adimensional de Velocidade (u^+ vs y^+)' font ',14'
set logscale x
set grid xtics ytics lw 1, lw 0.5
set xlabel 'y^+ (Distância adimensional da parede)' font ',13'
set ylabel 'u^+ (Velocidade adimensional)' font ',13'
set key bottom right box linewidth 1

nu = 1.5e-5
utau = 0.045

subcamada(x) = x
loglaw(x) = (1.0/0.41) * log(x) + 5.2

# Limites exatos solicitados
set xr [1e-2:1e5]
set yr [0:30]
plot subcamada(x) lw 2 lc rgb 'black' dt 2 title 'Subcamada (u^+=y^+)', loglaw(x) lw 2 lc rgb 'black' title 'Log-Law', 'RANS/KOmegaSST_highRE/clean_profile.dat' u ($1*utau/nu):($2/utau) w l lw 2.5 lc rgb '#0060ad' title 'KOmegaSST_highRE', 'RANS/KOmegaSST_lowRE_V1/clean_profile.dat' u ($1*utau/nu):($2/utau) w l lw 2.5 lc rgb '#dd181f' title 'KOmegaSST_lowRE_V1', 'RANS/KEpsilon_highRE_V1/clean_profile.dat' u ($1*utau/nu):($2/utau) w l lw 2.5 lc rgb '#00a000' title 'KEpsilon_highRE_V1', 'RANS/KEpsilon_lowRE_V1/clean_profile.dat' u ($1*utau/nu):($2/utau) w l lw 2.5 lc rgb '#ffa500' title 'KEpsilon_lowRE_V1', 'RANS/SA_LRN/clean_profile.dat' u ($1*utau/nu):($2/utau) w l lw 2.5 lc rgb '#8a2be2' title 'SA_LRN', 'SRS/DES_KO_LRN/clean_profile.dat' u ($1*utau/nu):($2/utau) w l lw 2.5 lc rgb '#ff1493' title 'DES_KO_LRN', 'SRS/LES-WALE_LRN/clean_profile.dat' u ($1*utau/nu):($2/utau) w l lw 2.5 lc rgb '#00ffff' title 'LES-WALE_LRN'
