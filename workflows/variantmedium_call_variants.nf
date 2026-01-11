include { CALL_VARIANTS as CALL_VARIANTS_SNV   } from './../modules/variantmedium/call/main.nf'
include { CALL_VARIANTS as CALL_VARIANTS_INDEL } from './../modules/variantmedium/call/main.nf'


workflow VARIANTMEDIUM_CALL_VARIANTS {

    take:
    ch_home_folder              // [path-to-tensors-folder]
    ch_pretrained_model_snv     // [path-to-pretrained-model-snv] 
    ch_pretrained_model_indel   // [path-to-pretrained-model-indel]

    main:

    ch_versions = channel.empty()
    ch_called_snv = channel.empty()
    ch_called_indel = channel.empty()

    // snv calling
    if (params.snv_calling) {
        
        CALL_VARIANTS_SNV (
            ch_home_folder,
            ch_pretrained_model_snv,
            "somatic_snv"
        )
        ch_called_snv = CALL_VARIANTS_SNV.out.call_outs
        ch_versions = ch_versions.mix(CALL_VARIANTS_SNV.out.versions)
    }

    // indel calling
    if (params.indel_calling) {
        
        CALL_VARIANTS_INDEL (
            ch_home_folder,
            ch_pretrained_model_indel,
            "somatic_indel"
        )
        ch_called_indel = CALL_VARIANTS_INDEL.out.call_outs
        ch_versions = ch_versions.mix(CALL_VARIANTS_INDEL.out.versions)
    }


    emit:

    snvs     = ch_called_snv
    indels   = ch_called_indel
    versions = ch_versions

}