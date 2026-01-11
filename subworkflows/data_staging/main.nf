//
// data staging for variant medium - references, models
//

include { STAGE_REFERENCES } from '../../modules/stage_refs/main'
include { STAGE_MODELS     } from '../../modules/stage_models/main'



workflow DATA_STAGING {

    take:
    ch_reference_dir // channel: [ val(meta), ["output-path-to-references"]]
    ch_models_dir    // channel: [ val(meta), ["output-path-to-models"]]

    main:

    ch_versions         = channel.empty()

    // stage reference files
    STAGE_REFERENCES("${params.bed_url}", ch_reference_dir)
    ch_versions = ch_versions.mix(STAGE_REFERENCES.out.versions)

    // stage models for indel and snv calling
    STAGE_MODELS(ch_models_dir)
    ch_versions = ch_versions.mix(STAGE_MODELS.out.versions)

    emit:

    versions     = ch_versions         // channel: [ versions.yml ]
}