#! /usr/bin/env python3
# -*- coding: utf-8 -*-

""" Simulates a cellular network for development/testing """

import logging
from logging.handlers import RotatingFileHandler
import math
from functools import reduce
from collections import defaultdict
from collections import OrderedDict
from rainman2.lib.environment.cellular.dev import utils

__author__ = 'Ari Saha (arisaha@icloud.com)'
__date__ = 'Tuesday, March 6th 2018, 10:11:29 am'


def setup_logging(module):
    logger = logging.getLogger(module)
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(
        "network.log", maxBytes=1048576, backupCount=20)
    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


class StaticNetwork:
    """
    Simulation of a cellular network where APs are statically positioned in
    every cell of the grid.
    """
    # pylint: disable=E1101
    def __init__(self, num_ues, num_aps, scale, explore_radius=1):
        self.num_ues = num_ues
        self.num_aps = num_aps
        self.scale = scale
        self.explore_radius = explore_radius

        # setup logger
        self.logger = setup_logging(self.__class__.__name__)

        self.logger.info("Specifications of the simulated cellular network:")
        self.logger.info("Number of UES: {}".format(self.num_ues))
        self.logger.info("Number of APs: {}".format(self.num_aps))
        self.logger.info("Scale of each grid: {}".format(self.scale))
        self.logger.info(
            "Explore radius for the APs: {}".format(self.explore_radius))

        # number of aps in x axis
        self.x_units = int(math.sqrt(self.num_aps))
        self.logger.debug("Number of APs in x axis: {}".format(self.x_units))

        # position of aps in each axis
        self.aps_per_axis = [
            (1 + (2 * i)) * self.scale for i in range(self.x_units)]
        self.logger.debug(
            "Location of APs in both axis: {}".format(self.aps_per_axis))

        # Populate AP information
        # location_to_ap_lookup is a local dictionary used to for fast lookup
        # of AP id based on the location.
        self._location_to_ap_lookup = {}
        # Create a Dictionary containing details about the APs within the grid.
        # _ap_dict is used locally only for network functions.
        self._ap_dict = self._place_aps()

        # UE Stats keeps track of number of UEs for each type of app. Only for
        # troubleshooting
        self.ue_app_stats = defaultdict(int)
        self.ue_sla_stats = defaultdict(int)

        # List containing details about the UEs within the grid.
        self._ue_dict = self._instantiate_ues()

        self.logger.debug("Simulated Network summary:")
        self.logger.debug(
            "AP_DICT: {}".format(self._ap_dict))
        self.logger.debug(
            "UE_DICT: {}".format(self._ue_dict))
        self.logger.debug(
            "UE_SLA_STATS: {}".format(self.ue_sla_stats))

    """ Methods for fetching Neighboring APs """
    def neighboring_ap_ids(self, current_ap_location, neighboring_aps):
        """
        Helper method to remove current ap from neighboring aps and return
        list of neighboring ap ids
        """
        neighboring_ap_ids = []
        for ap_location in neighboring_aps:
            if current_ap_location != ap_location:
                neighboring_ap_ids.append(
                    self._location_to_ap_lookup[ap_location])
        return neighboring_ap_ids

    def fetch_neighboring_aps(self, ue, ap):
        """
        Method to fetch list of neighboring aps based on UE's location and
        current AP.
        """
        # Fetch list of neighboring aps
        self.logger.debug("Fetching neighboring AP list for the UE")
        neighboring_aps = utils.get_neighboring_aps(
            ue.location, self.aps_per_axis, self.explore_radius)
        all_neighboring_aps =\
            neighboring_aps.within_grid + neighboring_aps.rest
        neighboring_ap_ids = self.neighboring_ap_ids(
            ap.location, all_neighboring_aps
        )
        return neighboring_ap_ids

    def update_neighboring_aps(self, ue, new_ap):
        """
        Method to update neighboring aps for the UE
        """
        self.logger.debug("Updating UE: {}'s neighboring aps".format(
            ue.ue_id))
        ue.neighboring_aps = self.fetch_neighboring_aps(ue, new_ap)

    """ Method to calculate UE's stats """
    def calculate_ue_throughput(self,
                                current_ap,
                                ue_ap_distance,
                                ue_required_bandwidth):
        """
        Helper to calculate ue_throughput for the current AP
        """
        ap_n_ues = self.total_ues(current_ap.n_ues)
        ap_uplink_bandwidth = current_ap.uplink_bandwidth
        ap_channel_bandwidth = current_ap.channel_bandwidth

        return utils.get_ue_throughput(
            self.scale,
            ue_ap_distance,
            ap_n_ues,
            ap_uplink_bandwidth,
            ap_channel_bandwidth,
            ue_required_bandwidth)

    def calculate_ue_sla(self, ue_throughput, ue_required_bandwidth):
        """
        Helper to calculate UE's SLA

        Returns:
             1: meets
            -1: doen't meet
        """
        meets = utils.get_ue_sla(ue_throughput, ue_required_bandwidth)
        if not meets:
            self.ue_sla_stats["Doesnot"] += 1
        else:
            self.ue_sla_stats["Meets"] += 1
        return meets

    def calculate_ue_signal_power(self, ue_ap_distance):
        """
        Helper to calculate UE's signal power
        """
        return utils.get_ue_sig_power(ue_ap_distance)

    def update_ue_stats(self, ue, ap):
        """
        Helper method to update UE's stats
        """
        self.logger.debug("Updating UE's stats!")
        # Update UE-AP distance
        ue.distance = utils.get_ue_ap_distance(
            ue.location, ap.location
        )
        # Update UE's throughput
        ue.throughput = self.calculate_ue_throughput(
            ap, ue.distance, ue.required_bandwidth
        )
        # Update UE's SLA
        ue.sla = self.calculate_ue_sla(ue.throughput, ue.required_bandwidth)
        ap.ues_meeting_sla[ue.app] += ue.sla

        # Get new signal power based on UE-AP
        ue.signal_power = self.calculate_ue_signal_power(ue.distance)

    """ Methods to instantiating UEs and APs """
    def _place_aps(self):
        """
        Method to place APs in the grid.
        This method creates a dictionary of APs with location tuple (x, y) as
        key and AP obj as value.
        Each AP obj represents a row with ap_id, location, n_ues, etc.
        """
        self.logger.debug("Placing APs in respective grids")
        ap_dict = {}
        ap_id = 1
        # Get x-axis location
        for xloc in self.aps_per_axis:
            # Get y-axis location
            for yloc in self.aps_per_axis:
                # update location
                location = (xloc, yloc)
                self._location_to_ap_lookup[location] = ap_id

                ap_dict[ap_id] = utils.AP(
                    ap_id=ap_id, location=location)

                self.logger.debug("AP {} info:".format(ap_id))
                self.logger.debug(ap_dict[ap_id].to_dict)

                ap_id += 1
        self.logger.debug("APs have been successfully placed!")
        return ap_dict

    def total_ues(self, n_ues_dict):
        """
        Helper to sum total number of ues the AP has.
        """
        return reduce(
            lambda x, y: x+y,
            [len(values) for values in n_ues_dict.values()])

    def _instantiate_ues(self):
        """
        Method to create UEs and connect them to their respective AP
        """
        self.logger.debug(
            "Instantiating {} UEs and placing them accordingly".format(
                self.num_ues))
        ue_dict = {}
        for ue_id in range(1, self.num_ues + 1):

            # Get app_type that the UE is running
            ue_app = utils.get_ue_app()
            self.ue_app_stats[ue_app] += 1
            required_bandwidth = utils.APPS_DICT[ue_app]

            # Get UE's location
            ue_location = utils.get_ue_location(
                ue_app, self.scale, self.aps_per_axis)

            # Get UE's closest AP
            (current_ap_location, neighboring_aps) = utils.get_ue_ap(
                ue_location, self.aps_per_axis, self.explore_radius)

            # Get current ap_id
            current_ap_id = self._location_to_ap_lookup[current_ap_location]

            # Update UE count for the AP
            current_ap = self._ap_dict[current_ap_id]
            current_ap.n_ues[ue_app].add(ue_id)

            new_ue = utils.UE(
                ue_id=ue_id,
                ap=current_ap_id,
                location=ue_location,
                app=ue_app,
                required_bandwidth=required_bandwidth,
                neighboring_aps=self.neighboring_ap_ids(
                    current_ap_location, neighboring_aps
                )
            )

            # Update new_ue's stats
            self.update_ue_stats(new_ue, current_ap)

            self.logger.debug("UE {} info:".format(ue_id))
            self.logger.debug(new_ue.to_dict)

            ue_dict[ue_id] = new_ue
        return ue_dict

    def validate_ue(self, ue_id):
        """
        Helper method to validate if UE with ue_id exists
        """
        try:
            ue = self._ue_dict[ue_id]
        except KeyError as error:
            self.logger.exception(
                "UE with ue_id: {} doesn't exists! Error: {}".format(
                    ue_id, error))
            raise
        else:
            return ue

    def validate_ap(self, ap_id):
        """
        Helper method to validate if AP with ap_id exists
        """
        try:
            ap = self._ap_dict[ap_id]
        except KeyError as error:
            self.logger.exception(
                "AP with ap_id: {} doesn't exists! Error: {}".format(
                    ap_id, error))
            raise
        else:
            return ap

    def handoff_to_ap(self, ue, current_ap, new_ap_id):
        """
        Method to handoff an UE to a new AP
        """
        self.logger.debug("Initiating Handoff!")

        # remove this ue from current AP
        self.logger.debug("Removing the UE from its current AP")
        current_ap.n_ues[ue.app].remove(ue.ue_id)
        current_ap.ues_meeting_sla[ue.app] -= ue.sla

        # locate the new AP
        new_ap = self.validate_ap(new_ap_id)

        self.logger.debug("Handing over the UE to new AP!")
        # update AP for the UE
        ue.ap = new_ap_id
        # add current UE to the requested AP
        new_ap.n_ues[ue.app].add(ue.ue_id)

        # update neighboring APs
        self.update_neighboring_aps(ue, new_ap)

        # update UE's stats
        self.update_ue_stats(ue, new_ap)

        self.logger.debug(
            "UE: {} is handed off from: {} to : {}".format(
                ue.ue_id, current_ap.ap_id, new_ap_id)
                )
        handoff_result = OrderedDict(
            DONE=True,
            UE=ue.to_dict,
            OLD_AP=current_ap.to_dict,
            NEW_AP=new_ap.to_dict
        )
        return handoff_result

    """ Internal APIs """

    def perform_handoff(self, ue_id, ap_id):
        """
        Method to simulate handoff of UE to a AP identified by its id
        """

        self.logger.debug(
            "Received request for a Handoff of UE: {} to AP: {}".format(
                ue_id, ap_id
            ))
        ue = self.validate_ue(ue_id)
        current_ap = self._ap_dict[ue.ap]

        self.logger.debug(
            "UE info: {}".format(ue.to_dict)
        )
        self.logger.debug(
            "UE's current_ap info: {}".format(current_ap.to_dict)
        )
        if ue.ap == ap_id:
            self.logger.debug(
                "Handoff: requested ap is same as current ap, aborting!")
            handoff_result = OrderedDict(
                DONE=False,
                UE=None,
                OLD_AP=None,
                NEW_AP=None
            )
            return handoff_result

        return self.handoff_to_ap(ue, current_ap, ap_id)

    def reset_network(self):
        """
        Re-initializes the network by instantiating APs and UEs again
        """
        self._ap_dict = None
        self._ue_dict = None

        # Place APs
        self._place_aps()

        # Instantiate UEs
        self._instantiate_ues()

    @property
    def ap_list(self):
        """
        Returns a list of APs.
        Converting ap_dict to ap_list to match what prod network api might
        send.
        """
        return [value.to_dict for value in self._ap_dict.values()]

    def ap_info(self, ap_id):
        """
        Method to return details about an AP
        """
        ap = self.validate_ap(ap_id)
        return ap.to_dict

    @property
    def ue_list(self):
        """
        Returns a list of UEs
        Converting ue_dict to ue_list to match what prod network api might
        send.
        """
        return [value.to_dict for value in self._ue_dict.values()]

    def ue_info(self, ue_id):
        """
        Method to return details about an UE
        """
        ue = self.validate_ue(ue_id)
        return ue.to_dict

    def ue_throughput(self, ue_id):
        """
        Method to retrieve UE's throughput
        """
        ue = self.validate_ue(ue_id)
        return ue.throughput

    def ue_sla(self, ue_id):
        """
        Method to retrieve UE's sla
        """
        ue = self.validate_ue(ue_id)
        return ue.sla

    def ue_signal_power(self, ue_id):
        """
        Method to retrieve UE's signal_power
        """
        ue = self.validate_ue(ue_id)
        return ue.signal_power

    def ue_neighboring_aps(self, ue_id):
        """
        Method to reteive UE's neighboring aps
        """
        ue = self.validate_ue(ue_id)
        current_ap = self.validate_ap(ue.ap)
        return self.fetch_neighboring_aps(ue, current_ap)

    def ap_sla(self, ap_id):
        """
        Method to retrieve AP's sla
        """
        ap = self.validate_ap(ap_id)
        return ap.ues_meeting_sla


class DynamicNetwork:
    """
    Simulation of a cellular network where APs are dynamically positioned in
    every cell of the grid.
    """
    def __init__(self, num_ues, num_aps, scale):
        self.num_ues = num_ues
        self.num_aps = num_aps
        self.scale = scale
