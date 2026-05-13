#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

#---------------------------------------
# Load helper functions
#---------------------------------------
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
HELPER_SCRIPT="${SCRIPT_DIR}/variantmedium_helpers.sh"
[[ -f "$HELPER_SCRIPT" ]] || {
    printf "[ERROR] Missing helper script: %s\n" "$HELPER_SCRIPT" >&2
    exit 1
}
# shellcheck source=/dev/null
source "$HELPER_SCRIPT"

usage() {
    cat <<EOF_USAGE

VariantMedium pipeline launcher

USAGE:
  $(basename "$0") [OPTIONS]

REQUIRED ARGUMENTS:
  --samplesheet               PATH        Path to the input CSV/TSV samplesheet
  --outdir                    PATH        Output directory for all pipeline results
  --profile                   STRING      Nextflow profile name (conda, singularity) [default: conda]
                                          [Parts of the pipeline may not support singularity - Prefer using conda]

OPTIONAL ARGUMENTS:
  --config                    PATH        Path to custom config file (.conf)
  --mount-path                PATH        Path to mount when using singularity profile [required for the singularity profile]
  --intervals                 PATH        Target region BED file (e.g. exome). Omit for WGS mode
  --skip-preprocessing                    Skip BAM preprocessing step
  --resume                                Resume from previous run
  --nf-report                             Generate Nextflow execution report
  --nf-trace                              Generate Nextflow execution trace
  --strelka-config            PATH        Path to custom Strelka2 config file
  --bam-prep-config           PATH        Path to custom BAM preprocessing config file
  --vcf-post-config           PATH        Path to custom VCF postprocessing config file
  --bam2tensor-config         PATH        Path to custom bam2tensor config file
  -h, --help                              Show this help message and exit

  DESCRIPTION:
  Command-line wrapper to run VariantMedium pipeline steps:
   1. Generate TSV inputs                       -> [VariantMedium generating input tsv files step]
   2. Stage reference data & models             -> [VariantMedium data staging step]
   3. BAM preprocessing                         -> [tronflow-bam-preprocessing]
   4. Candidate calling (Strelka2)              -> [tronflow-strelka2]
   5. Feature generation                        -> [tronflow-vcf-postprocessing]
   6. ExtraTrees candidate filtering            -> [VariantMedium filter_candidates step]
   7. Tensor generation (bam2tensor)            -> [bam2tensor]
   8. 3D DenseNet variant calling (SNV & INDEL) -> [VariantMedium call_variants step]

EOF_USAGE
    exit 0
}

#---------------------------------------
# Parse arguments
#---------------------------------------
PIPELINE_STEP=""
SAMPLESHEET=""
OUTDIR=""
BENCHMARK_DIR="benchmarks"
REF_DIR=""
MODELS_DIR=""
REF=""
INTERVALS=""
DBSNP=""
KNOWN_INDELS1=""
KNOWN_INDELS2=""
PROFILE="conda"
SKIP_PREPROCESSING=false
CONFIG_FILE=""
MOUNT_PATH=""
RESUME_REQUESTED=false
REQUEST_REPORT=false
REQUEST_TRACE=false
STRELKA_CONFIG=""
BAM_PREP_CONFIG=""
VCF_POST_CONFIG=""
BAM2TENSOR_CONFIG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --samplesheet) SAMPLESHEET="$2"; shift 2 ;;
        --outdir) OUTDIR="$2"; shift 2 ;;
        --profile) PROFILE="$2"; shift 2 ;;
        --config) CONFIG_FILE="$2"; shift 2 ;;
        --mount-path) MOUNT_PATH="$2"; shift 2 ;;
        --intervals) INTERVALS="$2"; shift 2 ;;
        --skip-preprocessing) SKIP_PREPROCESSING=true; shift ;;
        --resume) RESUME_REQUESTED=true; shift ;;
        --nf-report) REQUEST_REPORT=true; shift ;;
        --nf-trace) REQUEST_TRACE=true; shift ;;
        --strelka-config) STRELKA_CONFIG="$2"; shift 2 ;;
        --bam-prep-config) BAM_PREP_CONFIG="$2"; shift 2 ;;
        --vcf-post-config) VCF_POST_CONFIG="$2"; shift 2 ;;
        --bam2tensor-config) BAM2TENSOR_CONFIG="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) die "Unknown argument: $1" ;;
    esac
