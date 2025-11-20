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
    if (params.execution_step == "stage_data") {
        VARIANTMEDIUM_STAGE_DATA()
    }

    // ----------------------------------------
    // Run variantmedium candidate filtering (step - 5)
    // ----------------------------------------
    if (params.execution_step == "filter_candidates") {

        ch_tsv_input = channel.fromPath("${params.outdir}/tsv_folder/samples_w_cands.tsv", checkIfExists: true)
        ch_outdir = channel.fromPath("${params.outdir}/output_01_04_candidates_extratrees")
        ch_model_extra_tress_snv = channel.fromPath("${params.outdir}/data_staging/models/extra_trees.snv.joblib", checkIfExists: true)
        ch_model_extra_tress_indel = channel.fromPath("${params.outdir}/data_staging/models/extra_trees.indel.joblib", checkIfExists: true)
            
        VARIANTMEDIUM_FILTER_CANDIDATES (
            ch_tsv_input,
            ch_outdir,
            ch_model_extra_tress_snv,
            ch_model_extra_tress_indel
        )
    }

    // ----------------------------------------
    // Run variantmedium variant calling (step - 8)
    // ----------------------------------------
    if (params.execution_step == "call_variants") {
        
        ch_home_folder           = channel.fromPath("${params.outdir}/output_01_05_tensors")
        ch_output_path           = channel.fromPath("${params.outdir}/output_01_06_calls_densenet")
        ch_pretrained_model_snv  = channel.fromPath("${params.outdir}/data_staging/models/3ddensenet_snv.pt", checkIfExists: true)
        ch_pretrained_model_indel = channel.fromPath("${params.outdir}/data_staging/models/3ddensenet_indel.pt", checkIfExists: true)

        VARIANTMEDIUM_CALL_VARIANTS (
            ch_home_folder,
            ch_output_path,
            ch_pretrained_model_snv,
            ch_pretrained_model_indel,
        )
    }
}