import numpy as np
import random
import time
import torch
from collections import defaultdict
from torch.utils.data import Dataset, DataLoader
from typing import Dict

from src.dataloaders.input_parsers import *
from src.dataloaders.populator import populate

# from variantmedium.run import Hyperparams

logger = logging.getLogger(__name__)

random.seed(567497)
torch.manual_seed(37546)
np.random.seed(6746549)


class MutationDataset(Dataset):
    """Mutation dataset."""

    def __init__(
            self,
            data_paths: Dict[Text, Dict[Text, Text]],
            for_training: bool,
            unknown_strategy: Text,
            aug_rate: int = 0,
            aug_mixes: List = None,
            prediction_mode: Text = False,
    ):
        """ Initializer for mutation data set.

        :param in_homes: Home directories for pt files that contain one tensor.
        :param ground_truth_paths: Paths to the labels files.
        :param candidate_paths: Paths to the candidates files.
        :param for_training: True if initialized for training stage, else False.
        :param unknown_strategy: What to do with candidates with unknown labels.
        One of keep_as_false or discard.
        :param aug_rate: Augmentation rate for varying window size augmentation.
        :param aug_mixes: Augmentation mix for purity/downsampling augmentation.
        :param prediction_mode: The final prediction of the network.
        somatic/germline snv/indel etc.
        :param removed_channel: Channel(s) to remove to compute feature importance.
        """
        # initialize variables
        start = time.time()
        self.for_train = for_training
        self.aug_rate = aug_rate
        self.prediction_mode = prediction_mode
        self.for_final_validation = False
        self.val_clip_length = 0
        self.index_mappings = defaultdict(list)

        self.data_list = self._generate_data_list(
            data_paths,
            unknown_strategy,
            aug_mixes
        )

        self._print_info(aug_mixes)

        # During training, balancing is applied for better pos/neg ratio.
        self.balanced_data_list = []
        if self.for_train:
            self.mix_for_balance()

        end = time.time()
        logger.info(
            'Data is now in memory. Loading took {} minutes'.format(
                (end - start) / 60)
        )

    def _generate_data_list(
            self,
            data_paths: Dict[Text, Dict[Text, Text]],
            unknown_strategy: Text,
            aug_mixes: List = None,
    ):
        """ Fill in the list that encapsulates training/validation set.

        :param in_homes: Home directories for pt files that contain one tensor.
        :param ground_truth_paths: Paths to the labels files.
        :param candidate_paths: Paths to the candidates files.
        :param unknown_strategy: What to do with candidates with unknown labels.
        One of keep_as_false or discard.
        :param aug_rate: Augmentation rate for varying window size augmentation.
        :param aug_mixes: Augmentation mix for purity/downsampling augmentation.
        """
        all_data_list = []
        for sample, paths in data_paths.items():
            logger.info('Processing files in: {}'.format(paths['tensors']))

            df_merge = get_merged_df(
                paths,
                self.prediction_mode,
                self.for_train,
                aug_mixes,
                unknown_strategy
            )
            if df_merge is None:
                continue
            data_list, class_idx = populate(df_merge, sample, self.aug_rate)
            # save the file information and true, false, unknown index_mappings
            self._update_class_indices(class_idx, len(all_data_list))
            all_data_list.extend(data_list)
        return np.array(all_data_list)

    def _print_info(self, aug_mixes):
        """Print information about data

        :param aug_mixes: Augmentation mix for purity/downsampling augmentation.
        """

        logger.info('Number of tensors: {}'.format(len(self.data_list)))
        for key in self.index_mappings.keys():
            logger.info(
                'Number of {}s: {}'.format(key, len(self.index_mappings[key]))
            )
        if self.for_train:
            logger.info('Augmentation mixes used: {}'.format(aug_mixes))

    def _update_class_indices(self, new_indices, offset):
        """ Add the class information for each index in the data_list

        :param new_indices: The indices matching the AnnotatedTensor in data_list
        :param offset: Start index to add the indices to
        """
        for key in new_indices.keys():
            self.index_mappings[key].extend(
                [ind + offset for ind in new_indices[key]]
            )

    def mix_for_balance(self):
        """When training, use balanced data when available"""
        if self.prediction_mode in GERMLINE_MODES:
            num_instances = len(self.index_mappings['GERMLINE'])
        elif self.prediction_mode in SOMATIC_MODES:
            num_instances = len(self.index_mappings['SOMATIC'])
        else:
            raise Exception(
                'Prediction mode {} is not recognized'.format(
                    self.prediction_mode
                )
            )
        indices = []
        for key in self.index_mappings.keys():
            if len(self.index_mappings[key]) > 0:
                indices.extend(list(np.random.choice(
                    self.index_mappings[key],
                    size=min(num_instances, len(self.index_mappings[key]))
                )))
                random.shuffle(indices)
                # TODO: convert to np style
                self.balanced_data_list = [self.data_list[i] for i in indices]

    def __len__(self) -> int:
        """Get the length of the data set, different for training vs. testing.

        For train, return length of the balanced_data_list.
        Otherwise length of the data_list.

        :return: Length of the data set.
        """
        if self.for_train:
            return len(self.balanced_data_list)
        return len(self.data_list)

    def __getitem__(self, idx: int) -> Dict:
        """Get one item with index idx from the data set.

        When training, returns from the balanced_data_list, when testing returns from data_list.

        :param idx: Index of the item.
        :return: A dictionary of the tensor (key: 'X'), mutation type,
         (key: 'y1'), mutation length, type (key: 'y2'),
         also metadata (key: 'metadata') for evaluation.
        """
        if self.for_train:
            arr = torch.load(self.balanced_data_list[idx].tensor)
            clip_length = self.balanced_data_list[idx].clip_length
            if clip_length > 0:
                arr = clip_array(arr, arr.shape[3], self.aug_rate, clip_length)
            return {
                'X': arr,
                'y1': self.balanced_data_list[idx].mutation_type,
                'y2': self.balanced_data_list[idx].mutation_length_type
            }
        else:
            arr = torch.load(self.data_list[idx].tensor)
            clip_length = self.data_list[idx].clip_length
            if clip_length > 0:
                arr = clip_array(arr, arr.shape[3], self.aug_rate, clip_length)
            d = self.data_list[idx]
            return {
                'X': arr,
                'y1': d.mutation_type,
                'y2': d.mutation_length_type,
                'metadata': d.metadata
            }


