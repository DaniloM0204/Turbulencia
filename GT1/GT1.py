import os
import subprocess
import re
import numpy as np
import matplotlib.pyplot as plt

#! Limpeza e analise dos dados do GT1

def extrair_tempo_execucao(case_path):
    log_file = os.path.join(case_path, "log.foamRun")
    if not os.path.exists(log_file):
        return "N/A"
    try:
        with open(log_file, 'r') as f:
            for linha in reversed(f.readlines()):
                if "ExecutionTime" in linha:
                    return linha.strip().split("ExecutionTime = ")[1].split(" s")[0] + " s"
    except Exception:
        pass
    return "N/A"

def extrair_yplus(case_path, yplus_stdout):
    min_y = max_y = avg_y = "N/A"
    matches = re.findall(r'min:\s*([\d\.Ee\+\-]+)\s*max:\s*([\d\.Ee\+\-]+)\s*average:\s*([\d\.Ee\+\-]+)', yplus_stdout)
    if matches:
        return matches[-1]
    
    yplus_base = os.path.join(case_path, 'postProcessing', 'yPlus')
    if os.path.exists(yplus_base):
        tempos = sorted([d for d in os.listdir(yplus_base) if os.path.isdir(os.path.join(yplus_base, d))], key=float)
        if tempos:
            yplus_dat_path = os.path.join(yplus_base, tempos[-1], 'yPlus.dat')
            if os.path.exists(yplus_dat_path):
                with open(yplus_dat_path, 'r') as f:
                    linhas = [l for l in f.readlines() if not l.strip().startswith('#')]
                    if linhas:
                        dados = linhas[-1].split()
                        if len(dados) >= 4:
                            return dados[-3], dados[-2], dados[-1]
    return "N/A", "N/A", "N/A"

def processar_arquivo_sample(case_path, modelo_dir, case_label):
    output_dat = os.path.join(modelo_dir, f"dados_limpos_{case_label}.dat")
    base_sample = os.path.join(case_path, 'postProcessing', 'sampleDict0')
    
    if not os.path.exists(base_sample):
        return None

    tempos = sorted([d for d in os.listdir(base_sample) if os.path.isdir(os.path.join(base_sample, d))], key=float)
    if not tempos:
        return None

    pasta_final = os.path.join(base_sample, tempos[-1])
    xy_files = [f for f in os.listdir(pasta_final) if f.endswith('.xy')]
    if not xy_files:
        return None

    input_file = os.path.join(pasta_final, xy_files[0])
    with open(input_file, 'r') as fin, open(output_dat, 'w') as fout:
        for line in fin:
            if line.strip().startswith('#'):
                continue
            clean_line = line.replace('(', ' ').replace(')', ' ').replace(',', ' ')
            partes = clean_line.split()
            if len(partes) >= 2:
                try:
                    fout.write(f"{float(partes[0])}\t{float(partes[1])}\n")
                except ValueError:
                    pass
    return output_dat
# ==============================================================================

