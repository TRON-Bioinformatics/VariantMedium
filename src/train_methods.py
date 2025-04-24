import logging
import time

import numpy as np
import random
import torch
import torch.nn as nn

from dataloaders.data_loader import MutationDataLoader
from valid_methods import validate_network
from utils import *

# from variantmedium.early_stopping import EarlyStopping

logger = logging.getLogger(__name__)
random.seed(567497)
torch.manual_seed(37546)
np.random.seed(6746549)


def train_network(
        train_loader: MutationDataLoader,
        valid_loader: MutationDataLoader,
        network: nn.Module,
        criterion1: nn.modules.loss,
        criterion2: nn.modules.loss,
        optimizer: torch.optim.SGD,
        scheduler: torch.optim.lr_scheduler,
        hp,
        writer=None,
):
    """Train and validate the network with the given data set and hyperparameters.

    :param train_loader: MutationDataLoader object for the training set.
    :param valid_loader: MutationDataLoader object for the validation set.
    :param network: The network to be trained, initialized.
    :param criterion1: Loss function for mutation class prediction.
    :param criterion2: Loss function for mutation length class prediction.
    :param optimizer: Optimizer function.
    :param hp: Hyperparameters.
    :param writer: Writer object for TensorBoard
    """
    start_time = time.time()

    device, network = migrate_to_gpu(network)

    step = 0
    max_auprc = 0
    for epoch in range(hp.epoch):
        running_loss = 0.
        for i, data in enumerate(train_loader.get_data_loader(), 0):
            # get the inputs
            inputs, mutation_classes, mutation_length_classes = get_batch_data(
                data, device)
            network.train()
            # zero the parameter gradients
            optimizer.zero_grad()
            try:
                outputs1, outputs2 = network(inputs)
                loss1 = criterion1(outputs1, mutation_classes)
                loss2 = criterion2(outputs2, mutation_length_classes)
                loss = loss1 + loss2
                loss.backward()
                optimizer.step()
                scheduler.step()
                running_loss += float(loss.item())
                # print statistics
                step = save_stats(writer, loss, step, 'training_loss')
                if step % PRINT_FREQ == 0:
                    logger.info(
                        '{} {} loss: {:.3}'.format(
                            epoch + 1,
                            i + 1,
                            running_loss / PRINT_FREQ
                        )
                    )
                    running_loss = 0.
                if step % VALIDATION_FREQ == 0:
                    max_auprc, step = save_successful_model(
                        loader=valid_loader,
                        hp=hp,
                        network=network,
                        writer=writer,
                        max_score=max_auprc,
                        step=step,
                    )
            except RuntimeError as e:
                logger.error(e)

    save_successful_model(
        loader=valid_loader,
        hp=hp,
        network=network,
        writer=writer,
        max_score=max_auprc,
        step=step,
    )
    logger.info('Finished training network in {} minutes'.format(
        (time.time() - start_time) / 60
    ))


def save_successful_model(
        loader: MutationDataLoader,
        hp,
        network: nn.Module,
        writer,
        max_score: float,
        step: int,
):
    """Compute the performance over the validation set and save the model if
    it is better than prev models.

    :param loader: Loader for the validation set
    :param hp: Hyperparameters
    :param network: The model
    :param writer: Tensorboard writer object
    :param max_score: Maximum AUPRC value obtained so far
    :param step: Training step
    :return: max_auprc, step
    """
    _, _, score = validate_network(loader, hp, network=network)
    tag = 'validation_auprc'

    if score > max_score:
        torch.save(network.state_dict(), BEST_MODEL_FNAME)
        max_score = score

    step = save_stats(writer, score, step, tag)

    return max_score, step
