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

REQUIRED ARGUMENTS:
  --samplesheet               PATH        Path to the input CSV/TSV samplesheet
  --outdir                    PATH        Output directory for all pipeline results
  --profile                   STRING      Nextflow profile name (conda, singularity) [default: conda]
                                          [Parts of the pipeline may not support singularity - Prefer using conda]

OPTIONAL ARGUMENTS:
  --config                    PATH        Path to custom config file (.conf)
  --mount_path                PATH        Path to mount when using singularity profile [required for the singularity profile]
  --skip_data_staging                     Skip staging reference data & models
  --skip_preprocessing                    Skip BAM preprocessing step
  --skip_candidate_calling                Skip candidate calling step (if already generated VCFs are available)
  --skip_feature_generation               Skip VCF postprocessing / feature generation step (if already generated features are available)
  --skip_candidate_filtering              Skip ExtraTrees candidate filtering step (if already filtered candidates are available)
  --skip_tensor_generation                Skip tensor generation (if already generated tensors are available)
  --resume                                Resume from previous run
  --nf_report                             Generate Nextflow execution report
  --nf_trace                              Generate Nextflow execution trace
  --strelka_config            PATH        Path to custom Strelka2 config file
  --bam_prep_config           PATH        Path to custom BAM preprocessing config file
  --vcf_post_config           PATH        Path to custom VCF postprocessing config file
  --bam2tensor_config         PATH        Path to custom bam2tensor config file
  -h, --help                              Show this help message and exit

EOF
    exit 0
}

#---------------------------------------
# Parse arguments
#---------------------------------------
EXECUTION_STEP=""
SAMPLESHEET=""
OUTDIR=""
PROFILE="conda"
SKIP_DATA_STAGING=false
SKIP_PREPROCESSING=false
SKIP_CANDIDATE_CALLING=false
SKIP_FEATURE_GENERATION=false
SKIP_CANDIDATE_FILTERING=false
SKIP_TENSOR_GENERATION=false
CONFIG_FILE=""
MOUNT_PATH=""
RESUME=""
REQUEST_REPORT=false
REQUEST_TRACE=false
STRELKA_CONFIG=""
BAM_PREP_CONFIG=""
VCF_POST_CONFIG=""
BAM2TENSOR_CONFIG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        # required args
        --samplesheet) SAMPLESHEET="$2"; shift 2;;
        --outdir) OUTDIR="$2"; shift 2;;
        --profile) PROFILE="$2"; shift 2;;
        # optional args
        --config) CONFIG_FILE="$2"; shift 2;;
        --mount_path) MOUNT_PATH="$2"; shift 2;;
        --skip_data_staging) SKIP_DATA_STAGING=true; shift;;
        --skip_preprocessing) SKIP_PREPROCESSING=true; shift;;
        # debug options
        --skip_candidate_calling) SKIP_CANDIDATE_CALLING=true; shift;;
        --skip_feature_generation) SKIP_FEATURE_GENERATION=true; shift;;
        --skip_candidate_filtering) SKIP_CANDIDATE_FILTERING=true; shift;;
        --skip_tensor_generation) SKIP_TENSOR_GENERATION=true; shift;;
        # nf options
        --resume) RESUME="-resume"; shift;;
        --nf_report) REQUEST_REPORT=true; shift;;
        --nf_trace) REQUEST_TRACE=true; shift;;
        # custom config files
        --strelka_config) STRELKA_CONFIG="$2"; shift 2;;
        --bam_prep_config) BAM_PREP_CONFIG="$2"; shift 2;;
        --vcf_post_config) VCF_POST_CONFIG="$2"; shift 2;;
        --bam2tensor_config) BAM2TENSOR_CONFIG="$2"; shift 2;;
        -h|--help) usage;;
        *) die "Unknown argument: $1";;
    esac
done

#---------------------------------------
# Argument validation
#---------------------------------------

[[ -z "$SAMPLESHEET" ]] && die "Please provide samplesheet with the --samplesheet option"
[[ -f "$SAMPLESHEET" ]] || die "Samplesheet does not exist: $SAMPLESHEET"
[[ -z "$OUTDIR" ]] && die "--outdir is required"

# After OUTDIR is known, prepare report/trace args if requested
REPORT_ARGS=()
TRACE_ARGS=()
if [[ "$REQUEST_REPORT" == true ]]; then
    REPORT_ARGS=(-with-report "${OUTDIR}/report.html")
fi
if [[ "$REQUEST_TRACE" == true ]]; then
    TRACE_ARGS=(-with-trace "${OUTDIR}/trace.txt")
fi

#---------------------------------------
# mount path check
#---------------------------------------
if [[ "$PROFILE" == "singularity" ]]; then
    if [[ -z "$MOUNT_PATH" ]]; then
        die "Profile 'singularity' requires --mount_path to be provided."
    fi
    if [[ ! -d "$MOUNT_PATH" ]]; then
        die "Mount path does not exist: $MOUNT_PATH"
    fi
    log "Using Singularity mount path: $MOUNT_PATH"
