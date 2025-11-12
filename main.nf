// nf orchestrator for variant medium

include { VARIANTMEDIUM_RUN } from 'modules/variantmedium/run/main'
include { FILTER_CANDIDATES } from 'modules/variantmedium/filter/main'
include { PREPARE_INPUTS    } from 'modules/prepare_inputs/main'

workflow VARIANTMEDIUM {

}