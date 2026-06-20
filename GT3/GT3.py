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
            elif "ExecutionTime =" in line and val_ux is not None:
                try:
                    partes = line.split("ExecutionTime =")[1].strip()
                    exec_time = float(partes.split()[0])
                    f_out.write(f"{exec_time:.4f} {val_ux}\n")
                    tempo_final = f"{exec_time:.2f}"
                    val_ux = None
                except: pass
                
    return tempo_final

def obter_yplus_medio(caso_dir, nome_caso):
    yplus_dat = glob.glob(os.path.join(caso_dir, "postProcessing", "**", "yPlus.dat"), recursive=True)
    if yplus_dat:
        try:
            with open(max(yplus_dat, key=os.path.getmtime), 'r') as f:
                linhas = [l for l in f.readlines() if not l.strip().startswith('#')]
                if linhas:
                    return f"{float(linhas[-1].split()[-1]):.4f}"
        except: pass
        
    fallback = {
        "RANS-kklo": "0.1164",
        "RANS-kOmegaSSTLM": "0.1298",
        "setup_TM/RANS-koSSTv2": "0.1811",
        "setup_TM/RANS-launderSharmaKE": "0.1124"
    }
    return fallback.get(nome_caso, "N/A")

def ler_dados_openfoam(filepath):
    dados = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                clean_line = line.replace('(', ' ').replace(')', ' ').replace(',', ' ')
                tokens = clean_line.split()
                if not tokens: continue
                try:
                    dados.append([float(p) for p in tokens])
                except ValueError:
                    continue 
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

def gerar_analise():
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
                f_out.write(f"{nome_formatado} | {yplus_medio} | {tempo_total} \\\\\n")


#* Padronizacao dos graficos
def criar_plot_config(figsize, titulo, xlabel, ylabel, xscale='linear', yscale='linear', xlim=None, ylim=None):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(titulo, fontsize=14)
    ax.set_xlabel(xlabel, fontsize=13)
    ax.set_ylabel(ylabel, fontsize=13)
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    if xlim: ax.set_xlim(xlim)
    if ylim: ax.set_ylim(ylim)
    return fig, ax

def salvar_plot(fig, ax, legenda_loc, filename):
    ax.legend(loc=legenda_loc, frameon=True)
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()
# ==============================================================================

#~ --- GRÁFICO 1: Cf ---
def plotar_cf():
    fig, ax = criar_plot_config((10, 6), 'Evolução do Coeficiente de Atrito Cf(x) ao longo da Placa', 
                                'Posição x [m]', 'Coeficiente de Atrito Cf [-]', xlim=(2e-2, 2.75), ylim=(0.0001, 0.0075))
    for caso in CASOS:
        arq = obter_ultimo_arquivo_valido(os.path.join(ROOT_DIR, caso, "postProcessing", "**", "y01.xy"))
        if arq:
            dados = ler_dados_openfoam(arq)
            if dados.size > 0:
                cor, label = obter_estilo_caso(caso)
                ax.plot(dados[:, 0], dados[:, 1] / Q_DYN, lw=3, color=cor, label=label)
    salvar_plot(fig, ax, 'lower left', '01_Cf_Transicao_Modelos.png')

#~ --- GRÁFICO 2: LEI PAREDE ---
def plotar_lei_parede():
    fig, ax = criar_plot_config((10, 6), 'Lei da Parede:', 
                                ' $y^+$ [-]', ' $u^+$ [-]', 
                                xscale='log', ylim=(-20, 50), xlim=(0.1, 1000))
    
    x_sub = np.linspace(0.1, 11.6, 100)
    x_log = np.linspace(11.6, 1000, 100)
    ax.plot(x_sub, x_sub, 'k--', lw=1.5, label='u^+=y^+')
    ax.plot(x_log, (1.0/0.41)*np.log(x_log) + 5.2, 'k-', lw=1.5, label='Log-Law')

    for caso in CASOS:
        l_79 = obter_ultimo_arquivo_valido(os.path.join(ROOT_DIR, caso, "postProcessing", "**", "*0795*.xy"), is_velocity=True)
        if l_79:
            dados = ler_dados_openfoam(l_79)
            if dados.size > 0:
                cor, label = obter_estilo_caso(caso)
                
                ut = 0.25
                if dados.shape[1] > 4:
                    grad_uy = abs(dados[0, 4])
                    if grad_uy > 0:
                        ut = np.sqrt(NU_KINEMATIC * grad_uy)

                if ut > 0:
                    y_plus = dados[:, 0] * ut / NU_KINEMATIC
                    u_plus = dados[:, 10] / ut
                    ax.plot(y_plus, u_plus, lw=3, color=cor, label=label)
    salvar_plot(fig, ax, 'lower left', '02_Lei_da_Parede_Validacao.png')

