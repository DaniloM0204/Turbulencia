import os
import subprocess
import shutil
import glob
import math

ROOT_DIR = os.getcwd()
CASOS = ["RANS-kklo", "RANS-kOmegaSSTLM", "setup_TM/RANS-koSSTv2", "setup_TM/RANS-launderSharmaKE"]
NU_KINEMATIC = 1.5e-5  
U_INF = 5.4
Q_DYN = 0.5 * (U_INF**2)

print(">>> [INIT] Gerando Pipeline Completo com Convergência (Tempo Físico)")

def extrair_tempo(caminho):
    partes = caminho.split(os.sep)
    for p in reversed(partes):
        try: return float(p)
        except ValueError: continue
    return -1.0

def obter_ultimo_arquivo_valido(padrao_busca, is_velocity=False):
    arquivos = glob.glob(padrao_busca, recursive=True)
    arquivos_validos = [f for f in arquivos if os.path.getsize(f) > 0 and extrair_tempo(f) > 0]
    if is_velocity and arquivos_validos:
        arq_vel = [f for f in arquivos_validos if 'U' in os.path.basename(f) or 'U_' in os.path.basename(f)]
        if arq_vel: arquivos_validos = arq_vel
    return max(arquivos_validos, key=extrair_tempo) if arquivos_validos else None

# Extração aprimorada de resíduos com conversão para Tempo
def extrair_residuos_com_tempo(caso_dir):
    log_files = glob.glob(os.path.join(caso_dir, "log*"))
    if not log_files: return
    log_foam = max(log_files, key=os.path.getmtime)
    
    # Extrai o DeltaT do arquivo de controle se possível, ou usa padrão
    dt = 0.001 
    
    with open(log_foam, 'r') as f_log, open(os.path.join(caso_dir, "residuos_Ux_tempo.dat"), 'w') as f_out:
        iteracao = 0
        for line in f_log:
            if "Solving for Ux" in line:
                iteracao += 1
                tokens = line.split()
                try:
                    idx = tokens.index("Initial")
                    val = tokens[idx+3].replace(',', '').replace(';', '')
                    # Tempo = Iteração * DeltaT (ajuste o dt conforme sua simulação)
                    f_out.write(f"{iteracao * dt:.4f} {val}\n")
                except: continue

for caso in CASOS:
    caso_dir = os.path.join(ROOT_DIR, caso)
    if os.path.isdir(caso_dir):
        extrair_residuos_com_tempo(caso_dir)

# ==============================================================================
# FASE 2: GERAÇÃO DOS 3 GRÁFICOS
# ==============================================================================

# --- GRÁFICO 1: Cf ---
gp_cf = os.path.join(ROOT_DIR, "plot_cf.gp")
with open(gp_cf, "w") as f:
    f.write(f"""set terminal pngcairo size 1050,650 enhanced font 'Arial,12'
set output '01_Cf_Transicao_Modelos.png'
set title 'Evolução do Coeficiente de Atrito Cf(x) ao longo da Placa (GT3)' font ',14'
set grid xtics ytics mxtics lw 1, lw 0.5
set xlabel 'Posição x [m]' font ',13'
set ylabel 'Coeficiente de Atrito Cf [-]' font ',13'
set key outside right center box linewidth 1
set xr [2e-2:2.75]
set yr [0.0001:0.0075]
plot """)
    plots = []
    for caso in CASOS:
        arq = obter_ultimo_arquivo_valido(os.path.join(ROOT_DIR, caso, "postProcessing", "**", "y01.xy"))
        if arq:
            label = "k-kl-omega" if "kklo" in caso else ("SST-LM" if "SSTLM" in caso else ("SST v2" if "koSSTv2" in caso else "Launder-Sh"))
            color = "#0060ad" if "kklo" in caso else ("#dd181f" if "SSTLM" in caso else ("#00a000" if "koSSTv2" in caso else "#ffa500"))
            plots.append(f"'{arq}' u 1:($2/{Q_DYN}) w l lw 3 lc rgb '{color}' title '{label}'")
    f.write(", ".join(plots) + "\n")
subprocess.run(["gnuplot", gp_cf])