done

#---------------------------------------
# Load config file if provided
#---------------------------------------
if [[ -n "$CONFIG_FILE" ]]; then
    [[ -f "$CONFIG_FILE" ]] || die "Config file not found: $CONFIG_FILE"
    log "Loading config: $CONFIG_FILE"
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
fi

# Default profile if not provided anywhere
[[ -z "$PROFILE" ]] && PROFILE="conda"

# Required variables must exist after merging CLI + config
[[ -n "$SAMPLESHEET" ]] || die "SAMPLESHEET must be provided via --samplesheet or config file"
[[ -n "$OUTDIR"     ]] || die "OUTDIR must be provided via --outdir or config file"
[[ -n "$PROFILE"    ]] || die "PROFILE must be provided via --profile or config file"

# Validate samplesheet path
[[ -f "$SAMPLESHEET" ]] || die "Samplesheet does not exist: $SAMPLESHEET"

# Normalize OUTDIR
OUTDIR="$(realpath -m "$OUTDIR")"
[[ -n "${INTERVALS:-}" ]] && INTERVALS="$(realpath -m "$INTERVALS")"

#---------------------------------------
# Derived paths
#---------------------------------------
TSV_FOLDER="${OUTDIR}/tsv_folder"
[[ -z "$REF_DIR" ]]    && REF_DIR="${OUTDIR}/data_staging/ref_data"
[[ -z "$MODELS_DIR" ]] && MODELS_DIR="${OUTDIR}/data_staging/models"

#---------------------------------------
# Reference variables (update from config if provided)
#---------------------------------------
if [[ -n "$CONFIG_FILE" ]]; then
    [[ -n "${REF:-}" ]] && REF="$(realpath -m "$REF")"
    [[ -n "${DBSNP:-}" ]] && DBSNP="$(realpath -m "$DBSNP")"
    [[ -n "${KNOWN_INDELS1:-}" ]] && KNOWN_INDELS1="$(realpath -m "$KNOWN_INDELS1")"
    [[ -n "${KNOWN_INDELS2:-}" ]] && KNOWN_INDELS2="$(realpath -m "$KNOWN_INDELS2")"
fi

#---------------------------------------
# Set defaults if still empty
#---------------------------------------
[[ -z "$REF" ]]          && REF="${REF_DIR}/GRCh38.d1.vd1.fa"
[[ -z "$DBSNP" ]]        && DBSNP="${REF_DIR}/dbsnp_146.hg38.vcf.gz"
[[ -z "$KNOWN_INDELS1" ]]&& KNOWN_INDELS1="${REF_DIR}/ALL.wgs.1000G_phase3.GRCh38.ncbi_remapper.20150424.shapeit2_indels.vcf.gz"


#---------------------------------------
# mount path check
#---------------------------------------
if [[ "$PROFILE" == "singularity" ]]; then
    [[ -z "$MOUNT_PATH" ]] && die "Profile 'singularity' requires --mount_path"
    [[ -d "$MOUNT_PATH" ]] || die "Mount path does not exist: $MOUNT_PATH"
    log "Using Singularity mount path: $MOUNT_PATH"
fi

