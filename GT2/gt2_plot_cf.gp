set terminal pngcairo size 1000,650 enhanced font 'Arial,12'
set output 'GT2_02_Cf_Validacao.png'
set title 'Coeficiente de Atrito Local C_f vs Comprimento da Placa (x)' font ',14'
# Escala linear nos eixos X e Y
set grid xtics ytics mxtics mytics lw 1, lw 0.5
set xlabel 'Comprimento da placa x [m]' font ',13'
set ylabel 'Coeficiente de Atrito Local (C_f)' font ',13'
set key top right box linewidth 1

nu = 1.5e-5
Uinf = 1.0
q = 0.5 * 1.0 * Uinf**2

# Função interna para calcular Reynolds a partir da posição X e proteger contra div por 0
Re(x) = (x <= 1e-5) ? 1e-5 : (x * Uinf / nu)
Cf_laminar(x) = (x <= 1e-5) ? 0 : 0.664 / sqrt(Re(x))
Cf_turbulento(x) = (x <= 1e-5) ? 0 : 0.0592 / (Re(x)**0.2)

# Limites exatos solicitados
set xr [0:2]
set yr [0:0.014]
plot Cf_laminar(x) lw 2 lc rgb 'black' dt 2 title 'Laminar (Blasius)', Cf_turbulento(x) lw 2 lc rgb 'black' title 'Turbulento (Prandtl)', 'RANS/KOmegaSST_highRE/clean_cf.dat' u 1:($2/q) w l lw 2.5 lc rgb '#0060ad' title 'KOmegaSST_highRE', 'RANS/KOmegaSST_lowRE_V1/clean_cf.dat' u 1:($2/q) w l lw 2.5 lc rgb '#dd181f' title 'KOmegaSST_lowRE_V1', 'RANS/KEpsilon_highRE_V1/clean_cf.dat' u 1:($2/q) w l lw 2.5 lc rgb '#00a000' title 'KEpsilon_highRE_V1', 'RANS/KEpsilon_lowRE_V1/clean_cf.dat' u 1:($2/q) w l lw 2.5 lc rgb '#ffa500' title 'KEpsilon_lowRE_V1', 'RANS/SA_LRN/clean_cf.dat' u 1:($2/q) w l lw 2.5 lc rgb '#8a2be2' title 'SA_LRN', 'SRS/LES-WALE_LRN/clean_cf.dat' u 1:($2/q) w l lw 2.5 lc rgb '#ff1493' title 'LES-WALE_LRN'
