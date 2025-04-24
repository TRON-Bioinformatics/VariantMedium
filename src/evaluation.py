#!/usr/bin/env python
# Evaluation procedure

import logging

import numpy as np
import pandas as pd
import sklearn.metrics as metrics

import os
from typing import List, Text, Dict

from constants import *

logger = logging.getLogger(__name__)

np.random.seed(6746549)


def evaluate_model(hp, call_mode=False):
    out_path = '../all_runs_summary.tsv'
    pred_file = 'scores_{}.tsv'.format(hp.prediction_mode)
    evaluation, true_labels_no, false_labels_no = compute(
        hp.valid_paths,
        pred_file,
        hp.unknown_strategy_val,
        hp.prediction_mode,
        call_mode
    )

    with open('train_samples.txt', 'w') as outfile:
        for sample in hp.train_paths.keys():
            sample = sample.strip()
            print(sample, file=outfile)
    with open('valid_samples.txt', 'w') as outfile:
        for sample in hp.valid_paths.keys():
            sample = sample.strip()
            print(sample, file=outfile)

    if len(hp.train_paths.keys()) < 10:
        train_samples = list(hp.train_paths.keys())
    else:
        train_samples = 'train_samples.txt'
    if len(hp.valid_paths.keys()) < 10:
        valid_samples = list(hp.valid_paths.keys())
    else:
        valid_samples = 'valid_samples.txt'

    with open(out_path, 'a+') as f:
        f.write('\t'.join([
            str(hp.run),
            str(train_samples),
            str(valid_samples),
            str(hp.pretrained_model),
            str(hp.tensor_type),
            str(hp.architecture),
            str(hp.num_init_features),
            str(hp.growth_rate),
            str(hp.block_config),
            str(hp.bn_size),
            str(hp.batch_size),
            str(hp.learning_rate),
            str(hp.epoch),
            str(hp.aug_rate),
            str(hp.aug_mixes),
            str(hp.drop_rate),
            str(hp.prediction_mode),
            str(['{:.2f}'.format(w) for w in hp.class_balance.cpu()]),
        ])
        )
        f.write('\t{}\t{}\t'.format(
            true_labels_no, false_labels_no
        ))
        for key in sorted(evaluation.keys()):
            if type(evaluation[key]) == np.float64:
                f.write('{:.4f}'.format((evaluation[key])) + '\t')
            else:
                f.write('{}'.format((evaluation[key])) + '\t')
        f.write('\n')


def compute(
        valid_paths: Dict[Text, Dict[Text, Text]],
        predictions_path: Text,
        unknown_strategy: Text,
        prediction_mode: Text,
        call_mode: bool,
):
    """Run the final evaluation.

    :param labels_template: Template for the path to the labels files.
    :param predictions_path: Path to the file containing predicted variants and
    their assigned scores.

    """
    truth_paths = []
    candidate_paths = []
    for sample in valid_paths.keys():
        sample = sample.strip()
        truth_paths.append(valid_paths[sample]['labels'])
        candidate_paths.append(valid_paths[sample]['candidates'])

    true_labels, predicted_scores, df, labels_df = preprocess_files(
        truth_paths,
        candidate_paths,
        predictions_path,
        unknown_strategy,
        prediction_mode
    )

    write_predictions(df, predictions_path.replace('all_', ''), call_mode)

    if not call_mode:
        return (
            evaluate(true_labels, predicted_scores),
            len(labels_df[labels_df['LABEL'] == True]),
            len(labels_df[labels_df['LABEL'] == False])
        )
    else:
        return


