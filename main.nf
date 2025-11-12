// nf orchestrator for variant medium

// data staging modules
include { STAGE_REFERENCES  } from 'modules/stage_refs/main'
include { STAGE_MODELS      } from 'modules/stage_models/main'
include { PREPARE_INPUTS    } from 'modules/prepare_inputs/main'

// variant medium modules
include { VARIANTMEDIUM_RUN } from 'modules/variantmedium/run/main'
include { FILTER_CANDIDATES } from 'modules/variantmedium/filter/main'

workflow VARIANTMEDIUM {
}
