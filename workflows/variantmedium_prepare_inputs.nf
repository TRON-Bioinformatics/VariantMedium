include { PREPARE_INPUTS } from './../modules/prepare_inputs/main'


workflow VARIANTMEDIUM_PREPARE_INPUTS {

    take:
    ch_samplesheet

    main:

    PREPARE_INPUTS (
        ch_samplesheet,
        params.skip_preprocessing
    )

}