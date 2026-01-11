#!/usr/bin/env python

from src.filter_candidates.constants import PCAWG  # noqa: F401
from src.filter_candidates import constants_ml_snv, constants_ml_indel, extra_trees_functions, extra_trees_io  # noqa: F401
from src.filter_candidates.candidate_filtering import filter_candidates as filter_variant_candidates
import pandas as pd
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Extra trees filtering',
        description='ML based filtering method to remove unlikely somatic variants',
    )
    parser.add_argument('-i', '--input_files', type=str)
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('-m', '--model', type=str)
    parser.add_argument('--snv', action="store_true")
    parser.add_argument('--indel', action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(
        args.input_files, sep='\t', header=None
    )

    if args.snv:
        filter_variant_candidates(
            df,
            args.model,
            args.output,
            False
        )
    
    if args.indel:
        filter_variant_candidates(
            df,
            args.model,
            args.output,
            True
    )

    for sample in df[0].unique():

        dfs = []

        # snv
        if args.snv:
            snv_file = args.output.format("Production_Model", sample, "snv")
            df_snv = pd.read_csv(snv_file, sep="\t")
            dfs.append(df_snv)

        # indel
        if args.indel:
            indel_file = args.output.format("Production_Model", sample, "indel")
            df_indel = pd.read_csv(indel_file, sep="\t")
            dfs.append(df_indel)

        #  concat
        df_all = pd.concat(dfs)

        # Combined output filename
        out_file = args.output.format("Production_Model", sample, "")
        out_file = out_file.replace("_.tsv", ".tsv")

        df_all.to_csv(out_file, sep="\t", index=False)
