import os
import subprocess
import re

# --- CHAVE DE CONTROLE ---
RODAR_SIMULACAO = True 

def executar_e_analisar_caso_gt3(case_path, f_analise):
    if not os.path.exists(case_path): return None

    root_dir = os.getcwd()
    case_label = case_path.replace("/", "_").replace("-", "_")
    modelo_dir = os.path.join(root_dir, "Resultados_Graficos_GT3", f"Resultado_{case_label}")
    os.makedirs(modelo_dir, exist_ok=True)

    try:
        os.chdir(case_path)
        
        if RODAR_SIMULACAO:
            print(f"[{case_path}] Rodando simulação...")
            subprocess.run(['foamListTimes', '-rm'], stdout=subprocess.DEVNULL)
            subprocess.run(['blockMesh'], stdout=subprocess.DEVNULL, check=True)
            with open("log.foamRun", "w") as log_file:
                subprocess.run(['foamRun'], stdout=log_file, stderr=subprocess.STDOUT, check=True)

        # 2. Pós-processamento
        cmd_base = ['foamPostProcess', '-solver', 'incompressibleFluid', '-latestTime']
        subprocess.run(cmd_base + ['-func', 'wallShearStress'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        yplus_out = subprocess.run(cmd_base + ['-func', 'yPlus', '-latestTime'], capture_output=True, text=True)
        subprocess.run(cmd_base + ['-func', 'sampleDict'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. Métricas
        avg_y = "N/A"
        matches = re.findall(r'average:\s*([\d\.Ee\+\-]+)', yplus_out.stdout)
        if matches: avg_y = matches[-1]
        f_analise.write(f"Modelo: {case_path} | y+ (Med): {avg_y}\n")

        # 4. Extração do Coeficiente de Atrito (Cf) com Filtro Robusto
        output_cf = os.path.join(modelo_dir, "dados_cf.dat")
        base_sample = 'postProcessing/sampleDict'
        if not os.path.exists(base_sample): base_sample = 'postProcessing/sampleDict0'
        
        if os.path.exists(base_sample):
            tempos = [d for d in os.listdir(base_sample) if os.path.isdir(os.path.join(base_sample, d))]
            if tempos:
                tempo_recente = sorted(tempos, key=float)[-1]
                pasta_final = os.path.join(base_sample, tempo_recente)
                file_cf = next((f for f in os.listdir(pasta_final) if 'wall' in f.lower() or 'shear' in f.lower()), None)
                
                if file_cf:
                    with open(os.path.join(pasta_final, file_cf), 'r') as fin, open(output_cf, 'w') as fout:
                        for line in fin:
                            # Filtro: ignora linhas com texto, parênteses ou vazias
                            if any(c in line for c in ['#', '(', ')', 'bottom', 'top', 'patch']): continue
                            p = line.split()
                            if len(p) >= 2:
                                try:
                                    # Validação explícita de float
                                    x = float(p[0])
                                    tau = float(p[1])
                                    fout.write(f"{x}\t{abs(tau) / (0.5 * 5.4**2)}\n")
                                except ValueError:
                                    continue
        
        os.chdir(root_dir)
        return output_cf if os.path.exists(output_cf) else None

    except Exception as e:
        os.chdir(root_dir)
        print(f"Erro em {case_path}: {e}")
        return None

if __name__ == "__main__":
    CASES = ["RANS-kklo", "RANS-kOmegaSSTLM", "setup_TM/RANS-koSSTv2", "setup_TM/RANS-launderSharmaKE"]
    dados_proc = {}
    
    with open("Analise_GT3.txt", "w") as f_analise:
        for case in CASES:
            dat = executar_e_analisar_caso_gt3(case, f_analise)
            if dat: dados_proc[case] = dat

    if len(dados_proc) >= 2:
        base_graficos = "Resultados_Graficos_GT3"
        os.makedirs(base_graficos, exist_ok=True)
        script = os.path.join(base_graficos, "plot_comp.gp")
        with open(script, 'w') as f:
            f.write(f"set terminal pngcairo size 900,600 font 'Arial,12'\n")
            f.write(f"set output '{os.path.join(base_graficos, 'Comparativo_Cf_x.png')}'\n")
            f.write("set title 'Coeficiente de Atrito Local: Transição vs Turbulento'\n")
            f.write("set xlabel 'Posição (x) [m]'; set ylabel 'Cf'; set grid\nplot ")
            plots = [f"'{path}' w l title '{name}'" for name, path in dados_proc.items()]
            f.write(", ".join(plots))
        subprocess.run(['gnuplot', script])
        os.remove(script)
        
    print("\n[+] Processamento concluído.")