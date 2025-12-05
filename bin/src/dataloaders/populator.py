import logging
from collections import defaultdict

import pandas as pd
from typing import List, Text, Tuple, Dict

from src.constants import *
from src.dataloaders.annotated_tensor import AnnotatedTensor

logger = logging.getLogger(__name__)


def populate(
        df: pd.DataFrame,
        sample: Text,
        aug_rate: int = 0,
) -> Tuple[List[AnnotatedTensor], Dict[Text, List[int]]]:
    """ Populate a data frame with variant information, and save the indices
    for different classes.

    :param df: Input data frame with variant information.
    :param sample: The sample name (cell line/patient...).
    :param aug_rate: Augmentation rate for window size augmentation.
    :return:
    """
    df = assign_labels(df)
    df = add_augmented_examples(df, aug_rate)
    indices = get_class_indices(df)
    df.loc[indices['UNKNOWN'], 'CLASS_LABEL'] = NO_MUT
    data_list = generate_data_list(df, sample)

    return data_list, indices


def assign_labels(df: pd.DataFrame) -> pd.DataFrame:
    """ Assign categorical mutation type and length labels to candidate variants.

    :param df: Data frame of variants with mutation type and length information.
    :return: Data frame with categorical mutation type and length labels.
    """
    df.loc[:, 'LENGTH'] = df['LENGTH'].astype(int).abs()
    df.loc[:, 'CLASS_LENGTH'] = df['LENGTH']
    df.loc[df['LENGTH'] > 2, 'CLASS_LENGTH'] = 3

    df.loc[:, 'CLASS_LABEL'] = NO_LABEL
    df.loc[df['FILTER'].isin(NO_MUT_LABELS), 'CLASS_LABEL'] = NO_MUT
    df.loc[df['FILTER'].isin(GERMLINE_LABELS), 'CLASS_LABEL'] = GERMLINE
    df.loc[df['LABEL'] == True, 'CLASS_LABEL'] = SOMATIC
    df.loc[df['FILTER'].isna(), 'CLASS_LABEL'] = NO_LABEL

    df = df[~df['CLASS_LABEL'].isna()]
    return df


def add_augmented_examples(
        df: pd.DataFrame, aug_rate: int
) -> pd.DataFrame:
    """Add augmented examples to the data frame.

    :param df: Data frame containing file paths, labels, metadata.
    :param aug_rate: Augmentation rate for window size augmentation.
    :return: An extended data frame including augmented data points.
    """
    df.loc[:, 'CLIPPING'] = 0
    dfs = [df]
    for zero_out in range(1, aug_rate):
        df_repeat = df.copy(deep=True)
        df_repeat.loc[:, 'CLIPPING'] = zero_out
        dfs.append(df_repeat)
    df = pd.concat(dfs)
    return df.reset_index()


def get_class_indices(df: pd.DataFrame) -> pd.DataFrame:
    """ Get indices of different classes for each mutation type class.

    :param df: Data frame of all candidate variants
    :return: Indices of each class in the data frame.
    """
    classes_dict = CLASSES_DICT
    classes_dict['UNKNOWN'] = NO_LABEL

    index_mappings = defaultdict(list)
    for class_name, class_id in classes_dict.items():
        index_mappings[class_name].extend(
            df.index[(df['CLASS_LABEL'] == class_id)].to_list()
        )

    classes_dict.pop('UNKNOWN', None)

    return index_mappings


def generate_data_list(df: pd.DataFrame, sample: str) -> List[AnnotatedTensor]:
    """ Generate a list of AnnotatedTensor objects from candidate variants df.

    :param df: Candidate variants data frame.
    :param sample: Sample name of cell line/patient.
    :return: List of AnnotatedTensor objects from candidate variants & augmentations.
    """
    data_list = []
    for i, row in df.iterrows():
        try:
            rep = row['REPLICATE']
        except:
            rep = '1'
        annotated_tensor = AnnotatedTensor(
            tensor=row['FULL_PATH'],
            variant=int(row['CLASS_LABEL']),
            length=int(abs(row['CLASS_LENGTH'])),
            metadata=(
                row['CHROM'],
                int(row['POS']),
                row['REF'],
                row['ALT'],
                sample,
                rep,
                int(row['CLIPPING'])
            ),
            clip_length=row['CLIPPING'],
        )
        data_list.append(annotated_tensor)
    return data_list
