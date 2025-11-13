#!/usr/bin/env bash
#===============================================================================
# VariantMedium Full Pipeline
# Description: End-to-end variant calling pipeline using Nextflow and Python tools.
# Author: <Your Name>
#===============================================================================

set -Eeuo pipefail
IFS=$'\n\t'

#---------------------------------------
# Helper functions
#---------------------------------------

log() {
  local msg="$1"
  printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$msg"
}

die() {
  log "❌ ERROR: $1"
  exit 1
}

# Run a command safely with a descriptive step name
run_step() {
  local step_name="$1"
  shift
  log "🔹 Starting: ${step_name}"
  if "$@"; then
    log "✅ Completed: ${step_name}"
  else
    die "Step failed: ${step_name}"
  fi
}

#---------------------------------------
# Argument parsing
#---------------------------------------

if [[ $# -ne 1 ]]; then
  die "Usage: $0 <path_to_config.sh>"
fi

CONFIG_FILE="$1"
[[ -f "$CONFIG_FILE" ]] || die "Config file not found: $CONFIG_FILE"

# shellcheck disable=SC1090
source "$CONFIG_FILE"

#---------------------------------------
# Derived paths
#---------------------------------------

TSV_FOLDER="${OUT_FOLDER}/input_files"

#---------------------------------------
# Directory setup
#---------------------------------------

run_step "Creating output directories" \
  mkdir -p "${OUT_FOLDER}" \
           "${OUT_FOLDER}/input_files" \
           "${OUT_FOLDER}/output_01_01_preprocessed_bams" \
           "${OUT_FOLDER}/output_01_02_candidates_strelka2" \
           "${OUT_FOLDER}/output_01_03_vcf_postprocessing" \
           "${OUT_FOLDER}/output_01_04_candidates_extratrees/Production_Model" \
           "${OUT_FOLDER}/output_01_05_tensors" \
           "${OUT_FOLDER}/output_01_06_calls_densenet"

#---------------------------------------
# 0. Prepare input files
#---------------------------------------

run_step "Generating required TSV files" \
  python "${CODE_FOLDER}/scripts/prepare_input_files.py" \
    -i "${PAIRS}" \
    -o "${TSV_FOLDER}" \
    -O "${OUT_FOLDER}" \
    --skip_preprocessing "${SKIP_PREPROCESSING}"

#---------------------------------------
# 1. BAM preprocessing
#---------------------------------------

if [[ "${SKIP_PREPROCESSING}" == "True" ]]; then
  log "⚠️ Skipping BAM file preprocessing."
else
  cd "${OUT_FOLDER}/output_01_01_preprocessed_bams"

  run_step "BAM preprocessing (tronflow-bam-preprocessing)" \
    nextflow run tron-bioinformatics/tronflow-bam-preprocessing \
      -r v2.1.0 \
      -profile conda \
      -with-report \
      -with-trace \
      -resume \
      --input_files "${TSV_FOLDER}/preproc.tsv" \
      --reference "${REF}" \
      --intervals "${EXOME_BED}" \
      --dbsnp "${DBSNP}" \
      --known_indels1 "${KNOWN_INDELS1}" \
      --output "${OUT_FOLDER}/output_01_01_preprocessed_bams" \
      --skip_deduplication \
      --skip_metrics
fi

#---------------------------------------
# 2. Candidate calling (Strelka2)
#---------------------------------------

cd "${OUT_FOLDER}/output_01_02_candidates_strelka2"
INTERVALS_PARAM=()
[[ -n "${EXOME_BED:-}" ]] && INTERVALS_PARAM=(--intervals "${EXOME_BED}")

run_step "Running Strelka2 (tronflow-strelka2)" \
  nextflow run tron-bioinformatics/tronflow-strelka2 \
    -r v0.2.4 \
    -profile conda \
    -with-report \
    -with-trace \
    -resume \
    --input_files "${TSV_FOLDER}/pairs_wo_reps.tsv" \
    --reference "${REF}" \
    --output "${OUT_FOLDER}/output_01_02_candidates_strelka2" \
    "${INTERVALS_PARAM[@]}"

#---------------------------------------
# 3. Feature generation
#---------------------------------------

run_step "Feature generation (tronflow-vcf-postprocessing)" \
  nextflow run tron-bioinformatics/tronflow-vcf-postprocessing \
    -r v3.1.2 \
    -profile conda \
    -with-report \
    -with-trace \
    -resume \
    --input_vcfs "${TSV_FOLDER}/vcfs.tsv" \
    --input_bams "${TSV_FOLDER}/bams.tsv" \
    --reference "${REF}" \
    --output "${OUT_FOLDER}/output_01_03_vcf_postprocessing"

#---------------------------------------
# 4. Filtering candidates (Extra Trees)
#---------------------------------------

cd "${OUT_FOLDER}/output_01_04_candidates_extratrees"

run_step "Filtering candidates with Extra Trees" \
  python3 "${CODE_FOLDER}/src/filter_candidates/filter.py" \
    -i "${TSV_FOLDER}/samples_w_cands.tsv" \
    -m "${CODE_FOLDER}/models/extra_trees.{}.joblib" \
    -o "${OUT_FOLDER}/output_01_04_candidates_extratrees/{}/{}_{}.tsv"

#---------------------------------------
# 5. Tensor generation
#---------------------------------------

cd "${OUT_FOLDER}/output_01_05_tensors"

run_step "Tensor generation (bam2tensor)" \
  nextflow run tron-bioinformatics/bam2tensor \
    -r 1.0.2 \
    -profile conda \
    -with-report \
    -with-trace \
    --input_files "${TSV_FOLDER}/pairs_w_cands.tsv" \
    --publish_dir "${OUT_FOLDER}/output_01_05_tensors" \
    --reference "${REF}" \
    --window 150 \
    --max_coverage 500 \
    --read_length 50 \
    --max_mapq 60 \
    --max_baseq 82

#---------------------------------------
# 6. Variant calling (3D DenseNet)
#---------------------------------------

cd "${OUT_FOLDER}/output_01_06_calls_densenet"

run_step "3D DenseNet SNV calling" \
  python -u "${CODE_FOLDER}/src/run.py" call \
    --home_folder "${OUT_FOLDER}/output_01_05_tensors/" \
    --unknown_strategy_call keep_as_false \
    --pretrained_model "${CODE_FOLDER}/models/3ddensenet_snv.pt" \
    --prediction_mode somatic_snv \
    --out_path "${OUT_FOLDER}/output_01_06_calls_densenet" \
    --learning_rate 0.13 \
    --epoch 0 \
    --drop_rate 0.3 \
    --aug_rate 5 \
    --aug_mixes nan \
    --run call

run_step "3D DenseNet INDEL calling" \
  python -u "${CODE_FOLDER}/src/run.py" call \
    --home_folder "${OUT_FOLDER}/output_01_05_tensors/" \
    --unknown_strategy_call keep_as_false \
    --pretrained_model "${CODE_FOLDER}/models/3ddensenet_indel.pt" \
    --prediction_mode somatic_indel \
    --out_path "${OUT_FOLDER}/output_01_06_calls_densenet" \
    --learning_rate 0.13 \
    --epoch 0 \
    --drop_rate 0.5 \
    --aug_rate 5 \
    --aug_mixes nan \
    --run call

#---------------------------------------
# 7. Copy final outputs
#---------------------------------------

run_step "Copying final SNV and VCF files" \
  cp "${OUT_FOLDER}/output_01_06_calls_densenet/"*.somatic_snv.VariantMedium.{tsv,vcf} "${OUT_FOLDER}/"

log "🎉 Pipeline completed successfully!"
