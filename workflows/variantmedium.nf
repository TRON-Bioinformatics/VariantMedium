// nf orchestrator for variant medium

// include subworkflows
include { DATA_STAGING      } from './../subworkflows/data_staging/main'

// variant medium modules
include { CALL_VARIANTS     } from './../modules/variantmedium/call/main'
include { FILTER_CANDIDATES } from './../modules/variantmedium/filter/main'


workflow VARIANTMEDIUM {

    take:

    ch_samples

    main:

    ch_samples = channel.empty()

    
    // run data staging if --run_data_staging is true
    if (params.run_data_staging) {

        DATA_STAGING (
            params.reference_path,
            params.models_path  
        )

    }

    // filter candidate variants
    // FILTER_CANDIDATES ()


}