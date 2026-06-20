import glob
import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt

# Constantes
U_INF = 1.0
NU = 1.5e-5
RHO = 1.0
UTAU_REF = 0.045

CASOS_RANS = [
    "RANS/KOmegaSST_highRE", "RANS/KOmegaSST_lowRE_V1", 
    "RANS/KEpsilon_highRE_V1", "RANS/KEpsilon_lowRE_V1", "RANS/SA_LRN"
]
CASOS_SRS = ["SRS/DES_KO_LRN", "SRS/LES-WALE_LRN"]
TODOS_CASOS = CASOS_RANS + CASOS_SRS

CORES = ['#0060ad', '#dd181f', '#00a000', '#ffa500', '#8a2be2', '#ff1493', '#00ffff']

def ler_openfoam_blindado(caminho):
    dados = []
    try:
        with open(caminho, 'r') as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith('#') or linha.startswith('Time'):
                    continue
                
                limpa = linha.replace('(', ' ').replace(')', ' ').replace(',', ' ')
                partes = limpa.split()
                try:
                    numeros = [float(p) for p in partes]
                    if numeros: dados.append(numeros)
                except ValueError:
                    continue 
    except Exception as e:
        print(f"      [Erro de Leitura] {e}")
    return np.array(dados)

def gerar_analise_gt2():
    with open("Analise_GT2.txt", "w") as rel:
        rel.write(f"{'Caso':<50} | {'y+ Médio':<12} | {'Tempo de Execução':<20}\n")
        rel.write("-" * 90 + "\n")
        
        for caso in TODOS_CASOS:
            if not os.path.exists(f"{caso}/postProcessing"):
                print(f"Nao encontrado dados de postProcessing de {caso}")
                continue
            
            tempo = "N/A"
            logs = glob.glob(f"{caso}/log*")
            if logs:
                log_mais_recente = max(logs, key=os.path.getmtime)
                try:
                    with open(log_mais_recente, 'r') as f:
                        for l in reversed(f.readlines()):
                            if "ExecutionTime" in l or "ClockTime" in l:
                                partes = l.split()
                                if len(partes) >= 3:
                                    tempo = f"{partes[2]}s"
                                    break
                except Exception:
                    pass
                    
            yplus = "N/A"
            yplus_arquivos = glob.glob(os.path.join(caso, "postProcessing", "yplus_stats", "**", "yPlus.dat"), recursive=True)
            if yplus_arquivos:
                yplus_arquivo = max(yplus_arquivos, key=os.path.getmtime)
                try:
                    with open(yplus_arquivo, 'r') as f:
                        for l in reversed(f.readlines()):
                            l = l.strip()
                            if not l or l.startswith('#'):
                                continue
                            partes = l.split()
                            if len(partes) > 0:
                                try:
                                    yplus = f"{float(partes[-1]):.4f}"
                                    break
                                except ValueError:
                                    pass
                except Exception:
                    pass
            else:
                print(f"Arquivo yPlus.dat não encontrado em {caso}/postProcessing/yplus_stats.")

            rel.write(f"{caso:<50} | {yplus:<12} | {tempo:<20}\n")

