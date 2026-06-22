import os
import shutil
import subprocess
import re
import numpy as np
import matplotlib.pyplot as plt

def criar_variacao_Viscosidade(case_base, case_var):
    print(f"[*] Preparando variacao: {case_var}")
    if os.path.exists(case_var):
        shutil.rmtree(case_var)
    shutil.copytree(case_base, case_var)

    # Remove pastas de tempo antigas e pós-processamento para forcar recálculo
    for d in os.listdir(case_var):
        if d.replace('.', '').replace('-', '').isdigit() and float(d) != 0:
            caminho = os.path.join(case_var, d)
            if os.path.isdir(caminho):
                shutil.rmtree(caminho)
            
    path_post = os.path.join(case_var, "postProcessing")
    if os.path.exists(path_post):
        shutil.rmtree(path_post)
        
    for f in os.listdir(case_var):
        if f.startswith("log."):
            os.remove(os.path.join(case_var, f))

    # Aumenta viscosidade em 10x (transicao para quase laminar)
    modificado = False
    for prop_file in ["transportProperties", "physicalProperties"]:
        path_prop = os.path.join(case_var, "constant", prop_file)
        if os.path.exists(path_prop):
            with open(path_prop, 'r') as f:
                conteudo = f.read()
            
            novo = re.sub(r'\bnu\s+\[.*?\]\s+[\d\.\-eE]+;', 'nu              [0 2 -1 0 0 0 0] 1.5e-4;', conteudo)
            if novo == conteudo:
                novo = re.sub(r'\bnu\s+[\d\.\-eE]+;', 'nu              1.5e-4;', conteudo)
                
            if novo != conteudo:
                with open(path_prop, 'w') as f:
                    f.write(novo)
                modificado = True
                
    if modificado:
        print("    -> Sucesso: Viscosidade multiplicada por 10x.")
    else:
        print("    -> Aviso: Variavel 'nu' nao encontrada para alterar.")

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
        
        # Executa apenas se o log e o pos-processamento nao existirem
        if not (os.path.exists(log_run_path) and os.path.exists(post_path)):
            print(f"[*] Executando caso: {case_path}")
            
            # Malha (env=os.environ garante o ambiente OpenFOAM)
            env = os.environ
            if os.path.exists(os.path.join(case_path, "run_mesh.sh")):
                subprocess.run(['bash', 'run_mesh.sh'], cwd=case_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
            else:
                subprocess.run(['blockMesh'], cwd=case_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                if "planar" not in case_path.lower():
                    subprocess.run(['extrudeMesh'], cwd=case_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                    subprocess.run(['createPatch', '-overwrite'], cwd=case_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

            # Solver
            with open(log_run_path, "w") as log_file:
                if os.path.exists(os.path.join(case_path, "run_solver.sh")):
                    subprocess.run(['bash', 'run_solver.sh'], cwd=case_path, stdout=log_file, stderr=subprocess.STDOUT, env=env)
                else:
                    res = subprocess.run(['foamRun'], cwd=case_path, stdout=log_file, stderr=subprocess.STDOUT, env=env)
                    if res.returncode != 0:
                        subprocess.run(['simpleFoam'], cwd=case_path, stdout=log_file, stderr=subprocess.STDOUT, env=env)

            # Pos-processamento
            subprocess.run(['foamPostProcess', '-func', 'wallShearStress'], cwd=case_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
            yplus_proc = subprocess.run(['foamPostProcess', '-func', 'yPlus'], capture_output=True, text=True, cwd=case_path, env=env)
            yplus_out_stdout = yplus_proc.stdout
            subprocess.run(['foamPostProcess', '-func', 'sampleDict0'], cwd=case_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        else:
            print(f"[*] Poupando execucao de: {case_path}")
            yplus_out_stdout = ""

        tempo_exec = extrair_tempo_execucao(case_path)
        min_y, max_y, avg_y = extrair_yplus(case_path, yplus_out_stdout)

        f_analise.write(f"Modelo: {case_path}\n - Custo: {tempo_exec}\n - y+ Parede: Min {min_y} | Max {max_y} | Med {avg_y}\n---\n")
        
        output_dat = processar_arquivo_sample(case_path, modelo_dir, case_label)
        if output_dat is None:
            print(f"    -> Alerta: sampleDict nao extraido. Verifique log.")

        return output_dat

    except Exception as e:
        f_analise.write(f"Modelo: {case_path}\n FALHA NO SCRIPT: {e}\n---\n")
        return None

def plotar_resultados_gt1(dados_proc):
    base_graficos = "Resultados_Graficos_GT1"
    os.makedirs(base_graficos, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')

    if "laminar" in dados_proc and "turbulent_wedge" in dados_proc:
        dados_lam = np.loadtxt(dados_proc['laminar'])
        dados_turb = np.loadtxt(dados_proc['turbulent_wedge'])
        r_lam, v_lam = dados_lam[:, 0], dados_lam[:, 1]
        r_turb, v_turb = dados_turb[:, 0], dados_turb[:, 1]
        
        tem_planar = False
        if "turbulent_planar" in dados_proc and dados_proc['turbulent_planar']:
            dados_planar = np.loadtxt(dados_proc['turbulent_planar'])
            if dados_planar.size > 0:
                r_planar, v_planar = dados_planar[:, 0], dados_planar[:, 1]
                tem_planar = True
            
        tem_var = False
        if "turbulent_wedge_Viscoso" in dados_proc and dados_proc['turbulent_wedge_Viscoso']:
            dados_var = np.loadtxt(dados_proc['turbulent_wedge_Viscoso'])
            if dados_var.size > 0:
                r_var, v_var = dados_var[:, 0], dados_var[:, 1]
                tem_var = True
        
        r_teorico = np.linspace(0, 0.1, 200)
        c1, c2, c3, c4 = '#9400d3', '#009e73', '#d95f02', '#d62728'

        # Grafico 1
        plt.figure(figsize=(9, 6))
        plt.plot(r_lam, v_lam, marker='o', linestyle='-', color=c1, label='OpenFOAM - Laminar')
        plt.plot(r_turb, v_turb, marker='o', linestyle='-', color=c2, label='OpenFOAM - Turbulento Base')
        if tem_planar:
            plt.plot(r_planar, v_planar, marker='o', markevery=30, linestyle='-', color=c3, label='OpenFOAM - Turbulento (Planar)')
        if tem_var:
            plt.plot(r_var, v_var, marker='s', linestyle='--', color=c4, lw=2.5, label='OpenFOAM - Variacao (10x Viscoso)')
        
        plt.title('Velocidade radial na saida', fontsize=14)
        plt.xlabel('Raio (r) [m]', fontsize=12)
        plt.ylabel('Velocidade radial [m/s]', fontsize=12)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(base_graficos, '01_Velocidade_Radial.png'), dpi=200)
        plt.close()

        # Grafico 2
        v_poiseuille = 1.9865597264 * (1 - (r_teorico**2) / (0.1**2))
        plt.figure(figsize=(9, 6))
        plt.plot(r_lam, v_lam, marker='o', linestyle='', color=c1, label='OpenFOAM - Laminar')
        plt.plot(r_teorico, v_poiseuille, linestyle='-', color=c2, lw=2, label='Analitico (Poiseuille)')
        plt.title('Perfil laminar na saida', fontsize=14)
        plt.xlabel('Raio (r) [m]', fontsize=12)
        plt.ylabel('Velocidade radial [m/s]', fontsize=12)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(base_graficos, '02_Perfil_Laminar.png'), dpi=200)
        plt.close()

        # Grafico 3
        v_powerlaw = 1.26117411111 * (np.maximum(0, 1 - r_teorico/0.1))**(1./6.)
        plt.figure(figsize=(9, 6))
        plt.plot(r_teorico, v_powerlaw, marker='o', markevery=10, linestyle='-', color=c1, lw=2, label='Correlacao Turbulenta (n=6)')
        plt.plot(r_turb, v_turb, marker='o', linestyle='-', color=c2, label='OpenFOAM - Turbulento Base')
        if tem_planar:
            plt.plot(r_planar, v_planar, marker='o', markevery=30, linestyle='-', color=c3, lw=2, label='OpenFOAM - Turbulento (Planar)')
        if tem_var:
            plt.plot(r_var, v_var, marker='s', linestyle='--', color=c4, lw=2.5, label='OpenFOAM - Variacao (10x Viscoso)')
            
        plt.title('Perfil turbulento na saida', fontsize=14)
        plt.xlabel('Raio (r) [m]', fontsize=12)
        plt.ylabel('Velocidade radial [m/s]', fontsize=12)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(base_graficos, '03_Perfil_Turbulento.png'), dpi=200)
        plt.close()

if __name__ == "__main__":
    # Forca a destruicao e recriacao da variacao
    if os.path.exists("turbulent_wedge"):
        criar_variacao_Viscosidade("turbulent_wedge", "turbulent_wedge_Viscoso")

    CASES = ["laminar", "turbulent_planar", "turbulent_wedge", "turbulent_wedge_Viscoso"]
    dados_proc = {}

    with open("Analise_GT1.txt", "w") as f_analise:
        for case in CASES:
            dat = executar_e_analisar_caso_gt1(case, f_analise)
            if dat: 
                dados_proc[case] = dat

    plotar_resultados_gt1(dados_proc)
    print("\n[+] Analise finalizada. Graficos atualizados.")