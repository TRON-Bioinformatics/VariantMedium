#!/usr/bin/env bash

log() {
    printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

safe_step_key() {
    local raw="$1"
    local key
    key="$(echo "$raw" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '_')"
    key="${key#_}"
    key="${key%_}"
    printf "%s" "$key"
}

get_resume_token() {
    local step="$1"
    local key
    key="$(safe_step_key "$step")"

    [[ -f "$RESUME_DB" ]] || return 0
    awk -F'\t' -v k="$key" '$1==k {print $2}' "$RESUME_DB" | tail -n1
}

save_resume_token() {
    local step="$1"
    local token="$2"
    local key tmp
    key="$(safe_step_key "$step")"
    tmp="${RESUME_DB}.tmp"

    touch "$RESUME_DB"
    awk -F'\t' -v k="$key" '$1!=k {print $1"\t"$2}' "$RESUME_DB" > "$tmp"
    printf "%s\t%s\n" "$key" "$token" >> "$tmp"
    mv "$tmp" "$RESUME_DB"
}

append_resume_args() {
    local step="$1"
    local -n cmd_ref="$2"
    local token

    [[ "$RESUME_REQUESTED" == true ]] || return 0

    # Avoid passing -resume more than once for a single Nextflow invocation.
    if [[ " ${cmd_ref[*]} " == *" -resume "* ]]; then
        return 0
    fi

    token="$(get_resume_token "$step")"
    if [[ -n "$token" ]]; then
        cmd_ref+=("-resume" "$token")
        log "Using step-specific resume token for ${step}: ${token}"
    else
        cmd_ref+=("-resume")
        log "No stored resume token for ${step}; using default -resume"
    fi
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
    local step_log session_id cmd_str
    step_log="${OUTDIR}/.nextflow_${PIPELINE_STEP}.log"

    if [[ "${RESUME_REQUESTED:-false}" == true ]]; then
        printf -v cmd_str '%q ' "${cmd[@]}"
        log "DEBUG command (${PIPELINE_STEP}): ${cmd_str}"
    fi

    # Run command and stream stdout/stderr.
    "${cmd[@]}" 2>&1 | tee -a "${OUTDIR}/pipeline.log" | tee "$step_log"
    local status=${PIPESTATUS[0]}
    if [[ "$status" -ne 0 ]]; then
        die "Step failed: $step"
    fi

    if [[ "${cmd[0]}" == "nextflow" && -n "${PIPELINE_STEP:-}" ]]; then
        session_id="$(awk '
            BEGIN { id = "" }
            {
                if (match($0, /[Ss]ession UUID:[[:space:]]*[0-9a-fA-F-]+/)) {
                    s = substr($0, RSTART, RLENGTH)
                    sub(/[Ss]ession UUID:[[:space:]]*/, "", s)
                    id = s
                }
            }
            END { print id }
        ' "$step_log" || true)"
        if [[ -n "$session_id" ]]; then
            save_resume_token "$PIPELINE_STEP" "$session_id"
            log "Stored resume token for ${PIPELINE_STEP}: ${session_id}"
        else
            log "WARNING: Could not detect Session UUID for ${PIPELINE_STEP}; resume token was not updated (non-fatal)."
        fi
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

