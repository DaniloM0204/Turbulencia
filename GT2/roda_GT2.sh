#!/bin/bash

# ─── Casos ────────────────────────────────────────────────────────────────────
CASES=(
    "RANS/KEpsilon_highRE_V1"
    "RANS/KEpsilon_lowRE_V1"
    "RANS/KOmegaSST_highRE"
    "RANS/KOmegaSST_lowRE_V1"
    "RANS/SA_LRN"
    "SRS/DES_KO_LRN"
    "SRS/LES-WALE_LRN"
)

ROOT_DIR="$(pwd)"
ANALISE="$ROOT_DIR/Analise_GT2.txt"
SAMPLE_DICT_REF="$ROOT_DIR/RANS/KEpsilon_highRE_V1/system/sampleDict"
> "$ANALISE"

# ─── Helpers ──────────────────────────────────────────────────────────────────

# Lê o campo 'application' do controlDict → usado no -solver do foamPostProcess
ler_solver() {
    grep -E '^\s*application\s+' "$1/system/controlDict" 2>/dev/null \
        | awk '{gsub(";",""); print $2}' | head -1
}

# Garante que o sampleDict existe (copia do RANS de referência se faltar)
preparar_sampleDict() {
    local case="$1"
    if [ ! -f "$case/system/sampleDict" ]; then
        if [ -f "$SAMPLE_DICT_REF" ]; then
            cp "$SAMPLE_DICT_REF" "$case/system/sampleDict"
        else
            echo "[ERRO] sampleDict de referência não encontrado: $SAMPLE_DICT_REF" >&2
        fi
    fi
}

# ─── Função principal ─────────────────────────────────────────────────────────
executar_caso() {
    local case_path="$1"

    if [ ! -d "$case_path" ]; then
        echo "[ERRO] Caso não encontrado: $case_path" >&2
        return 1
    fi

    local case_label="${case_path//\//_}"
    local modelo_dir="$ROOT_DIR/Resultados_Graficos/Resultado_${case_label}"
    mkdir -p "$modelo_dir"

    cd "$case_path"

    # Garante sampleDict antes de qualquer coisa
    preparar_sampleDict "."

    # Lê o solver para passar ao foamPostProcess
    local solver
    solver=$(ler_solver ".")
    if [ -z "$solver" ]; then
        echo "[ERRO] Não foi possível ler 'application' do controlDict em $case_path" >&2
        cd "$ROOT_DIR"
        return 1
    fi

    # 1. Simulação (pula se postProcessing já existe)
    if [ ! -d "postProcessing" ]; then

        foamListTimes -rm > /dev/null 2>&1 || true

        if ! blockMesh > log.blockMesh 2>&1; then
            echo "[ERRO] blockMesh falhou em $case_path — veja log.blockMesh" >&2
            cd "$ROOT_DIR"; return 1
        fi

        if ! foamRun > log.foamRun 2>&1; then
            echo "[ERRO] foamRun falhou em $case_path — veja log.foamRun" >&2
            cd "$ROOT_DIR"; return 1
        fi

        # 2. Pós-processamento com -solver para carregar modelo de turbulência
        if ! foamPostProcess -solver "$solver" -func wallShearStress -latestTime > /dev/null 2>&1; then
            echo "[AVISO] wallShearStress falhou em $case_path" >&2
        fi

        if ! foamPostProcess -solver "$solver" -func yPlus -latestTime > /dev/null 2>&1; then
            echo "[AVISO] yPlus falhou em $case_path" >&2
        fi

        if ! foamPostProcess -solver "$solver" -func sampleDict -latestTime > /dev/null 2>&1; then
            echo "[ERRO] sampleDict falhou em $case_path" >&2
            cd "$ROOT_DIR"; return 1
        fi
    fi

    # 3. Métricas → Analise_GT2.txt
    # RANS: postProcessing/yPlus/0/yPlus.dat
    # SRS:  postProcessing/yPlus/yplus_stats/<tempo>/yPlus.dat  (OpenFOAM 12)
    local avg_y="N/A"
    local yplus_dat=""

    # Tenta caminho RANS primeiro
    if [ -f "postProcessing/yPlus/0/yPlus.dat" ]; then
        yplus_dat="postProcessing/yPlus/0/yPlus.dat"
    # Tenta caminho SRS (OF 12)
    elif [ -d "postProcessing/yPlus/yplus_stats" ]; then
        local yplus_time
        yplus_time=$(ls "postProcessing/yPlus/yplus_stats" | grep -E '^[0-9]+(\.[0-9]+)?$' | sort -g | tail -1)
        [ -n "$yplus_time" ] && yplus_dat="postProcessing/yPlus/yplus_stats/$yplus_time/yPlus.dat"
    fi

    if [ -f "$yplus_dat" ]; then
        avg_y=$(awk 'NR>1 {last=$NF} END {if (last) print last; else print "N/A"}' "$yplus_dat")
    else
        echo "[AVISO] yPlus.dat não encontrado em nenhum caminho conhecido ($case_path)" >&2
    fi
    echo "Modelo: $case_path | y+ Parede (Med): $avg_y" >> "$ANALISE"

    # 4. Extração de dados
    local sample_path="postProcessing/sampleDict"
    if [ ! -d "$sample_path" ]; then
        echo "[ERRO] postProcessing/sampleDict não gerado em $case_path" >&2
        cd "$ROOT_DIR"; return 1
    fi

    local latest_time
    latest_time=$(ls "$sample_path" | grep -E '^[0-9]+(\.[0-9]+)?$' | sort -g | tail -1)

    if [ -z "$latest_time" ]; then
        echo "[ERRO] Nenhum tempo encontrado em $sample_path ($case_path)" >&2
        cd "$ROOT_DIR"; return 1
    fi

    local pasta="$sample_path/$latest_time"
    local files
    files=$(ls "$pasta")

    # Extração U → uy.dat
    local u_file
    u_file=$(echo "$files" | grep -E 'U|profile' | head -1)
    [ -z "$u_file" ] && u_file=$(echo "$files" | head -1)
    if [ -n "$u_file" ]; then
        awk '$1+0==$1 && $2+0==$2 && NF>=2 {printf "%s\t%s\n", $1, $2}' \
            "$pasta/$u_file" > "$modelo_dir/uy.dat"
    else
        echo "[AVISO] Nenhum arquivo U encontrado em $pasta ($case_path)" >&2
    fi

    # Extração wallShearStress → cf.dat
    local cf_file
    cf_file=$(echo "$files" | grep -iE 'wall|shear' | head -1)
    if [ -n "$cf_file" ]; then
        awk '$1+0==$1 && $2+0==$2 && NF>=2 {
            cf = ($2 < 0) ? -$2 : $2
            printf "%s\t%.6g\n", $1, 2.0*cf
        }' "$pasta/$cf_file" > "$modelo_dir/cf.dat"
    else
        echo "[AVISO] Nenhum arquivo wallShearStress encontrado em $pasta ($case_path)" >&2
    fi

    cd "$ROOT_DIR"
}

