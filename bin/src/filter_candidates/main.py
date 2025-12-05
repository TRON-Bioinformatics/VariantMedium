import argparse
import numpy as np
import pandas as pd
from joblib import dump

from src.filter_candidates.extra_trees_functions import read_and_fit, compute_metrics, \
    apply_threshold
from src.filter_candidates.constants import *
from src.filter_candidates.constants_ml_snv import *
from src.filter_candidates.constants_ml_indel import *
from src.filter_candidates.extra_trees_io import get_all_dfs, save_results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--candidates', type=str)
    parser.add_argument('-p', '--candidates_public', type=str)
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('-l', '--labels', type=str)
    parser.add_argument('-m', '--model', type=str)
    args = parser.parse_args()

    cand = args.candidates
    candp = args.candidates_public
    label = args.labels
    model = args.model
    out = args.output

    c8 = 'COLO_829_Model'
    m1 = 'MZ_PC_1_Model'
    m2 = 'MZ_PC_2_Model'
    p0 = 'Production_Model'

    workflow(c8, REPS, cand, candp, label, model, out, False)
    workflow(m1, REPS, cand, candp, label, model, out, False)
    workflow(m2, REPS, cand, candp, label, model, out, False)
    workflow(c8, REPS, cand, candp, label, model, out, True)
    workflow(m1, REPS, cand, candp, label, model, out, True)
    workflow(m2, REPS, cand, candp, label, model, out, True)

    workflow(p0, REPS, cand, candp, label, model, out, False)
    workflow(p0, REPS, cand, candp, label, model, out, True)


def workflow(
        model_name,
        replicates,
        cands_tmpl,
        cands_public_tmpl,
        labels_tmpl,
        model_tmpl,
        out_tmpl,
        for_indel
):
    features, label, sets, thresholds, tuned_params, muttype = get_params(
        for_indel
    )
    print('\nWorkflow for {}, {} started.'.format(model_name, muttype))

    clf, train_df = read_and_fit(
        train_samples=sets[model_name]['train'],
        replicates=replicates,
        cands_template=cands_tmpl,
        cands_public_template=cands_public_tmpl,
        labels_template=labels_tmpl,
        features=features,
        label=label,
        tuned_params=tuned_params,
        for_indel=for_indel
    )

    dump(clf, model_tmpl.format(model_name, muttype))
    train_df = apply_threshold(
        clf=clf,
        df=train_df,
        threshold=thresholds[model_name],
        features=features,
        label=label
    )

    valid_df = workflow_validation(
        model_name,
        replicates,
        cands_tmpl,
        cands_public_tmpl,
        labels_tmpl.replace('.tsv', '.val.tsv'),
        for_indel,
        features,
        label,
        sets,
        thresholds,
        'valid',
        clf,
        set_threshold=True
    )
    if model_name == 'Production_Model':
        cands_tmpl = cands_public_tmpl
    test_df = workflow_validation(
        model_name,
        replicates,
        cands_tmpl,
        cands_public_tmpl,
        labels_tmpl,
        for_indel,
        features,
        label,
        sets,
        thresholds,
        'test',
        clf
    )

    all_samples = list(np.concatenate(list(sets[model_name].values())).flat)
    all_dfs = pd.concat([train_df, valid_df, test_df])

    save_results(
        df=all_dfs,
        tmpl=out_tmpl,
        model_name=model_name,
        samples=all_samples,
        muttype=muttype,
        w_label=True
    )
    print('Workflow for {}, {} finished.\n\n\n'.format(model_name, muttype))


def get_params(for_indel):
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
    return features, label, sets, thresholds, tuned_params, muttype


def filter_simple(df):
    df = df[~((df['normal_af'] > 0.05) & (df['normal_dp'] > 20))].reset_index(
        drop=True)
    df = df[df['normal_ac'] < 3].reset_index(drop=True)
    df = df[df['primary_ac'] > 2].reset_index(drop=True)
    df = df[df['primary_af'] > 0.01].reset_index(drop=True)

    return df


def workflow_validation(
        model_name,
        replicates,
        cands_tmpl,
        cands_public_tmpl,
        labels_tmpl,
        for_indel,
        features,
        label,
        sets,
        thresholds,
        set_type,
        clf,
        set_threshold=False
):
    print(model_name, set_type)
    df = get_all_dfs(
        samples=sets[model_name][set_type],
        replicates=replicates,
        cands_template=cands_tmpl,
        cands_public_template=cands_public_tmpl,
        labels_template=labels_tmpl,
        features=features,
        for_indel=for_indel
    )

    print('{:7.4} {:7} {:7} {:6} {:6} {:6} {:5} {:5} {:5} {:8}'.format(
        'Thresh', 'Cands', 'Call', 'True', 'TP', 'FN', 'Prec', 'Recal', 'F1',
        'Fbeta'
    ))

    if set_threshold:
        max_fbeta = 0
        for th in range(1, 50, 1):
            df_tmp = df.copy(deep=True)
            df_tmp = apply_threshold(
                clf=clf,
                df=df_tmp,
                threshold=th / 1000,
                features=features,
                label=label
            )
            fbeta = compute_metrics(df_tmp, th)
            if fbeta > max_fbeta:
                thresholds[model_name] = th / 1000
                max_fbeta = fbeta

    df = apply_threshold(
        clf=clf,
        df=df,
        threshold=thresholds[model_name],
        features=features,
        label=label
    )
    print('After normal evidence filtering')
    df = filter_simple(df)
    compute_metrics(df, thresholds[model_name])
    return df


if __name__ == '__main__':
    main()