#---------------------------------------
# Logging summary
#---------------------------------------
log "---------------------------------------------"
log "  Samplesheet              : ${SAMPLESHEET:-<from config>}"
log "  Config file              : ${CONFIG_FILE:-<none>}"
log "  Output dir               : $OUTDIR"
log "  Profile                  : $PROFILE"
log "  Skip bam preprocessing   : $SKIP_PREPROCESSING"
log "  References dir           : $REF_DIR"
log "  Models dir               : $MODELS_DIR"
log "  Reference                : $REF"
log "  Intervals                : $INTERVALS"
log "  dbSNP                    : $DBSNP"
log "  Known Indels             : $KNOWN_INDELS1"
log "  Mount path               : ${MOUNT_PATH:-<none>}"
log "  Resume                   : $RESUME_REQUESTED"
log "  Request NF report        : $REQUEST_REPORT"
log "  Request NF trace         : $REQUEST_TRACE"
log "---------------------------------------------"

#---------------------------------------
# Resolve pipeline root directory (where this script lives)
#---------------------------------------
PIPELINE_DIR="$SCRIPT_DIR"

#---------------------------------------
# Prepare output directories
#---------------------------------------
mkdir -p "$OUTDIR"
PIPE_LOG="${OUTDIR}/pipeline.log"
: > "$PIPE_LOG"

mkdir -p \
    "${OUTDIR}/${BENCHMARK_DIR}" \
    "${OUTDIR}/output_01_01_preprocessed_bams" \
    "${OUTDIR}/output_01_02_candidates_strelka2" \
    "${OUTDIR}/output_01_03_vcf_postprocessing" \
    "${OUTDIR}/output_01_04_candidates_extratrees/Production_Model" \
    "${OUTDIR}/output_01_05_tensors" \
    "${OUTDIR}/output_01_06_calls_densenet"


#---------------------------------------
# 1. Prepare TSV input files
#---------------------------------------
PIPELINE_STEP="generate_tsv_files"
readarray -t REPORT_ARGS < <(generate_nf_report "$PIPELINE_STEP")
CMD=(nextflow run "${PIPELINE_DIR}" -profile "${PROFILE}" -work-dir "${OUTDIR}/work/${PIPELINE_STEP}" --samplesheet "${SAMPLESHEET}" --outdir "${OUTDIR}" --execution_step "${PIPELINE_STEP}")
CMD+=("${REPORT_ARGS[@]}")
[[ "$SKIP_PREPROCESSING" == true ]] && CMD+=(--skip_preprocessing)
[[ -n "$MOUNT_PATH" ]] && CMD+=(--mount_path "${MOUNT_PATH}")
[[ "$RESUME_REQUESTED" == true ]] && CMD+=(-resume)
run_step "Generating TSV input files" "${CMD[@]}"

#---------------------------------------
# 2. Stage reference data & models
#---------------------------------------
    PIPELINE_STEP="data_staging"
    readarray -t REPORT_ARGS < <(generate_nf_report "$PIPELINE_STEP")
CMD=(nextflow run "${PIPELINE_DIR}" -profile "${PROFILE}" -work-dir "${OUTDIR}/work/${PIPELINE_STEP}" --samplesheet "${SAMPLESHEET}" --outdir "${OUTDIR}" --execution_step "${PIPELINE_STEP}")
    CMD+=("${REPORT_ARGS[@]}")
    [[ -n "$MOUNT_PATH" ]] && CMD+=(--mount_path "${MOUNT_PATH}")
[[ "$RESUME_REQUESTED" == true ]] && CMD+=(-resume)
    run_step "Staging reference data and models" "${CMD[@]}"

# Validate staged inputs required by downstream modules.
[[ -d "$REF_DIR" ]] || die "Reference directory does not exist after data staging: $REF_DIR"
[[ -d "$MODELS_DIR" ]] || die "Models directory does not exist after data staging: $MODELS_DIR"
[[ -f "$REF" ]] || die "Reference FASTA missing: $REF"
if [[ ! -f "$INTERVALS" ]]; then
    log "WARNING: Intervals BED missing: $INTERVALS. Pipeline will run in WGS mode."
