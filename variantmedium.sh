#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

#---------------------------------------
# Helper functions
#---------------------------------------

log() {
  printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

die() {
  log "❌ ERROR: $1"
  exit 1
}

run_step() {
  local step="$1"
  shift
  log "🔹 Starting: $step"
  if "$@"; then
    log "✅ Completed: $step"
  else
    die "Step failed: $step"
  fi
}

usage() {
cat <<EOF

VariantMedium pipeline launcher

USAGE:
  $(basename "$0") [OPTIONS]

REQUIRED OPTIONS:
  --samplesheet        PATH        Path to the input CSV/TSV samplesheet
  --outdir             PATH        Output directory for all pipeline results
  --profile            STRING      Nextflow profile name (e.g. conda, singularity) [default: conda]

OPTIONAL:
  --data_staging       True|False  Whether to stage data before running (default: True)
  --skip_preprocessing True|False  Skip BAM preprocessing step (default: False)

GENERAL:
  -h, --help                       Show this help message and exit

DESCRIPTION:
  Command-line wrapper to run VariantMedium pipeline steps:
   1. Generate TSV inputs             - [VariantMedium prepare_tsv_inputs]
   2. Stage reference data & models   - [VariantMedium stage_data]
   3. BAM preprocessing               - [tronflow-bam-preprocessing]
   4. Candidate calling (Strelka2)    - [tronflow-strelka2]
   5. Feature generation              - [tronflow-vcf-postprocessing]
   6. ExtraTrees candidate filtering  - [VariantMedium candidate filtering]
   7. Tensor generation (bam2tensor)  - [bam2tensor]
   8. 3D DenseNet variant calling     - [VariantMedium DenseNet calling (snv & indel)]

EOF
exit 0
}

#---------------------------------------
# Parse arguments
#---------------------------------------

SAMPLESHEET=""
OUTDIR=""
PROFILE="conda"
DATA_STAGING="True"
SKIP_PREPROCESSING="False"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --samplesheet) SAMPLESHEET="$2"; shift 2;;
    --outdir) OUTDIR="$2"; shift 2;;
    --profile) PROFILE="$2"; shift 2;;
    --data_staging) DATA_STAGING="$2"; shift 2;;
    --skip_preprocessing) SKIP_PREPROCESSING="$2"; shift 2;;
    -h|--help) usage;;
    *) die "Unknown argument: $1";;
  esac
done

#---------------------------------------
# Argument validation
#---------------------------------------

[[ -z "$SAMPLESHEET" ]] && die "--samplesheet is required"
[[ -z "$OUTDIR" ]]      && die "--outdir is required"
[[ -z "$PROFILE" ]]     && die "--profile is required"

[[ -f "$SAMPLESHEET" ]] || die "Samplesheet does not exist: $SAMPLESHEET"

mkdir -p "$OUTDIR"

#---------------------------------------
# Derived paths
#---------------------------------------

TSV_FOLDER="${OUTDIR}/tsv_folder"

#---------------------------------------
# Output directories
#---------------------------------------

run_step "Creating output directories" \
  mkdir -p \
    "${OUTDIR}/output_01_01_preprocessed_bams" \
    "${OUTDIR}/output_01_02_candidates_strelka2" \
    "${OUTDIR}/output_01_03_vcf_postprocessing" \
    "${OUTDIR}/output_01_04_candidates_extratrees/Production_Model" \
    "${OUTDIR}/output_01_05_tensors" \
    "${OUTDIR}/output_01_06_calls_densenet"

#---------------------------------------
# 0. Prepare input files
#---------------------------------------

run_step "Generating required TSV input files" \
  nextflow run tron-bioinformatics/VariantMedium \
    -profile ${PROFILE} \
    --samplesheet "${SAMPLESHEET}" \
    --outdir "${OUTDIR}" \
    --execution_step prepare_tsv_inputs \
    --skip_preprocessing "${SKIP_PREPROCESSING}"

#---------------------------------------
# 1. BAM preprocessing
#---------------------------------------

if [[ "$SKIP_PREPROCESSING" == "True" ]]; then
  log "⚠️ Skipping BAM preprocessing."
