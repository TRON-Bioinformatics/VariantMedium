// nf orchestrator for variant medium candidate filtering step

include { FILTER_CANDIDATES as FILTER_CANDIDATES_SNV   } from './../modules/variantmedium/filter/main'
include { FILTER_CANDIDATES as FILTER_CANDIDATES_INDEL } from './../modules/variantmedium/filter/main'



workflow VARIANTMEDIUM_FILTER_CANDIDATES {

    take:

    ch_input_tsv
    ch_output_dir
    ch_model_extra_trees_snv
    ch_model_extra_trees_indel

    main:

    ch_versions = channel.empty()
    ch_filtered_candidates_indels = channel.empty()
    ch_filtered_candidates_snvs   = channel.empty()

    // indel filtering
    if ( params.indel_calling ) {
        
        FILTER_CANDIDATES_INDEL (
            ch_input_tsv,
            ch_model_extra_trees_indel,
            'indel',
            ch_output_dir
        )
        ch_filtered_candidates_indels = FILTER_CANDIDATES_INDEL.out.filtered_candidates
        ch_versions = ch_versions.mix(FILTER_CANDIDATES_INDEL.out.versions)
    }

    // snv filtering
    if ( params.snv_calling ) {
        
        FILTER_CANDIDATES_SNV (
            ch_input_tsv,
            ch_model_extra_trees_snv,
            'snv',
            ch_output_dir
        )
        ch_filtered_candidates_snvs = FILTER_CANDIDATES_SNV.out.filtered_candidates
        ch_versions = ch_versions.mix(FILTER_CANDIDATES_SNV.out.versions)
    }

    emit:

    ch_filtered_candidates_indels = ch_filtered_candidates_indels
    ch_filtered_candidates_snvs   = ch_filtered_candidates_snvs
    versions                      = ch_versions

}