def preprocess_files(
        truth_paths: List[Text],
        candidate_paths: List[Text],
        predictions_path: Text,
        unknown_strategy: Text,
        prediction_mode: Text
):
    """Merge truth and predictions to prepare them for comparison.

    :param truth_paths: Path to the miseq_confirmation file.
    :param predictions_path: Path to the file containing predicted mutations
    and scores for each.
    :param unknown_strategy: Strategy to apply when mutation status is unknown.
    One of keep_as_false/discard.
    :param prediction_mode: What type of variants are predicted by the network.
    somatic/germline, point/indel.
    :return: A pandas dataframe containing common candidates in ground truth
    and predicted mutations.
    """
    labels_df = preprocess_input_files(truth_paths, prediction_mode, True)
    candidates_df = preprocess_input_files(candidate_paths, prediction_mode)
    if 'LABEL' in candidates_df.columns:
        candidates_df = candidates_df.drop(columns=['LABEL'])
    if 'FILTER' in candidates_df.columns:
        candidates_df = candidates_df.drop(columns=['FILTER'])
    preds_df = preprocess_predictions_file(predictions_path, prediction_mode)

    df = merge_files(
        labels_df,
        candidates_df,
        preds_df,
        unknown_strategy,
        predictions_path
    )

    true_labels = df['LABEL'].values.tolist()
    predicted_scores = df['SCORE'].values.tolist()

    return true_labels, predicted_scores, df, labels_df


def preprocess_input_files(
        paths: List[Text],
        prediction_mode: Text,
        add_label: bool = False
) -> pd.DataFrame:
    """Preprocess the truth files to be compatible with predictions&candidates.

    :param paths: Path to the miseq_confirmation file.
    :param prediction_mode: What type of variants are predicted by the network.
    somatic/germline, point/indel.
    :return: A Pandas dataframe containing variants and their mutation class.
    """
    df = pd.DataFrame()
    for path in paths:
        # Read the ground truth files and merge
        truth_df = pd.read_csv(
            path,
            sep='\t',
            dtype={'CHROM': str, 'POS': int, 'REF': str, 'ALT': str,
                   'SAMPLE': str, 'FILTER': str}
        )
        truth_df['SAMPLE'] = str(os.path.split(os.path.split(path)[0])[1])
        if ('LABEL' not in truth_df.columns) and add_label:
            truth_df.loc[
                truth_df['FILTER'].isin(SOMATIC_LABELS), 'LABEL'] = True
            truth_df.loc[
                truth_df['FILTER'].isin(NO_MUT_LABELS), 'LABEL'] = False
            truth_df.loc[
                truth_df['FILTER'].isin(GERMLINE_LABELS), 'LABEL'] = False
            truth_df = truth_df[~truth_df['LABEL'].isna()]
        df = pd.concat([df, truth_df], sort=True)

    if prediction_mode in SNP_MODES:
        df = df[df['REF'].str.len() == df['ALT'].str.len()]
    if prediction_mode in INDEL_MODES:
        df = df[df['REF'].str.len() != df['ALT'].str.len()]
    return df


def preprocess_predictions_file(
        predictions_path: Text,
        prediction_mode: Text
) -> pd.DataFrame:
    """PPreprocess the predictions file to be compatible with candidates&truth.

    :param predictions_path: Path to the file containing predicted mutations
    and scores for each.
    :param prediction_mode: What type of variants are predicted by the network.
    somatic/germline, point/indel.
    :return: A pandas dataframe containing candidate variants and model scores.
    """
    df = pd.read_csv(predictions_path, sep='\t', dtype={'CHROM': str})
    if prediction_mode in SNP_MODES:
        df = df[df['REF'].str.len() == df['ALT'].str.len()]
    if prediction_mode in INDEL_MODES:
        df = df[df['REF'].str.len() != df['ALT'].str.len()]
    return df


