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
    if (params.execution_step == "prepare_tsv_inputs") {
        VARIANTMEDIUM_PREPARE_INPUTS(ch_samplesheet)
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
    if (params.execution_step == "filter") {
        
        ch_tsv_input = channel.fromPath("${params.outdir}/tsv_folder/samples_w_cands.tsv", checkIfExists: true)
        ch_outdir = channel.fromPath("${params.outdir}/output_01_04_candidates_extratrees", checkIfExists: true)
        ch_model_extra_tress_snv = channel.fromPath("${params.outdir}/data_staging/models/extra_trees.snv.joblib", checkIfExists: true)
        ch_model_extra_tress_indel = channel.fromPath("${params.outdir}/data_staging/models/extra_trees.indel.joblib", checkIfExists: true)
            
        VARIANTMEDIUM_FILTER_CANDIDATES(
            ch_tsv_input,
            ch_outdir,
            ch_model_extra_tress_snv,
            ch_model_extra_tress_indel
        )
    }

    // ----------------------------------------
    // Run variantmedium variant calling (step - 8)
    // ----------------------------------------

}