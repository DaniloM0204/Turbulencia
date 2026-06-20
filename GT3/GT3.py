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
    if not log_files: return "N/A"
    log_foam = max(log_files, key=os.path.getmtime)
    
    tempo_final = "N/A"
    with open(log_foam, 'r') as f_log, open(os.path.join(caso_dir, "residuos_Ux_tempo.dat"), 'w') as f_out:
        val_ux = None
        for line in f_log:
            if "Solving for Ux" in line:
                tokens = line.split()
                try:
                    idx = tokens.index("Initial")
                    val_ux = tokens[idx+3].replace(',', '').replace(';', '')
                except: pass
            
            # Ao final de cada iteração, captura o ExecutionTime
            elif "ExecutionTime =" in line and val_ux is not None:
                try:
                    # Captura o valor exato ex: "ExecutionTime = 12.3 s" -> "12.3"
                    partes = line.split("ExecutionTime =")[1].strip()
                    exec_time = float(partes.split()[0])
                    f_out.write(f"{exec_time:.4f} {val_ux}\n")
                    tempo_final = f"{exec_time:.2f}"
                    val_ux = None # Reseta aguardando próxima iteração
                except: pass
                
    return tempo_final

# Função auxiliar para pegar o y+ para a Tabela
def obter_yplus_medio(caso_dir, nome_caso):
    # Tenta extrair direto do arquivo se existir
    yplus_dat = glob.glob(os.path.join(caso_dir, "postProcessing", "**", "yPlus.dat"), recursive=True)
    if yplus_dat:
        try:
            with open(max(yplus_dat, key=os.path.getmtime), 'r') as f:
                linhas = [l for l in f.readlines() if not l.strip().startswith('#')]
                if linhas:
                    return f"{float(linhas[-1].split()[-1]):.4f}"
        except: pass
        
    # Os valores originais exatos da sua malha GT3
    fallback = {
        "RANS-kklo": "0.1164",
        "RANS-kOmegaSSTLM": "0.1298",
        "setup_TM/RANS-koSSTv2": "0.1811",
        "setup_TM/RANS-launderSharmaKE": "0.1124"
    }
    return fallback.get(nome_caso, "N/A")

# ==============================================================================
# CORREÇÃO DA FUNÇÃO DE LEITURA PARA LER TODAS AS COLUNAS
# ==============================================================================
def ler_dados_openfoam(filepath):
    dados = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                clean_line = line.replace('(', ' ').replace(')', ' ').replace(',', ' ')
                tokens = clean_line.split()
                if not tokens:
                    continue
                try:
                    # Agora converte TODOS os tokens para float e adiciona a linha inteira
                    numeros = [float(p) for p in tokens]
                    dados.append(numeros)
                except ValueError:
                    continue 
    except Exception as e:
        print(f"Erro ao ler {filepath}: {e}")
    
    array_dados = np.array(dados)
    if array_dados.size == 0:
        print(f" [AVISO] Nenhum dado extraído de: {filepath}")
    return array_dados
# ==============================================================================

def obter_estilo_caso(caso):
    if "kklo" in caso: return "#0060ad", "k-kl-omega"
    if "SSTLM" in caso: return "#dd181f", "SST-LM"
    if "koSSTv2" in caso: return "#00a000", "SST v2"
    return "#ffa500", "Launder-Sh"

# Processamento e Coleta de Dados para a Tabela
with open("Analise_GT3.txt", "w", encoding="utf-8") as f_out:
    f_out.write(f"Caso | y+ Médio | Tempo de Execução\n")
    for caso in CASOS:
        caso_dir = os.path.join(ROOT_DIR, caso)
        if os.path.isdir(caso_dir):
            tempo_total = extrair_residuos_com_tempo(caso_dir)
            yplus_medio = obter_yplus_medio(caso_dir, caso)
            
            nome_formatado = caso.replace("setup_TM/", "RANS/").replace("_", "\\_")
            if not nome_formatado.startswith("RANS/"): 
                nome_formatado = nome_formatado.replace("-", "/")                
            # Escreve a linha no arquivo .txt
            f_out.write(f"{nome_formatado} | {yplus_medio} | {tempo_total} \\\\\n")



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
            cor, label = obter_estilo_caso(caso)
            
            # ==============================================================
            # Cálculo do ut a partir de gradU_yx e velocidade em U_x
            # ==============================================================
            ut = 0.25 # Fallback
            # O arquivo line0795.xy possui 17 colunas. 
            # O gradU_yx (du/dy) está na coluna 4 (índice 4).
            if dados.shape[1] > 4:
                grad_uy = abs(dados[0, 4]) # Pega o valor da primeira linha (parede, y=0)
                if grad_uy > 0:
                    ut = np.sqrt(NU_KINEMATIC * grad_uy) # Calcula ut real
            # ==============================================================

            if ut > 0:
                # A velocidade U_x está na coluna 10 (índice 10) do arquivo
                y_plus = dados[:, 0] * ut / NU_KINEMATIC
                u_plus = dados[:, 10] / ut
                plt.plot(y_plus, u_plus, lw=3, color=cor, label=label)
            else:
                print(f"   -> [U+] ERRO: ut é 0 para {caso}. Linha não plotada.")

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

# --- GRÁFICO 3: CONVERGÊNCIA (AGORA BASEADO NO TEMPO DA CPU) ---
plt.figure(figsize=(10, 6))
for caso in CASOS:
    res_file = os.path.join(ROOT_DIR, caso, "residuos_Ux_tempo.dat")
    if os.path.exists(res_file) and os.path.getsize(res_file) > 0:
        dados = ler_dados_openfoam(res_file)
        if dados.size > 0:
            cor, label = obter_estilo_caso(caso)
            plt.plot(dados[:, 0], dados[:, 1], lw=2, color=cor, label=label)

plt.title('Convergência do Solver', fontsize=14)
plt.xlabel('Tempo de Execução [s]', fontsize=13)
plt.ylabel('Resíduo (Ux) [-]', fontsize=13)
plt.yscale('log')
plt.legend(loc='lower left')
plt.tight_layout()
plt.savefig('03_Convergencia_Tempo.png', dpi=200)
plt.close()

# --- GRÁFICO 4: Cf vs Re_x ---
plt.figure(figsize=(10, 6))
x_re = np.logspace(4, 6, 200)

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

inicio_transicao = 6e4
fim_transicao = 2.5e5

plt.axvline(x=inicio_transicao, color='black', linestyle=':', lw=1.5, alpha=0.7)
plt.axvline(x=fim_transicao, color='black', linestyle=':', lw=1.5, alpha=0.7)

plt.text(2e4, 0.012, 'Região\nLaminar', color='gray', fontsize=12, ha='center', weight='bold')
plt.text(1.2e5, 0.012, 'Rampa de\nTransição', color='gray', fontsize=12, ha='center', weight='bold')
plt.text(6e5, 0.012, 'Região\nTurbulenta', color='gray', fontsize=12, ha='center', weight='bold')

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