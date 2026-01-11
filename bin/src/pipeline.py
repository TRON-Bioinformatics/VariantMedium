import logging
import numpy as np
import random
import time

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter

from src.constants import BEST_MODEL_FNAME
from src.architecture import initialize_network
from src.dataloaders.data_loader import MutationDataLoader
from src.train_methods import train_network
from src.valid_methods import validate_network
from src.utils import save_scores

logger = logging.getLogger(__name__)

random.seed(567497)
torch.manual_seed(37546)
np.random.seed(6746549)


def pipeline(hp, call: bool = False):
    """Pipeline for training and validating the network.
    :param hp: hyperparameters.
    """
    start = time.time()
    logger.info(hp)

    writer = SummaryWriter(hp.tensorboard_dir)

    valid_loader = MutationDataLoader(hp)
    if hp.epoch > 0:
        train_loader = MutationDataLoader(hp=hp, for_training=True)
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

        network = initialize_network(hp, network_path=hp.pretrained_model)
        # criterions for mutation class, and mutation length class.
        criterion1 = nn.CrossEntropyLoss(
            weight=hp.class_balance.to(device, dtype=torch.float)
        )
        criterion2 = nn.CrossEntropyLoss()
        # optimizer
        optimizer = optim.SGD(
            network.parameters(), lr=hp.learning_rate, momentum=0.9
        )
        scheduler = torch.optim.lr_scheduler.CyclicLR(
            optimizer, base_lr=hp.learning_rate, max_lr=hp.learning_rate
        )

        train_network(
            train_loader,
            valid_loader,
            network,
            criterion1,
            criterion2,
            optimizer,
            scheduler,
            hp,
            writer,
        )

        logger.info(network)
        del network
    else:
        BEST_MODEL_FNAME = hp.pretrained_model
    torch.cuda.empty_cache()
    valid_loader.dataset.for_final_validation = True
    scores_valid, metadata_valid, _ = validate_network(
        valid_loader, hp, BEST_MODEL_FNAME
    )
    save_scores(
        scores_valid,
        metadata_valid,
        hp.out_path,
        hp.prediction_mode,
        call_mode=call
    )

    if writer:
        writer.close()

    logger.info('Program finished in {} minutes'.format(
        (time.time() - start) / 60
    ))
