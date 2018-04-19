#! /usr/bin/env python3
# -*- coding: utf-8 -*-

""" Test cases for interface """

import pytest
from collections import OrderedDict
from rainman2 import RAINMAN2
from rainman2.lib import interface
from rainman2.lib.environment.cellular.dev import client as cellular_dev_client

__author__ = 'Ari Saha (arisaha@icloud.com)'
__date__ = 'Sunday, April 1st 2018, 9:02:19 pm'

QLEARNING_REGRESSION_CONFIG = OrderedDict(
    EPISODES=1000,
    ALPHA=0.1,
    GAMMA=0.8,
    EPSILON=0.3,
    EPSILON_DECAY=0.999,
    EPSILON_MIN=0.01,
    VERBOSE=False,
)

CELLULAR_DEV_CONFIG = OrderedDict(
    NAME='Cellular',
    TYPE='Dev',
    SERVER='0.0.0.0',
    SERVER_PORT='8000',
    VERBOSE=True
)


@pytest.fixture
def rainman_instance():
    """
    Create a Rainman instance
    """
    RAINMAN2.algorithm_config = QLEARNING_REGRESSION_CONFIG
    RAINMAN2.environment_config = CELLULAR_DEV_CONFIG
    return RAINMAN2


def test_build_env_client(rainman_instance):
    """
    Tests _build_env_client function
    """
    client = rainman_instance._build_env_client('Cellular')
    assert isinstance(client, cellular_dev_client.CellularDevClient)


@pytest.fixture
def test_build_env_instance(rainman_instance):
    """
    Tests _build_env_instance function.
    """
    env_instance = rainman_instance._build_env_instance('Cellular')
    assert isinstance(env_instance,
                      interface.SUPPORTED_ENVIRONMENTS['Cellular'])
    return env_instance


def test_build_alg_instance(rainman_instance, test_build_env_instance):
    """
    Tests _build_alg_instance function.
    """
    alg_instance = rainman_instance._build_alg_instance(
        'Qlearning', test_build_env_instance, 'Naive')
    assert isinstance(alg_instance,
                      interface.SUPPORTED_ALGORITHMS['Qlearning'])
    return alg_instance


def main():
    """
    Test locally
    """
    rainman = rainman_instance()
    env_instance = test_build_env_instance(rainman)
    test_build_alg_instance(rainman, env_instance)


if __name__ == '__main__':
    main()
