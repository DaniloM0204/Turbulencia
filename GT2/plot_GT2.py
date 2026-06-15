import os
import subprocess

def processar_caso(case_path):
    # Procura em todo o diretório postProcessing
    post_dir = os.path.join(os.getcwd(), case_path, "postProcessing")
    if not os.path.exists(post_dir): return None

    # Diretório para salvar os dados limpos
    output_dir = os.path.join(os.getcwd(), "Resultados_Formatados", case_path.replace("/", "_"))
    os.makedirs(output_dir, exist_ok=True)
    
    dados_processados = {}
    
    for root, _, files in os.walk(post_dir):
        for f in files:
            if f in ['profile0.xy', 'profile1.xy']:
                origem = os.path.join(root, f)
                destino = os.path.join(output_dir, f.replace('.xy', '.dat'))
                
                # Limpeza rigorosa: mantém apenas colunas numéricas
                with open(origem, 'r') as fin, open(destino, 'w') as fout:
                    for line in fin:
                        # Ignora linhas de texto/cabeçalho
                        if any(c in line for c in ['(', ')', '#', 'Time', 'patch', 'X', 'Y', 'Z']): continue
                        c = line.split()
                        if len(c) >= 2:
                            try:
                                fout.write(f"{float(c[0])}\t{float(c[1])}\n")
                            except ValueError: continue
                
                dados_processados[f.replace('.xy', '')] = destino
    return dados_processados

def plotar_comparativo(dados, c1, c2, nome_fig, chave):
    f1 = dados.get(c1, {}).get(chave)
    f2 = dados.get(c2, {}).get(chave)
    
    if f1 and f2:
        with open("temp.gp", "w") as s:
            s.write(f"set terminal pngcairo size 800,600\n"
                    f"set output 'Figuras_Finais/{nome_fig}.png'\n"
                    f"set grid; set xlabel 'Distância (y)'; set ylabel 'Velocidade (U)'\n"
                    f"plot '{f1}' w l title '{c1}', '{f2}' w l title '{c2}'\n")
        subprocess.run(['gnuplot', "temp.gp"])
        os.remove("temp.gp")
        print(f"[+] Gráfico gerado: {nome_fig}.png")

if __name__ == "__main__":
    CASES = ["RANS/KEpsilon_highRE_V1", "RANS/KEpsilon_lowRE_V1", "RANS/KOmegaSST_highRE", 
             "RANS/KOmegaSST_lowRE_V1", "RANS/SA_LRN", "SRS/DES_KO_LRN", "SRS/LES-WALE_LRN"]
    
    os.makedirs("Figuras_Finais", exist_ok=True)
    dados_coletados = {c: processar_caso(c) for c in CASES}
    
    # Exemplo de comparativos (adicione os que precisar)
    plotar_comparativo(dados_coletados, "RANS/KOmegaSST_highRE", "RANS/KOmegaSST_lowRE_V1", "KOmega_Comp", "profile1")
    print("--- Processamento concluído ---")