def executar_e_analisar_caso_gt1(case_path, f_analise):
    if not os.path.exists(case_path):
        return None

    root_dir = os.getcwd()
    case_label = case_path.replace("/", "_")
    modelo_dir = os.path.join(root_dir, "Resultados_Graficos_GT1", f"Resultado_{case_label}")
    os.makedirs(modelo_dir, exist_ok=True)

    try:
        log_run_path = os.path.join(case_path, "log.foamRun")
        post_path = os.path.join(case_path, "postProcessing")
        
        # Verifica se a simulação já foi executada anteriormente
        if not (os.path.exists(log_run_path) and os.path.exists(post_path)):
            print(f"[{case_path}] Construindo malha e calculando...")
            subprocess.run(['foamListTimes', '-rm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=case_path)
            subprocess.run(['blockMesh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, cwd=case_path)
            
            if "planar" not in case_path.lower():
                subprocess.run(['extrudeMesh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, cwd=case_path)
                subprocess.run(['createPatch', '-overwrite'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, cwd=case_path)

            with open(log_run_path, "w") as log_file:
                subprocess.run(['foamRun'], stdout=log_file, stderr=subprocess.STDOUT, check=True, cwd=case_path)

            cmd_base = ['foamPostProcess', '-solver', 'incompressibleFluid', '-latestTime']
            subprocess.run(cmd_base + ['-func', 'wallShearStress'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=case_path)
            yplus_proc = subprocess.run(cmd_base + ['-func', 'yPlus'], capture_output=True, text=True, cwd=case_path)
            yplus_out_stdout = yplus_proc.stdout
            subprocess.run(cmd_base + ['-func', 'sampleDict0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=case_path)
        else:
            print(f"[{case_path}] Simulação realizada, resgatando os dados...")
            yplus_out_stdout = ""

        tempo_exec = extrair_tempo_execucao(case_path)
        min_y, max_y, avg_y = extrair_yplus(case_path, yplus_out_stdout)

        f_analise.write(f"Modelo: {case_path}\n - Custo: {tempo_exec}\n - y+ Parede: Min {min_y} | Max {max_y} | Med {avg_y}\n - Tensão Cisalhante processada.\n---\n")
        
        output_dat = processar_arquivo_sample(case_path, modelo_dir, case_label)
        
        print(f"    [+] Concluído com sucesso.")
        return output_dat

    except Exception as e:
        f_analise.write(f"Modelo: {case_path}\n FALHA NUMERICA: {e}\n---\n")
        print(f"[{case_path}] Erro: {e}")
        return None

def plotar_resultados_gt1(dados_proc):
    base_graficos = "Resultados_Graficos_GT1"
    plt.style.use('seaborn-v0_8-whitegrid')

    if "laminar" in dados_proc and "turbulent_wedge" in dados_proc:
        dados_lam = np.loadtxt(dados_proc['laminar'])
        dados_turb = np.loadtxt(dados_proc['turbulent_wedge'])
        r_lam, v_lam = dados_lam[:, 0], dados_lam[:, 1]
        r_turb, v_turb = dados_turb[:, 0], dados_turb[:, 1]
        
        tem_planar = False
        if "turbulent_planar" in dados_proc:
            dados_planar = np.loadtxt(dados_proc['turbulent_planar'])
            r_planar, v_planar = dados_planar[:, 0], dados_planar[:, 1]
            tem_planar = True
        
        r_teorico = np.linspace(0, 0.1, 200)
        c1, c2, c3 = '#9400d3', '#009e73', '#d95f02'

        # 1. Comparativo Numérico
        plt.figure(figsize=(9, 6))
        plt.plot(r_lam, v_lam, marker='o', linestyle='-', color=c1, label='OpenFOAM - Solução Laminar')
        plt.plot(r_turb, v_turb, marker='o', linestyle='-', color=c2, label='OpenFOAM - Turbulento (Wedge)')
        if tem_planar:
            plt.plot(r_planar, v_planar, marker='o', markevery=30, linestyle='-', color=c3, label='OpenFOAM - Turbulento (Planar)')
        plt.title('Velocidade radial na saída', fontsize=14)
        plt.xlabel('Raio (r) [m]', fontsize=12)
        plt.ylabel('Velocidade radial [m/s]', fontsize=12)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(base_graficos, '01_Velocidade_Radial.png'), dpi=200)
        plt.close()

        # 2. Laminar vs Poiseuille
        v_poiseuille = 1.9865597264 * (1 - (r_teorico**2) / (0.1**2))
        plt.figure(figsize=(9, 6))
        plt.plot(r_lam, v_lam, marker='o', linestyle='', color=c1, label='OpenFOAM - Solução Laminar')
        plt.plot(r_teorico, v_poiseuille, linestyle='-', color=c2, lw=2, label='Solução Analítica (Poiseuille)')
        plt.title('Perfil laminar na saída', fontsize=14)
        plt.xlabel('Raio (r) [m]', fontsize=12)
        plt.ylabel('Velocidade radial [m/s]', fontsize=12)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(base_graficos, '02_Perfil_Laminar.png'), dpi=200)
        plt.close()

        # 3. Turbulento vs Power Law
        v_powerlaw = 1.26117411111 * (np.maximum(0, 1 - r_teorico/0.1))**(1./6.)
        plt.figure(figsize=(9, 6))
        plt.plot(r_teorico, v_powerlaw, marker='o', markevery=10, linestyle='-', color=c1, lw=2, label='Correlação Turbulenta (n=6)')
        plt.plot(r_turb, v_turb, marker='o', linestyle='-', color=c2, label='OpenFOAM - Turbulento (Wedge)')
        if tem_planar:
            plt.plot(r_planar, v_planar, marker='o', markevery=30, linestyle='-', color=c3, lw=2, label='OpenFOAM - Turbulento (Planar)')
        plt.title('Perfil turbulento na saída', fontsize=14)
        plt.xlabel('Raio (r) [m]', fontsize=12)
        plt.ylabel('Velocidade radial [m/s]', fontsize=12)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(base_graficos, '03_Perfil_Turbulento.png'), dpi=200)
        plt.close()

if __name__ == "__main__":
    CASES = ["laminar", "turbulent_planar", "turbulent_wedge"]
    dados_proc = {}

    with open("Analise_GT1.txt", "w") as f_analise:
        for case in CASES:
            dat = executar_e_analisar_caso_gt1(case, f_analise)
            if dat: 
                dados_proc[case] = dat

    plotar_resultados_gt1(dados_proc)