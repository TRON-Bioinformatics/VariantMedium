# VARIANTMEDIUM

Toolbox for mutation calling using deep learning

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
the following format **without header**. All fields are in string format, so you are free to choose
the name and replicate_pair_identifier as long as they make a unique tuple.

| sample name  | replicate pair identifier | tumor bam path  | normal bam path |
|--------|-----------------------------|-------------------|-------------------|
| sample_1  | rep_1 | tumor_1.bam  | normal_1.bam |
| sample_2  | rep_2 | tumor_2.bam  | normal_2.bam |

Define the following variables in `config.conf`:

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
