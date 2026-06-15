import os
import subprocess
import re

def executar_e_analisar_caso_gt1(case_path, f_analise):
    if not os.path.exists(case_path):
        return None

    root_dir = os.getcwd()
    case_label = case_path.replace("/", "_")
    modelo_dir = os.path.join(root_dir, "Resultados_Graficos_GT1", f"Resultado_{case_label}")
    os.makedirs(modelo_dir, exist_ok=True)

    try:
        os.chdir(case_path)
        print(f"[{case_path}] Construindo malha e calculando (Isso pode demorar)...")

        # 1. Limpeza, Malha (com extrusão para duto) e Execução
        subprocess.run(['foamListTimes', '-rm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['blockMesh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(['extrudeMesh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(['createPatch', '-overwrite'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        with open("log.foamRun", "w") as log_file:
            subprocess.run(['foamRun'], stdout=log_file, stderr=subprocess.STDOUT, check=True)

        # 2. Pós-processamento Nativo
        cmd_base = ['foamPostProcess', '-solver', 'incompressibleFluid', '-latestTime']
        subprocess.run(cmd_base + ['-func', 'wallShearStress'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        yplus_out = subprocess.run(cmd_base + ['-func', 'yPlus'], capture_output=True, text=True)
        subprocess.run(cmd_base + ['-func', 'sampleDict0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. Extração de métricas para Analise_GT1.txt
        tempo_exec = "N/A"
        try:
            with open("log.foamRun", "r") as lf:
                for linha in reversed(lf.readlines()):
                    if "ExecutionTime" in linha:
                        tempo_exec = linha.strip().split("ExecutionTime = ")[1].split(" s")[0] + " s"
                        break
        except: pass

        # Filtro Regex corrigido (sem \E) e com mecanismo de Fallback (leitura do arquivo .dat)
        min_y, max_y, avg_y = "N/A", "N/A", "N/A"
        matches = re.findall(r'min:\s*([\d\.Ee\+\-]+)\s*max:\s*([\d\.Ee\+\-]+)\s*average:\s*([\d\.Ee\+\-]+)', yplus_out.stdout)
        
        if matches:
            min_y, max_y, avg_y = matches[-1]
        else:
            # Plano B: Busca os dados dentro da pasta gerada pelo utilitário yPlus
            yplus_dat_path = os.path.join('postProcessing', 'yPlus', '0', 'yPlus.dat')
            if os.path.exists(yplus_dat_path):
                with open(yplus_dat_path, 'r') as f:
                    linhas = f.readlines()
                    if len(linhas) > 1: # Garante que tem dados além do cabeçalho
                        dados = linhas[-1].split()
                        if len(dados) >= 4:
                            min_y, max_y, avg_y = dados[-3], dados[-2], dados[-1]

        f_analise.write(f"Modelo: {case_path}\n - Custo: {tempo_exec}\n - y+ Parede: Min {min_y} | Max {max_y} | Med {avg_y}\n - Tensão Cisalhante processada.\n---\n")

        # 4. Leitura e Limpeza dos Dados (.xy -> .dat)
        base_sample = os.path.join('postProcessing', 'sampleDict0')
        tempo_recente = sorted([d for d in os.listdir(base_sample) if os.path.isdir(os.path.join(base_sample, d))], key=float)[-1]
        pasta_final = os.path.join(base_sample, tempo_recente)
        input_file = os.path.join(pasta_final, [f for f in os.listdir(pasta_final) if f.endswith('.xy')][0])
        
        os.chdir(root_dir)
        output_dat = os.path.join(modelo_dir, f"dados_limpos_{case_label}.dat")
        
        with open(os.path.join(case_path, input_file), 'r') as fin, open(output_dat, 'w') as fout:
            for line in fin:
                if not line.strip().startswith(('#', '(', ')')):
                    partes = line.split()
                    if len(partes) >= 2:
                        try: fout.write(f"{float(partes[0])}\t{float(partes[1])}\n")
                        except ValueError: pass

        print(f"    [+] Concluído com sucesso.")
        return output_dat

    except Exception as e:
        f_analise.write(f"Modelo: {case_path}\n FALHA NUMERICA: {e}\n---\n")
        os.chdir(root_dir)
        print(f"[{case_path}] Erro: {e}")
        return None


if __name__ == "__main__":
    CASES = ["laminar", "turbulent_wedge"]
    dados_proc = {}
    
    print("=== INICIANDO WORKFLOW COMPLETO DO GT1 ===")
    with open("Analise_GT1.txt", "w") as f_analise:
        f_analise.write("=== RELATÓRIO TÉCNICO GT1 ===\n")
        
        for case in CASES:
            dat = executar_e_analisar_caso_gt1(case, f_analise)
            if dat: dados_proc[case] = dat

        # Discussão Teórica Solicitada no T1.pdf
        f_analise.write("\n=== ANÁLISE CRÍTICA: WEDGE VS PLANAR ===\n")
        f_analise.write("A condição 'wedge' resolve equações em coordenadas cilíndricas assumindo axi-simetria.\n")
        f_analise.write("Isso capta a física 3D de um tubo circular com custo computacional quasi-1D, \n")
        f_analise.write("sendo superior em fidelidade à condição planar, que simula escoamento entre placas paralelas.\n")

    # =========================================================
    # GERAÇÃO DOS 3 GRÁFICOS SOLICITADOS NO GNUPLOT
    # =========================================================
    base_graficos = "Resultados_Graficos_GT1"

    if "laminar" in dados_proc and "turbulent_wedge" in dados_proc:
        
        # Gráfico 1: Comparativo Numérico (Laminar vs Turbulento)
        script1 = os.path.join(base_graficos, "01_Radial_Velocity.gp")
        with open(script1, 'w') as f:
            f.write(f"set terminal pngcairo size 800,600 font 'Arial,12'\nset output '{os.path.join(base_graficos, '01_Velocidade_Radial.png')}'\n")
            f.write("set title 'Velocidade radial na saída'\nset xlabel 'Raio (r)'\nset ylabel 'Velocidade radial'\nset grid\n")
            f.write(f"plot '{dados_proc['laminar']}' u 1:2 w lp pt 7 title 'OpenFOAM - Solução Laminar', \\\n")
            f.write(f"     '{dados_proc['turbulent_wedge']}' u 1:2 w lp pt 7 title 'OpenFOAM - Solução Turbulenta'\n")
        subprocess.run(['gnuplot', script1])
        os.remove(script1)

        # Gráfico 2: Laminar Numérico vs Poiseuille Analítico
        script2 = os.path.join(base_graficos, "02_Laminar_Profile.gp")
        with open(script2, 'w') as f:
            f.write(f"set terminal pngcairo size 800,600 font 'Arial,12'\nset output '{os.path.join(base_graficos, '02_Perfil_Laminar.png')}'\n")
            f.write("set title 'Perfil laminar na saída'\nset xlabel 'Raio (r)'\nset ylabel 'Velocidade radial'\nset grid\n")
            f.write(f"plot '{dados_proc['laminar']}' u 1:2 w p pt 7 title 'OpenFOAM - Solução Laminar', \\\n")
            f.write(f"     1.9865597264*(1-x**2/(0.1)**2) title 'Solução Analítica (Poiseuille)'\n")
        subprocess.run(['gnuplot', script2])
        os.remove(script2)

        # Gráfico 3: Turbulento Numérico vs Power Law
        script3 = os.path.join(base_graficos, "03_Turbulent_Profile.gp")
        with open(script3, 'w') as f:
            f.write(f"set terminal pngcairo size 800,600 font 'Arial,12'\nset output '{os.path.join(base_graficos, '03_Perfil_Turbulento.png')}'\n")
            f.write("set title 'Perfil turbulento na saída'\nset xlabel 'Raio (r)'\nset ylabel 'Velocidade radial'\nset grid\n")
            f.write(f"plot 1.26117411111*(1-x/0.1)**(1./6.) title 'Correlação Turbulenta - Lei de Potência (n=6)', \\\n")
            f.write(f"     '{dados_proc['turbulent_wedge']}' u 1:2 w lp pt 7 title 'OpenFOAM - Solução Turbulenta'\n")
        subprocess.run(['gnuplot', script3])
        os.remove(script3)

    print("\n=== GT1 PROCESSADO ===")
    print("-> Verifique a pasta Resultados_Graficos_GT1 para os 3 plots comparativos.")