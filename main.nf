// nf orchestrator for variant medium

// data staging subworkflow
include { DATA_STAGING } from './subworkflows/data_staging/main'

// variant medium modules
include { CALL_VARIANTS     } from './modules/variantmedium/run/main'
include { FILTER_CANDIDATES } from './modules/variantmedium/filter/main'

// multiqc
include { MULTIQC } from './modules/multiqc/main'



workflow VARIANTMEDIUM {

    
    main:

    ch_references_path = channel.fromPath("ref")
    ch_models_path = channel.fromPath("models")

    // run data staging if --run_data_staging is true
    DATA_STAGING (
        ch_references_path,
        ch_models_path
    )


}

workflow {

    VARIANTMEDIUM()
}