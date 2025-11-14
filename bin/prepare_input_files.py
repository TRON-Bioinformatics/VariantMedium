#!/usr/bin/env python
# coding: utf-8

import argparse
import os
from pathlib import Path
import pandas as pd


# -------------------------------------------------------
# Utility: normalize all paths (absolute, resolved)
# -------------------------------------------------------
def resolve_path(p):
    return Path(p).expanduser().resolve()


# -------------------------------------------------------
# Automatically detect CSV or TSV
# -------------------------------------------------------
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


# -------------------------------------------------------
# Validation of input files + BAM/BAI existence
# -------------------------------------------------------
def validate_paths(inpath, folder, out_folder_vm, df):
    if not inpath.exists():
        raise FileNotFoundError(f"Input file not found: {inpath}")

    if not folder.exists():
        raise FileNotFoundError(f"Output TSV folder not found: {folder}")

    if not out_folder_vm.exists():
        raise FileNotFoundError(f"Pipeline output folder not found: {out_folder_vm}")

    for _, row in df.iterrows():
        tumor = resolve_path(row["tumor_bam"])
        normal = resolve_path(row["normal_bam"])

        if not tumor.exists():
            raise FileNotFoundError(f"Tumor BAM missing: {tumor}")

        if not normal.exists():
            raise FileNotFoundError(f"Normal BAM missing: {normal}")

        if not tumor.with_suffix(".bai").exists():
            raise FileNotFoundError(f"Tumor BAI missing: {tumor.with_suffix('.bai')}")

        if not normal.with_suffix(".bai").exists():
            raise FileNotFoundError(f"Normal BAI missing: {normal.with_suffix('.bai')}")


# -------------------------------------------------------
# MAIN TSV GENERATOR
# -------------------------------------------------------
def make_input(df, folder, out_folder_vm, skip_preprocessing):

    prepath = folder / "preproc.tsv"
    bampath = folder / "bams.tsv"
    vcfpath = folder / "vcfs.tsv"
    paipath = folder / "pairs_wo_reps.tsv"
    b2tpath = folder / "pairs_w_cands.tsv"
    etrpath = folder / "samples_w_cands.tsv"

    prefile = prepath.open("w")
    bamfile = bampath.open("w")
    vcffile = vcfpath.open("w")
    paifile = paipath.open("w")
    b2tfile = b2tpath.open("w")
    etrfile = etrpath.open("w")

    for _, row in df.iterrows():

        sample = row["sample_name"]
        reppair = str(row["pair_identifier"])
        tumor = resolve_path(row["tumor_bam"])
        normal = resolve_path(row["normal_bam"])

        sample_rep = f"{sample}_{reppair}"

        # -------------------------------
        # Preprocessing file
        # -------------------------------
        if skip_preprocessing != "True":
            print(f"{sample_rep}_tumor\ttumor\t{tumor}", file=prefile)
            print(f"{sample_rep}_normal\tnormal\t{normal}", file=prefile)

            tumor = out_folder_vm / "output_01_01_preprocessed_bams" / f"{sample_rep}_tumor" / f"{sample_rep}_tumor.preprocessed.bam"
            normal = out_folder_vm / "output_01_01_preprocessed_bams" / f"{sample_rep}_normal" / f"{sample_rep}_normal.preprocessed.bam"

        # -------------------------------
        # Bams
        # -------------------------------
        print(f"{sample_rep}\tprimary:{tumor}", file=bamfile)
        print(f"{sample_rep}\tnormal:{normal}", file=bamfile)

        # -------------------------------
        # VCF candidates
        # -------------------------------
        strelka_vcf = (
            out_folder_vm
            / "output_01_02_candidates_strelka2"
            / sample_rep
            / f"{sample_rep}.strelka2.somatic.vcf.gz"
        )

        print(f"{sample}_{reppair}\t{strelka_vcf}", file=vcffile)

        # -------------------------------
        # pairs_wo_reps.tsv
        # -------------------------------
        print(f"{sample}_{reppair}\t{tumor}\t{normal}", file=paifile)

        # -------------------------------
        # samples_w_cands.tsv
        # -------------------------------
        print(
            sample,
            "call",
            reppair,
            out_folder_vm / "output_01_03_vcf_postprocessing" / sample_rep / f"{sample_rep}.vaf.vcf",
            file=etrfile,
            sep="\t",
        )

        # -------------------------------
        # pairs_w_cands.tsv
        # -------------------------------
        print(
            sample,
            "call",
            reppair,
            tumor,
            f"{tumor}.bai",
            normal,
            f"{normal}.bai",
            out_folder_vm / "output_01_04_candidates_extratrees" / "Production_Model" / f"{sample}.tsv",
            file=b2tfile,
            sep="\t",
        )

    prefile.close()
    bamfile.close()
    vcffile.close()
    paifile.close()
    etrfile.close()
    b2tfile.close()


# -------------------------------------------------------
# Entrypoint
# -------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Prepares necessary input files")
    parser.add_argument("-i", "--input_file", type=str)
    parser.add_argument("-o", "--out_folder", type=str)
    parser.add_argument("-O", "--out_folder_vm", type=str)
    parser.add_argument("-s", "--skip_preprocessing", type=str)

    args = parser.parse_args()

    inpath = resolve_path(args.input_file)
    folder = resolve_path(args.out_folder)
    out_folder_vm = resolve_path(args.out_folder_vm)

    df = read_samplesheet(inpath)

    validate_paths(inpath, folder, out_folder_vm, df)
    make_input(df, folder, out_folder_vm, args.skip_preprocessing)