# ─── Loop principal ───────────────────────────────────────────────────────────
declare -A DADOS_UY
declare -A DADOS_CF

for c in "${CASES[@]}"; do
    if executar_caso "$c"; then
        case_label="${c//\//_}"
        modelo_dir="$ROOT_DIR/Resultados_Graficos/Resultado_${case_label}"
        [ -s "$modelo_dir/uy.dat" ] && DADOS_UY["$c"]="$modelo_dir/uy.dat"
        [ -s "$modelo_dir/cf.dat" ] && DADOS_CF["$c"]="$modelo_dir/cf.dat"
    fi
done

# ─── Plotagem ─────────────────────────────────────────────────────────────────
plot_pair() {
    local c1="$1" c2="$2" tag="$3"

    if [ -n "${DADOS_UY[$c1]+x}" ] && [ -n "${DADOS_UY[$c2]+x}" ]; then
        gnuplot -e "
            set terminal pngcairo;
            set output 'Grafico_${tag}_uy.png';
            set logscale x; set grid;
            plot '${DADOS_UY[$c1]}' w l title '$c1',
                 '${DADOS_UY[$c2]}' w l title '$c2'
        " 2>/dev/null || echo "[AVISO] gnuplot falhou para ${tag}_uy" >&2
    fi

    if [ -n "${DADOS_CF[$c1]+x}" ] && [ -n "${DADOS_CF[$c2]+x}" ]; then
        gnuplot -e "
            set terminal pngcairo;
            set output 'Grafico_${tag}_cf.png';
            set grid;
            plot '${DADOS_CF[$c1]}' w l title '$c1',
                 '${DADOS_CF[$c2]}' w l title '$c2'
        " 2>/dev/null || echo "[AVISO] gnuplot falhou para ${tag}_cf" >&2
    fi
}

plot_pair "RANS/KEpsilon_highRE_V1" "RANS/KEpsilon_lowRE_V1" "parede"
plot_pair "SRS/DES_KO_LRN"          "SRS/LES-WALE_LRN"       "srs"

echo "[+] Processamento concluído."