else
  cd "${OUTDIR}/output_01_01_preprocessed_bams"

  run_step "BAM preprocessing (tronflow-bam-preprocessing)" \
    nextflow run tron-bioinformatics/tronflow-bam-preprocessing \
      -r v2.1.0 \
      -profile ${PROFILE} \
      --input_files "${TSV_FOLDER}/preproc.tsv" \
      --reference "${REF}" \
      --intervals "${EXOME_BED}" \
      --dbsnp "${DBSNP}" \
      --known_indels1 "${KNOWN_INDELS1}" \
      --output "${OUTDIR}/output_01_01_preprocessed_bams" \
      --skip_deduplication \
      --skip_metrics \
      -resume \
      -with-report \
      -with-trace
fi

#---------------------------------------
# 2. Candidate calling (Strelka2)
#---------------------------------------

cd "${OUTDIR}/output_01_02_candidates_strelka2"
INTERVALS_PARAM=()
[[ -n "${EXOME_BED:-}" ]] && INTERVALS_PARAM=(--intervals "${EXOME_BED}")

run_step "Running Strelka2 (tronflow-strelka2)" \
  nextflow run tron-bioinformatics/tronflow-strelka2 \
    -r v0.2.4 \
    -profile ${PROFILE} \
    --input_files "${TSV_FOLDER}/pairs_wo_reps.tsv" \
    --reference "${REF}" \
    --output "${OUTDIR}/output_01_02_candidates_strelka2" \
    "${INTERVALS_PARAM[@]}" \
    -resume \
    -with-report \
    -with-trace

#---------------------------------------
# 3. Feature generation
#---------------------------------------

run_step "Feature generation (tronflow-vcf-postprocessing)" \
  nextflow run tron-bioinformatics/tronflow-vcf-postprocessing \
    -r v3.1.2 \
    -profile ${PROFILE} \
    --input_vcfs "${TSV_FOLDER}/vcfs.tsv" \
    --input_bams "${TSV_FOLDER}/bams.tsv" \
    --reference "${REF}" \
    --output "${OUTDIR}/output_01_03_vcf_postprocessing" \
    -resume \
    -with-report \
    -with-trace

#---------------------------------------
# 4. Extra Trees filtering
#---------------------------------------

cd "${OUTDIR}/output_01_04_candidates_extratrees"

run_step "Filtering candidates with Extra Trees" \
  python3 "${CODE_FOLDER}/src/filter_candidates/filter.py" \
    -i "${TSV_FOLDER}/samples_w_cands.tsv" \
    -m "${CODE_FOLDER}/models/extra_trees.{}.joblib" \
    -o "${OUTDIR}/output_01_04_candidates_extratrees/{}/{}_{}.tsv"

#---------------------------------------
# 5. Tensor generation
#---------------------------------------

cd "${OUTDIR}/output_01_05_tensors"

run_step "Tensor generation (bam2tensor)" \
  nextflow run tron-bioinformatics/bam2tensor \
    -r 1.0.2 \
    -profile ${PROFILE} \
    --input_files "${TSV_FOLDER}/pairs_w_cands.tsv" \
    --publish_dir "${OUTDIR}/output_01_05_tensors" \
    --reference "${REF}" \
    --window 150 \
    --max_coverage 500 \
    --read_length 50 \
    --max_mapq 60 \
    --max_baseq 82 \
    -with-report \
    -with-trace

#---------------------------------------
# 6. DenseNet SNV/Indel calling
#---------------------------------------

cd "${OUTDIR}/output_01_06_calls_densenet"

run_step "3D DenseNet SNV calling" \
  python -u "${CODE_FOLDER}/src/run.py" call \
    --home_folder "${OUTDIR}/output_01_05_tensors/" \
    --pretrained_model "${CODE_FOLDER}/models/3ddensenet_snv.pt" \
    --prediction_mode somatic_snv \
    --out_path "${OUTDIR}/output_01_06_calls_densenet"

run_step "3D DenseNet INDEL calling" \
  python -u "${CODE_FOLDER}/src/run.py" call \
    --home_folder "${OUTDIR}/output_01_05_tensors/" \
    --pretrained_model "${CODE_FOLDER}/models/3ddensenet_indel.pt" \
    --prediction_mode somatic_indel \
    --out_path "${OUTDIR}/output_01_06_calls_densenet"

#---------------------------------------
# 7. Final output collection
#---------------------------------------

run_step "Copying final SNV/VCF outputs" \
  cp "${OUTDIR}/output_01_06_calls_densenet/"*.somatic_snv.VariantMedium.{tsv,vcf} "${OUTDIR}/"

log "🎉 Pipeline completed successfully!"
