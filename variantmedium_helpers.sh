#!/usr/bin/env bash

log() {
    printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

die() {
    log "ERROR: $1"
    exit 1
}

run_step() {
    local step="$1"
    shift
    log "Started: $step"

    local cmd=("$@")
    local step_log
    step_log="${OUTDIR}/.nextflow_${PIPELINE_STEP}.log"

    # Run command and stream stdout/stderr.
    "${cmd[@]}" 2>&1 | tee -a "${OUTDIR}/pipeline.log" | tee "$step_log"
    local status=${PIPESTATUS[0]}
    if [[ "$status" -ne 0 ]]; then
        die "Step failed: $step"
    fi

    log "Completed: $step"
}

# Build Nextflow report/trace args for a given pipeline step.
generate_nf_report() {
    local step="$1"
    if [[ "${REQUEST_REPORT}" == true ]]; then
        printf '%s\n' "-with-report" "${OUTDIR}/${BENCHMARK_DIR}/report_${step}.html"
    fi
    if [[ "${REQUEST_TRACE}" == true ]]; then
        printf '%s\n' "-with-trace" "${OUTDIR}/${BENCHMARK_DIR}/trace_${step}.txt"
    fi
}

