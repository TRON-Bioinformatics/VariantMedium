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
    log "🔹 Started: $step"
    # Run command and stream stdout/stderr
    "$@" 2>&1 | tee -a "${OUTDIR}/pipeline.log"
    if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
        die "Step failed: $step"
    fi
    log "✅ Completed: $step"
}

usage() {
    cat <<EOF

VariantMedium pipeline launcher

USAGE:
  $(basename "$0") [OPTIONS]

REQUIRED OPTIONS:
  --samplesheet        PATH        Path to the input CSV/TSV samplesheet
  --outdir             PATH        Output directory for all pipeline results
  --profile            STRING      Nextflow profile name (conda, singularity) [default: conda]
  --config             PATH        Path to custom config file (.conf)

OPTIONAL:
  --skip_data_staging             Skip staging reference data & models
  --skip_preprocessing            Skip BAM preprocessing step

GENERAL:
  -h, --help                      Show this help message and exit

DESCRIPTION:
  Command-line wrapper to run VariantMedium pipeline steps:
   1. Generate TSV inputs                       -> [VariantMedium generate_tsv_files step]
   2. Stage reference data & models             -> [VariantMedium stage_data step]
   3. BAM preprocessing                         -> [tronflow-bam-preprocessing]
   4. Candidate calling (Strelka2)              -> [tronflow-strelka2]
   5. Feature generation                        -> [tronflow-vcf-postprocessing]
   6. ExtraTrees candidate filtering            -> [VariantMedium filter_candidates step]
   7. Tensor generation (bam2tensor)            -> [bam2tensor]
   8. 3D DenseNet variant calling (SNV & INDEL) -> [VariantMedium call_variants step]

EOF
    exit 0
}

#---------------------------------------
# Parse arguments
#---------------------------------------

SAMPLESHEET=""
OUTDIR=""
PROFILE="conda"
SKIP_DATA_STAGING=false
SKIP_PREPROCESSING=false
CONFIG_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --samplesheet) SAMPLESHEET="$2"; shift 2;;
        --outdir) OUTDIR="$2"; shift 2;;
        --profile) PROFILE="$2"; shift 2;;
        --config) CONFIG_FILE="$2"; shift 2;;
        --skip_data_staging) SKIP_DATA_STAGING=true; shift;;
        --skip_preprocessing) SKIP_PREPROCESSING=true; shift;;
        -h|--help) usage;;
        *) die "Unknown argument: $1";;
    esac
done

#---------------------------------------
# Argument validation
#---------------------------------------

[[ -z "$SAMPLESHEET" ]] && die "--samplesheet is required"
[[ -f "$SAMPLESHEET" ]] || die "Samplesheet does not exist: $SAMPLESHEET"
[[ -z "$OUTDIR" ]] && die "--outdir is required"

# ------------------------------
# Load config file if provided
# ------------------------------
if [[ -n "$CONFIG_FILE" ]]; then
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "[ERROR] Config file not found: $CONFIG_FILE"
        exit 1
    fi
    echo "[INFO] Loading config: $CONFIG_FILE"
    source "$CONFIG_FILE"
fi

#---------------------------------------
log ""
log "Samplesheet: $SAMPLESHEET"
log "Output directory: $OUTDIR"
log "Profile: $PROFILE"
log "Skip data staging: $SKIP_DATA_STAGING"
log "Skip BAM preprocessing: $SKIP_PREPROCESSING"
log ""
#---------------------------------------

mkdir -p "$OUTDIR"
PIPE_LOG="${OUTDIR}/pipeline.log"
: > "$PIPE_LOG"

#---------------------------------------
# Derived paths
#---------------------------------------

TSV_FOLDER="${OUTDIR}/tsv_folder"
REF_DIR="${OUTDIR}/data_staging/ref_data"
REF="${REF_DIR}/GRCh38.d1.vd1.fa"
EXOME_BED="${REF_DIR}/S07604624_Covered.bed.gz"
DBSNP="${REF_DIR}/dbsnp_146.hg38.vcf.gz"
KNOWN_INDELS1="${REF_DIR}/ALL.wgs.1000G_phase3.GRCh38.ncbi_remapper.20150424.shapeit2_indels.vcf.gz"

mkdir -p \
    "${OUTDIR}/output_01_01_preprocessed_bams" \
    "${OUTDIR}/output_01_02_candidates_strelka2" \
    "${OUTDIR}/output_01_03_vcf_postprocessing" \
    "${OUTDIR}/output_01_04_candidates_extratrees" \
    "${OUTDIR}/output_01_05_tensors" \
    "${OUTDIR}/output_01_06_calls_densenet"

#---------------------------------------
# 1. Prepare TSV input files
#---------------------------------------

CMD=(nextflow run main.nf
    -profile "${PROFILE}"
    --samplesheet "${SAMPLESHEET}"
    --outdir "${OUTDIR}"
    --execution_step generate_tsv_files
)

