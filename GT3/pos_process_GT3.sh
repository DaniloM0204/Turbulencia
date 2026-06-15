#!/bin/bash

# Ativa o ambiente virtual se existir
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Roda o pos processamento em python
python3 plot_GT3.py