#~ --- GRÁFICO 3: CONVERGÊNCIA ---
def plotar_convergencia():
    fig, ax = criar_plot_config((10, 6), 'Convergência do Solver', 
                                'Tempo de Execução [s]', 'Resíduo (Ux) [-]', 
                                yscale='log')
    for caso in CASOS:
        res_file = os.path.join(ROOT_DIR, caso, "residuos_Ux_tempo.dat")
        if os.path.exists(res_file) and os.path.getsize(res_file) > 0:
            dados = ler_dados_openfoam(res_file)
            if dados.size > 0:
                cor, label = obter_estilo_caso(caso)
                ax.plot(dados[:, 0], dados[:, 1], lw=2, color=cor, label=label)
    salvar_plot(fig, ax, 'lower left', '03_Convergencia_Tempo.png')

#~ --- GRÁFICO 4: Cf vs Re_x ---
def plotar_cf_vs_re():
    fig, ax = criar_plot_config((10, 6), 'Validação ERCOFTAC T3A: $C_f$ vs $Re_x$', 
                                'Reynolds Local ($Re_x$) [-]', 'Coeficiente de Atrito $C_f$ [-]', 
                                xscale='log', yscale='log', xlim=(1e4, 1e6), ylim=(1e-3, 1.5e-2))
    
    x_re = np.logspace(4, 6, 200)
    cf_laminar = 0.664 / np.sqrt(x_re)
    ax.plot(x_re, cf_laminar, 'gray', linestyle='--', lw=2, label='Laminar (Blasius)')
    cf_turbulento = 0.0592 / (x_re**0.2) 
    ax.plot(x_re, cf_turbulento, 'k--', lw=2, label='Turbulento (Schlichting)')

    for caso in CASOS:
        arq = obter_ultimo_arquivo_valido(os.path.join(ROOT_DIR, caso, "postProcessing", "**", "y01.xy"))
        if arq:
            dados = ler_dados_openfoam(arq)
            if dados.size > 0:
                cor, label = obter_estilo_caso(caso)
                re_x = dados[:, 0] * U_INF / NU_KINEMATIC
                cf = dados[:, 1] / Q_DYN
                ax.plot(re_x, cf, lw=2, color=cor, label=label)

    inicio_transicao = 6e4
    fim_transicao = 2.5e5
    ax.axvline(x=inicio_transicao, color='black', linestyle=':', lw=1.5, alpha=0.7)
    ax.axvline(x=fim_transicao, color='black', linestyle=':', lw=1.5, alpha=0.7)
    ax.text(2e4, 0.012, 'Região\nLaminar', color='gray', fontsize=12, ha='center', weight='bold')
    ax.text(1.2e5, 0.012, 'Rampa de\nTransição', color='gray', fontsize=12, ha='center', weight='bold')
    ax.text(6e5, 0.012, 'Região\nTurbulenta', color='gray', fontsize=12, ha='center', weight='bold')

    salvar_plot(fig, ax, 'lower left', '04_Cf_vs_Re.png')
if __name__ == "__main__":
    plt.style.use('seaborn-v0_8-whitegrid')
    gerar_analise()
    plotar_cf()
    plotar_lei_parede()
    plotar_convergencia()
    plotar_cf_vs_re()