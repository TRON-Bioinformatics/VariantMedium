import logging
import numpy as np
import random
import time
from collections import OrderedDict
from typing import Text

import torch
from src.models.densesomatic3d import densesomatic3d

logger = logging.getLogger(__name__)
random.seed(567497)
torch.manual_seed(37546)
np.random.seed(6746549)


def select_architecture(hp):
    """ Select an architecture and initialize a model with it.

    :param hp: Hyperparameters
    :return: A model initialized with selected architecture.
    """
    if hp.architecture == 'DenseSomatic3D':
        # remove ref and pos hyperparams.channels, separate by ref, tum, nor
        return densesomatic3d(
            init_features=hp.num_init_features,
            growth_rate=hp.growth_rate,
            block_config=tuple(hp.block_config),
            bn_size=hp.bn_size,
            channels=int((hp.channels - 2) / 2),
            drop_rate=hp.drop_rate,
        )
    else:
        raise Exception('Selected architecture {} is not supported'.format(
            hp.architecture
        ))


def initialize_network(hp, network_path: Text = None):
    """Initialize the network based on the given parameters.

    :param hp: Hyperparameters.
    :param network_path: Path to the pretrained network if there is one.
    :return: Initialized network, loaded with pretrained weights if given.
    """
    start_time = time.time()
    network = select_architecture(hp)
    if network_path:
        logger.info('Loading pretrained network {}'.format(network_path))
        if torch.cuda.is_available():
            network.load_state_dict(torch.load(network_path), strict=False)
        else:
            network.load_state_dict(
                torch.load(network_path, map_location=torch.device('cpu')),
                strict=False
            )

        new_state_dict = OrderedDict()
        for k, v in network.state_dict().items():
            name = k.replace('module.', '')
            new_state_dict[name] = v
        network.load_state_dict(new_state_dict)
    logger.info('Initialized network in {} seconds'.format(
        time.time() - start_time
    ))
    return network
