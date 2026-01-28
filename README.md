## VariantMedium - Somatic variant calling from matched tumor-normal paired short-read sequencing data using 3D DenseNets

VariantMedium is a deep learning-based somatic variant caller for matched tumor-normal short-read sequencing data. It integrates machine learning–based filtering and 3D convolutional neural networks to classify candidate sites as somatic, germline, or non-variant, with high sensitivity and robustness across diverse genomic contexts and sample types.

### Pre-requisites to the VariantMedium Pipeline

- nextflow >= 24.10.3 (install run environment with `conda env create -f envs/run.yml`)
- conda >= 4.4 (miniconda >=23.11.0 recommended)
- CUDA 11.4 (optional for GPU support)

## Usage

First, you will need to state the paths to your tumor-normal BAM pairs in a tab separated file in
the following format **with header**. All fields are in string format, so you are free to choose
the name and pair_identifier as long as they make a unique tuple.

| sample_name | pair_identifier | tumor_bam                   | normal_bam                 |
| ----------- | --------------- | --------------------------- | -------------------------- |
| sample1     | 1               | /path/to/sample1_tumor.bam | /path/to/sample1_normal.bam |
| sample2     | 1               | /path/to/sample2_tumor.bam | /path/to/sample2_normal.bam |

### Command line pipeline launcher
```
VariantMedium pipeline launcher

USAGE:
  variantmedium.sh [OPTIONS]

REQUIRED ARGUMENTS:
  --samplesheet               PATH        Path to the input CSV/TSV samplesheet
  --outdir                    PATH        Output directory for all pipeline results
  --profile                   STRING      Nextflow profile name (conda, singularity) [default: conda]
                                          [Parts of the pipeline may not support singularity - Prefer using conda]

OPTIONAL ARGUMENTS:
  --config                    PATH        Path to custom config file (.conf)
  --mount-path                PATH        Path to mount when using singularity profile [required for the singularity profile]
  --skip-data-staging                     Skip staging reference data & models
  --skip-preprocessing                    Skip BAM preprocessing step
  --skip-candidate-calling                Skip candidate calling step (if already generated VCFs are available)
  --skip-feature-generation               Skip VCF postprocessing / feature generation step (if already generated features are available)
  --skip-candidate-filtering              Skip ExtraTrees candidate filtering step (if already filtered candidates are available)
  --skip-tensor-generation                Skip tensor generation (if already generated tensors are available)
  --resume                                Resume from previous run
  --nf-report                             Generate Nextflow execution report
  --nf-trace                              Generate Nextflow execution trace
  --strelka-config            PATH        Path to custom Strelka2 config file
  --bam-prep-config           PATH        Path to custom BAM preprocessing config file
  --vcf-post-config           PATH        Path to custom VCF postprocessing config file
  --bam2tensor-config         PATH        Path to custom bam2tensor config file
  -h, --help                              Show this help message and exit

  DESCRIPTION:
  Command-line wrapper to run VariantMedium pipeline steps:
   1. Generate TSV inputs                       -> [VariantMedium generating input tsv files step]
   2. Stage reference data & models             -> [VariantMedium data staging step]
   3. BAM preprocessing                         -> [tronflow-bam-preprocessing]
   4. Candidate calling (Strelka2)              -> [tronflow-strelka2]
   5. Feature generation                        -> [tronflow-vcf-postprocessing]
   6. ExtraTrees candidate filtering            -> [VariantMedium filter_candidates step]
   7. Tensor generation (bam2tensor)            -> [bam2tensor]
   8. 3D DenseNet variant calling (SNV & INDEL) -> [VariantMedium call_variants step]

```

### Usage
- The pipeline launcher has 3 required arguments `--samplesheet`, `--outdir`, `--profile`

```bash
$ bash variantmedium.sh \
  --samplesheet <path/to/samplesheet.csv> \
  --outdir <path/to/pipeline-output-directory> \
  --profile conda  
```

- If reference datasets and models are available locally, use the paths via the config file `(*.conf)`. `--skip-data-staging` is to be used to skip the data (models & references) download. Local paths should be passed through the config file in this case.

