## VariantMedium - Somatic variant calling from matched tumor-normal paired short-read sequencing data using 3D DenseNets

VariantMedium is a deep learning-based somatic variant caller for matched tumor-normal short-read sequencing data. It integrates machine learning–based filtering and 3D convolutional neural networks to classify candidate sites as somatic, germline, or non-variant, with high sensitivity and robustness across diverse genomic contexts and sample types.

## Dependencies

- nextflow >= 24.10.3
- conda >= 4.4 (miniconda >=23.11.0 recommended)
- CUDA 11.4 (optional for GPU support)

## Installation

```{bash}
git clone https://github.com/TRON-Bioinformatics/variantmedium.git
cd variantmedium
```

### Build conda environments

```{bash}
bash build.sh config.conf
```

## Usage

First, you will need to state the paths to your tumor-normal BAM pairs in a tab separated file in
the following format **with header**. All fields are in string format, so you are free to choose
the name and pair_identifier as long as they make a unique tuple.

| sample_name | pair_identifier | tumor_bam                   | normal_bam                 |
| ----------- | --------------- | --------------------------- | -------------------------- |
| sample1     | 1               | /path/to/sample1_normal.bam | /path/to/sample1_tumor.bam |
| sample2     | 1               | /path/to/sample2_normal.bam | /path/to/sample2_tumor.bam |

### Command line pipeline launcher
```
VariantMedium pipeline launcher

USAGE:
  variantmedium.sh [OPTIONS]

REQUIRED ARGUMENTS:
  --samplesheet        PATH        Path to the input CSV/TSV samplesheet
  --outdir             PATH        Output directory for all pipeline results
  --profile            STRING      Nextflow profile name (conda, singularity) [default: conda]
                                   [Parts of the pipeline may not support singularity - Prefer using conda]
  --config             PATH        Path to custom config file (.conf)

OPTIONAL ARGUMENTS:
  --skip_data_staging             Skip staging reference data & models
  --skip_preprocessing            Skip BAM preprocessing step
  --nf_report                     Generate Nextflow execution report
  --nf_trace                      Generate Nextflow execution trace

GET HELP:
  -h, --help                      Show this help message and exit

DESCRIPTION:
  Command-line wrapper to run VariantMedium pipeline steps:
   1. Generate TSV inputs                       -> [VariantMedium generate_tsv_files step]
   2. Stage reference data & models             -> [VariantMedium stage_data step]
   3. BAM preprocessing                         -> [tronflow-bam-preprocessing]
   4. Candidate calling (Strelka2)              -> [tronflow-strelka2]
   5. Feature generation                        -> [tronflow-vcf-postprocessing]
   6. ExtraTrees candidate filtering            -> [VariantMedium filter_candidates step]
   7. Tensor generation (bam2tensor)            -> [bam2tensor]
   8. 3D DenseNet variant calling (SNV & INDEL) -> [VariantMedium call_variants step]
```

Define the following variables in `config.conf`(optional):

- `CODE_FOLDER` Directory of the VariantMedium source code
- `ENV_FOLDER` Directory for conda envirnments
- `REF_FOLDER` Directory for reference data
- `PAIRS` File path to tab-separated table with samples associated to tumor/normal BAM files
- `OUT_FOLDER` Output folder
- `KNOWN_INDELS1` Common indel variant file for BAM preprocessing pipeline
- `DBSNP` dbDNP VCF file for BAM preprocessing pipeline
- `REF` Reference genome
- `EXOME_BED` Target region defintion as BED file (e.g. exome) - Leave empty ("") if calling in WGS


If you need to apply BAM-Preprocessing and need the resource files, you can
download the full reference data for the human genome hg38, run 'sh download_ref.sh` and use
configurations as defined in 'config_hg38.conf' for the reference genome GrcH38. This script also provides download commands for
reference genome and S07604624 SureSelect Human All Exon V6+UTR from UCSC if you need them.

**Please make sure the index for the BAM file exists with the ".bai" extension under the same
directory, e.g. for bams/tumor.bam you have bams/tumor.bai. Also please make sure that the tumor and
normal bam files do not have the same file name, even if they are under different directories. (
Linking with a new file name is ok)**

Finally, run the VariantMedium pipeline by

```{bash}
bash run.sh config.conf
```

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
