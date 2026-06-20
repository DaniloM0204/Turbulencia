import os
import subprocess
import re
import numpy as np
import matplotlib.pyplot as plt

def executar_e_analisar_caso_gt1(case_path, f_analise):
    if not os.path.exists(case_path):
        return None

    root_dir = os.getcwd()
    case_label = case_path.replace("/", "_")
    modelo_dir = os.path.join(root_dir, "Resultados_Graficos_GT1", f"Resultado_{case_label}")
    os.makedirs(modelo_dir, exist_ok=True)

    try:
        os.chdir(case_path)
        output_dat = os.path.join(modelo_dir, f"dados_limpos_{case_label}.dat")
        yplus_out_stdout = ""

        # Se já simulado, puxa os dados; caso contrário, executa a simulação
        if os.path.exists("log.foamRun") and os.path.exists("postProcessing"):
            print(f"[{case_path}] Simulação realizada, resgatando os dados...")
        else:
            print(f"[{case_path}] Construindo malha e calculando (Isso pode demorar)...")
            subprocess.run(['foamListTimes', '-rm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['blockMesh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            # =========================================================================
            # CORREÇÃO: extrudeMesh e createPatch rodam APENAS se NÃO for o caso planar
            # =========================================================================
            if "planar" not in case_path.lower():
                subprocess.run(['extrudeMesh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                subprocess.run(['createPatch', '-overwrite'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            # =========================================================================

            with open("log.foamRun", "w") as log_file:
                subprocess.run(['foamRun'], stdout=log_file, stderr=subprocess.STDOUT, check=True)

            cmd_base = ['foamPostProcess', '-solver', 'incompressibleFluid', '-latestTime']
            subprocess.run(cmd_base + ['-func', 'wallShearStress'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            yplus_proc = subprocess.run(cmd_base + ['-func', 'yPlus'], capture_output=True, text=True)
            yplus_out_stdout = yplus_proc.stdout
            subprocess.run(cmd_base + ['-func', 'sampleDict0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Extração de métricas
        tempo_exec = "N/A"
        try:
            with open("log.foamRun", "r") as lf:
                for linha in reversed(lf.readlines()):
                    if "ExecutionTime" in linha:
                        tempo_exec = linha.strip().split("ExecutionTime = ")[1].split(" s")[0] + " s"
                        break
        except: pass

        min_y, max_y, avg_y = "N/A", "N/A", "N/A"
        matches = re.findall(r'min:\s*([\d\.Ee\+\-]+)\s*max:\s*([\d\.Ee\+\-]+)\s*average:\s*([\d\.Ee\+\-]+)', yplus_out_stdout)
        
        if matches:
            min_y, max_y, avg_y = matches[-1]
        else:
            # Busca os dados dentro da pasta gerada pelo utilitário yPlus 
            yplus_base = os.path.join('postProcessing', 'yPlus')
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
                                    min_y, max_y, avg_y = dados[-3], dados[-2], dados[-1]

        f_analise.write(f"Modelo: {case_path}\n - Custo: {tempo_exec}\n - y+ Parede: Min {min_y} | Max {max_y} | Med {avg_y}\n - Tensão Cisalhante processada.\n---\n")
        #Leitura e Limpeza Segura dos Dados (.xy -> .dat)
        base_sample = os.path.join('postProcessing', 'sampleDict0')
        if os.path.exists(base_sample):
            tempo_recente = sorted([d for d in os.listdir(base_sample) if os.path.isdir(os.path.join(base_sample, d))], key=float)[-1]
            pasta_final = os.path.join(base_sample, tempo_recente)
            xy_files = [f for f in os.listdir(pasta_final) if f.endswith('.xy')]
            
            if xy_files:
                input_file = os.path.join(pasta_final, xy_files[0])
                with open(input_file, 'r') as fin, open(output_dat, 'w') as fout:
                    for line in fin:
                        if not line.strip().startswith('#'):
                            clean_line = line.replace('(', ' ').replace(')', ' ').replace(',', ' ')
                            partes = clean_line.split()
                            if len(partes) >= 2:
                                try: fout.write(f"{float(partes[0])}\t{float(partes[1])}\n")
                                except ValueError: pass

        os.chdir(root_dir)
        print(f"    [+] Concluído com sucesso.")
        return output_dat

    except Exception as e:
        f_analise.write(f"Modelo: {case_path}\n FALHA NUMERICA: {e}\n---\n")
        os.chdir(root_dir)
        print(f"[{case_path}] Erro: {e}")
        return None

if __name__ == "__main__":
    CASES = ["laminar","turbulent_planar", "turbulent_wedge"]
    dados_proc = {}
    
    print("=== INICIANDO WORKFLOW COMPLETO DO GT1 ===")
    with open("Analise_GT1.txt", "w") as f_analise:
        f_analise.write("=== RELATÓRIO TÉCNICO GT1 ===\n")
        
        for case in CASES:
            dat = executar_e_analisar_caso_gt1(case, f_analise)
            if dat: dados_proc[case] = dat

        f_analise.write("\n=== ANÁLISE CRÍTICA: WEDGE VS PLANAR ===\n")
        f_analise.write("A condição 'wedge' resolve equações em coordenadas cilíndricas assumindo axi-simetria.\n")
        f_analise.write("Isso capta a física 3D de um tubo circular com custo computacional quasi-1D, \n")
        f_analise.write("sendo superior em fidelidade à condição planar, que simula escoamento entre placas paralelas.\n")

    # Plot do pos-processamento
    base_graficos = "Resultados_Graficos_GT1"
    plt.style.use('seaborn-v0_8-whitegrid')

if "laminar" in dados_proc and "turbulent_wedge" in dados_proc:
        
        # Carregando os dados originais
        dados_lam = np.loadtxt(dados_proc['laminar'])
        dados_turb = np.loadtxt(dados_proc['turbulent_wedge'])
        r_lam, v_lam = dados_lam[:, 0], dados_lam[:, 1]
        r_turb, v_turb = dados_turb[:, 0], dados_turb[:, 1]
        
        tem_planar = False
        if "turbulent_planar" in dados_proc:
            dados_planar = np.loadtxt(dados_proc['turbulent_planar'])
            r_planar, v_planar = dados_planar[:, 0], dados_planar[:, 1]
            tem_planar = True
        
        # Eixo radial teórico universal
        r_teorico = np.linspace(0, 0.1, 200)

        # Cores padrão
        c1 = '#9400d3'
        c2 = '#009e73'
        c3 = '#d95f02'

        # --- Comparativo Numérico ---
        plt.figure(figsize=(9, 6))
        plt.plot(r_lam, v_lam, marker='o', linestyle='-', color=c1, label='OpenFOAM - Solução Laminar')
        plt.plot(r_turb, v_turb, marker='o', linestyle='-', color=c2, label='OpenFOAM - Turbulento (Wedge)')
        if tem_planar:
            plt.plot(r_planar, v_planar, marker='^', linestyle='--', color=c3, label='OpenFOAM - Turbulento (Planar)')
        
        plt.title('Velocidade radial na saída', fontsize=14)
        plt.xlabel('Raio (r) [m]', fontsize=12)
        plt.ylabel('Velocidade radial [m/s]', fontsize=12)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(base_graficos, '01_Velocidade_Radial.png'), dpi=200)
        plt.close()

        # --- Laminar vs Poiseuille ---
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

        # --- Turbulento vs Power Law ---
        v_powerlaw = 1.26117411111 * (np.maximum(0, 1 - r_teorico/0.1))**(1./6.)
        
        plt.figure(figsize=(9, 6))
        plt.plot(r_teorico, v_powerlaw, linestyle='-', color=c1, lw=2, label='Correlação Turbulenta (n=6)')
        plt.plot(r_turb, v_turb, marker='o', linestyle='-', color=c2, label='OpenFOAM - Turbulento (Wedge)')
        if tem_planar:
            plt.plot(r_planar, v_planar, marker='^', linestyle='--', color=c3, label='OpenFOAM - Turbulento (Planar)')
        
        plt.title('Perfil turbulento na saída', fontsize=14)
        plt.xlabel('Raio (r) [m]', fontsize=12)
        plt.ylabel('Velocidade radial [m/s]', fontsize=12)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(base_graficos, '03_Perfil_Turbulento.png'), dpi=200)
        plt.close()