$SKIP_PREPROCESSING && CMD+=(--skip_preprocessing)
CMD+=(-resume)

run_step "Generating TSV input files" "${CMD[@]}"

#---------------------------------------
# 2. Stage reference data & models
#---------------------------------------

if [[ "$SKIP_DATA_STAGING" == true ]]; then
    log "⚠️ Skipping data staging"
else
    CMD=(nextflow run main.nf
        -profile "${PROFILE}"
        --samplesheet "${SAMPLESHEET}"
        --outdir "${OUTDIR}"
        --execution_step stage_data
    )
    $SKIP_PREPROCESSING && CMD+=(--skip_preprocessing)
    CMD+=(-resume)

    run_step "Staging reference data and models" "${CMD[@]}"
fi

#---------------------------------------
# 3. BAM preprocessing
#---------------------------------------

if [[ "$SKIP_PREPROCESSING" == true ]]; then
    log "⚠️ Skipping BAM preprocessing"
else
    pushd "${OUTDIR}/output_01_01_preprocessed_bams" >/dev/null

    CMD=(nextflow run tron-bioinformatics/tronflow-bam-preprocessing
        -r v2.1.0
        -profile "${PROFILE}"
        --input_files "${TSV_FOLDER}/preproc.tsv"
        --reference "${REF}"
        --intervals "${EXOME_BED}"
        --dbsnp "${DBSNP}"
        --known_indels1 "${KNOWN_INDELS1}"
        --output "${OUTDIR}/output_01_01_preprocessed_bams"
        --skip_deduplication
        --skip_metrics
        -resume
        -with-report
        -with-trace
    )

    run_step "BAM preprocessing" "${CMD[@]}"
    popd >/dev/null
fi

#---------------------------------------
# 4. Candidate calling (Strelka2)
#---------------------------------------

pushd "${OUTDIR}/output_01_02_candidates_strelka2" >/dev/null

INTERVALS_PARAM=()
[[ -f "$EXOME_BED" ]] && INTERVALS_PARAM=(--intervals "$EXOME_BED")

CMD=(nextflow run tron-bioinformatics/tronflow-strelka2
    -r v0.2.4
    -profile "${PROFILE}"
    --input_files "${TSV_FOLDER}/pairs_wo_reps.tsv"
    --reference "${REF}"
    --output "${OUTDIR}/output_01_02_candidates_strelka2"
)
CMD+=("${INTERVALS_PARAM[@]}")
CMD+=(-resume -with-report -with-trace)

run_step "Candidate calling (Strelka2)" "${CMD[@]}"
popd >/dev/null

#---------------------------------------
# 5. Feature generation
#---------------------------------------

CMD=(nextflow run tron-bioinformatics/tronflow-vcf-postprocessing
    -r v3.1.2
    -profile "${PROFILE}"
    --input_vcfs "${TSV_FOLDER}/vcfs.tsv"
    --input_bams "${TSV_FOLDER}/bams.tsv"
    --reference "${REF}"
    --output "${OUTDIR}/output_01_03_vcf_postprocessing"
    -resume -with-report -with-trace
)

run_step "Feature generation" "${CMD[@]}"

#---------------------------------------
# 6. ExtraTrees candidate filtering
#---------------------------------------

CMD=(nextflow run main.nf
    -profile "${PROFILE}"
    --samplesheet "${SAMPLESHEET}"
    --outdir "${OUTDIR}/output_01_04_candidates_extratrees"
    --execution_step filter_candidates
    -with-report
    -with-trace
)
run_step "ExtraTrees candidate filtering" "${CMD[@]}"

#---------------------------------------
# 7. Tensor generation
#---------------------------------------

pushd "${OUTDIR}/output_01_05_tensors" >/dev/null

CMD=(nextflow run tron-bioinformatics/bam2tensor
    -r 1.0.2
    -profile "${PROFILE}"
    --input_files "${TSV_FOLDER}/pairs_w_cands.tsv"
    --publish_dir "${OUTDIR}/output_01_05_tensors"
    --reference "${REF}"
    --window 150
    --max_coverage 500
    --read_length 50
    --max_mapq 60
    --max_baseq 82
    -with-report
    -with-trace
)

run_step "Tensor generation" "${CMD[@]}"
popd >/dev/null

#---------------------------------------
# 8. 3D DenseNet variant calling
#---------------------------------------

pushd "${OUTDIR}/output_01_06_calls_densenet" >/dev/null

CMD=(nextflow run main.nf
    -profile "${PROFILE}"
    --samplesheet "${SAMPLESHEET}"
    --outdir "${OUTDIR}/output_01_06_calls_densenet"
    --execution_step call_variants
    -with-report
    -with-trace
)

run_step "3D DenseNet SNV/Indel calling" "${CMD[@]}"
popd >/dev/null

log "🎉 Pipeline completed successfully!"
