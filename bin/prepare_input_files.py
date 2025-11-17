#!/usr/bin/env python

import argparse
from pathlib import Path
import pandas as pd

# Automatically detect CSV or TSV
def read_samplesheet(path):
    text = Path(path).read_text().splitlines()[0]
    if "," in text and "\t" not in text:
        sep = ","
    elif "\t" in text and "," not in text:
        sep = "\t"
    else:
        raise ValueError(
            "Cannot detect delimiter (file contains mixed separators). "
            "Ensure the file is strictly comma OR tab separated."
        )
    return pd.read_csv(path, sep=sep, header=0)

# Validation of input BAMs + BAI files
def validate_paths(df, skip_preprocessing):
    for _, row in df.iterrows():
        tumor = Path(row["tumor_bam"])
        normal = Path(row["normal_bam"])
        if not tumor.exists():
            raise FileNotFoundError(f"Tumor BAM missing: {tumor}")
        if not normal.exists():
            raise FileNotFoundError(f"Normal BAM missing: {normal}")
        if skip_preprocessing.lower() != "true":
            if not tumor.with_suffix(".bai").exists():
                raise FileNotFoundError(f"Tumor BAI missing: {tumor.with_suffix('.bai')}")
            if not normal.with_suffix(".bai").exists():
                raise FileNotFoundError(f"Normal BAI missing: {normal.with_suffix('.bai')}")

# Generate TSVs
def make_input(df, skip_preprocessing):
    cwd = Path.cwd()
    prefile = (cwd / "preproc.tsv").open("w")
    bamfile = (cwd / "bams.tsv").open("w")
    vcffile = (cwd / "vcfs.tsv").open("w")
    paifile = (cwd / "pairs_wo_reps.tsv").open("w")
    b2tfile = (cwd / "pairs_w_cands.tsv").open("w")
    etrfile = (cwd / "samples_w_cands.tsv").open("w")

    for _, row in df.iterrows():
        sample = row["sample_name"]
        reppair = str(row["pair_identifier"])
        tumor_orig = Path(row["tumor_bam"])
        normal_orig = Path(row["normal_bam"])
        sample_rep = f"{sample}_{reppair}"

        if skip_preprocessing.lower() != "true":
            # Preprocessing paths
            tumor = Path("output_01_01_preprocessed_bams") / f"{sample_rep}_tumor" / f"{sample_rep}_tumor.preprocessed.bam"
            normal = Path("output_01_01_preprocessed_bams") / f"{sample_rep}_normal" / f"{sample_rep}_normal.preprocessed.bam"

            # Write preproc TSV
            print(f"{sample_rep}_tumor\ttumor\t{tumor_orig}", file=prefile)
            print(f"{sample_rep}_normal\tnormal\t{normal_orig}", file=prefile)
        else:
            # If skipping preprocessing, use original BAM paths
            tumor = tumor_orig
            normal = normal_orig

        # BAM TSV
        print(f"{sample_rep}\tprimary:{tumor}", file=bamfile)
        print(f"{sample_rep}\tnormal:{normal}", file=bamfile)

        # VCF candidates
        strelka_vcf = Path("output_01_02_candidates_strelka2") / sample_rep / f"{sample_rep}.strelka2.somatic.vcf.gz"
        print(f"{sample}_{reppair}\t{strelka_vcf}", file=vcffile)

        # pairs_wo_reps
        print(f"{sample}_{reppair}\t{tumor}\t{normal}", file=paifile)

        # samples_w_cands
        print(
            sample,
            "call",
            reppair,
            Path("output_01_03_vcf_postprocessing") / sample_rep / f"{sample_rep}.vaf.vcf",
            file=etrfile,
            sep="\t",
        )

        # pairs_w_cands
        print(
            sample,
            "call",
            reppair,
            tumor,
            f"{tumor}.bai",
            normal,
            f"{normal}.bai",
            Path("output_01_04_candidates_extratrees") / "Production_Model" / f"{sample}.tsv",
            file=b2tfile,
            sep="\t",
        )

    prefile.close()
    bamfile.close()
    vcffile.close()
    paifile.close()
    etrfile.close()
    b2tfile.close()

# Entrypoint
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Prepares necessary input files")
    parser.add_argument("-i", "--input_file", type=str, required=True)
    parser.add_argument("-s", "--skip_preprocessing", type=str, default="False")
    args = parser.parse_args()

    df = read_samplesheet(Path(args.input_file))
    validate_paths(df, args.skip_preprocessing)
    make_input(df, args.skip_preprocessing)