fi

#---------------------------------------
# Derived paths
#---------------------------------------

TSV_FOLDER="${OUTDIR}/tsv_folder"
REF_DIR="${OUTDIR}/data_staging/ref_data"
REF="${REF_DIR}/GRCh38.d1.vd1.fa"
EXOME_BED="${REF_DIR}/S07604624_Covered.bed.gz"
DBSNP="${REF_DIR}/dbsnp_146.hg38.vcf.gz"
KNOWN_INDELS1="${REF_DIR}/ALL.wgs.1000G_phase3.GRCh38.ncbi_remapper.20150424.shapeit2_indels.vcf.gz"

# ------------------------------
# Load config file if provided
# ------------------------------
if [[ -n "$CONFIG_FILE" ]]; then
    [[ -f "$CONFIG_FILE" ]] || die "Config file not found: $CONFIG_FILE"
    log "Loading config: $CONFIG_FILE"
    source "$CONFIG_FILE"
fi

#---------------------------------------
log "---------------------------------------------"
log "Samplesheet              : $SAMPLESHEET"
log "Output directory         : $OUTDIR"
log "Profile                  : $PROFILE"
log "Skip Data Staging        : $SKIP_DATA_STAGING"
log "Skip BAM preprocessing   : $SKIP_PREPROCESSING"
log "Skip Candidate Calling   : $SKIP_CANDIDATE_CALLING"
log "Skip Feature Generation  : $SKIP_FEATURE_GENERATION"
log "Skip Candidate Filtering : $SKIP_CANDIDATE_FILTERING"
log "Skip Tensor Generation   : $SKIP_TENSOR_GENERATION"
log "---------------------------------------------"
#---------------------------------------

mkdir -p "$OUTDIR"
PIPE_LOG="${OUTDIR}/pipeline.log"
: > "$PIPE_LOG"

#---------------------------------------
mkdir -p \
    "${OUTDIR}/output_01_01_preprocessed_bams" \
    "${OUTDIR}/output_01_02_candidates_strelka2" \
    "${OUTDIR}/output_01_03_vcf_postprocessing" \
    "${OUTDIR}/output_01_04_candidates_extratrees/Production_Model" \
    "${OUTDIR}/output_01_05_tensors" \
    "${OUTDIR}/output_01_06_calls_densenet"

#---------------------------------------
# 1. Prepare TSV input files
#---------------------------------------
EXECUTION_STEP="generate_tsv_files"
CMD=(nextflow run main.nf
    -profile "${PROFILE}"
    --samplesheet "${SAMPLESHEET}"
    --outdir "${OUTDIR}"
    --execution_step "${EXECUTION_STEP}"
)
# add report/trace args if requested
CMD+=("${REPORT_ARGS[@]}" "${TRACE_ARGS[@]}")

[[ "$SKIP_PREPROCESSING" == true ]] && CMD+=(--skip_preprocessing)
[[ -n "$MOUNT_PATH" ]] && CMD+=(--mount_path "${MOUNT_PATH}")
[[ -n "$RESUME" ]] && CMD+=("$RESUME")

run_step "Generating TSV input files" "${CMD[@]}"

#---------------------------------------
# 2. Stage reference data & models
#---------------------------------------
EXECUTION_STEP="stage_data"
if [[ "$SKIP_DATA_STAGING" == true ]]; then
    log "⚠️ Skipping data staging"
else
    CMD=(nextflow run main.nf
        -profile "${PROFILE}"
        --samplesheet "${SAMPLESHEET}"
        --outdir "${OUTDIR}"
        --execution_step "${EXECUTION_STEP}"
    )
    CMD+=("${REPORT_ARGS[@]}" "${TRACE_ARGS[@]}")
    [[ -n "$MOUNT_PATH" ]] && CMD+=(--mount_path "${MOUNT_PATH}")
    [[ -n "$RESUME" ]] && CMD+=("$RESUME")

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
    )
    CMD+=("${REPORT_ARGS[@]}" "${TRACE_ARGS[@]}")

    # add custom BAM preprocessing config if provided
    [[ -n "$BAM_PREP_CONFIG" ]] && CMD+=(-c "$BAM_PREP_CONFIG")

    [[ -n "$RESUME" ]] && CMD+=("$RESUME")
    run_step "BAM preprocessing" "${CMD[@]}"
    popd >/dev/null
fi

#---------------------------------------
# 4. Candidate calling (Strelka2)
#---------------------------------------
if [[ "$SKIP_CANDIDATE_CALLING" == true ]]; then
    log "⚠️ Skipping Candidate Calling (Strelka2)"
