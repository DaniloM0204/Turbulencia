#!/bin/bash
source /Volumes/OpenFOAM/OpenFOAM-12/etc/bashrc


foamCleanTutorials

blockMesh

checkMesh | tee log.checkMesh
