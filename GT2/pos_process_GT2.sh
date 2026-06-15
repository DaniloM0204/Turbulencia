#!/bin/bash

CASES="RANS/KEpsilon_highRE_V1 RANS/KEpsilon_lowRE_V1 RANS/KOmegaSST_highRE RANS/KOmegaSST_lowRE_V1 RANS/SA_LRN SRS/DES_KO_LRN SRS/LES-WALE_LRN"

echo "--- Iniciando processamento do GT2 ---"

# Salva a pasta raiz do GT2 para poder voltar sempre para ela
ROOT_DIR=$(pwd)

for case in $CASES; do
    if [ -d "$case" ]; then
        echo ">>> Processando: $case"
        
        # 1. ENTRA na pasta do caso para rodar os comandos nativos do OpenFOAM
        cd "$ROOT_DIR/$case"
        
        # Executa o pós-processamento nativo do OpenFOAM se a pasta postProcessing não existir
        if [ ! -d "postProcessing" ]; then
            echo "    [!] Pasta postProcessing não encontrada. Gerando dados via sampleDict..."
            # Executa a amostragem usando a ferramenta nativa do caso
            # Se o dicionário tiver outro nome no tutorial, mude aqui (ex: -func sample)
            foamPostProcess -func sampleDict0 -latestTime > /dev/null 2>&1
        fi
        
        # 2. VOLTA para a raiz para rodar o Python com o caminho correto
        cd "$ROOT_DIR"
        
        # Ativa o ambiente virtual antes de rodar o python
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        fi

        # Chama o Python passando a pasta do caso
        python3 plot_GT2.py "$case"
        
    else
        echo "Pasta $case não encontrada."
    fi
done

echo "--- Processamento concluído! ---"