class MutationDataLoader:
    """Class that encapsulates a torch.utils.data.DataLoader object."""

    def __init__(self, hp, for_training: bool = False):
        """ Initializer for data loader object.

        Takes a list of home directories of the input .pt files, a list of
        matching label files, candidate files, a batch size, and whether it is
        initialized for training/testing.

        :param hp: hyperparameters.
        :param for_training: True if initialized for train, False otherwise
        """
        if for_training:
            paths = hp.train_paths
            unknown_strategy = hp.unknown_strategy_tr
        else:
            paths = hp.valid_paths
            unknown_strategy = hp.unknown_strategy_val

        self.dataset = MutationDataset(
            paths,
            for_training,
            unknown_strategy,
            hp.aug_rate,
            hp.aug_mixes,
            hp.prediction_mode,
        )
        if for_training:
            self.batch_size = hp.batch_size
        else:
            self.batch_size = hp.batch_size * 4
        self.for_train = for_training

    def get_data_loader(self) -> DataLoader:
        """Get the data loader object.

        Behaves differently for training vs. testing.

        :return: Iterable DataLoader object.
        """
        if self.for_train:
            self.dataset.mix_for_balance()

        g = torch.Generator()
        g.manual_seed(5686)
        data_loader = DataLoader(
            self.dataset,
            batch_size=self.batch_size,
            num_workers=8,
            pin_memory=True,
            generator=g
        )
        return data_loader

    def seed_worker(worker_id):
        worker_seed = torch.initial_seed() % 2 ** 32
        np.random.seed(worker_seed)
        random.seed(worker_seed)