else
    pushd "${OUTDIR}/output_01_02_candidates_strelka2" >/dev/null

    # Handle intervals only if BED exists
    INTERVALS_PARAM=()
    [[ -f "$EXOME_BED" ]] && INTERVALS_PARAM=(--intervals "$EXOME_BED")

    CMD=(nextflow run tron-bioinformatics/tronflow-strelka2
        -profile "${PROFILE}"
        --input_files "${TSV_FOLDER}/pairs_wo_reps.tsv"
        --reference "${REF}"
        --output "${OUTDIR}/output_01_02_candidates_strelka2"
        -r v0.2.4
    )
    CMD+=("${REPORT_ARGS[@]}" "${TRACE_ARGS[@]}")

    # Include custom config only if provided
    [[ -n "$STRELKA_CONFIG" ]] && CMD+=(-c "$STRELKA_CONFIG")

    # Add optional intervals
    CMD+=("${INTERVALS_PARAM[@]}")

    # Resume and mount
    [[ -n "$RESUME" ]] && CMD+=("$RESUME")
    [[ -n "$MOUNT_PATH" ]] && CMD+=(--mount_path "${MOUNT_PATH}")

    run_step "Candidate calling (Strelka2)" "${CMD[@]}"
    popd >/dev/null
fi

#---------------------------------------
# 5. Feature generation
#---------------------------------------
if [[ "$SKIP_FEATURE_GENERATION" == true ]]; then
    log "⚠️ Skipping VCF postprocessing"
else
    CMD=(nextflow run tron-bioinformatics/tronflow-vcf-postprocessing
        -r v3.1.2
        -profile "${PROFILE}"
        --input_vcfs "${TSV_FOLDER}/vcfs.tsv"
        --input_bams "${TSV_FOLDER}/bams.tsv"
        --reference "${REF}"
        --output "${OUTDIR}/output_01_03_vcf_postprocessing"
    )
    CMD+=("${REPORT_ARGS[@]}" "${TRACE_ARGS[@]}")

    # Add custom VCF postprocessing config if provided
    [[ -n "$VCF_POST_CONFIG" ]] && CMD+=(-c "$VCF_POST_CONFIG")

    [[ -n "$RESUME" ]] && CMD+=("$RESUME")
    run_step "Feature generation" "${CMD[@]}"
fi

#---------------------------------------
# 6. ExtraTrees candidate filtering
#---------------------------------------
if [[ "$SKIP_CANDIDATE_FILTERING" == true ]]; then
    log "⚠️ Skipping ExtraTrees candidate filtering"
else
    EXECUTION_STEP="filter_candidates"
    CMD=(nextflow run main.nf
        -profile "${PROFILE}"
        --samplesheet "${SAMPLESHEET}"
        --outdir "${OUTDIR}"
        --execution_step "${EXECUTION_STEP}"
    )
    CMD+=("${REPORT_ARGS[@]}" "${TRACE_ARGS[@]}")
    [[ -n "$RESUME" ]] && CMD+=("$RESUME")
    [[ -n "$MOUNT_PATH" ]] && CMD+=(--mount_path "${MOUNT_PATH}")
    run_step "ExtraTrees candidate filtering" "${CMD[@]}"
fi
#---------------------------------------
# 7. Tensor generation
#---------------------------------------
if [[ "$SKIP_TENSOR_GENERATION" == true ]]; then
    log "⚠️ Skipping Tensor generation"
else
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
    )
    CMD+=("${REPORT_ARGS[@]}" "${TRACE_ARGS[@]}")

    # Add custom bam2tensor config if provided
    [[ -n "$BAM2TENSOR_CONFIG" ]] && CMD+=(-c "$BAM2TENSOR_CONFIG")

    [[ -n "$RESUME" ]] && CMD+=("$RESUME")
    run_step "Tensor generation" "${CMD[@]}"
    popd >/dev/null
fi
#---------------------------------------
# 8. 3D DenseNet variant calling
#---------------------------------------

pushd "${OUTDIR}/output_01_06_calls_densenet" >/dev/null

EXECUTION_STEP="call_variants"
CMD=(nextflow run main.nf
    -profile "${PROFILE}"
    --samplesheet "${SAMPLESHEET}"
    --outdir "${OUTDIR}/output_01_06_calls_densenet"
    --execution_step "${EXECUTION_STEP}"
)
CMD+=("${REPORT_ARGS[@]}" "${TRACE_ARGS[@]}")
[[ -n "$RESUME" ]] && CMD+=("$RESUME")
[[ -n "$MOUNT_PATH" ]] && CMD+=(--mount_path "${MOUNT_PATH}")
run_step "3D DenseNet SNV/Indel calling" "${CMD[@]}"
popd >/dev/null

#---------------------------------------
log "🎉 Pipeline completed successfully!"
#---------------------------------------
