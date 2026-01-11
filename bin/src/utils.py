import logging

import numpy as np
import pandas as pd
import random
import os
import torch
from sklearn.metrics import average_precision_score as aps
from sklearn.metrics import roc_auc_score  as auroc

from src.constants import *

logger = logging.getLogger(__name__)
random.seed(567497)
torch.manual_seed(37546)
np.random.seed(6746549)


def get_batch_data(data, device):
    """ Get data from the current batch and move them to the GPU

    :param data: Data in the current batch
    :param device: GPU device
    :return: inputs, mutation_classes, mutation_length_classes
    """
    inputs, classes1, classes2 = data['X'], data['y1'], data['y2']
    inputs = inputs.to(device, dtype=torch.float, non_blocking=True)
    mutation_classes = classes1.to(device, dtype=torch.long, non_blocking=True)
    length_classes = classes2.to(device, dtype=torch.long, non_blocking=True)
    return inputs, mutation_classes, length_classes


def migrate_to_gpu(network):
    """ Move the network to the GPU.

    :param network: The neural network object.
    :return: Connected device and the network in the device.
    """
    is_gpu_avail = torch.cuda.is_available()
    logger.info('Moving the network to the GPU. GPU available: {}'.format(
        is_gpu_avail
    ))
    device = torch.device("cuda:0" if is_gpu_avail else "cpu")
    if torch.cuda.device_count() > 1:
        logger.info('Using multiple GPUs.')
        network = torch.nn.DataParallel(network)
    network.to(device)
    logger.info('Network migration complete')
    return device, network


def save_stats(writer, loss, step, loss_type):
    """ Save statistics during training
    :param writer: The Tensorboard writer object.
    :param loss: Loss value
    :param step: Training step.
    :param loss_type: Type of loss (training/validation)
    :return:
    """
    if writer:
        writer.add_scalar(loss_type, loss, step)
    if loss_type == 'training_loss':
        return step + 1
    else:
        return step


def compute_binary_performance(labels, scores, prediction_mode):
    """ Compute the performance on binary classification task.
    somatic/not
    germline/not

    :param labels: Ground truth labels.
    :param scores: Predictions by the network.
    :param prediction_mode: Somatic/germline prediction modes.
    :return: AUPRC, AUROC, and final scores in binary classification task.
    """
    if prediction_mode in GERMLINE_MODES:
        labels_bin = (labels == GERMLINE)
        preds_ens = scores[:, GERMLINE] - scores[:, NO_MUT]
    elif prediction_mode in SOMATIC_MODES:
        labels_bin = (labels == SOMATIC)
        preds_ens = scores[:, SOMATIC] - \
                    scores[:, NO_MUT] - \
                    scores[:, GERMLINE]
    else:
        raise Exception('Prediction mode not recognized')

    auprc_all = -1.
    auroc_all = -1.
    if len(np.unique(labels_bin)) > 1:
        auprc_all = aps(labels_bin, preds_ens)
        auroc_all = auroc(labels_bin, preds_ens)

    return auprc_all, auroc_all, preds_ens


def print_performance(labels, scores, auprc_all, auroc_all):
    """ Print the AUPRC/AUROC values of different classification tasks.
    somatic, germline, no mutation, overall(binary)

    :param labels: Ground truh labels.
    :param scores: Neural network scores.
    :param auprc_all: AUPRC value on binary classification task
    :param auroc_all: AUROC value on binary classification task
    """
    classes_dict = CLASSES_DICT

    t = 'Average precision {:11}: {:.3}'
    labels = np.array(labels)
    for class_name, class_id in classes_dict.items():
        labels_n = (labels != class_id) == False
        logger.info(t.format(class_name, aps(labels_n, scores[:, class_id])))

    logger.info(t.format('OVERALL', auprc_all))
    logger.info('Area under ROC {:14}: {:.3}'.format('OVERALL', auroc_all))


