import os
import glob
import numpy as np
import matplotlib.pyplot as plt

ROOT_DIR = os.getcwd()
CASOS = ["RANS-kklo", "RANS-kOmegaSSTLM", "setup_TM/RANS-koSSTv2", "setup_TM/RANS-launderSharmaKE"]
NU_KINEMATIC = 1.5e-5  
U_INF = 5.4
Q_DYN = 0.5 * (U_INF**2)


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

def extrair_residuos_com_tempo(caso_dir):
    log_files = glob.glob(os.path.join(caso_dir, "log*"))
    if not log_files: return
    log_foam = max(log_files, key=os.path.getmtime)
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
                    f_out.write(f"{iteracao * dt:.4f} {val}\n")
                except: continue

# ==============================================================================
# NOVA FUNÇÃO DE LEITURA (IMITA O GNUPLOT - IGNORA PARÊNTESES E SUJEIRAS)
# ==============================================================================
def ler_dados_openfoam(filepath):
    dados = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                # Transforma "0.01 (0.05 0 0)" em "0.01  0.05 0 0"
                clean_line = line.replace('(', ' ').replace(')', ' ').replace(',', ' ')
                tokens = clean_line.split()
                if len(tokens) >= 2:
                    try:
                        x = float(tokens[0])
                        y = float(tokens[1])
                        dados.append([x, y])
                    except ValueError:
                        continue # Ignora cabeçalhos de texto
    except Exception as e:
        print(f"Erro ao ler {filepath}: {e}")
    
    array_dados = np.array(dados)
    if array_dados.size == 0:
        print(f" [AVISO] Nenhum dado extraído de: {filepath}")
    return array_dados

def obter_estilo_caso(caso):
    if "kklo" in caso: return "#0060ad", "k-kl-omega"
    if "SSTLM" in caso: return "#dd181f", "SST-LM"
    if "koSSTv2" in caso: return "#00a000", "SST v2"
    return "#ffa500", "Launder-Sh"

for caso in CASOS:
    caso_dir = os.path.join(ROOT_DIR, caso)
    if os.path.isdir(caso_dir):
        extrair_residuos_com_tempo(caso_dir)

plt.style.use('seaborn-v0_8-whitegrid')

# --- GRÁFICO 1: Cf ---
plt.figure(figsize=(10, 6))
for caso in CASOS:
    arq = obter_ultimo_arquivo_valido(os.path.join(ROOT_DIR, caso, "postProcessing", "**", "y01.xy"))
    if arq:
        dados = ler_dados_openfoam(arq)
        if dados.size > 0:
            cor, label = obter_estilo_caso(caso)
            plt.plot(dados[:, 0], dados[:, 1] / Q_DYN, lw=3, color=cor, label=label)

plt.title('Evolução do Coeficiente de Atrito Cf(x) ao longo da Placa (GT3)', fontsize=14)
plt.xlabel('Posição x [m]', fontsize=13)
plt.ylabel('Coeficiente de Atrito Cf [-]', fontsize=13)
plt.xlim(2e-2, 2.75)
plt.ylim(0.0001, 0.0075)
plt.legend(loc='lower left')
plt.tight_layout()
plt.savefig('01_Cf_Transicao_Modelos.png', dpi=200)
plt.close()

# --- GRÁFICO 2: LEI PAREDE ---
plt.figure(figsize=(10, 6))
x_sub = np.linspace(0.1, 11.6, 100)
x_log = np.linspace(11.6, 1000, 100)
plt.plot(x_sub, x_sub, 'k--', lw=1.5, label='u^+=y^+')
plt.plot(x_log, (1.0/0.41)*np.log(x_log) + 5.2, 'k-', lw=1.5, label='Log-Law')

for caso in CASOS:
    l_79 = obter_ultimo_arquivo_valido(os.path.join(ROOT_DIR, caso, "postProcessing", "**", "*0795*.xy"), is_velocity=True)
    if l_79:
        dados = ler_dados_openfoam(l_79)
        if dados.size > 0:
            ut = 0.25 # Valor médio representativo original
            cor, label = obter_estilo_caso(caso)
            plt.plot(dados[:, 0] * ut / NU_KINEMATIC, dados[:, 1] / ut, lw=3, color=cor, label=label)