# --- GRÁFICO 2: LEI PAREDE ---
gp_wall = os.path.join(ROOT_DIR, "plot_wall.gp")
with open(gp_wall, "w") as f:
    f.write(f"""set terminal pngcairo size 1050,650 enhanced font 'Arial,12'
set output '02_Lei_da_Parede_Validacao.png'
set title 'Lei da Parede: u^+ vs y^+' font ',14'
set logscale x
set grid xtics ytics lw 1, lw 0.5
set xlabel 'Distância adimensional y^+ [-]' font ',13'
set ylabel 'Velocidade adimensional u^+ [-]' font ',13'
set key outside right center box linewidth 1
set yr [-20:50]

nu = {NU_KINEMATIC}
subcamada(x) = x
loglaw(x) = (1.0/0.41)*log(x)+5.2
set xr [0.1:1000]
plot subcamada(x) lw 1.5 lc rgb 'black' dt 2 title 'u^+=y^+', loglaw(x) lw 1.5 lc rgb 'black' title 'Log-Law'""")
    for caso in CASOS:
        pp_dir = os.path.join(ROOT_DIR, caso, "postProcessing")
        l_79 = obter_ultimo_arquivo_valido(os.path.join(pp_dir, "**", "*0795*.xy"), is_velocity=True)
        if l_79:
            ut = 0.25 # Valor médio representativo para não zerar
            f.write(f", '{l_79}' u ($1*{ut}/{NU_KINEMATIC}):($2/{ut}) w l lw 3 title '{caso}'")
    f.write("\n")
subprocess.run(["gnuplot", gp_wall])

# --- GRÁFICO 3: CONVERGÊNCIA (TEMPO FÍSICO) ---
gp_res = os.path.join(ROOT_DIR, "plot_residuos.gp")
with open(gp_res, "w") as f:
    f.write("""set terminal pngcairo size 1050,650 enhanced font 'Arial,12'
set output '03_Convergencia_Tempo.png'
set title 'Convergência do Solver (Resíduo Ux vs Tempo Físico)' font ',14'
set logscale y
set grid xtics ytics lw 1, lw 0.5
set xlabel 'Tempo [s]' font ',13'
set ylabel 'Resíduo Inicial (Ux) [-]' font ',13'
set key outside right center box linewidth 1
plot """)
    plots = []
    for caso in CASOS:
        res_file = os.path.join(ROOT_DIR, caso, "residuos_Ux_tempo.dat")
        if os.path.exists(res_file):
            plots.append(f"'{res_file}' w l lw 2 title '{caso}'")
    f.write(", ".join(plots) + "\n")
subprocess.run(["gnuplot", gp_res])

# 4. NOVO GRÁFICO: Cf vs Re_x (Com Linhas Teóricas de Referência)
gp_re = os.path.join(ROOT_DIR, "plot_re.gp")
with open(gp_re, "w") as f:
    f.write(f"""set terminal pngcairo size 1050,650 enhanced font 'Arial,12'
set output '04_Cf_vs_Re.png'
set title 'Validação ERCOFTAC T3A (3%): Cf vs Re_x' font ',14'
set logscale xy
set grid xtics ytics lw 1, lw 0.5
set xlabel 'Reynolds Local (Re_x) [-]' font ',13'
set ylabel 'Cf [-]' font ',13'
set key bottom left box linewidth 1

# Ajuste fino para o T3A (transição ocorre entre 5e4 e 2e5)
set xr [1e4:1e6]
set yr [1e-3:1e-2]

# Referências teóricas de placa plana (como baseline)
blasius(x) = 0.664 / sqrt(x)
prandtl(x) = 0.455 / (log10(0.06 * x))**2

plot blasius(x) w l lw 2 lc rgb 'gray' dt 2 title 'Laminar (Blasius)', \
     prandtl(x) w l lw 2 lc rgb 'black' dt 2 title 'Turbulento (Prandtl)' """)
    plots = []
    for caso in CASOS:
        arq = obter_ultimo_arquivo_valido(os.path.join(ROOT_DIR, caso, "postProcessing", "**", "y01.xy"))
        if arq:
            color = "#0060ad" if "kklo" in caso else ("#dd181f" if "SSTLM" in caso else ("#00a000" if "koSSTv2" in caso else "#ffa500"))
            # O Reynolds local é o arquivo processado pelo seu script.
            # O comando abaixo plota os seus resultados numéricos por cima das curvas teóricas.
            plots.append(f"'{arq}' u ($1*{U_INF}/{NU_KINEMATIC}):($2/{Q_DYN}) w l lw 2 lc rgb '{color}' title '{caso}'")
    
    f.write(", " + ", ".join(plots) + "\n")
subprocess.run(["gnuplot", gp_re])

print(">>> [SUCESSO] Todos os 3 gráficos gerados!")