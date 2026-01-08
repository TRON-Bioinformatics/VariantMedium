include { PARSE_SAMPLESHEET               } from './subworkflows/parse_samplesheet'
include { VALIDATE_PARAMETERS             } from './subworkflows/parameter_validation'
include { VARIANTMEDIUM_PREPARE_INPUTS    } from './workflows/variantmedium_prepare_inputs'
include { VARIANTMEDIUM_STAGE_DATA        } from './workflows/variantmedium_stage_data'
include { VARIANTMEDIUM_FILTER_CANDIDATES } from './workflows/variantmedium_filter_candidates.nf'
include { VARIANTMEDIUM_CALL_VARIANTS     } from './workflows/variantmedium_call_variants.nf'

workflow {

    // ----------------------------------------
    // Parameter validation
    // ----------------------------------------
    VALIDATE_PARAMETERS()

    // ----------------------------------------
    // Samplesheet validation
    // ----------------------------------------
    ch_samplesheet = channel.empty()
    def samplesheetFile = file(params.samplesheet)
    if( !samplesheetFile.exists() ) {
        log.error "ERROR: Samplesheet filepath does not exist: ${params.samplesheet}"
    }  else {
        ch_samplesheet = channel.fromPath("${params.samplesheet}")
    }
    log.info "[INFO] Samplesheet -> [${samplesheetFile}]"
    PARSE_SAMPLESHEET(ch_samplesheet)

    // ----------------------------------------
    // Variantmedium prepare input tsv files (step - 1)
    // ----------------------------------------
    if (params.execution_step == "generate_tsv_files") {
        VARIANTMEDIUM_PREPARE_INPUTS(
            ch_samplesheet,
            "${params.outdir}"
        )   
    }

    // ----------------------------------------
    // Variantmedium stage ref data & models (step - 2)
    // ----------------------------------------
    if (params.execution_step == "data_staging") {
        VARIANTMEDIUM_STAGE_DATA()
    }

    // ----------------------------------------
    // Run variantmedium candidate filtering (step - 5)
    // ----------------------------------------
    if (params.execution_step == "candidate_filtering") {

        ch_tsv_input = channel.fromPath("${params.outdir}/${params.prepare_tsv_outs}/samples_w_cands.tsv", checkIfExists: true)
        ch_outdir = channel.fromPath("${params.outdir}/${params.candidate_filtering_outs}/{}/{}_{}.tsv")
        ch_model_extra_trees_snv = channel.fromPath("${params.outdir}/${params.data_staging_outs}/${params.models_dir}/extra_trees.snv.joblib", checkIfExists: true)
        ch_model_extra_trees_indel = channel.fromPath("${params.outdir}/${params.data_staging_outs}/${params.models_dir}/extra_trees.indel.joblib", checkIfExists: true)
            
        VARIANTMEDIUM_FILTER_CANDIDATES (
            ch_tsv_input,
            ch_outdir,
            ch_model_extra_trees_snv,
            ch_model_extra_trees_indel
        )
    }

    // ----------------------------------------
    // Run variantmedium variant calling (step - 8)
    // ----------------------------------------
    if (params.execution_step == "variant_calling") {
        
        ch_home_folder           = channel.fromPath("${params.outdir}/${params.bam2tensor_outs}", checkIfExists: true)
        ch_pretrained_model_snv  = channel.fromPath("${params.outdir}/${params.data_staging_outs}/${params.models_dir}/3ddensenet_snv.pt", checkIfExists: true)
        ch_pretrained_model_indel = channel.fromPath("${params.outdir}/${params.data_staging_outs}/${params.models_dir}/3ddensenet_indel.pt", checkIfExists: true)

        VARIANTMEDIUM_CALL_VARIANTS (
            ch_home_folder,
            ch_pretrained_model_snv,
            ch_pretrained_model_indel
        )
    }
}