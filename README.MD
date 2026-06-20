# Análise dos casos GT1, GT2 e GT3 com OpenFOAM 

Este repositório contém uma suíte de automação em Python para execução, extração de dados e pós-processamento de simulações de Dinâmica dos Fluidos Computacional (CFD) utilizando o **OpenFOAM**. O projeto é dividido em três Grupos de Trabalho (GTs), focados em diferentes fenômenos físicos: Escoamento Interno, Camada Limite Turbulenta e Modelagem de Transição.

## Pré-requisitos

Para executar os scripts perfeitamente, garanta que seu ambiente possui:
- **OpenFOAM** (Configurado e carregado no terminal, ex: `source /opt/openfoam10/etc/bashrc`)
- **Python 3.x**
- **Bibliotecas Python:** `numpy`, `matplotlib` (Instale com: `pip install numpy matplotlib`)

---

## Execução dos Casos

### 🔹 GT1: Escoamento Interno (Planar vs. Wedge)
**Objetivo:** Comparar o escoamento incompressível em dutos utilizando formulação puramente planar (2D) versus coordenada cilíndrica/axi-simétrica (condição `wedge`).
- **Modelos Avaliados:** `laminar`, `turbulent_wedge`.
- **Como executar cada caso:**
  ```bash
  cd GT1
  python3 GT1.py
  cd ..
  cd GT2
  python3 GT2.py
  cd ..
  cd GT3
  python3 GT3.py


### 2. Tabela Comparativa (Entradas e Saídas do Projeto)

Abaixo está a matriz técnica para você anexar à documentação do seu projeto ou relatório. Ela mapeia exatamente as condições de contorno (entradas) e o que os scripts extraem de cada caso (saídas).

| Módulo | Foco Físico | Modelos Analisados | Entradas Necessárias (Parâmetros / Arquivos) | Saídas Geradas (Gráficos e Relatórios) |
| :--- | :--- | :--- | :--- | :--- |
| **GT1** | Escoamento interno em Dutos (Laminar vs Turbulento) | 1. `laminar` (Planar)<br>2. `turbulent_wedge` (Axi-simétrico) | - Setup base OpenFOAM (`U`, `p`, `nut`).<br>- Dicionários de malha (`blockMeshDict`, `extrudeMeshDict`).<br>- Ferramenta `foamRun`. | 📄 **Txt:** `Analise_GT1.txt` (Análise crítica, custo computacional, $y^+$).<br>📈 **Plots (Gnuplot):**<br>- 01: Vel. Radial Comparativa<br>- 02: Validação Analítica Laminar (Poiseuille)<br>- 03: Validação Turbulenta (Lei de Potência) |
| **GT2** | Camada Limite Turbulenta (Placa Plana) | **RANS:** $k$-$\omega$ SST (High/Low-Re), $k$-$\epsilon$ (High/Low-Re), SA.<br>**SRS:** DES, LES-WALE. | - $U_\infty = 1.0$ m/s<br>- $\nu = 1.5 \times 10^{-5}$ m²/s<br>- Execução prévia de `run_all.sh` e `yplus.sh`.<br>- Linhas do `sampleDict` (`profile0.xy`, `profile1.xy`). | 📄 **Txt:** `Analise_GT2.txt` (Tabela de $y^+$ médio e Tempo).<br>📈 **Plots (Matplotlib):**<br>- 01: Lei da Parede ($u^+$ vs $y^+$)<br>- 02: $C_f$ Local ao longo da placa ($X$)<br>- 03: Perfil da Camada Limite ($Y$ vs $U/U_\infty$) |
| **GT3** | Transição Laminar-Turbulento (ERCOFTAC T3A) | 1. `k-kl-omega`<br>2. `SST-LM`<br>3. `SST v2`<br>4. `Launder-Sharma k-e` | - $U_\infty = 5.4$ m/s<br>- $\nu = 1.5 \times 10^{-5}$ m²/s<br>- Logs de execução (`log.foamRun`).<br>- Extrações espaciais (`y01.xy` e `*0795*.xy`). | 📈 **Plots (Gnuplot):**<br>- 01: Transição do $C_f$ ao longo da placa.<br>- 02: Validação da Lei da Parede.<br>- 03: Convergência Temporal (Resíduos $U_x$).<br>- 04: Validação $C_f$ vs $Re_x$ (comparativo com curvas teóricas de Blasius e Prandtl). |

### Notas Técnicas para o seu Projeto:
* **Geração de Gráficos:** Note que o `GT2` foi estruturado usando Python nativo (`matplotlib`) para os gráficos, o que é excelente para manipulação de arrays (numpy). Já o `GT1` e o `GT3` automatizam a criação de scripts do software externo `Gnuplot`.
* **Tratamento de Malha:** No GT1 a malha é gerada em tempo de execução pelo Python (`blockMesh` > `extrudeMesh`). No GT2 e GT3, os scripts em Python assumem que as malhas e simulações já foram (ou estão sendo) rodadas externamente e atuam mais como poderosos extratores de resultados.