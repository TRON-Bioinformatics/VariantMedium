#!/usr/bin/env bash

set -e
set -o pipefail  # Catch failures in piped commands

. $1

mkdir -p ${ENV_FOLDER}


### download models
cd ${CODE_FOLDER}/models
#!/bin/bash

# Function to download a file and verify its checksum
download_and_verify() {
  local URL=$url
  local FILENAME=$filename
  local EXPECTED_MD5=$checksum

  echo "Downloading $FILENAME from $URL..."

  # Download the file using curl
  if ! curl -L --retry 5 --retry-delay 2 --retry-max-time 60 --fail -o "$FILENAME" -H "Accept: application/octet-stream" "$URL"; then
    echo "Error: Failed to download $FILENAME from $URL" >&2
    exit 1
  fi

  # Calculate actual MD5
  ACTUAL_MD5=$(md5sum "$FILENAME" | awk '{ print $1 }')

  # Compare checksums
  if [ "$EXPECTED_MD5" != "$ACTUAL_MD5" ]; then
    echo "Error: Checksum mismatch for $FILENAME" >&2
    echo "Expected: $EXPECTED_MD5" >&2
    echo "Actual:   $ACTUAL_MD5" >&2
    exit 1
  else
    echo "Checksum verified for $FILENAME"
  fi

  echo "Download successful: $FILENAME"
}

url="https://huggingface.co/tron-mainz/3ddensenet_snv/resolve/main/3ddensenet_snv.pt"
filename="3ddensenet_snv.pt"
checksum="0caf56d20bf3324a7d36614229105cc1"  # Replace with actual checksum
download_and_verify

url="https://huggingface.co/tron-mainz/3ddensenet_indel/resolve/main/3ddensenet_indel.pt"
filename="3ddensenet_indel.pt"
checksum="a48a4d46df5c041c61d320d10c3857ca"  # Replace with actual checksum
download_and_verify

url="https://huggingface.co/tron-mainz/extra_trees.snv/resolve/main/extra_trees.snv.joblib"
filename="extra_trees.snv.joblib"
checksum="8fa269b15cba16b98b107b594b162b72"  # Replace with actual checksum
download_and_verify

url="https://huggingface.co/tron-mainz/extra_trees.indel/resolve/main/extra_trees.indel.joblib"
filename="extra_trees.indel.joblib"
checksum="511718696c1c0997832b5b942beebf54"  # Replace with actual checksum
download_and_verify


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


