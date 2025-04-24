import argparse
import pandas as pd

from joblib import load

from constants_ml_snv import *
from constants_ml_indel import *
from extra_trees_functions import apply_threshold
from extra_trees_io import save_results, get_df, query_vcf_to_tsv
from main import filter_simple


def filter(
        df,
        model_tmpl,
        out_tmpl,
        for_indel
):
    samples = df[0].drop_duplicates().values
    features, label, sets, thresholds, _, muttype = get_params(
        for_indel, samples
    )
    print('\nFiltering {} candidates.'.format(muttype))

    clf = load(model_tmpl.format(muttype))

    all_cands = []
    for sample in samples:
        df_sample = df[df[0] == sample].reset_index(drop=True)
        for row in df_sample.iterrows():
            sample = row[1][0]
            rep = str(row[1][2])
            cand_vcf = row[1][3]
            cand_file = cand_vcf.replace('.vcf', '.tsv')
            query_vcf_to_tsv(cand_vcf, cand_file)
            df2 = get_df(
                (sample, rep),
                cand_file,
                features,
                for_indel=for_indel
            )
            df2['SAMPLE'] = sample
            all_cands.append(df2)

    all_cands_df = pd.concat(all_cands)
    # TODO: assign NaN to values with . or impute with replicate value
    # print(all_cands_df.columns)
    # all_cands_df = all_cands_df.groupby(['SAMPLE', 'ID']).mean().reset_index()
    # print(all_cands_df.columns)

    call_df = workflow_call(
        all_cands_df,
        features,
        thresholds,
        clf
    )

    if len(call_df) == 0:
        raise Exception('All candidates were filtered out by extra trees')

    save_results(
        df=call_df,
        tmpl=out_tmpl,
        model_name='Production_Model',
        samples=samples,
        muttype=muttype,
        w_label=False
    )
    print('Finished filtering {} candidates.\n\n\n'.format(muttype))


def get_params(for_indel, samples):
    label = LABEL
    if for_indel:
        features = FEATURES_INDEL
        thresholds = THRESHOLDS_INDEL
        sets = SETS_INDEL
        tuned_params = TUNED_PARAMS_INDEL
        muttype = 'indel'
    else:
        features = FEATURES_SNV
        thresholds = THRESHOLDS_SNV
        sets = SETS_SNV
        tuned_params = TUNED_PARAMS_SNV
        muttype = 'snv'

    sets['Production_Model']['test'] = samples
    return features, label, sets, thresholds, tuned_params, muttype


def workflow_call(
        cands_df,
        features,
        thresholds,
        clf
):
    df = apply_threshold(
        clf=clf,
        df=cands_df,
        threshold=thresholds['Production_Model'],
        features=features,
        label=None
    )
    print('{:7} {:7}'.format(len(df), len(df[df['EXTRATREES_CALL'] == 1])))
    len_before = len(df[df['EXTRATREES_CALL'] == 1])
    df = filter_simple(df)
    print('{:7} {:7}'.format(len_before, len(df[df['EXTRATREES_CALL'] == 1])))
    return df


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
