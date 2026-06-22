import os
import subprocess

def main():
    root_dir = os.getcwd()
    # Estrutura de pastas e scripts
    scripts = [
        ("GT1", "GT1.py"),
        ("GT2", "GT2.py"),
        ("GT3", "GT3.py")
    ]

    for folder, filename in scripts:
        target_dir = os.path.join(root_dir, folder)
        script_path = os.path.join(target_dir, filename)

        if not os.path.exists(target_dir):
            print(f"Pasta {folder} não encontrada.")
            continue
        
        try:
            # Executa o script dentro do diretório correspondente
            process = subprocess.run(['python3', filename], cwd=target_dir, capture_output=False, check=False)
            
            if process.returncode != 0:
                print(f"A execução de {filename} falhou.")
                
        except Exception as e:
            print(f"Não foi possível executar {filename} em {folder}. Erro: {e}")

if __name__ == "__main__":
    main()