import numpy as np
import random
import torch
import torch.nn as nn
from torch.nn import functional as F
from typing import Dict, List, Tuple, Text

from architecture import initialize_network
from dataloaders.data_loader import MutationDataLoader
from utils import *

# import os
# import sys
# module_path = os.path('temperature_scaling/')
# if module_path not in sys.path:
#     sys.path.append(module_path)
# from temperature_scaling import ModelWithTemperature
random.seed(567497)
torch.manual_seed(37546)
np.random.seed(6746549)


def validate_network(
        loader: MutationDataLoader,
        hp,
        network_path: str = None,
        network: nn.Module = None,
):
    """Validate the performance using an independent data set.

    Either network_path or network has to be passed in order for this function to work.

    :param hp: Hyperparameters object
    :param writer: Writer object for Tensorboard
    :param loader: MutationDataLoader object for the independent validation set.
    :param network_path: Path to the trained network.
    :param network: Trained network. If network_path is given, this is ignored.
    :param is_final: Is this the final run for this
    :return: Average precision values, binary predictions, metadata
    """
    if not network_path and not network:
        raise Exception(
            'Both network and network network_path are empty. You need to input one of them.'
        )
    if network_path:
        network = initialize_network(hp, network_path)

    seed = 0
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    device, network = migrate_to_gpu(network)

    # if is_final:
    #     network = f(network)
    #     network.set_temperature(loader.get_data_loader())
    #     torch.save(network.state_dict(), 'best_model.pt')

    # aug_rate = 0
    # if loader.dataset.for_final_validation:
    #     aug_rate = hp.aug_rate
    arr_len = len(loader.get_data_loader().dataset.data_list)
    if torch.cuda.is_available():
        scores_arr = torch.zeros(arr_len, 3, dtype=torch.float16).cuda()
        labels_arr = torch.zeros(arr_len, dtype=torch.int8).cuda()
    else:
        scores_arr = torch.zeros(arr_len, 3, dtype=torch.float)
        labels_arr = torch.zeros(arr_len, dtype=torch.int8)
    metadata_arr = np.ndarray([arr_len, 7], dtype=object)

    with torch.no_grad():
        start = 0
        # for a in range(aug_rate + 1):
        #     loader.dataset.val_clip_length = a
        for i, data in enumerate(loader.get_data_loader()):
            network.eval()
            inputs, labels, metadata = data['X'], data['y1'], data['metadata']
            inputs = inputs.to(device, dtype=torch.float, non_blocking=True)
            scores, _ = network(inputs)

            end = start + len(scores)
            scores_arr[start:end] = scores
            labels_arr[start:end] = labels
            for ind in range(7):
                metadata_arr[start:end, ind] = metadata[ind]
            start = end
        if torch.cuda.is_available():
            scores_arr = F.softmax(scores_arr.cuda(), dim=1)
        else:
            scores_arr = F.softmax(scores_arr, dim=1)

    nn_scores, auprc = sum_up(
        hp,
        scores_arr.cpu().numpy(),
        labels_arr.cpu().numpy()
    )
    return nn_scores, metadata_arr, auprc


def extend_metadata(all_metadata: Dict[Text, List], metadata: Tuple[List]):
    """Extend the metadata dictionary with incoming information.

    :param all_metadata: The main metadata dictionary.
    :param metadata: The new metadata tuple.
    """
    all_metadata['chr'].extend(metadata[0])
    all_metadata['pos'].extend(metadata[1])
    all_metadata['ref'].extend(metadata[2])
    all_metadata['alt'].extend(metadata[3])
    all_metadata['sample'].extend(metadata[4])
    all_metadata['replicate'].extend(metadata[5])
    all_metadata['clipping'].extend(metadata[6])


def sum_up(hp, scores, labels):
    """ Sum up validation by computing the AUPRC/AUROC scores and printing them.

    :param hp: Hyperparameters.
    :param scores: Scores assigned to each variant by the network.
    :param labels: Ground truth labels.
    :return: Scores by NN, AUPRC value on binary classification task.
    """
    # get auprc
    auprc_all, auroc_all, nn_scores = compute_binary_performance(
        labels, scores, hp.prediction_mode,
    )

    print_performance(
        labels, scores, auprc_all, auroc_all,
    )

    scores = np.append(scores, np.reshape(nn_scores, [nn_scores.shape[0], 1]),
                       axis=1)

    return scores, auprc_all
