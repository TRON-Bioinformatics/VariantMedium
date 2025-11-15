include { PREPARE_INPUTS } from './../modules/prepare_inputs/main'


workflow PREPARE_PIPELINE_INPUTS {

    take:
    ch_samplesheet

    main:

    PREPARE_INPUTS (
        ch_samplesheet,
        params.skip_preprocessing
    )

}