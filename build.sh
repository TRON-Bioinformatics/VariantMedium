#!/usr/bin/env bash

set -e

. $1

mkdir -p ${ENV_FOLDER}

### create conda envs
echo "Creating variantmedium environment"
conda env create \
--no-default-packages \
-f environment.yml \
--prefix ${ENV_FOLDER}/variantmedium 
echo "Created variantmedium environment"

echo "Creating extra trees environment"
conda env create \
--no-default-packages \
-f environment_et.yml \
--prefix ${ENV_FOLDER}/variantmedium-extratrees 
echo "Created extra trees environment"


