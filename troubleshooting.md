## Issues with conda packages


### Conda installation and setup
In the case you run into problems with conda installation, we recommend installing a fresh miniconda:

```{bash}
wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh
mkdir ~/.conda
bash Miniconda3-py39_4.12.0-Linux-x86_64.sh -b && cp ~/miniconda3/bin/* /usr/local/bin/
rm -f Miniconda3-py39_4.12.0-Linux-x86_64.sh
conda --version
```

The code snippet above would install a fresh miniconda instance on your home directory

We also recommend adding the following in your conda config (~/.condarc):

```
channels:
  - conda-forge
  - bioconda
  - r
  - defaults
```

### Failed to create Conda environment - LibMambaUnsatisfiableError

Setting channel priority to flexible will fix this error:

```{bash}
conda config --set channel_priority flexible
```


## Nextflow installation

You can install latest nextflow as follows, given you have Bash 3.2 (or later) and Java 17 (or later, up to 23) installed:

```{bash}
wget -qO- https://get.nextflow.io | bash && cp nextflow /usr/local/bin/nextflow
nextflow help
```

## bam2tensor doesn't produce output

This is typically caused by a missing BAM index, which is assumed to have the same prefix as the BAM file (tumor.bam -> tumor.bai). 

It could also be caused by wrong positions of tumor and normal BAMs in the input tsvs (First bam is always the tumor, second is always the normal).

Please make sure that tumor and normal BAM file names are different. If they are the same you can link one/both with a new name.


## Pipeline won't run with test data set

We currently don't support test data sets where the region is limited to a small region in the genome. VariantMedium is built and tested for variant calling in WES/WGS data


