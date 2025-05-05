#!/usr/bin/env bash

set -e
set -o pipefail  # Catch failures in piped commands

. $1

mkdir -p ${ENV_FOLDER}


### download models
cd ${CODE_FOLDER}/models

URL="https://huggingface.co/tron-mainz/3ddensenet_snv/resolve/main/3ddensenet_snv.pt"
FILENAME="3ddensenet_snv.pt"

echo "Downloading $FILENAME from $URL..."

if ! curl -L --retry 5 --retry-delay 2 --retry-max-time 60 --fail -o "$FILENAME" "$URL"; then
  echo "Error: Failed to download $FILENAME from $URL" >&2
  exit 1
fi

echo "Download successful: $FILENAME"

URL="https://huggingface.co/tron-mainz/3ddensenet_indel/blob/main/3ddensenet_indel.pt"
FILENAME="3ddensenet_indel.pt"

echo "Downloading $FILENAME from $URL..."

if ! curl -L --retry 5 --retry-delay 2 --retry-max-time 60 --fail -o "$FILENAME" "$URL"; then
  echo "Error: Failed to download $FILENAME from $URL" >&2
  exit 1
fi

echo "Download successful: $FILENAME"

URL="https://huggingface.co/tron-mainz/extra_trees.indel/blob/main/extra_trees.indel.joblib"
FILENAME="extra_trees.indel.joblib"

echo "Downloading $FILENAME from $URL..."

if ! curl -L --retry 5 --retry-delay 2 --retry-max-time 60 --fail -o "$FILENAME" "$URL"; then
  echo "Error: Failed to download $FILENAME from $URL" >&2
  exit 1
fi

echo "Download successful: $FILENAME"

URL="https://huggingface.co/tron-mainz/extra_trees.snv/blob/main/extra_trees.snv.joblib"
FILENAME="extra_trees.snv.joblib"

echo "Downloading $FILENAME from $URL..."

if ! curl -L --retry 5 --retry-delay 2 --retry-max-time 60 --fail -o "$FILENAME" "$URL"; then
  echo "Error: Failed to download $FILENAME from $URL" >&2
  exit 1
fi

echo "Download successful: $FILENAME"

cd ${CODE_FOLDER}


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


