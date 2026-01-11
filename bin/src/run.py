from pandas.core.window.ewm import *
import logging
import warnings
from collections import defaultdict

import fire
import numpy as np
import os
import random
import torch
from glob import glob
from typing import List, Text

from src.constants import GERMLINE_MODES, SOMATIC_MODES, UNKNOWN_STRATEGIES, \
    DATASETS
from src.evaluation import evaluate_model
from src.pipeline import pipeline

FORMAT = '%(levelname)s %(asctime)-15s %(name)-20s %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)

random.seed(567497)
torch.manual_seed(37546)
np.random.seed(6746549)


class Hyperparams:
    """Train/call the VariantMedium models with given data & hyperparameters"""

    def __init__(
            self,
            run: Text,
            home_folder: Text,
            prediction_mode: Text,
            out_path: Text = os.getcwd(),
            learning_rate: float = 0.,
            epoch: int = 0,
            drop_rate: float = 0.,
            batch_size: int = 64,
            class_balance: List[float] = (0.3, 0.3, 0.4),
            pretrained_model: Text = None,
            num_init_features: int = 256,
            growth_rate: int = 16,
            bn_size: int = 4,
            block_config: List[int] = (4,),
            aug_rate: int = 0,
            aug_mixes: List[Text] = None,
            tensor_type: Text = 'freq150',
            unknown_strategy_tr: Text = 'keep_as_false',
            unknown_strategy_val: Text = 'keep_as_false',
            unknown_strategy_call: Text = 'discard',
    ):
        """Constructor for training.

        :param home_folder: Home folder containing all the necessary data.
        tensors, labels, candidates, train/test.
        :param prediction_mode: Predict one of: somatic_snv, somatic_indel,
        germline_snp, germline_indel.
        :param out_path: Output directory.
        :param learning_rate: Learning rate for training.
        :param epoch: Number of epochs.
        :param drop_rate: Dropout rate.
        :param batch_size: Batch size.
        :param class_balance: Weights for each class for computing loss.
        :param pretrained_model: Path to the pretrained model.
        :param num_init_features: Number of input features to the DenseNet
        :param growth_rate: Growth rate of the DenseNet
        :param bn_size: Bottleneck size of the DenseNet
        :param block_config: Block configuration of the DenseNet
        :param aug_rate: Augmentation rate for tensor_type size aug.
        :param aug_mixes: Purity/downsampling/normal contamination mixes.
        :param tensor_type: Tensor type and window size, e.g. freq150.
        :param unknown_strategy_tr: What to do with unknown class in training.
        keep_as_false or discard
        :param unknown_strategy_val: What to do with unknown class in validation.
        keep_as_false or discard
        """
        self.architecture = 'DenseSomatic3D'
        self.channels = 24
        self.num_classes = 3
        self.run = run
        self._set_home_folder(home_folder)
        self.out_path = out_path

        self.aug_mixes = aug_mixes

        self._set_pretrained_model(pretrained_model)
        self._set_tensorboard_dir()
        self._set_prediction_mode(prediction_mode)

        self.tensor_type = tensor_type
        self.num_init_features = num_init_features
        self.growth_rate = growth_rate
        self.bn_size = bn_size
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.aug_rate = aug_rate
        self.drop_rate = drop_rate
        self.epoch = epoch
        self._set_block_config(block_config)
        self._set_class_balance(class_balance)
        self.unknown_strategy_tr = self._check_unknown_strategy(
            unknown_strategy_tr, 'Training'
        )
        self.unknown_strategy_val = self._check_unknown_strategy(
            unknown_strategy_val, 'Validation'
        )
        self.unknown_strategy_call = self._check_unknown_strategy(
            unknown_strategy_call, 'Calling'
        )

    def train(self):
        if self.learning_rate <= 0.:
            raise Exception(
                "Learning rate should be higher than 0 for training"
            )
        # if self.epoch <= 0:
        #     raise Exception(
        #         "Number of epochs should be higher than 0 for training"
        #     )
        self.train_paths = self._get_tensors_folders('train', self.tensor_type)
        self.valid_paths = self._get_tensors_folders('valid', self.tensor_type)
        pipeline(self)
        evaluate_model(self)

    def call(self):
        if self.pretrained_model is None:
            raise Exception(
                "No pretrained model is given for call mode. Exiting..."
            )
        self.train_paths = {'model': self.pretrained_model}
        self.valid_paths = self._get_tensors_folders('call', self.tensor_type)
        self.unknown_strategy_val = self.unknown_strategy_call
        pipeline(self, call=True)

        if list(self.valid_paths.values())[0]['labels']:
            evaluate_model(self, call_mode=True)

    def evaluate(self):
        if self.pretrained_model is None:
            raise Exception(
                "No pretrained model is given for call mode. Exiting..."
            )
        self.train_paths = {'model': self.pretrained_model}
        self.valid_paths = self._get_tensors_folders('call', self.tensor_type)
        if len(self.valid_paths) == 0:
            raise Exception('No path found for evaluation mode. Make sure '
                            'your call folder is not empty, and the paths are '
                            'correct')
        self.unknown_strategy_val = self.unknown_strategy_call
        evaluate_model(self)

    def _set_home_folder(self, home_folder):
        if not os.path.exists(home_folder):
            raise Exception(
                'The path to the home_folder does not exist: {}'.format(
                    home_folder
                )
            )
        self.home_folder = home_folder

    def _get_tensors_folders(self, dataset, tensor_type):
        if dataset not in DATASETS:
            raise Exception(
                'Dataset {} is not supported. Should be one of : {}'.format(
                    dataset, DATASETS
                )
            )
        dataset_home = os.path.join(self.home_folder, dataset)
        sample_paths = os.path.join(dataset_home, '*')
        samples = [os.path.split(path)[1] for path in glob(sample_paths)]
        data_paths = defaultdict(dict)
        for sample in samples:
            sample_dir = os.path.join(dataset_home, sample)
            tensors, labels, candidates = self._process_sample_paths(
                sample, sample_dir, tensor_type, dataset
            )
            data_paths[sample]['tensors'] = tensors
            data_paths[sample]['labels'] = labels
            data_paths[sample]['candidates'] = candidates
        return data_paths

    def _process_sample_paths(self, sample, sample_dir, tensor_type, dataset):
        if os.path.exists(sample_dir):
            tensors_home = os.path.join(sample_dir, tensor_type)
            labels_path = os.path.join(sample_dir, 'labels.tsv')
            candidates_path = os.path.join(sample_dir, 'candidates.tsv')
            if (os.path.exists(tensors_home) and
                    os.path.exists(labels_path) and
                    os.path.exists(candidates_path)):
                return tensors_home, labels_path, candidates_path
            elif (dataset == 'call' and
                  os.path.exists(tensors_home) and
                  os.path.exists(candidates_path)):
                return tensors_home, None, candidates_path
            raise Exception(
                'The sample {} does not contain sufficient data to proceed. '
                'Please check if tensor folder, labels file and candidates '
                'file exists under directory {}'.format(sample, sample_dir)
            )
        raise Exception(
            'The input path for sample {} does not exist: {}'.format(
                sample, sample_dir
            )
        )

    def _set_tensorboard_dir(self):
        self.tensorboard_dir = os.path.join(
            self.home_folder, 'tensorboard', str(self.run)
        )
        os.makedirs(self.tensorboard_dir, exist_ok=True)

    def _set_prediction_mode(self, prediction_mode):
        if not (prediction_mode in GERMLINE_MODES
                or prediction_mode in SOMATIC_MODES):
            raise Exception(
                'Prediction mode is not valid. Should be one of {} {}'.format(
                    GERMLINE_MODES, SOMATIC_MODES
                )
            )
        self.prediction_mode = prediction_mode

    def _set_block_config(self, block_config):
        if len(block_config) > 2:
            warnings.warn(
                'DenseNets with more than 3 blocks are not suitable for '
                'frequency matrices and will cause errors'
            )
        self.block_config = block_config

    def _set_class_balance(self, class_balance):
        if len(class_balance) != self.num_classes:
            raise Exception(
                'The number of classes in the class balance field does not'
                'match the number of classes in the assigned architecture'
            )
        self.class_balance = torch.Tensor(class_balance)

    def _check_unknown_strategy(self, strategy, dataset):
        if strategy not in UNKNOWN_STRATEGIES:
            raise Exception(
                '{} set unknown strategy "{}" not recognized. Should be one of '
                'keep_as_false or discard.'.format(dataset, strategy)
            )
        return strategy

    def _set_pretrained_model(self, pretrained_model):
        if not pretrained_model or not os.path.exists(pretrained_model):
            warnings.warn(
                'Pretrained model not given or the path to it does not exist. '
                'The weights will be initialized randomly.'
            )
            self.pretrained_model = None
        else:
            self.pretrained_model = pretrained_model

    def __repr__(self):
        return '\n' \
               'Model type: {}\n' \
               'Train samples: {}\n' \
               'Validation samples: {}\n' \
               'Window size: {}\n' \
               'Number of initial features: {}\n' \
               'Growth rate: {}\n' \
               'Bottleneck size: {}\n' \
               'Block configuration: {}\n' \
               'Channels: {}\n' \
               'Class balance: {}\n' \
               'Batch size: {}\n' \
               'Learning rate: {}\n' \
               'Epochs: {}\n' \
               'Augmentation rate: {}\n' \
               'Augmentation mixes: {}\n' \
               'Drop rate: {}\n' \
               'Predict germline variants: {}\n' \
               'Unknown strategy training: {}\n' \
               'Unknown strategy validation: {}\n' \
               'Pretrained path: {}\n'.format(
            self.architecture,
            list(self.train_paths.keys()),
            list(self.valid_paths.keys()),
            self.tensor_type,
            self.num_init_features,
            self.growth_rate,
            self.bn_size,
            self.block_config,
            self.channels,
            self.class_balance,
            self.batch_size,
            self.learning_rate,
            self.epoch,
            self.aug_rate,
            self.aug_mixes,
            self.drop_rate,
            self.prediction_mode,
            self.unknown_strategy_tr,
            self.unknown_strategy_val,
            self.pretrained_model
        )
