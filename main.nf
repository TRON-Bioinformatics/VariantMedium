include { PREPARE_PIPELINE_INPUTS } from './workflows/prepare_inputs'
include { PARSE_SAMPLESHEET       } from './subworkflows/parse_samplesheet'
include { VARIANTMEDIUM           } from './workflows/variantmedium'

workflow {

    // ----------------------------------------
    // Check if required params are provided
    // ----------------------------------------
    //output dir check
    if(!params.outdir) {
        log.error "Please provide a output directory with --outdir"
    }
    // check for samplesheet
    if(!params.samplesheet) {
        log.error "Please provide a samplesheet with --samplesheet"
    }
    // check for execution step
    if(!params.execution_step) {
        log.error "Please provide an execution step with --execution_step"
    }
    // check if data_dir is provided when run with singularity
    if(workflow.profile.contains("singularity") && !params.data_dir) {
        log.error "Please provide path to the bam files as bind mount when running with singularity"
    }

    // ----------------------------------------
    // Samplesheet validation
    // ----------------------------------------
    ch_samplesheet = channel.empty()
    def samplesheetFile = file(params.samplesheet)
    if( !samplesheetFile.exists() ) {
        log.error "ERROR: Samplesheet filepath does not exist: ${params.samplesheet}"
    }  else {
        ch_samplesheet = channel.fromPath("${params.samplesheet}")
    }
    log.info "[INFO] Samplesheet -> ${samplesheetFile}"
    PARSE_SAMPLESHEET(ch_samplesheet)

    // ----------------------------------------
    // Prepare inputs
    // ----------------------------------------
    if (params.execution_step == "prepare_inputs") {
        PREPARE_PIPELINE_INPUTS(ch_samplesheet)
    }
    
    // ----------------------------------------
    // Run variantmedium
    // ----------------------------------------
    if (params.execution_step == "call") {
        VARIANTMEDIUM(ch_samplesheet)
    }

}