# Configuração de alta qualidade
set terminal pngcairo size 1000,700 enhanced font 'Arial,12'
set output 'Comparativo_Modelos.png'

# Estilo de bordas e grade
set border 31 linewidth 1.5
set grid xtics ytics mxtics mytics lw 1, lw 0.5
set key outside right top box linestyle 1

# Rótulos e fontes
set xlabel 'y (Distância da parede [m])' font ",14"
set ylabel 'U (Velocidade [m/s])' font ",14"

# Estilos de linha profissionais (Cores sóbrias e linhas grossas)
set style line 1 lc rgb '#0060ad' lt 1 lw 3 # Azul (High-Re)
set style line 2 lc rgb '#dd181f' lt 1 lw 3 # Vermelho (Low-Re)

# Plotagem
plot 'RANS/KOmegaSST_highRE/postProcessing/sampleDict/2000/profile0.xy' u 1:2 w l ls 1 title 'K-Omega SST High-Re',\
     'RANS/KOmegaSST_lowRE_V1/postProcessing/sampleDict/2000/profile0.xy' u 1:2 w l ls 2 title 'K-Omega SST Low-Re'