```bash
$ bash variantmedium.sh \
  --samplesheet <path/to/samplesheet.csv> \
  --outdir <path/to/pipeline-output-directory> \
  --profile conda \
  --skip-data-staging \
  --config <run.conf>
```

- Similarly if pre-processed bams are available locally or pre-processing is not required, use the `--skip-preprocessing`. See the help message to skip subsequent steps if the need arises.

```bash
$ bash variantmedium.sh \
  --samplesheet <path/to/samplesheet.csv> \
  --outdir <path/to/pipeline-output-directory> \
  --profile conda \
  --skip-preprocesing \
  --config <run.conf>
```

- The pipeline can be resumed from the previous failed step with the `--resume` option.

```bash
$ bash variantmedium.sh \
  --samplehsheet <path/to/samplesheet.csv> \
  --outdir <path/to/pipeline-output-directory> \
  --profile conda \
  --resume
```

- Pipeline reports and trace files can be generated with the `--nf-report` and `--nf-trace` options.
```bash
$ bash variantmedium.sh \
  --samplehsheet <path/to/samplesheet.csv> \
  --outdir <path/to/pipeline-output-directory> \
  --profile conda \
  --nf-report \
  --nf-trace \
```

Define the following variables in `config.conf`(optional):
### Optional Configuration Variables (`config.conf`)

| Variable        | Description                                                                                       |
|-----------------|---------------------------------------------------------------------------------------------------|
| `REF_DIR`       | Directory for reference data                                                                      |
| `MODELS_DIR`    | Directory for trained models                                                                      |
| `KNOWN_INDELS1` | Common indel variant file for BAM preprocessing pipeline                                          |
| `KNOWN_INDELS2` | Common indel variant file for BAM preprocessing pipeline (optional)                               |
| `DBSNP`         | dbSNP VCF file for BAM preprocessing pipeline                                                     |
| `REF`           | Reference genome                                                                                  |
| `EXOME_BED`     | Target region definition as BED file (e.g., exome). Leave empty (`""`) if calling in WGS         |
------------------------------------------------------------------------------------------------------------------------

### Slurm Execution
To run the pipeline on a slurm executor an example script would look something as below, although this would change as per the organization's HPC infrastructure setup.
```bash
#!/usr/bin/env bash

#SBATCH --job-name=<job-name>
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=32
#SBATCH --nodes=<nodes>
#SBATCH --nodelist=<nodelist>
#SBATCH --partition=<gpu-partition-name>
#SBATCH --mem=128G
#SBATCH --gpus=1
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=<user-email>

set -euo pipefail

echo "[INFO] Job started on $(hostname)"

# run `bash variantmedium.sh --help` or README.md to see other
# run-specific options to execute the variantmedium pipeline.

bash variantmedium.sh \
    --profile conda \
    --samplesheet <path/to/samplesheet> \
    --outdir <outdir> \
    --resume

echo "[INFO] Job finished at: $(date)"
```

**Please make sure the index for the BAM file exists with the ".bai" extension under the same
directory, e.g. for bams/tumor.bam you have bams/tumor.bai. Also please make sure that the tumor and
normal bam files do not have the same file name, even if they are under different directories. (
Linking with a new file name is ok)**

#### Output

You will then find the calls in your `OUT_FOLDER` as tsv and VCF files. (<sample_name>
.somatic_snv.VariantMedium.vcf/<sample_name>.somatic_snv.VariantMedium.tsv) The variants are sorted
by the neural network score.

## Errors running the pipeline

We listed the solutions to common errors we encountered when running this pipeline under
[troubleshooting.md](https://github.com/TRON-Bioinformatics/VariantMedium/blob/main/troubleshooting.md) document in this repository

## Training data

We share the cell-line sequencing data and orthogonal deep sequencing confirmation of variants under
controlled access. The data is avaliable
under [European Genome-Phenome Archive (EGA)](https://ega-archive.org/studies/EGAS00001007633)
with accession number `EGAS00001007633`

## Citation

A manuscript describing the method will be available soon.

## License

- The source code is distributed under a [MIT license](LICENSE.sourcecode)
- The parts of the source code that use torchvision are distributed
  under [BSD 3-Clause License](LICENSE.torchvision)
- The machine learning models in the folder `models` are distributed
  under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)
