#!/bin/bash

LOG_DIR="logs_checkMesh"
mkdir -p "$LOG_DIR"

echo "=================================================="
echo " Iniciando verificação de malhas (checkMesh)      "
echo "=================================================="

find . -maxdepth 6 -path "*/constant/polyMesh" -type d | while read mesh_dir; do
    case_dir=$(dirname "$(dirname "$mesh_dir")")
    safe_filename=$(echo "$case_dir" | tr '/' '_')
    log_file="$LOG_DIR/${safe_filename}_checkMesh.log"
    
    echo -n "Processando: $case_dir ... "
    checkMesh -case "$case_dir" > "$log_file" 2>&1
    
    # Extrai as métricas principais do log de forma limpa para o terminal
    if grep -q "Mesh OK" "$log_file"; then
        if grep -q "High aspect ratio" "$log_file"; then
            echo "OK (com razão de aspecto alta - esperado)"
        else
            echo "OK (perfeita)"
        fi
    else
        echo "ERRO! Verifique o log em detalhes."
    fi
done

echo ""
echo "=================================================="
echo " Verificações concluídas!                         "
echo " Logs salvos na pasta: $LOG_DIR                  "
echo "=================================================="