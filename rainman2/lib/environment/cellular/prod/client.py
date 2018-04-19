#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Provides Rest apis for interaction with Production cellular network
"""

from rainman2.lib.environment.cellular import client_template


__author__ = 'Ari Saha (arisaha@icloud.com)'
__date__ = 'Tuesday, February 20th 2018, 2:06:00 pm'


class CellularProdClient(client_template.Base):
    def __init__(self):
        pass