def merge_files(
        labels_df,
        candidates_df,
        preds_df,
        unknown_strategy,
        predictions_path
):
    """Compute the dataframe that contains validated & falsified mutations.

    :param labels_df: Data frame containing variants in ground truth.
    :param preds_df: Data frame containing variants with NN predictions.
    :return: A data frame of validated & falsified mutations, along with their predictions.
    """
    # Merge two dataframes
    labels_df['SAMPLE'] = labels_df['SAMPLE'].astype('str')
    preds_df['SAMPLE'] = preds_df['SAMPLE'].astype('str')
    candidates_df['SAMPLE'] = candidates_df['SAMPLE'].astype('str')
    labels_df['CHROM'] = labels_df['CHROM'].astype('str')
    preds_df['CHROM'] = preds_df['CHROM'].astype('str')
    candidates_df['CHROM'] = candidates_df['CHROM'].astype('str')
    labels_df['POS'] = labels_df['POS'].astype('int')
    preds_df['POS'] = preds_df['POS'].astype('int')
    candidates_df['POS'] = candidates_df['POS'].astype('int')

    merge_cols = ['CHROM', 'POS', 'REF', 'ALT', 'SAMPLE']
    df = pd.merge(
        labels_df,
        preds_df,
        how='outer',
        on=merge_cols
    )

    # TODO: remove later
    if 0. in df['REPLICATE'].unique():
        df.loc[df['REPLICATE'] == 0., 'REPLICATE'] = 1.

    if 'REP' in candidates_df.columns:
        candidates_df['REPLICATE'] = candidates_df['REP'].astype('float')
        merge_cols.append('REPLICATE')
    df = pd.merge(
        df,
        candidates_df,
        how='left',
        on=merge_cols
    )

    # Remove/keep variants with unknown mutation type based on the strategy.
    if unknown_strategy == 'discard':
        df = df[~df['LABEL'].isna()]
    else:
        df['LABEL'].fillna(False, inplace=True)

    # if the network doesn't have a prediction for a variant, assign the
    # lowest possible value, -1.00001
    df.loc[df['SCORE'].isna(), 'SCORE'] = -1.00001
    df.loc[df['FILTER'].isna(), 'FILTER'] = 'NA'

    df.loc[df['normal_ac'].isna(), 'normal_ac'] = -1
    df.loc[df['normal_af'].isna(), 'normal_af'] = -0.00001
    df.loc[df['normal_dp'].isna(), 'normal_dp'] = -1
    df.loc[df['primary_ac'].isna(), 'primary_ac'] = -1
    df.loc[df['primary_af'].isna(), 'primary_af'] = -0.00001
    df.loc[df['primary_dp'].isna(), 'primary_dp'] = -1

    # remove germline variants predicted by DeepVariant, they are not to be
    # included in evaluation.
    df = df[~df['FILTER'].isin(GERMLINE_LABELS_LQ)]

    # save intermediate file
    cols = [
        'CHROM', 'POS', 'REF', 'ALT', 'SAMPLE', 'FILTER', 'LABEL', 'SCORE',
        'REPLICATE'
    ]
    df[cols].to_csv(
        predictions_path.replace('.tsv', '.annotated.tsv'),
        sep='\t',
        index=False
    )

    # compute final network scores.
    # df = df.drop(columns=['CLIPPING'])

    dfs = []
    for gr in df.groupby('FILTER'):
        for gr1 in gr[1].groupby('LABEL'):
            df1 = gr1[1]
            df1['FILTER'] = str(gr[0])
            df1['LABEL'] = int(gr1[0])
            dfs.append(df1)
    df = pd.concat(dfs)

    return df


def evaluate(labels: List[bool], preds: List[float]):
    """Evaluate the performance of the classifier given the ground truth and the predicted scores.

    :param labels: Labels obtained from deep seq e.g. True if somatic.
    :param preds: Predicted likelihoods of being a somatic mutation.
    :return: Precision, recall, F1 score, TN, FP, FN, TP, Total, AUPRC, AUROC.
    """
    scores = {}
    pr, rc, f1 = 'Precision-{}', 'Recall-{}', 'F1-{}'
    _tn, _fp, _fn, _tp, _total = '=TN-{}', '=FP-{}', '=FN-{}', '=TP-{}', '=All-{}'
    cutoff = 0.
    predlabels = [True if score > cutoff else False for score in preds]
    scores[pr.format(cutoff)] = metrics.precision_score(labels, predlabels)
    scores[rc.format(cutoff)] = metrics.recall_score(labels, predlabels)
    scores[f1.format(cutoff)] = metrics.f1_score(labels, predlabels)
    tn, fp, fn, tp = metrics.confusion_matrix(labels, predlabels).ravel()
    scores[_tn.format(cutoff)] = tn
    scores[_fp.format(cutoff)] = fp
    scores[_fn.format(cutoff)] = fn
    scores[_tp.format(cutoff)] = tp
    scores[_total.format(cutoff)] = tn + fp + fn + tp

    avg_precision = metrics.average_precision_score(
        y_true=labels,
        y_score=preds,
    )
    roc_auc = metrics.roc_auc_score(
        y_true=labels,
        y_score=preds,
    )

    logger.info('Average precision: {}'.format(avg_precision))

    scores.update({'Average precision': avg_precision, 'AUROC': roc_auc})
    return scores


