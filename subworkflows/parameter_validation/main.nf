workflow VALIDATE_PARAMETERS {

    log.info "[INFO] Validating parameters"

    // check for outdir
    if(!params.outdir) {
        log.error "Please provide a output directory with --outdir"
        exit(1)
    }
    
    // check for samplesheet
    if(!params.samplesheet) {
        log.error "Please provide a samplesheet with --samplesheet"
        exit(1)
    }
    
    // check for execution step
    if(!params.execution_step) {
        log.error "Please provide an execution step with --execution_step"
        exit(1)
    }
    
    // check if execution step is valid
    def valid_steps = ["generate_tsv_files", "data_staging", "candidate_filtering", "variant_calling"]
    if(!valid_steps.contains(params.execution_step)) {
        log.error "Invalid execution step: ${params.execution_step}. Valid options are: [${valid_steps.join(', ')}]"
        exit(1)
    }

    // check if mount_path is provided when run with singularity
    if(workflow.profile.contains("singularity") && !params.mount_path) {
        log.error "Please provide path to the bam files as bind mount when running with singularity profile with --mount_path"
        exit(1)
    }

    log.info "[INFO] Parameters validated successfully"

}