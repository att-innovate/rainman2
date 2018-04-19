#! /usr/bin/env python3
# -*- coding: utf-8 -*-

""" Test cases for cli """

import pytest

# pylint: disable=unused-import
from pytest_mock import mocker  # noqa
from click.testing import CliRunner
from rainman2 import RAINMAN2
from rainman2.cli.main import cli

__author__ = 'Ari Saha (arisaha@icloud.com)'
__date__ = 'Thursday, March 1st 2018, 9:10:28 pm'


@pytest.fixture()
def runner():
    return CliRunner()


def test_cellular_qlearning_naive_cmd(runner, mocker):  # noqa
    # pylint: disable= E1101
    mocker.patch.object(RAINMAN2, 'run_experiment')
    RAINMAN2.run_experiment.return_value = 0
    result = runner.invoke(cli, ['Cellular', 'qlearning_naive'])
    assert result.exit_code == 0
    RAINMAN2.run_experiment.assert_called_with(
        'Cellular', 'Qlearning', 'Naive')


def test_cellular_qlearning_linear_regression_cmd(runner, mocker):  # noqa
    # pylint: disable= E1101
    mocker.patch.object(RAINMAN2, 'run_experiment')
    RAINMAN2.run_experiment.return_value = 0
    result = runner.invoke(
        cli, ['Cellular', 'qlearning_linear_regression'])
    assert result.exit_code == 0
    RAINMAN2.run_experiment.assert_called_with(
        'Cellular', 'Qlearning', 'LinearRegression')


def test_cellular_qlearning_nn_cmd(runner, mocker):  # noqa
    # pylint: disable= E1101
    mocker.patch.object(RAINMAN2, 'run_experiment')
    RAINMAN2.run_experiment.return_value = 0
    result = runner.invoke(cli, ['Cellular', 'qlearning_nn'])
    assert result.exit_code == 0
    RAINMAN2.run_experiment.assert_called_with(
        'Cellular', 'Qlearning', 'NN')
