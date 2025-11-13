include { PREPARE_PIPELINE_INPUTS  } from './workflow/prepareinputs'
include { VARIANTMEDIUM            } from './workflow/variantmedium'

workflow {

    // ----------------------------------------
    // Check if outdir is provided
    // ----------------------------------------
    if( !params.outdir ) {
        log.error "ERROR: Please provide a output directory with --outdir"
    }
    
    // ----------------------------------------
    // Check if samplesheet is provided
    // ----------------------------------------
    if( !params.samplesheet ) {
        log.error "ERROR: Please provide a samplesheet with --samplesheet"
    }

    // ----------------------------------------
    // Check if the file exists
    // ----------------------------------------
    def samplesheetFile = file(params.samplesheet)
    if( !samplesheetFile.exists() ) {
        log.error "ERROR: Samplesheet filepath does not exist: ${params.samplesheet}"
    }  else {
        ch_samplesheet = channel.fromPath("${params.samplesheet}")
    }

    log.info "[INFO] Using samplesheet: ${samplesheetFile}"


    // prepare input files for variantmedium workflow
    if (params.prepare_inputs_dir) {

        ch_outdir = channel.fromPath("${params.outdir}")
        ch_prepare_inputs_dir = channel.fromPath("${params.prepare_input_dir}")

        PREPARE_PIPELINE_INPUTS(
            ch_samplesheet,
            ch_outdir,
            ch_prepare_inputs_dir,
            params.skip_bam_preprocessing
        )

    }
    
    // VARIANTMEDIUM(ch_samplesheet)

}