plt.title('Lei da Parede: $u^+$ vs $y^+$', fontsize=14)
plt.xlabel('Distância adimensional $y^+$ [-]', fontsize=13)
plt.ylabel('Velocidade adimensional $u^+$ [-]', fontsize=13)
plt.xscale('log')
plt.xlim(0.1, 1000)
plt.ylim(-20, 50)
plt.legend(loc='lower left')
plt.tight_layout()
plt.savefig('02_Lei_da_Parede_Validacao.png', dpi=200)
plt.close()

# --- GRÁFICO 3: CONVERGÊNCIA ---
plt.figure(figsize=(10, 6))
for caso in CASOS:
    res_file = os.path.join(ROOT_DIR, caso, "residuos_Ux_tempo.dat")
    if os.path.exists(res_file) and os.path.getsize(res_file) > 0:
        dados = ler_dados_openfoam(res_file)
        if dados.size > 0:
            cor, label = obter_estilo_caso(caso)
            plt.plot(dados[:, 0], dados[:, 1], lw=2, color=cor, label=label)

plt.title('Convergência do Solver (Resíduo Ux vs Tempo)', fontsize=14)
plt.xlabel('Tempo [s]', fontsize=13)
plt.ylabel('Resíduo (Ux) [-]', fontsize=13)
plt.yscale('log')
plt.legend(loc='lower left')
plt.tight_layout()
plt.savefig('03_Convergencia_Tempo.png', dpi=200)
plt.close()

# --- GRÁFICO 4: Cf vs Re_x ---
plt.figure(figsize=(10, 6))
x_re = np.logspace(4, 6, 200)

# Correções nas linhas teóricas
cf_laminar = 0.664 / np.sqrt(x_re)
plt.plot(x_re, cf_laminar, 'gray', linestyle='--', lw=2, label='Laminar (Blasius)')

cf_turbulento = 0.0592 / (x_re**0.2) 
plt.plot(x_re, cf_turbulento, 'k--', lw=2, label='Turbulento (Schlichting)')

for caso in CASOS:
    arq = obter_ultimo_arquivo_valido(os.path.join(ROOT_DIR, caso, "postProcessing", "**", "y01.xy"))
    if arq:
        dados = ler_dados_openfoam(arq)
        if dados.size > 0:
            cor, label = obter_estilo_caso(caso)
            re_x = dados[:, 0] * U_INF / NU_KINEMATIC
            cf = dados[:, 1] / Q_DYN
            plt.plot(re_x, cf, lw=2, color=cor, label=label)

# ==========================================
# Demarcação de Regiões T3A
# ==========================================
inicio_transicao = 6e4
fim_transicao = 2.5e5

plt.axvline(x=inicio_transicao, color='black', linestyle=':', lw=1.5, alpha=0.7)
plt.axvline(x=fim_transicao, color='black', linestyle=':', lw=1.5, alpha=0.7)

plt.text(2e4, 0.012, 'Região\nLaminar', color='gray', fontsize=12, ha='center', weight='bold')
plt.text(1.2e5, 0.012, 'Rampa de\nTransição', color='gray', fontsize=12, ha='center', weight='bold')
plt.text(6e5, 0.012, 'Região\nTurbulenta', color='gray', fontsize=12, ha='center', weight='bold')
# ==========================================

plt.title('Validação ERCOFTAC T3A: $C_f$ vs $Re_x$', fontsize=14)
plt.xlabel('Reynolds Local ($Re_x$) [-]', fontsize=13)
plt.ylabel('Coeficiente de Atrito $C_f$ [-]', fontsize=13)
plt.xscale('log')
plt.yscale('log')

plt.xlim(1e4, 1e6)
plt.ylim(1e-3, 1.5e-2) 

plt.legend(loc='lower left', fontsize=10, frameon=True)
plt.tight_layout()
plt.savefig('04_Cf_vs_Re.png', dpi=200)
plt.close()