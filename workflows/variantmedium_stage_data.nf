include { DATA_STAGING } from './../subworkflows/data_staging/main'


workflow VARIANTMEDIUM_STAGE_DATA {

    main:

    DATA_STAGING (
        "${params.reference_dir}",
        "${params.models_dir}"
    )

}