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
    STAGE_REFERENCES(ch_reference_dir)
    ch_versions = ch_versions.mix(STAGE_REFERENCES.out.versions)

    // stage models for indel and snv calling
    STAGE_MODELS(ch_models_dir)
    ch_versions = ch_versions.mix(STAGE_MODELS.out.versions)

    emit:
    
    // references
    grch38_vcf_gz           = STAGE_REFERENCES.out.grch38_vcf_gz
    dbsnp_vcf_gz            = STAGE_REFERENCES.out.dbsnp_vcf_gz
    grch38_gatk_indices     = STAGE_REFERENCES.out.grch38_gatk_indices
    grch38_dict             = STAGE_REFERENCES.out.grch38_dict
    grch38_fa               = STAGE_REFERENCES.out.grch38_fa
    grch38_fai              = STAGE_REFERENCES.out.grch38_fai
    grch38_fa_targz         = STAGE_REFERENCES.out.grch38_fa_targz
    covered_bb_S07604624    = STAGE_REFERENCES.out.covered_bb_S07604624
    covered_bed_S07604624   = STAGE_REFERENCES.out.covered_bed_S07604624
    
    // models
    model_ddensenet_indel   = STAGE_MODELS.out.ddensenet_indel
    model_ddensenet_snv     = STAGE_MODELS.out.ddensenet_snv
    model_extra_trees_indel = STAGE_MODELS.out.extra_trees_indel
    model_extra_trees_snv   = STAGE_MODELS.out.extra_trees_snv

    versions     = ch_versions         // channel: [ versions.yml ]
}