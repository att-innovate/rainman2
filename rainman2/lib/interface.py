#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Defines internal interface for rainman2
"""

import logging
from rainman2.utils import exceptions
from rainman2.utils import common_utils
from rainman2.lib.algorithm.Qlearning import controller

from rainman2.lib.environment.cellular import base as cellular_base

__author__ = 'Ari Saha (arisaha@icloud.com)'
__date__ = 'Thursday, February 15th 2018, 1:29:18 pm'


SUPPORTED_ALGORITHMS = {
    'Qlearning': controller.QController
}

SUPPORTED_ENVIRONMENTS = {
    'Cellular': cellular_base.CellularNetworkEnv,
}


class Rainman2:
    # pylint: disable=too-few-public-methods
    """
    Definition of internal API
    """
    def __init__(self, settings):
        """
        Initialize internal API object
        """
        self.settings = settings
        self.algorithm_config = self.settings.algorithm_config
        self.environment_config = self.settings.environment_config
        self.update_env = self.settings.update_env

        self.logger = logging.getLogger(self.__class__.__name__)

    def _build_env_client(self, env_name):
        """
        Helper to build envrionment's client if any
        """
        if env_name == 'Cellular':
            try:
                client = cellular_base.initialize_client(
                    self.environment_config)
            except exceptions.ClientNotImplemented as error:
                self.logger.debug("Error: {}".format(error))
                raise
            else:
                return client
        return None

    def _build_env_instance(self, env_name):
        """
        Helper method to instantiate Env object
        """
        self.environment_config = self.update_env(env_name)
        if env_name not in SUPPORTED_ENVIRONMENTS:
            error = "Environment: {} is not implemented!".format(env_name)
            self.logger.debug(error)
            raise exceptions.EnvironmentNotImplemented(error)
        self.logger.info(
            "Building Environment instance: {}".format(env_name))
        env_client = self._build_env_client(env_name)
        return SUPPORTED_ENVIRONMENTS[env_name](
            self.environment_config, env_client)

    def _build_alg_instance(self, algorithm_name, env_instance, agent_name):
        """
        Helper method to instantiate Alg object

        Args:
            algorithm_name: (instance of agorithm)
                Reinforcement-Learning algorithm to evaluate the environment.
            agent_name: (instance of agent)
                Algorithm's agent
        """
        if algorithm_name not in SUPPORTED_ALGORITHMS:
            error = "Algorithm: {} is not implemented".format(algorithm_name)
            self.logger.debug(error)
            raise exceptions.AlgorithmNotImplemented(error)
        self.logger.debug(
            "Building Algorithm instance: {}".format(algorithm_name))
        return SUPPORTED_ALGORITHMS[algorithm_name](
            self.algorithm_config, env_instance, agent_name)

    @common_utils.timeit
    def run_experiment(self, env_name, algorithm_name, agent_name=None):
        """
        Defines interface to run an experiment

        Args:
            env_name: (Name of the environment)
                Environment Name
            algorithm_name: (instance of agorithm)
                Reinforcement-Learning algorithm to evaluate the environment.
            agent_name: (instance of agent)
                Algorithm's agent

        Returns:
            results: (instance of output)
        """
        self.logger.info("Starting experiment!")

        try:
            env_instance = self._build_env_instance(env_name)
        except exceptions.EnvironmentNotImplemented as error:
            raise

        try:
            alg_instance = self._build_alg_instance(
                algorithm_name, env_instance, agent_name)
        except exceptions.AlgorithmNotImplemented as error:
            raise

        try:
            output = alg_instance.execute()
        except Exception as error:
            self.logger.exception(
                "Experiment failed! Error: {}".format(error))
        else:
            return output


def main():
    """
    Performance testing
    """
    # Server profile: num_ues=200, APs=16, Scale=200.0, explore_radius=1
    from collections import OrderedDict
    from rainman2.settings import SETTINGS
    ALGORITHM_CONFIG = OrderedDict(
        EPISODES=1,
        ALPHA=0.2,
        GAMMA=0.9,
        EPSILON=0.3,
        EPSILON_DECAY=0.99,
        EPSILON_MIN=0.01,
        VERBOSE=True,
        L1_HIDDEN_UNITS=13,
        L2_HIDDEN_UNITS=13,
        L1_ACTIVATION='relu',
        L2_ACTIVATION='relu',
        LOSS_FUNCTION='mean_squared_error',
        OPTIMIZER='Adam',
    )

    CELLULAR_MODEL_CONFIG = OrderedDict(
        NAME='Cellular',
        TYPE='Dev',
        SERVER='0.0.0.0',
        SERVER_PORT='8000',
        VERBOSE=True,
    )

    rainman2 = Rainman2(SETTINGS)
    rainman2.algorithm_config = ALGORITHM_CONFIG
    rainman2.environment_config = CELLULAR_MODEL_CONFIG

    result = rainman2.run_experiment("Cellular", "Qlearning", "Naive")
    print("Number of states encountered: {}".format(len(result.Q)))
    print("Number of q_ap_states encountered: {}".format(len(result.Q_ap)))
    print(result.Q)
    print(result.Q_ap)


if __name__ == '__main__':
    main()
