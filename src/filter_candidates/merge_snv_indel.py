import argparse
import numpy as np
import pandas as pd

from constants import *
from constants_ml_snv import SETS_SNV


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str)
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    inf = args.input
    out = args.output

    for set in SETS_SNV.keys():
        all_samples = list(np.concatenate(list(SETS_SNV[set].values())).flat)
        for sample in all_samples:
            df_snv = pd.read_csv(inf.format(set, sample, 'snv'), sep='\t')
            if sample == 'AML31':  # doesn't have INDEL labels
                df_snv.to_csv(out.format(set, sample), sep='\t', index=False)
                continue
            df_indel = pd.read_csv(inf.format(set, sample, 'indel'), sep='\t')
            df = pd.concat([df_snv, df_indel])
            print(sample, len(df))
            if sample in CELL_LINES_WO_DEEPSEQ:
                df = df[df['FILTER'] != 'unknown'].reset_index(drop=True)
            print(sample, len(df))
            print()
            df.to_csv(out.format(set, sample), sep='\t', index=False)


if __name__ == '__main__':
    main()
