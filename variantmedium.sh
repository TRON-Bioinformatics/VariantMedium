#!/bin/bash

set -eu

. $1
TSV_FOLDER=${OUT_FOLDER}/input_files

CONDA_PATH=$(which conda)
CONDA_PATH="$(dirname "${CONDA_PATH}")"
CONDA_PATH="$(dirname "${CONDA_PATH}")"
CONDA_ACT=${CONDA_PATH}/bin/activate

mkdir -p ${OUT_FOLDER}
mkdir -p ${OUT_FOLDER}/input_files
mkdir -p ${OUT_FOLDER}/output_01_01_preprocessed_bams
mkdir -p ${OUT_FOLDER}/output_01_02_candidates_strelka2
mkdir -p ${OUT_FOLDER}/output_01_03_vcf_postprocessing
mkdir -p ${OUT_FOLDER}/output_01_04_candidates_extratrees
mkdir -p ${OUT_FOLDER}/output_01_04_candidates_extratrees/Production_Model
mkdir -p ${OUT_FOLDER}/output_01_05_tensors
mkdir -p ${OUT_FOLDER}/output_01_06_calls_densenet


### 0. Prepare input files
echo "Activating variantmedium environment"
source ${CONDA_ACT} ${ENV_FOLDER}/variantmedium
echo "Activated variantmedium environment"
echo "Generating required TSV files"
python ${CODE_FOLDER}/scripts/prepare_input_files.py \
-i ${PAIRS} \
-o ${TSV_FOLDER} \
-O ${OUT_FOLDER} \
--skip_preprocessing ${SKIP_PREPROCESSING} # skip preprocessing
conda deactivate
echo "Required TSV files generated"

### 1. BAM preprocessing
if [[ "${SKIP_PREPROCESSING}" == "True" ]]
then
  echo "Skipping BAM file preprocessing"
else
  echo "Preprocessing BAM files"
  cd ${OUT_FOLDER}/output_01_01_preprocessed_bams
  nextflow run tron-bioinformatics/tronflow-bam-preprocessing \
  -r v2.1.0 \
  -profile conda \
  -with-report \
  -with-trace \
  -resume \
  --input_files ${TSV_FOLDER}/preproc.tsv  \
  --reference ${REF} \
  --intervals ${EXOME_BED} \
  --dbsnp ${DBSNP} \
  --known_indels1 ${KNOWN_INDELS1} \
  --output ${OUT_FOLDER}/output_01_01_preprocessed_bams \
  --skip_deduplication \
  --skip_metrics
  echo "BAM preprocessing complete"
fi

### 2. Call candidates
echo "Running Strelka2 to get candidate VCFs"
cd ${OUT_FOLDER}/output_01_02_candidates_strelka2

if [[ "${EXOME_BED}" == "" ]]
then
  INTERVALS_PARAM=""
else
  INTERVALS_PARAM="--intervals ${EXOME_BED} "
fi

nextflow run tron-bioinformatics/tronflow-strelka2 \
-profile conda \
-with-report \
-with-trace \
-resume \
--input_files ${TSV_FOLDER}/pairs_wo_reps.tsv \
--reference ${REF} \
--output ${OUT_FOLDER}/output_01_02_candidates_strelka2 \
-r v0.2.4 \
${INTERVALS_PARAM}
echo "Strelka2 run complete"

### 3. Generate features for candidates
echo "Running tronflow-vcf-postprocessing to generate features"
nextflow run tron-bioinformatics/tronflow-vcf-postprocessing \
-r v3.1.2 \
-profile conda \
-with-report \
-with-trace \
-resume \
--input_vcfs ${TSV_FOLDER}/vcfs.tsv \
--input_bams ${TSV_FOLDER}/bams.tsv \
--reference ${REF} \
--output ${OUT_FOLDER}/output_01_03_vcf_postprocessing
echo "Feature generation complete"

### 4. Filter candidates using extra trees
echo "Activating extra trees environment"
source ${CONDA_ACT} ${ENV_FOLDER}/variantmedium-extratrees
echo "Activated extra trees environment"
echo "Filtering candidates"
cd ${OUT_FOLDER}/output_01_04_candidates_extratrees
python3 ${CODE_FOLDER}/src/filter_candidates/filter.py \
-i ${TSV_FOLDER}/samples_w_cands.tsv \
-m ${CODE_FOLDER}/models/extra_trees.{}.joblib \
-o ${OUT_FOLDER}/output_01_04_candidates_extratrees/{}/{}_{}.tsv
conda deactivate
echo "Candidate filtering complete"

### 5. Generate tensors
echo "Generating tensors"
cd ${OUT_FOLDER}/output_01_05_tensors
nextflow run tron-bioinformatics/bam2tensor \
-r 1.0.2 \
-profile conda \
-with-report \
-with-trace \
--input_files ${TSV_FOLDER}/pairs_w_cands.tsv \
--publish_dir ${OUT_FOLDER}/output_01_05_tensors \
--reference ${REF} \
--window 150 \
--max_coverage 500 \
--read_length 50 \
--max_mapq 60 \
--max_baseq 82
echo "Tensor generation complete"

### Call variants
echo "Activating variantmedium environment"
source ${CONDA_ACT} ${ENV_FOLDER}/variantmedium
echo "Activated variantmedium environment"
echo "Running 3D DenseNets to make final SNV calls"
python -u ${CODE_FOLDER}/src/run.py call \
--home_folder ${OUT_FOLDER}/output_01_05_tensors/ \
--unknown_strategy_call keep_as_false \
--pretrained_model ${CODE_FOLDER}/models/3ddensenet_snv.pt \
--prediction_mode somatic_snv \
--out_path ${OUT_FOLDER}/output_01_06_calls_densenet \
--learning_rate 0.13 \
--epoch 0 \
--drop_rate 0.3 \
--aug_rate 5 \
--aug_mixes nan \
--run call
echo "Final SNV calls made"

echo "Running 3D DenseNets to make final INDEL calls"
python -u ${CODE_FOLDER}/src/run.py call \
--home_folder ${OUT_FOLDER}/output_01_05_tensors/ \
--prediction_mode somatic_indel \
--out_path ${OUT_FOLDER}/output_01_06_calls_densenet \
--learning_rate 0.13 \
--epoch 0 \
--drop_rate 0.5 \
--aug_rate 5 \
--aug_mixes nan \
--unknown_strategy_call keep_as_false \
--pretrained_model ${CODE_FOLDER}/models/3ddensenet_indel.pt \
--run call
conda deactivate
echo "Final INDEL calls made"

cp ${OUT_FOLDER}/output_01_06_calls_densenet/*.somatic_snv.VariantMedium.tsv ${OUT_FOLDER}/
cp ${OUT_FOLDER}/output_01_06_calls_densenet/*.somatic_snv.VariantMedium.vcf ${OUT_FOLDER}/
