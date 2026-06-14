#!/bin/bash


foamCleanTutorials

blockMesh

checkMesh | tee log.checkMesh
