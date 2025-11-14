// nf orchestrator for variant medium

// include subworkflows
include { DATA_STAGING      } from './../subworkflows/data_staging/main'
include { PARSE_SAMPLESHEET } from './../subworkflows/parse_samplesheet/main'

// variant medium modules
include { CALL_VARIANTS     } from './../modules/variantmedium/call/main'
include { FILTER_CANDIDATES } from './../modules/variantmedium/filter/main'


workflow VARIANTMEDIUM {

    take:

    ch_samplesheet

    main:

    ch_temp = channel.empty()
    ch_samples = channel.empty()

    ch_references_path = channel.fromPath("${params.reference_path}" ? "${params.reference_path}": "ref")
    ch_models_path = channel.fromPath("${params.models_path}" ? "${params.models_path}": "models")

    
    // run data staging if --run_data_staging is true
    if (params.run_data_staging) {

        DATA_STAGING (
            ch_references_path,
            ch_models_path
        )

    }

    // get samples from samplesheet
    ch_samplesheet = channel.fromPath("${params.samplesheet}")
    PARSE_SAMPLESHEET(ch_samplesheet)

    // filter candidate variants
    FILTER_CANDIDATES ()


}