fi
[[ -f "${MODELS_DIR}/3ddensenet_snv.pt" ]] || die "SNV DenseNet model missing: ${MODELS_DIR}/3ddensenet_snv.pt"
[[ -f "${MODELS_DIR}/3ddensenet_indel.pt" ]] || die "INDEL DenseNet model missing: ${MODELS_DIR}/3ddensenet_indel.pt"
[[ -f "${MODELS_DIR}/extra_trees.snv.joblib" ]] || die "SNV ExtraTrees model missing: ${MODELS_DIR}/extra_trees.snv.joblib"
[[ -f "${MODELS_DIR}/extra_trees.indel.joblib" ]] || die "INDEL ExtraTrees model missing: ${MODELS_DIR}/extra_trees.indel.joblib"

#---------------------------------------
# 3. BAM preprocessing
#---------------------------------------
if [[ "$SKIP_PREPROCESSING" == true ]]; then
    log "Skipping BAM preprocessing"
else
    PIPELINE_STEP="bam_preprocessing"
    readarray -t REPORT_ARGS < <(generate_nf_report "$PIPELINE_STEP")
    [[ -f "$DBSNP" ]] || die "dbSNP VCF missing: $DBSNP"
    [[ -f "$KNOWN_INDELS1" ]] || die "Known indels VCF missing: $KNOWN_INDELS1"

    BAM_INTERVALS_PARAM=()
    if [[ -f "$INTERVALS" ]]; then
        BAM_INTERVALS_PARAM=(--intervals "$INTERVALS")
    else
        log "WARNING: BAM preprocessing is running without intervals because Intervals BED is unavailable."
    fi

    CMD=(nextflow run tron-bioinformatics/tronflow-bam-preprocessing
        --r v2.2.2
        -profile "${PROFILE}"
        -work-dir "${OUTDIR}/work/${PIPELINE_STEP}"
        --input_files "${TSV_FOLDER}/preproc.tsv"
        --reference "${REF}"
        --dbsnp "${DBSNP}"
        --known_indels1 "${KNOWN_INDELS1}"
        --output "${OUTDIR}/output_01_01_preprocessed_bams"
        --skip_prepare_bam
        --skip_metrics)
    CMD+=("${BAM_INTERVALS_PARAM[@]}")
    CMD+=("${REPORT_ARGS[@]}")

    # add custom BAM preprocessing config if provided
    [[ -n "$BAM_PREP_CONFIG" ]] && CMD+=(-c "$BAM_PREP_CONFIG")
    [[ "$RESUME_REQUESTED" == true ]] && CMD+=(-resume)
    run_step "BAM preprocessing" "${CMD[@]}"
fi

#---------------------------------------
# 4. Candidate calling (Strelka2)
#---------------------------------------
PIPELINE_STEP="candidate_calling"
readarray -t REPORT_ARGS < <(generate_nf_report "$PIPELINE_STEP")
# Handle intervals only if BED exists
INTERVALS_PARAM=()
[[ -f "$INTERVALS" ]] && INTERVALS_PARAM=(--intervals "$INTERVALS")

CMD=(nextflow run tron-bioinformatics/tronflow-strelka2
    -profile "${PROFILE}"
    -work-dir "${OUTDIR}/work/${PIPELINE_STEP}"
    --input_files "${TSV_FOLDER}/pairs_wo_reps.tsv"
    --reference "${REF}"
    --output "${OUTDIR}/output_01_02_candidates_strelka2"
    -r v0.2.5
)
CMD+=("${REPORT_ARGS[@]}")
# Include custom config only if provided
[[ -n "$STRELKA_CONFIG" ]] && CMD+=("-c" "$STRELKA_CONFIG")
# Add optional intervals
CMD+=("${INTERVALS_PARAM[@]}")
[[ "$RESUME_REQUESTED" == true ]] && CMD+=(-resume)
[[ -n "$MOUNT_PATH" ]] && CMD+=("--mount_path" "$MOUNT_PATH")
run_step "Candidate calling (Strelka2)" "${CMD[@]}"

