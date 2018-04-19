#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Rainman2

"""

from rainman2.utils import logging_utils
from rainman2.lib import interface
from rainman2.settings import SETTINGS


__author__ = 'Ari Saha (arisaha@icloud.com)'
__date__ = 'Wednesday, February 14th 2018, 10:52:29 am'


# version
__version__ = '1.0'

# logging setup
logging_utils.setup_logging()

RAINMAN2 = interface.Rainman2(SETTINGS)
