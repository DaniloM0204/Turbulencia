#!/bin/bash

# --- CONFIGURAÇÃO ---
CASES=("RANS-kklo" "RANS-kOmegaSSTLM" "setup_TM/RANS-koSSTv2" "setup_TM/RANS-launderSharmaKE")
RESULT_DIR="Resultados_Graficos_GT3"
ANALISE_FILE="Analise_GT3.txt"
U_INF=5.4
DENOMINADOR=$(echo "0.5 * $U_INF * $U_INF" | bc -l)

mkdir -p "$RESULT_DIR"
echo "=== RELATÓRIO TÉCNICO GT3 - TRANSIÇÃO ===" > "$ANALISE_FILE"

# --- LOOP PRINCIPAL ---
for case in "${CASES[@]}"; do
    if [ ! -d "$case" ]; then continue; fi
    
    echo "[$case] Processando..."
    cd "$case" || continue

    # 1. Execução (apenas se não existir postProcessing)
    if [ ! -d "postProcessing" ]; then
        foamListTimes -rm > /dev/null 2>&1
        blockMesh > /dev/null 2>&1
        foamRun > log.foamRun 2>&1
        foamPostProcess -func wallShearStress -latestTime > /dev/null 2>&1
        foamPostProcess -func yPlus -latestTime > /dev/null 2>&1
        foamPostProcess -func sampleDict -latestTime > /dev/null 2>&1
    fi

    # 2. Métricas de y+ (Leitura do arquivo)
    AVG_Y="N/A"
    YPLUS_DAT=$(find postProcessing -name "yPlus.dat" | head -n 1)
    if [ -f "$YPLUS_DAT" ]; then
        AVG_Y=$(tail -n 1 "$YPLUS_DAT" | awk '{print $NF}')
    fi
    echo "Modelo: $case | y+ (Med): $AVG_Y" >> "../../$ANALISE_FILE"

    # 3. Extração de dados (U e Cf)
    MODELO_DIR="../../$RESULT_DIR/Resultado_${case//\//_}"
    mkdir -p "$MODELO_DIR"
    
    SAMPLE_PATH=$(find postProcessing -name "sampleDict" -o -name "sampleDict0" | head -n 1)
    if [ -d "$SAMPLE_PATH" ]; then
        # Pega a pasta de tempo mais recente
        PASTA=$(ls -d "$SAMPLE_PATH"/* | sort -n | tail -1)
        
        # Extração U
        U_FILE=$(find "$PASTA" -name "*U*" -o -name "*profile*" | head -n 1)
        if [ -f "$U_FILE" ]; then
            grep -vE '(#|\(|\)|bottom|top)' "$U_FILE" | awk '{print $1, $2}' > "$MODELO_DIR/uy.dat"
        fi

        # Extração Cf
        CF_FILE=$(find "$PASTA" -name "*wall*" -o -name "*shear*" | head -n 1)
        if [ -f "$CF_FILE" ]; then
            grep -vE '(#|\(|\)|bottom|top)' "$CF_FILE" | awk -v d=$DENOMINADOR '{print $1, abs($2)/d}' > "$MODELO_DIR/cf.dat"
        fi
    fi
    cd ..
done

# 4. Geração do gráfico único
echo "Gerando gráfico comparativo..."
gnuplot << EOF
set terminal pngcairo size 900,600 font 'Arial,12'
set output '$RESULT_DIR/Comparativo_Cf_x.png'
set title 'Coeficiente de Atrito Local: Transição vs Turbulento'
set xlabel 'Posição (x) [m]'; set ylabel 'Cf'; set grid
plot for [file in system("ls $RESULT_DIR/*/cf.dat")] file w l title file
EOF

echo -e "\n[+] Processamento concluído. Verifique Analise_GT3.txt e Resultados_Graficos_GT3/"