def save_scores(preds, metadata, out_path, prediction_mode, call_mode):
    """ Save neural network scores and other variant information to a file.

    :param preds: Scores assigned to each candidate variant by the model
    :param metadata: Info on variant such as the position, sample etc.
    :param out_path: The path to the output folder.
    """
    df = pd.DataFrame(metadata, columns=HEADER)
    df['SCORE_NOMUT'] = preds[:, NO_MUT]
    df['SCORE_GERMLINE'] = preds[:, GERMLINE]
    df['SCORE_SOMATIC'] = preds[:, SOMATIC]
    df['SCORE'] = preds[:, ALL]
    df = df[
        [
            'SAMPLE', 'CHROM', 'POS', 'REF', 'ALT', 'REPLICATE', 'CLIPPING',
            'SCORE', 'SCORE_NOMUT', 'SCORE_GERMLINE', 'SCORE_SOMATIC'
        ]
    ]
    out_name = os.path.join(out_path, 'all_scores_{}.tsv'.format(prediction_mode))
    df.to_csv(out_name, sep='\t', index=False, float_format='%.15f')

    df_comb = df.groupby(
        ['SAMPLE', 'CHROM', 'POS', 'REF', 'ALT', 'REPLICATE']
    ).mean(numeric_only=True).sort_values('SCORE', ascending=False).reset_index()
    df_comb.to_csv(
        out_name.replace('all_', ''),
        sep='\t',
        index=False,
        float_format='%.15f'
    )
    write_predictions(df_comb, out_path, prediction_mode, call_mode)

def write_predictions(df, out_path, muttype, call_mode):
    """ Write the final predictions to a file.

    :param df: Data frame containing variants, NN predictions
    :param out_path: The path to the output folder.
    :param path: Path to the output file.
    """
    if not call_mode:
        return

    df['SCORE'] = df['SCORE'].astype(float)

    for gr in df.groupby(by='SAMPLE'):
        df_s = gr[1]
        df_s = df_s.sort_values(['SCORE']).reset_index(drop=True)
        if muttype == 'somatic_snv':
            df_s = df_s[df_s['SCORE'] > SNV_THRESHOLD].reset_index(drop=True)
        else:
            df_s['IS_DEL'] = False
            df_s.loc[df_s['REF'].str.len() > df_s['ALT'].str.len(), 'IS_DEL'] = True
            df_s_del = df_s[(df_s['IS_DEL'] == True) & (df_s['SCORE'] > DEL_THRESHOLD)]
            df_s_ins = df_s[(df_s['IS_DEL'] == False) & (df_s['SCORE'] > INS_THRESHOLD)]
            df_s = pd.concat([df_s_ins, df_s_del]).reset_index(drop=True)

        df_s = df_s.sort_values(by=['SCORE'], ascending=False)
        df_s['SCORE'] = df_s['SCORE'].round(6)
        df_s = df_s[['SAMPLE', 'CHROM', 'POS', 'REF', 'ALT', 'SCORE']]

        tsv_file = os.path.join(out_path, '{}.{}.VariantMedium.tsv'.format(gr[0], muttype))
        df_s.to_csv(tsv_file, sep='\t', index=False)

        df_s['INFO'] = 'SCORE=' + df_s['SCORE'].astype(str)
        vcf_file = os.path.join(out_path, '{}.{}.VariantMedium.vcf'.format(gr[0], muttype))
        save_as_vcf(df_s, vcf_file, df_s['INFO'], 'PASS')


def save_as_vcf(df, file_name, info='.', filter='.'):
    df['ID'] = '.'
    df['INFO'] = info
    df['FILTER'] = filter
    df = df.rename(columns={'CHROM': '#CHROM'})
    df = df.sort_values(
        by=['#CHROM', 'POS']).drop_duplicates().reset_index()
    header = '##fileformat=VCFv4.2\n' \
             '#CHROM\tPOS\tID\tREF\tALT\tFILTER\tINFO\n'
    if type(info) != str:
        header = '##fileformat=VCFv4.2\n' \
                 '##INFO=<ID=SCORE,Number=A,Type=Float,Description="Model assigned score">\n' \
                 '#CHROM\tPOS\tID\tREF\tALT\tFILTER\tINFO\n'
    with open(file_name, 'w+') as f:
        f.write(header)
        for index, row in df[
            ['#CHROM', 'POS', 'ID', 'REF', 'ALT', 'FILTER', 'INFO']
        ].iterrows():
            f.write('\t'.join([str(v) for v in row.values]) + '\n')