def write_predictions(df: pd.DataFrame, path: Text, call_mode: bool):
    """ Write the final predictions to a file.

    :param df: Data frame containing variants, their truth class, NN predictions
    :param path: Path to the output file.
    """
    df = df.sort_values(by=['SCORE'], ascending=False)
    df.to_csv(
        path,
        sep='\t',
        index=False
    )

    if not call_mode:
        return

    if 'snv' in path:
        muttype = 'snv'
    else:
        muttype = 'indel'

    for gr in df.groupby(by='SAMPLE'):
        df_s = gr[1]
        df_s = df_s.sort_values(['CHROM', 'POS']).reset_index(drop=True)
        if muttype == 'snv':
            df_s = df_s[df_s['SCORE'] > SNV_THRESHOLD].reset_index(drop=True)
        else:
            df_s['IS_DEL'] = False
            df_s.loc[
                df_s['REF'].str.len() > df_s['ALT'].str.len(), 'IS_DEL'
            ] = True
            df_s_del = df_s[
                (df_s['IS_DEL'] == True) & (df_s['SCORE'] > DEL_THRESHOLD)
                ]
            df_s_ins = df_s[
                (df_s['IS_DEL'] == False) & (df_s['SCORE'] > INS_THRESHOLD)
                ]

            df_s = pd.concat([df_s_ins, df_s_del]).reset_index(drop=True)

        df_s['SCORE'] = df_s['SCORE'].round(6)
        df_s = df_s[['SAMPLE', 'CHROM', 'POS', 'REF', 'ALT', 'SCORE']]

        df_s.to_csv('{}.{}.VariantMedium.tsv'.format(gr[0], muttype), sep='\t',
                    index=False)

        df_s['INFO'] = 'SCORE=' + df_s['SCORE']
        save_as_vcf(df_s, '{}.{}.VariantMedium.vcf'.format(gr[0], muttype),
                    df_s['INFO'], 'PASS')


def save_as_vcf(df, file_name, info='.', filter='.'):
    df['ID'] = '.'
    df['INFO'] = info
    df['FORMAT'] = filter
    df['FILTER'] = '.'
    df = df.rename(columns={'CHROM': '#CHROM'})
    df = df.sort_values(
        by=['#CHROM', 'POS']).drop_duplicates().reset_index()
    header = '##fileformat=VCFv4.2\n' \
             '#CHROM\tPOS\tID\tREF\tALT\tFILTER\tFORMAT\tINFO\n'
    if type(info) != str:
        header = '##fileformat=VCFv4.2\n' \
                 '##INFO=<ID=SCORE,Number=A,Type=Float,Description="Model assigned score">\n' \
                 '##INFO=<ID=LABEL,Number=A,Type=String,Description="Deep sequencing result">\n' \
                 '#CHROM\tPOS\tID\tREF\tALT\tFILTER\tFORMAT\tINFO\n'
    with open(file_name, 'w+') as f:
        f.write(header)
        for index, row in df[
            ['#CHROM', 'POS', 'ID', 'REF', 'ALT', 'FILTER', 'FORMAT',
             'INFO']
        ].iterrows():
            f.write('\t'.join([str(v) for v in row.values]) + '\n')
