#!/usr/bin/env python

import argparse
from pathlib import Path
import pandas as pd

# Detect CSV/TSV
def read_samplesheet(path):
    text = Path(path).read_text().splitlines()[0]
    if "," in text and "\t" not in text:
        sep = ","
    elif "\t" in text and "," not in text:
        sep = "\t"
    else:
        raise ValueError("Cannot detect delimiter. File must be comma OR tab separated.")
    return pd.read_csv(path, sep=sep, header=0)

# Validate BAM + BAI
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
                raise FileNotFoundError(f"Missing tumor BAI: {tumor.with_suffix('.bai')}")
            if not normal.with_suffix(".bai").exists():
                raise FileNotFoundError(f"Missing normal BAI: {normal.with_suffix('.bai')}")

# Generate TSVs (written into current dir)
def make_input(df, skip_preprocessing, output_dir):
    output_dir = Path(output_dir)

    cwd = Path.cwd()
    prefile  = (cwd / "preproc.tsv").open("w")
    bamfile  = (cwd / "bams.tsv").open("w")
    vcffile  = (cwd / "vcfs.tsv").open("w")
    paifile  = (cwd / "pairs_wo_reps.tsv").open("w")
    b2tfile  = (cwd / "pairs_w_cands.tsv").open("w")
    etrfile  = (cwd / "samples_w_cands.tsv").open("w")

    for _, row in df.iterrows():
        sample = row["sample_name"]
        pair   = str(row["pair_identifier"])
        tumor_orig  = Path(row["tumor_bam"])
        normal_orig = Path(row["normal_bam"])

        rep = f"{sample}_{pair}"

        # Helper to prefix pipeline output paths
        def out(path: str):
            return output_dir / path

        # Preprocessing paths
        if skip_preprocessing.lower() != "true":
            tumor = out(f"output_01_01_preprocessed_bams/{rep}_tumor/{rep}_tumor.preprocessed.bam")
            normal = out(f"output_01_01_preprocessed_bams/{rep}_normal/{rep}_normal.preprocessed.bam")

            print(f"{rep}_tumor\ttumor\t{tumor_orig}", file=prefile)
            print(f"{rep}_normal\tnormal\t{normal_orig}", file=prefile)
        else:
            tumor = tumor_orig
            normal = normal_orig

        # bams.tsv
        print(f"{rep}\tprimary:{tumor}", file=bamfile)
        print(f"{rep}\tnormal:{normal}", file=bamfile)

        # vcfs.tsv
        strelka_vcf = out(f"output_01_02_candidates_strelka2/{rep}/{rep}.strelka2.somatic.vcf.gz")
        print(f"{sample}_{pair}\t{strelka_vcf}", file=vcffile)

        # pairs_wo_reps.tsv
        print(f"{sample}_{pair}\t{tumor}\t{normal}", file=paifile)

        # samples_w_cands.tsv
        vaf_vcf = out(f"output_01_03_vcf_postprocessing/{rep}/{rep}.vaf.vcf")
        print(sample, "call", pair, vaf_vcf, sep="\t", file=etrfile)

        # ------------------------------
        # pairs_w_cands.tsv (Production_Model!)
        # ------------------------------
        # pairs_w_cands
        extratrees_tsv = out(
            f"output_01_04_candidates_extratrees/Production_Model/{sample}.tsv"
        )
        extratrees_tsv.touch(exist_ok=True)

        print(
            sample,
            "call",
            pair,
            tumor,
            tumor.with_suffix(".bai"),
            normal,
            normal.with_suffix(".bai"),
            extratrees_tsv,
            sep="\t",
            file=b2tfile,
        )

    prefile.close()
    bamfile.close()
    vcffile.close()
    paifile.close()
    etrfile.close()
    b2tfile.close()


# Entrypoint
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", required=True)
    parser.add_argument("-o", "--output_dir", default=".")
    parser.add_argument("-s", "--skip_preprocessing", default="False")
    args = parser.parse_args()

    df = read_samplesheet(args.input_file)
    validate_paths(df, args.skip_preprocessing)
    make_input(df, args.skip_preprocessing, args.output_dir)
    print("[INFO] Input TSV files generated successfully")
