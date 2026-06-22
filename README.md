# Análise CFD com OpenFOAM (GT1, GT2 e GT3)

Este repositório contém scripts de automação em Python para a extração de dados, análise métrica e pós-processamento gráfico de simulações realizadas no OpenFOAM. O projeto está dividido em três estudos de caso focados em escoamentos externos e internos.

---

## Pré-requisitos

Antes de executar os scripts, certifique-se de que seu ambiente atende aos seguintes requisitos:

- **OpenFOAM** (Carregado corretamente no terminal, ex: `source /opt/openfoam10/etc/bashrc`)
- **Python 3.x**
- **Bibliotecas Python:** `numpy`, `matplotlib` (Instale com: `pip install numpy matplotlib`)

---

## Execução

Você pode executar os estudos de caso de duas formas:

### 1. Execução Automatizada

Para rodar **todos** os casos na ordem correta e dentro de suas respectivas pastas, basta executar o script na raiz do projeto:

```bash
python3 GT_all.py
```

### 1.1 Execução Reseta Tudo

Caso o usuário queira realizar um reset em todas as pastas e depois rodar caso por caso, deve seguir os seguintes comandos:

```bash
bash sh all_casos.sh
```



### 2. Execução Manual

Se preferir rodar apenas um caso específico, entre na pasta desejada do inicio e execute o script Python correspondente:

```bash
cd GT1
foamCleanTutorials
python3 GT1.py
```

---

## Entradas e Saídas Esperadas

A tabela abaixo resume as entradas necessárias e as saídas geradas por cada módulo.

| Módulo | Foco Físico | Entradas Necessárias | Saídas Geradas |
|--------|------------|---------------------|----------------|
| GT1 | Escoamento interno (Laminar vs Turbulento) | Pastas `laminar`, `turbulent_*` prontas para simular ou já simuladas | `Analise_GT1.txt` (métricas), `01_Velocidade_Radial.png`, `02_Perfil_Laminar.png`, `03_Perfil_Turbulento.png` |
| GT2 | Camada Limite Turbulenta | Pastas `RANS/` e `SRS/` prontas para simular ou já simuladas, contendo `postProcessing/` com `sampleDict` ativo | `Analise_GT2.txt` (Tabela de y+ e tempo), `GT2_01_Lei_da_Parede.png`, `GT2_02_Cf_Validacao.png`, `GT2_03_Perfil_Camada_Limite.png` |
| GT3 | Transição Laminar-Turbulento (T3A) | Pastas `RANS-*` e `setup_TM/` prontas para simular ou já simuladas, com logs e arquivos `*.xy` do sample | `Analise_GT3.txt` (Tabela de y+ e tempo), `01_Cf_Transicao_Modelos.png`, `02_Lei_da_Parede_Validacao.png`, `03_Convergencia_Tempo.png`, `04_Cf_vs_Re.png` |

---

## Estrutura de Pastas Esperada

O repositório deve estar organizado da seguinte forma:

```
/ (Raiz do Projeto)
├── GT_all.py
├── README.md
├── GT1
│   ├── GT1.py
│   ├── laminar/
│   └── turbulent_wedge/
├── GT2
│   ├── GT2.py
│   ├── RANS/
│   ├── SRS/
│   └── ...
└── GT3
    ├── GT3.py
    ├── RANS-kklo/
    ├── RANS-kOmegaSSTLM/
    └── ...
```

---

## Observações Finais

Após a execução, as pastas de cada GT gerarão subpastas para guardar os gráficos (`Resultados_Graficos_GT*` ou imagens `.png` na raiz do respectivo GT) e os arquivos `.txt` de análise métrica.