def gerar_graficos_gt2():
    plt.style.use('seaborn-v0_8-whitegrid')

    fig1, ax1 = plt.subplots(figsize=(10, 6))
    ax1.set_title("Perfil Adimensional de Velocidade ($u^+$ vs $y^+$)", fontsize=14)
    ax1.set_xlabel("$y^+$ (Distância adimensional da parede)", fontsize=12)
    ax1.set_ylabel("$u^+$ (Velocidade adimensional)", fontsize=12)
    ax1.set_xscale('log')
    ax1.set_xlim(1e-2, 1e5)
    ax1.set_ylim(0, 30)

    y_sub = np.linspace(1e-2, 11.6, 100)
    ax1.plot(y_sub, y_sub, 'k--', linewidth=2, label='Subcamada Viscosa ($u^+ = y^+$)')
    y_log = np.linspace(11.6, 1e5, 100)
    ax1.plot(y_log, (1.0/0.41)*np.log(y_log) + 5.2, 'k-', linewidth=2, label='Lei Logarítmica')

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.set_title("Coeficiente de Atrito Local $C_f$ vs Comprimento da Placa", fontsize=14)
    ax2.set_xlabel("Comprimento da placa $x$ [m]", fontsize=12)
    ax2.set_ylabel("Coeficiente de Atrito Local ($C_f$)", fontsize=12)
    ax2.set_xlim(0, 2)
    ax2.set_ylim(0, 0.014)

    x_teorico = np.linspace(1e-3, 2.0, 500)
    Re_x = (x_teorico * U_INF) / NU
    ax2.plot(x_teorico, 0.664 / np.sqrt(Re_x), 'k--', linewidth=2, label='Laminar (Blasius)')
    ax2.plot(x_teorico, 0.0592 / (Re_x**0.2), 'k-', linewidth=2, label='Turbulento (Prandtl)')

    fig3, ax3 = plt.subplots(figsize=(8, 8))
    ax3.set_title("Perfil de Velocidade na Camada Limite", fontsize=14)
    ax3.set_xlabel("Velocidade Adimensional (U/U_inf)", fontsize=12)
    ax3.set_ylabel("Distância da parede y [m]", fontsize=12)
    ax3.set_xlim(0, 1.2)
    ax3.set_ylim(0, 0.1)

    idx_cor = 0
    for caso in TODOS_CASOS:
        nome_curto = caso.split('/')[-1]
        
        if not os.path.exists(f"{caso}/postProcessing"):
            continue

        sample_dir = os.path.join(caso, "postProcessing", "sampleDict")
        arq_tau = None
        tau_valido = False
        ultimo_tempo_str = ""
        x_coords = None
        tau_mag = None

        if os.path.exists(sample_dir):
            tempos = []
            for d in os.listdir(sample_dir):
                if os.path.isdir(os.path.join(sample_dir, d)):
                    try: tempos.append((float(d), d))
                    except ValueError: pass
            
            if tempos:
                ultimo_tempo_str = sorted(tempos)[-1][1]
                dir_alvo = os.path.join(sample_dir, ultimo_tempo_str)
                
                caminho_profile1 = os.path.join(dir_alvo, "profile1.xy")
                if os.path.exists(caminho_profile1):
                    arq_tau = caminho_profile1

        if arq_tau:
            data_tau = ler_openfoam_blindado(arq_tau)
            if len(data_tau) > 0 and data_tau.shape[1] >= 7:
                x_coords = data_tau[:, 0] - 0.1
                tau_mag = np.linalg.norm(data_tau[:, 4:7], axis=1)
                tau_dinamico = tau_mag * RHO
                Cf = tau_dinamico / (0.5 * RHO * U_INF**2)
                mask = x_coords > 0.001
                ax2.plot(x_coords[mask], Cf[mask], color=CORES[idx_cor], linewidth=2.5, label=nome_curto)
                tau_valido = True

        arq_u = None
        u_mag = None
        y_coord = None

        if ultimo_tempo_str:
            dir_alvo = os.path.join(sample_dir, ultimo_tempo_str)
            caminho_profile0 = os.path.join(dir_alvo, "profile0.xy")
            if os.path.exists(caminho_profile0):
                arq_u = caminho_profile0
        
        if arq_u:
            data_u = ler_openfoam_blindado(arq_u)
            if len(data_u) > 0 and data_u.shape[1] >= 4:
                y_coord = np.abs(data_u[:, 0] - np.min(data_u[:, 0]))
                u_mag = np.linalg.norm(data_u[:, 1:4], axis=1)
                
                if tau_valido and x_coords is not None:
                    x_prof = 1.90334 
                    idx_closest = np.argmin(np.abs(x_coords - x_prof))
                    u_tau = np.sqrt(tau_mag[idx_closest])
                else:
                    u_tau = UTAU_REF
                
                y_plus = (y_coord * u_tau) / NU
                u_plus = u_mag / u_tau
                
                mask_u = y_plus > 1e-3
                ax1.axvline(x=5, color='gray', linestyle='--', linewidth=1, alpha=0.7)
                ax1.axvline(x=30, color='gray', linestyle='--', linewidth=1, alpha=0.7)
                ax1.plot(y_plus[mask_u], u_plus[mask_u], color=CORES[idx_cor], linewidth=2.5, label=nome_curto)

        if u_mag is not None and y_coord is not None:
            ax3.plot(u_mag / U_INF, y_coord, color=CORES[idx_cor], linewidth=2.5, label=nome_curto)

        idx_cor = (idx_cor + 1) % len(CORES)

    ax1.legend(loc='lower right', frameon=True)
    fig1.tight_layout()
    fig1.savefig("GT2_01_Lei_da_Parede.png", dpi=300)

    ax2.legend(loc='upper right', frameon=True)
    fig2.tight_layout()
    fig2.savefig("GT2_02_Cf_Validacao.png", dpi=300)

    ax3.legend(loc='upper left', frameon=True)
    fig3.savefig("GT2_03_Perfil_Camada_Limite.png", dpi=300)

if __name__ == "__main__":
    subprocess.run("find . -name '*.sh' -exec sed -i 's/\\r$//' {} \\;", shell=True, stderr=subprocess.DEVNULL)
    gerar_analise_gt2()
    gerar_graficos_gt2()