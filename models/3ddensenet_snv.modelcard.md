---
language:
  - en

license: cc-by-nc-nd-4.0

tags:
  - NGS
  - somatic-variant-calling
---

# Model Card for Model ID

This is a 3D DenseNet model for detection of somatic SNV candidates.

## Model Details

### Model Description

- **Developed by:** Özlem Muslu
- **Funded by :** European Research Council (“ERC Advanced Grant “SUMMIT” (Ugur Sahin): 789256”)
- **License:** cc-by-nc-nd-4.0

### Model Sources

- **Repository:** https://github.com/TRON-Bioinformatics/VariantMedium

## Uses

Using matched tumor-normal paired short read sequencing data, you can call a list of somatic point mutations.


### Downstream Use

This model is a part of VariantMedium somatic variant caller and is integrated directly into its workflow https://github.com/TRON-Bioinformatics/VariantMedium

### Out-of-Scope Use

The model on its own is not intended to create a final list of variant calls, it is intended a part of a pipeline (https://github.com/TRON-Bioinformatics/VariantMedium)

## Bias, Risks, and Limitations

The model is trained on the output of cell line WES, TCGA WES, and an AML WGS, both originating from short read Illumina sequencing. It is tested for other cancer entities and mostly for solid tumors, but is not tested for non-Illumina sequencing.

### Recommendations

We recommend using this model for Illumina-based WES and WGS (paired, short read).

## Training Details

### Training Data

Matched tumor-normal sequencing published under https://ega-archive.org/studies/EGAS00001007633 , https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000178.v11.p8 , and https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000159.v13.p5.

## Evaluation

Evaluation on two independent cohorts. More information can be found on our publication linked under: https://github.com/TRON-Bioinformatics/VariantMedium 

### Testing Data, Factors & Metrics

#### Testing Data

Tested on independent data sets:
- [PCAWG-Pilot63](https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000178.v11.p8)
- [SEQC2 WES samples](ftp://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/seqc/Somatic_Mutation_WG/)

#### Summary

