#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Declares external APIs

e.g.:
(venv)$ rainman2 --help
Using TensorFlow backend.
Rainman2's logging has been configured!
Usage: rainman2 [OPTIONS] COMMAND [ARGS]...

  Rainman2's cli

Options:
  --verbose BOOLEAN      show verbose output for debugging
  --epsilon_min FLOAT    min value for epsilon to stop updating
  --epsilon_decay FLOAT  rate at which epsilon gets updated
  --epsilon FLOAT        epsilon for epsilon-greedy policy
  --gamma FLOAT          discount factor
  --alpha FLOAT          learning rate
  --episodes INTEGER     numeber of episodes/epochs
  --help                 Show this message and exit.

Commands:
    Cellular  Arguments for cellular environment

Each Environment will list all the possible algorithms
(venv)$ rainman2 --alpha 0.6 Cellular --help
Using TensorFlow backend.
Rainman2's logging has been configured!
Usage: rainman2 Cellular [OPTIONS] COMMAND [ARGS]...

  Arguments for cellular environment

Options:
  --env_type [Dev|Prod]  type of cellular network: Dev/Prod
  --help                       Show this message and exit.

Commands:
  qlearning_linear_regression  Qlearning with Linear Regressor as Function...
  qlearning_naive              Qlearning without any function approximator...
  qlearning_nn                 Qlearning with Neural Network as Function...

For using qlearning with NN FA on stationary cellular env model:
rainman2 --episodes 1000 --alpha 0.01 --gamma 0.9 --epsilon 0.01
Cellular qlearning_nn --l1_hidden_units 10 --l1_activation relu
"""

import logging
import click
from rainman2 import RAINMAN2

__author__ = 'Ari Saha'
__date__ = 'Friday, February 16th 2018, 3:04:16 pm'

RUNNING_ALG_CONFIG = RAINMAN2.algorithm_config
RUNNING_ENV_CONFIG = RAINMAN2.environment_config


@click.option('--episodes', type=click.INT,
              default=RUNNING_ALG_CONFIG['EPISODES'],
              help='numeber of episodes/epochs')
@click.option('--alpha', type=click.FLOAT,
              default=RUNNING_ALG_CONFIG['ALPHA'],
              help='learning rate')
@click.option('--gamma', type=click.FLOAT,
              default=RUNNING_ALG_CONFIG['GAMMA'],
              help='discount factor')
@click.option('--epsilon', type=click.FLOAT,
              default=RUNNING_ALG_CONFIG['EPSILON'],
              help='epsilon for epsilon-greedy policy')
@click.option('--epsilon_decay', type=click.FLOAT,
              default=RUNNING_ALG_CONFIG['EPSILON_DECAY'],
              help='rate at which epsilon gets updated')
@click.option('--epsilon_min', type=click.FLOAT,
              default=RUNNING_ALG_CONFIG['EPSILON_MIN'],
              help='min value for epsilon to stop updating')
@click.option('--verbose', type=click.BOOL,
              default=RUNNING_ALG_CONFIG['VERBOSE'],
              help='show verbose output for debugging')
@click.group('cli')
def cli(episodes,
        alpha,
        gamma,
        epsilon,
        epsilon_decay,
        epsilon_min,
        verbose):
    # pylint: disable=too-many-arguments
    """
    Rainman2's cli
    """

    RUNNING_ALG_CONFIG['EPISODES'] = episodes
    RUNNING_ALG_CONFIG['ALPHA'] = alpha
    RUNNING_ALG_CONFIG['GAMMA'] = gamma
    RUNNING_ALG_CONFIG['EPSILON'] = epsilon
    RUNNING_ALG_CONFIG['EPSILON_DECAY'] = epsilon_decay
    RUNNING_ALG_CONFIG['EPSILON_MIN'] = epsilon_min
    RUNNING_ALG_CONFIG['VERBOSE'] = verbose


@cli.group('Cellular')
@click.option('--env_type', type=click.Choice(['Dev', 'Prod']),
              default='Dev',
              help='type of cellular network: Dev/Prod')
def Cellular(env_type):
    # pylint: disable=too-many-arguments
    """
    Arguments for cellular environment
    """

    RUNNING_ENV_CONFIG = RAINMAN2.update_env('Cellular')
    RUNNING_ENV_CONFIG['TYPE'] = env_type


@Cellular.command('qlearning_naive')
def qlearning_naive_cmd():
    """
    Qlearning without any function approximator

    Returns:
        Q: (dict)
            Q(s,a) values
        poliy: (object)
            optimal policy
    """
    logger = logging.getLogger(__name__)
    try:
        RAINMAN2.run_experiment('Cellular', 'Qlearning', 'Naive')
    except Exception as error:
        logger.exception(error)


@Cellular.command('qlearning_linear_regression')
def qlearning_linear_regression_cmd():
    # pylint: disable=invalid-name
    """
    Qlearning with Linear Regressor as Function Approximator

    Returns:
        Q: (dict)
            Q(s,a) values
        policy: (object)
            optimal policy
    """
    logger = logging.getLogger(__name__)
    try:
        RAINMAN2.run_experiment(
            'Cellular', 'Qlearning', 'LinearRegression')
    except Exception as error:
        logger.exception(error)


@Cellular.command('qlearning_nn')
@click.option('--l1_hidden_units', type=click.INT,
              default=RUNNING_ALG_CONFIG['L1_HIDDEN_UNITS'],
              help='hidden units for layer-1')
@click.option('--l2_hidden_units', type=click.INT,
              default=RUNNING_ALG_CONFIG['L2_HIDDEN_UNITS'],
              help='hidden units for layer-2')
@click.option('--l1_activation', type=click.Choice(['relu']),
              default=RUNNING_ALG_CONFIG['L1_ACTIVATION'],
              help='type of activation for layer-1')
@click.option('--l2_activation', type=click.Choice(['relu']),
              default=RUNNING_ALG_CONFIG['L2_ACTIVATION'],
              help='type of activation for layer-2')
@click.option('--loss_function', type=click.Choice(['mean_squared_error']),
              default=RUNNING_ALG_CONFIG['LOSS_FUNCTION'],
              help='loss function')
@click.option('--optimizer', type=click.Choice(['Adam']),
              default=RUNNING_ALG_CONFIG['OPTIMIZER'],
              help='optimizer used in the last layer')
def qlearning_nn_cmd(l1_hidden_units,
                     l2_hidden_units,
                     l1_activation,
                     l2_activation,
                     loss_function,
                     optimizer):
    """
    Qlearning with Neural Network as Function Approximator

    Returns:
        Q: (dict)
            Q(s,a) values
        policy: (object)
            optimal policy
    """
    RUNNING_ALG_CONFIG['L1_HIDDEN_UNITS'] = l1_hidden_units
    RUNNING_ALG_CONFIG['L2_HIDDEN_UNITS'] = l2_hidden_units
    RUNNING_ALG_CONFIG['L1_ACTIVATION'] = l1_activation
    RUNNING_ALG_CONFIG['L2_ACTIVATION'] = l2_activation
    RUNNING_ALG_CONFIG['LOSS_FUNCTION'] = loss_function
    RUNNING_ALG_CONFIG['OPTIMIZER'] = optimizer
    logger = logging.getLogger(__name__)
    try:
        RAINMAN2.run_experiment('Cellular', 'Qlearning', 'NN')
    except Exception as error:
        logger.exception(error)
