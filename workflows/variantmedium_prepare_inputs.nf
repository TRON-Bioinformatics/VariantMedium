include { PREPARE_INPUTS } from './../modules/prepare_inputs/main'


workflow VARIANTMEDIUM_PREPARE_INPUTS {

    take:
    ch_samplesheet
    ch_output_path

    main:

    PREPARE_INPUTS (
        ch_samplesheet,
        ch_output_path,
        params.skip_preprocessing
    )

}