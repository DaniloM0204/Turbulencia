#!/bin/bash

echo "Limpando resultados anteriores dos casos GT1, GT2 e GT3"
# Detecta todas as pastas e realiza limpeza
for case_path in GT1/* GT2/RANS/* GT2/SRS/* GT3/RANS-* GT3/setup_TM/*; do
    [ -d "$case_path/0" ] && foamCleanTutorials -case "$case_path"
done

echo "Limpando resultado dos script em python"
rm -rf GT*/Resultados_Graficos_GT* GT*/*.png GT*/Analise_GT*.txt GT*/residuos_Ux_tempo.dat GT3/RANS-kklo_TU_alta

python3 GT_all.py

if [ $? -eq 0 ]; then
    echo "Execução finalizada com sucesso."
else
    echo "Falha na execução."
fi