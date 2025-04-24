import glob
import io
import logging
import numpy as np
import os
import pandas as pd
import random
import torch
from typing import List, Text

from constants import *

logger = logging.getLogger(__name__)

random.seed(567497)
torch.manual_seed(37546)
np.random.seed(6746549)

def get_merged_df(
        paths, prediction_mode, for_train, aug_list, unknown_strategy
):
    """Get a data frame containing all the necessary information of instances

    :param paths:
    :param prediction_mode:
    :param for_train:
    :param aug_list:
    :param unknown_strategy:
    :return: Data frame combining input lists and data frames
    """
    # read in generated tensor file list
    paths_df = get_paths(get_file_paths(paths['tensors'], for_train, aug_list))
    if len(paths_df) == 0:
        logger.warning('No input files detected for the sample')
        return None

    # read in candidate somatic mutations list
    cands_df = parse_variants(paths['candidates'], prediction_mode)
    cands_df = cands_df[['CHROM', 'POS', 'REF', 'ALT']]
    if len(cands_df) == 0:
        logger.warning('Candidate list is empty')
        return None

    # if given, read in the labels and merge with candidates df
    # otherwise, use candidates_df directly
    if paths['labels'] is not None:
        labels_df = parse_variants(paths['labels'], prediction_mode)
        labels_df.loc[:, 'LABEL'] = False
        labels_df.loc[labels_df['FILTER'].isin(SOMATIC_LABELS), 'LABEL'] = True
        df_merge = combine_candidates_and_labels(
            labels_df, cands_df, unknown_strategy=unknown_strategy
        )
    else:
        df_merge = cands_df
        cands_df['FILTER'] = 'unknown'
        cands_df['LABEL'] = 0

    # merge files and convert to desired format
    df_merge = df_merge.merge(paths_df, how='inner')
    df_merge = df_merge[df_merge['TYPE'].notna()]
    if len(df_merge) == 0:
        logger.warning('Candidate list and tensors merged, no survivors')
        return None
    return df_merge


def get_file_paths(
        input_home: Text,
        for_train: bool,
        aug_mixes: List[Text] = None
) -> List[Text]:
    """Get the list of paths that point to the tensor objects.

    :param input_home: Home directory for tensor objects.
    :param for_train: Whether this is initialized for training or testing.
    :param aug_mixes: Augmentation mix for purity/downsampling augmentation.
    :return: A list of paths.
    """
    file_list = glob.glob(
        '{}/purity-1.0-downsample-1.0-contamination-0.0/*.pt'.format(
            input_home
        ))

    if not for_train:
        return file_list

    if not aug_mixes:
        return file_list

    for aug in aug_mixes:
        upsampled_home = os.path.join(input_home, aug)
        if os.path.exists(upsampled_home):
            file_list.extend(glob.glob('{}/{}'.format(upsampled_home, '*.pt')))

    return file_list


def get_paths(file_list: List[Text]) -> pd.DataFrame:
    """Given a file list, generate data frame with path and variant information.

    :param file_list: List of full paths to tensor files.
    :param columns: Column names of the data frame.
    :return: A dataframe containing full path, chromosome, position and other
    variant information.
    """
    metadata = list(map(get_variant_properties_from_file, file_list))
    # generate data frame from file paths
    df_paths = pd.DataFrame(metadata)
    try:
        df_paths.columns = FILE_NAME_COLUMNS
    except:
        df_paths.columns = FILE_NAME_COLUMNS_NO_REP
    df_paths.loc[:, 'POS'] = df_paths['POS'].astype(int)

    return df_paths


def get_variant_properties_from_file(fpath: Text) -> List[Text]:
    """ Get variant properties such as chromosome, position etc. by parsing the
    file name.

    :param fpath: Path to tensor file
    :return: List containing following information on the variant:
    chromosome, position, mutation type, mutation length, time of creation
    """
    inner_list = [fpath]
    inner_list.extend(os.path.split(fpath)[1].replace('.pt', '').split('-'))
    return inner_list


