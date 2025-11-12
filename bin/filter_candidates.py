#!/usr/bin/env python3
import sys
import os

# Add the src folder to Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.filter_candidates.filter import filter
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
    args = parser.parse_args()

    df = pd.read_csv(
        args.input_files, sep='\t', header=None
    )

    filter(
        df,
        args.model,
        args.output,
        False
    )
    filter(
        df,
        args.model,
        args.output,
        True
    )

    for sample in df[0].unique():
        df_snv = pd.read_csv(
            args.output.format('Production_Model', sample, 'snv'), sep='\t')
        df_indel = pd.read_csv(
            args.output.format('Production_Model', sample, 'indel'), sep='\t')
        df_all = pd.concat([df_snv, df_indel])
        fname = args.output.format('Production_Model', sample, '')
        fname = fname.replace('_.tsv', '.tsv')
        df_all.to_csv(
            fname,
            sep='\t',
            index=False
        )