#---------------------------------------
# 5. Feature generation
#---------------------------------------
PIPELINE_STEP="feature_generation"
readarray -t REPORT_ARGS < <(generate_nf_report "$PIPELINE_STEP")
CMD=(nextflow run tron-bioinformatics/tronflow-vcf-postprocessing
    -r v3.1.4
    -profile "${PROFILE}"
    -work-dir "${OUTDIR}/work/${PIPELINE_STEP}"
    --input_vcfs "${TSV_FOLDER}/vcfs.tsv"
    --input_bams "${TSV_FOLDER}/bams.tsv"
    --reference "${REF}"
--output "${OUTDIR}/output_01_03_vcf_postprocessing")
CMD+=("${REPORT_ARGS[@]}")
# Add custom VCF postprocessing config if provided
[[ -n "$VCF_POST_CONFIG" ]] && CMD+=(-c "$VCF_POST_CONFIG")
[[ "$RESUME_REQUESTED" == true ]] && CMD+=(-resume)
    run_step "Feature generation" "${CMD[@]}"

#---------------------------------------
# 6. ExtraTrees candidate filtering
#---------------------------------------
PIPELINE_STEP="candidate_filtering"
readarray -t REPORT_ARGS < <(generate_nf_report "$PIPELINE_STEP")
CMD=(nextflow run "${PIPELINE_DIR}" -profile "${PROFILE}" -work-dir "${OUTDIR}/work/${PIPELINE_STEP}" --samplesheet "${SAMPLESHEET}" --outdir "${OUTDIR}" --execution_step "${PIPELINE_STEP}")
CMD+=("${REPORT_ARGS[@]}")
[[ "$RESUME_REQUESTED" == true ]] && CMD+=(-resume)
[[ -n "$MOUNT_PATH" ]] && CMD+=(--mount_path "${MOUNT_PATH}")
run_step "ExtraTrees candidate filtering" "${CMD[@]}"

#---------------------------------------
# 7. Tensor generation
#---------------------------------------
PIPELINE_STEP="tensor_generation"
readarray -t REPORT_ARGS < <(generate_nf_report "$PIPELINE_STEP")
CMD=(nextflow run tron-bioinformatics/bam2tensor
    -r 1.0.2
    -profile "${PROFILE}"
    -work-dir "${OUTDIR}/work/${PIPELINE_STEP}"
    --input_files "${TSV_FOLDER}/pairs_w_cands.tsv"
    --publish_dir "${OUTDIR}/output_01_05_tensors"
    --reference "${REF}"
    --window 150
    --max_coverage 500
    --read_length 50
    --max_mapq 60
--max_baseq 82)
CMD+=("${REPORT_ARGS[@]}")
# Add custom bam2tensor config if provided
[[ -n "$BAM2TENSOR_CONFIG" ]] && CMD+=(-c "$BAM2TENSOR_CONFIG")
[[ "$RESUME_REQUESTED" == true ]] && CMD+=(-resume)
run_step "Tensor generation" "${CMD[@]}"

#---------------------------------------
# 8. 3D DenseNet variant calling
#---------------------------------------
PIPELINE_STEP="variant_calling"
readarray -t REPORT_ARGS < <(generate_nf_report "$PIPELINE_STEP")
CMD=(nextflow run "${PIPELINE_DIR}" -profile "${PROFILE}" -work-dir "${OUTDIR}/work/${PIPELINE_STEP}" --samplesheet "${SAMPLESHEET}" --outdir "${OUTDIR}" --execution_step "${PIPELINE_STEP}")
CMD+=("${REPORT_ARGS[@]}")
[[ "$RESUME_REQUESTED" == true ]] && CMD+=(-resume)
[[ -n "$MOUNT_PATH" ]] && CMD+=(--mount_path "$MOUNT_PATH")
run_step "3D DenseNet SNV/Indel calling" "${CMD[@]}"

cp ${OUTDIR}/output_01_06_calls_densenet/*.somatic_snv.VariantMedium.tsv ${OUTDIR}/
cp ${OUTDIR}/output_01_06_calls_densenet/*.somatic_snv.VariantMedium.vcf ${OUTDIR}/

log "Pipeline completed successfully"
