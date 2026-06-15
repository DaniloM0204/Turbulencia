#!/bin/bash

# Limpeza e configuracao do ambiente
foamCleanTutorials

# Execucao do mesh sem redirecionar logs com pontos
blockMesh

# Execucao da extrusao
extrudeMesh > log_extrudeMesh

# Correcao de patches
createPatch -overwrite > log_createPatch

# Verificacao do mesh
checkMesh > log_checkMesh