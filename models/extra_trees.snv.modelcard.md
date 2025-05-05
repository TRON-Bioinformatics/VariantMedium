---
language:
  - en

license: cc-by-nc-nd-4.0

tags:
  - NGS
  - somatic-variant-calling
---

# Model Card for Model ID

This is an extra trees model for sensitive detection of somatic SNV candidates.

## Model Details

### Model Description

- **Developed by:** Özlem Muslu
- **Funded by :** European Research Council (“ERC Advanced Grant “SUMMIT” (Ugur Sahin): 789256”)
- **License:** cc-by-nc-nd-4.0

### Model Sources

- **Repository:** https://github.com/TRON-Bioinformatics/VariantMedium

## Uses

Using matched tumor-normal paired short read sequencing data, you can call a sensitive list of somatic point mutations.

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
- primary_rsbq
- primary_rsbq_pv
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
- normal_rsbq
- normal_rsbq_pv
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

Given a BAM file:
1. BAM preprocessing (https://github.com/TRON-Bioinformatics/tronflow-bam-preprocessing)
2. Candidate variant calling (https://github.com/TRON-Bioinformatics/tronflow-strelka2)
3. Variant normalization and feature extraction (https://github.com/TRON-Bioinformatics/tronflow-vcf-postprocessing)

#### Training Hyperparameters

```python
hyperparams = [
    {
        'n_estimators': [500, 600],
        'max_depth': [20, 25],
        'criterion': ['entropy'],
        'max_features': ['sqrt', 'log2'],
        'bootstrap': [True, False]
    },
    {
        'n_estimators': [700, 800],
        'max_depth': [30, 35],
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

| Metric      | CV    | Validation | Test Set |
|-------------|-------|------------|----------|
| Precision   | 0.97  | 0.129      | 0.9407   |
| Recall      | 0.98  | 0.979      | 0.8294   |
| F1 Score    | 0.98  | 0.228      | 0.8815   |

#### Summary

We observed high recall in both cross-validation and validation sets. Test set recall dropped slightly compared to control (0.8563 -> 0.8294), but precision increased.

---

## Environmental Impact

Carbon emissions can be estimated using the [Machine Learning Impact calculator](https://mlco2.github.io/impact#compute) presented in [Lacoste et al. (2019)](https://arxiv.org/abs/1910.09700).

- **Hardware Type:** DGX2  
- **Hours used:** 2  
- **Compute Region:** Germany  

---