def combine_candidates_and_labels(
        labels_df: pd.DataFrame,
        candidates_df: pd.DataFrame,
        unknown_strategy: Text
) -> pd.DataFrame:
    """ Merge the ground truth and candidate data frames

    :param labels_df: Data frame containing ground truth information
    :param candidates_df: Data frame containing candidate variant information
    :param unknown_strategy: What to do with variants whose labels are unknown.
    keep_as_false or discard
    :return: Merged data frame with processed columns
    """
    df = labels_df.merge(
        candidates_df,
        how='right',
        on=['CHROM', 'POS', 'REF', 'ALT']
    )

    if unknown_strategy == 'keep_as_false':
        df.loc[df['LABEL'].isna(), 'LABEL'] = False
    elif unknown_strategy == 'discard':
        df = df[df['LABEL'].notna()]

    if 'FILTER' not in df.columns:
        df.loc[:, 'FILTER'] = df['FILTER_x']
        na_indices = df['FILTER'].isna()
        df.loc[na_indices, 'FILTER'] = df.loc[na_indices, 'FILTER_y']
        df = df.drop(columns=['FILTER_x', 'FILTER_y'])

    return df


def parse_variants(
        path: Text, prediction_mode: Text
) -> pd.DataFrame:
    """Parse a VCF formatted file or a TSV

    :param path: Path to the candidate file.
    :param prediction_mode: What type of variant to predict (point/indel)
    :return: A data frame of variants.
    """
    try:
        df = pd.read_csv(path, sep='\t', dtype={'CHROM': str})
        df['CHROM'] = df['CHROM'].astype(str)
        if len(df.columns) < 4:
            raise Exception('Read the file in wrong format. Trying again.')
    except: #TODO: just check the file extension...
        try:
            with open(path, 'r') as f:
                lines = [l for l in f if not l.startswith('##')]

            # Convert the lines to a dataframe.
            df = pd.read_csv(
                io.StringIO(u''.join(lines)),
                dtype={'#CHROM': str, 'POS': int, 'ID': str, 'REF': str,
                       'ALT': str, 'QUAL': str, 'FILTER': str, 'INFO': str},
                sep='\t'
            )

            # Rename column
            df.rename(columns={'#CHROM': 'CHROM'}, inplace=True)
        except:
            raise Exception(
                'Wrong variants file type/format. Please check {}.'.format(
                    path
                )
            )
    if prediction_mode in SNP_MODES:
        df = df[df['REF'].str.len() == df['ALT'].str.len()]
    if prediction_mode in INDEL_MODES:
        df = df[df['REF'].str.len() != df['ALT'].str.len()]
    return df


def read_array(
        file_path: str,
        clip_length: int,
        aug_rate: int,
) -> torch.Tensor:
    """ Read the input array from disk.

    :param file_path: Path to the tensor file.
    :param clip_length: How much to clip from each side of the tensor.
    :param aug_rate: Augmentation rate for window size augmentation.
    :return:
    """
    arr = torch.load(file_path)
    if clip_length > 0:
        arr = clip_array(arr, arr.shape[3], aug_rate, clip_length)
    return arr


def clip_array(
        arr: torch.Tensor,
        width: int,
        aug_rate: int,
        clip_length: int
) -> torch.Tensor:
    """ Zero out sides of the tensor to mimick a smaller window size around the
    variant.

    :param arr: The input tensor
    :param width: Width of the tensor
    :param aug_rate: Augmentation rate for window size augmentation.
    :param clip_length: How much to clip from each side of the tensor.
    :return: Tensor with certain amount (or none) zeroed out widthwise.
    """
    zero_out_amount = 0
    if aug_rate > 0:
        zero_out_amount = int(
            (width / (aug_rate * 2)) * clip_length)
    if zero_out_amount * 2 == width:
        zero_out_amount = zero_out_amount - 1
    arr[:, :, :, 0:zero_out_amount] = 0
    arr[:, :, :, width - zero_out_amount:width] = 0

    return arr
