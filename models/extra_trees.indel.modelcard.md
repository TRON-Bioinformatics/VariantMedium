---
language:
  - en

license: cc-by-nc-nd-4.0

tags:
  - NGS
  - somatic-variant-calling
---

# Model Card for Model ID

This is an extra trees model for sensitive detection of somatic indel candidates.

## Model Details

### Model Description

- **Developed by:** Özlem Muslu
- **Funded by :** European Research Council (“ERC Advanced Grant “SUMMIT” (Ugur Sahin): 789256”)
- **License:** cc-by-nc-nd-4.0

### Model Sources

- **Repository:** https://github.com/TRON-Bioinformatics/VariantMedium

## Uses

Using matched tumor-normal paired short read sequencing data, you can call a sensitive list of somatic small indels.

### Direct Use

You can extract features from a matched tumor-normal sequencing pair using https://github.com/TRON-Bioinformatics/tronflow-vcf-postprocessing and use this model on its output. Specific features this model utilizes are:
- primary_af
- primary_dp
- primary_ac
- primary_pu
- primary_pw
- primary_k
- primary_rsmq
- primary_rsmq_pv
- primary_rspos
- primary_rspos_pv
- normal_af
- normal_dp
- normal_ac
- normal_pu
- normal_pw
- normal_k
- normal_rsmq
- normal_rsmq_pv
- normal_rspos
- normal_rspos_pv


### Downstream Use

This model is a part of VariantMedium somatic variant caller and is integrated directly into its workflow https://github.com/TRON-Bioinformatics/VariantMedium.

### Out-of-Scope Use

The model on its own is not intended to create a final list of variant calls, it is intended for filtering out noticeable false positives.

## Bias, Risks, and Limitations

The model is trained on the output of cell line WES and an AML WGS, both originating from short read Illumina sequencing. It is tested for other cancer entities and for solid tumors, but is not tested for non-Illumina sequencing.

### Recommendations

We recommend using this model for Illumina-based WES and WGS (paired, short read).

## Training Details

### Training Data

Matched tumor-normal sequencing published under https://ega-archive.org/studies/EGAS00001007633 and https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000159.v13.p5.

### Training Procedure

scikit-learn GridSearchCV. Hyperparameters are given under the relevant section.

#### Preprocessing

Given matched tumor-normal BAM files:
1. BAM preprocessing (https://github.com/TRON-Bioinformatics/tronflow-bam-preprocessing)
2. Candidate variant calling (https://github.com/TRON-Bioinformatics/tronflow-strelka2)
3. Variant normalization and feature extraction (https://github.com/TRON-Bioinformatics/tronflow-vcf-postprocessing)

#### Training Hyperparameters

```python
hyperparams = [
    {
        'n_estimators': [100, 200],
        'max_depth': [5, 10],
        'criterion': ['entropy'],
        'max_features': ['sqrt', 'log2'],
        'bootstrap': [True, False]
    },
    {
        'n_estimators': [300, 400],
        'max_depth': [10, 15],
        'criterion': ['entropy'],
        'max_features': ['sqrt', 'log2'],
        'bootstrap': [True, False]
    }
]

```

## Evaluation

Evaluation using CV and a left out cell line.

### Testing Data, Factors & Metrics

#### Testing Data

Tested on independent data sets:
- [PCAWG-Pilot63](https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000178.v11.p8)
- [SEQC2 WES samples](ftp://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/seqc/Somatic_Mutation_WG/)

#### Metrics

Sensitivity and precision, with sensitivity as the primary metric since the aim was to filter out noticeable false positives instead of coming up with a final list of variants.

### Results

| Metric      | Test Set |
|-------------|----------|
| Precision   | 0.8564   |
| Recall      | 0.6048   |
| F1 Score    | 0.7089   |

#### Summary

Test set recall dropped slightly compared to control (0.6167 -> 0.6048), but precision increased (0.8216 -> 0.8564).

