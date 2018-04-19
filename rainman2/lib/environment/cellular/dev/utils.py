#! /usr/bin/env python3
# -*- coding: utf-8 -*-

""" Utility for storing common lib and data structures """

import math
from collections import namedtuple
from itertools import product
import numpy as np
import simplejson as json

__author__ = 'Ari Saha (arisaha@icloud.com)'
__date__ = 'Wednesday, March 14th 2018, 2:31:37 pm'

APPS_DICT = {"web": 0.25, "video": 2.0, "voice": 0.1, "others": 0.05}

NEIGHBORING_APS = namedtuple('NEIGHBORING_APS', ['within_grid', 'rest'])


class AP:
    def __init__(self,
                 ap_id=0,
                 location=None,
                 n_ues=None,
                 ues_meeting_sla=None,
                 max_connections=50,
                 uplink_bandwidth=25.0,
                 channel_bandwidth=10.0,
                 ):

        # Id of the AP
        self.ap_id = ap_id
        # location of the AP
        self.location = location
        # number of UEs currently connected to the AP
        # Dictionary with App_type as keys and list of ue_id as values
        self.n_ues = self._initialize_n_ues()
        # number of UEs meeting their SLAs
        self.ues_meeting_sla = self._initialize_ues_slas()
        # maximum connections AP can have
        self.max_connections = max_connections
        # uplink bandwidth of the AP
        self.uplink_bandwidth = uplink_bandwidth
        # channel bandwidth of the AP
        self.channel_bandwidth = channel_bandwidth

    def _initialize_n_ues(self):
        """
        Helper to setup an empty dictionary with type of Apps as keys.
        {"web": set(), "voice": set(), "video": set(), "others": set()}
        """
        return {key: set() for key in APPS_DICT.keys()}

    def _initialize_ues_slas(self):
        """
        Helper to setup an empty dictionary with type of Apps as keys.
        {"web": 0, "voice": 0, "video": 0, "others": 0}
        """
        return {key: 0 for key in APPS_DICT.keys()}

    @property
    def to_dict(self):
        """
        Formats class AP to a dict
        """
        return self.__dict__

    def __repr__(self):
        """
        Helper to represent AP in the form of:
        "AP {'ap_id: 4, 'location': (x, y), 'n_ues': 154}
        """
        return "<AP {}>".format(self.to_dict)


class UE:
    def __init__(self,
                 ue_id=0,
                 ap=0,
                 location=None,
                 app=None,
                 required_bandwidth=0,
                 neighboring_aps=None,
                 distance=0,
                 throughput=0,
                 sla=1,
                 signal_power=-100,
                 ):

        # Id of the UE
        self.ue_id = ue_id
        # The access Point (AP) UE is conncted to. AP is identified by its
        # location
        self.ap = ap
        # Location of the UE (used for calculating sig_power)
        self.location = location
        # Type of application (Web/Video) the UE is running currently
        self.app = app
        # Required bandwidth for the UE based on the APP
        self.required_bandwidth = required_bandwidth
        # List of neighboring APs
        self.neighboring_aps = neighboring_aps
        # Distance between AP and UE
        self.distance = distance
        # UE's Throughput
        self.throughput = throughput
        # SLA. Default is meets SLA (1)
        self.sla = sla
        # Signal power between UE and AP
        self.signal_power = signal_power

    @property
    def to_dict(self):
        """
        Formats class UE to a dict
        """
        return self.__dict__

    @property
    def to_json(self):
        """
        Formats class UE to a json serializable format
        """
        return json.dumps(
            self, default=lambda o: o.to_dict, sort_keys=True, indent=4)

    def __repr__(self):
        """
        Helper to represent UE in the form of:
        "<UE {'ud_id': 1, 'location': (x, y), 'ap': 4}>
        """
        return "<UE {}>".format(self.to_dict)


def get_ue_app():
    """
    Function to randomly generate apps for UE and returns app_type and required
    bandwidth
    """
    prob = np.around(np.random.rand(), decimals=3)

    # 70% of UEs are running "web" application
    if prob < 0.7:
        return "web"
    # rest are running "video"
    return "video"


def get_random_location(_min, _max):
    """
    Function to generate random (x, y) between min and max
    """
    xloc = np.random.randint(_min, _max)
    yloc = np.random.randint(_min, _max)
    return (xloc, yloc)


def get_center_grid(scale, aps_per_axis):
    """
    Function to generate random x and y within 1.5*scale of radius
    """
    mid_point = sum(aps_per_axis) / len(aps_per_axis)
    _min = mid_point - 1.5*scale
    _max = mid_point + 1.5*scale
    return get_random_location(_min, _max)


def get_ue_location(app_type, scale, aps_per_axis):
    """
    Function to generate location for UE based on the app.

    UEs running video based apps will be placed in the center for the grid.
    This is designed so as to simulate 'high traffic load' in certain parts
    of the network which will force a handoff to neighboring APs.

    Args:
        app_type: (string):
        Type of application UE is running.

        scale: (float):
        Scale of each grid. e.g. 100.0 => Each grid is of 100.0 units

        aps_per_axis: (list):
        List of points in X-axis where APs are located.

    Returns:
        location: (tuple):
        Tuple of X and Y in the grid.
    """
    if app_type == "video":
        # place in within the center of the grid
        return get_center_grid(scale, aps_per_axis)
    # place it anywhere on the grid
    return get_random_location(0, (1 + (2 * len(aps_per_axis)) * scale))


def get_interval(value, num_list):
    """
    Helper to find the interval within which the value lies
    """
    if value < num_list[0]:
        return (num_list[0], num_list[0])
    if value > num_list[-1]:
        return (num_list[-1], num_list[-1])
    if value == num_list[0]:
        return (num_list[0], num_list[1])
    if value == num_list[-1]:
        return (num_list[-2], num_list[-1])

    for index, num in enumerate(num_list):
        if value <= num:
            return (num_list[index - 1], num_list[index])


def get_aps_in_grid(ue_location, aps_per_axis):
    """
    Function to retrieve a list of neighboring APs in the grid of the UE.
    """
    _min, _max = ue_location[0], ue_location[1]
    _min_interval = get_interval(_min, aps_per_axis)
    _max_interval = get_interval(_max, aps_per_axis)
    return list(set(product(_min_interval, _max_interval)))


def valid_ap(ap, aps_per_axis):
    """
    Helper to validate ap
    """
    ap_x, ap_y = ap
    return (ap_x in aps_per_axis and ap_y in aps_per_axis)


def get_valid_neighbors(ap, aps_per_axis):
    """
    Helper to return only valid neighbors
    """

    scale = aps_per_axis[1] - aps_per_axis[0]
    _aps = [
        (ap[0] - scale, ap[1]),
        (ap[0] + scale, ap[1]),
        (ap[0], ap[1] - scale),
        (ap[0], ap[1] + scale)]

    valid_aps = []

    for ap in _aps:
        if valid_ap(ap, aps_per_axis):
            valid_aps.append(ap)
    return valid_aps


def get_extended_neighboring_aps(closest_aps, aps_per_axis, radius):
    """
    Function to search for All APs within a given radius from the closest APs.
    """
    if not radius:
        return closest_aps

    all_aps = set(closest_aps)
    for ap in closest_aps:
        all_aps.update(get_valid_neighbors(ap, aps_per_axis))
    return get_extended_neighboring_aps(
        list(all_aps), aps_per_axis, radius - 1)


def get_neighboring_aps(ue_location, aps_per_axis, radius=1):
    """
    Function to retrieve a list of neighboring APs with a given radius
    around the UE.
    """
    neighboring_aps_in_grid = get_aps_in_grid(ue_location, aps_per_axis)
    rest = set()
    if radius > 1:
        rest.update(get_extended_neighboring_aps(
            neighboring_aps_in_grid, aps_per_axis, radius - 1))
        rest -= set(neighboring_aps_in_grid)
    return NEIGHBORING_APS(
        within_grid=neighboring_aps_in_grid, rest=list(rest))


def get_ue_ap_distance(ap_location, ue_location):
    """
    Function to calculate distance between UE and AP
    """
    ap_location = np.array(ap_location)
    ue_location = np.array(ue_location)
    return np.around(
        np.linalg.norm(ap_location - ue_location), decimals=3)


def get_closest_ap_location(neighboring_aps, ue_location):
    """
    Function that returns closest AP's location from the neighboring ap list
    """
    closest_ap = neighboring_aps[0]
    min_distance = get_ue_ap_distance(closest_ap, ue_location)
    for ap_location in neighboring_aps[1:]:
        distance = get_ue_ap_distance(ap_location, ue_location)
        if distance < min_distance:
            min_distance = distance
            closest_ap = ap_location
    return closest_ap


def get_ue_ap(ue_location, aps_per_axis, radius):
    """
    Function to retrive the closest AP to the UE
    """
    neighboring_aps = get_neighboring_aps(ue_location, aps_per_axis, radius)

    closest_ap_location = get_closest_ap_location(
        neighboring_aps.within_grid, ue_location)
    all_neighboring_aps = neighboring_aps.within_grid + neighboring_aps.rest
    return (closest_ap_location, all_neighboring_aps)


def calculate_distance_factor(ue_ap_distance, scale):
    """
    Function to calculate distance factor
    """
    return np.around(
        (math.exp(-(ue_ap_distance)/(2 * scale))), decimals=3)


def calculate_radio_bandwidth(distance_factor, ap_channel_bandwidth):
    """
    Function to calculate radio bandwidth of the AP
    """
    # calculate radio bandwidth
    return np.around((distance_factor * ap_channel_bandwidth), decimals=3)


def calculate_network_bandwidth(n_ues_on_ap, ap_uplink_bandwidth):
    """
    Function to calculate network bandwidth
    """
    # Ap factor
    ap_factor = 1
    # to avoid ZeroDivisionError
    if n_ues_on_ap:
        ap_factor /= n_ues_on_ap

    # network bandwidth
    return np.around((
        ap_factor * ap_uplink_bandwidth), decimals=3)


def get_ue_throughput(scale,
                      ue_ap_distance,
                      n_ues_on_ap,
                      ap_uplink_bandwidth,
                      ap_channel_bandwidth,
                      app_required_bandwidth):
    """
    Function to calculate throughput of UE
    """
    distance_factor = calculate_distance_factor(ue_ap_distance, scale)

    radio_bandwidth = calculate_radio_bandwidth(
        distance_factor, ap_channel_bandwidth)

    network_bandwidth = calculate_network_bandwidth(
        n_ues_on_ap, ap_uplink_bandwidth)

    return min(radio_bandwidth, network_bandwidth, app_required_bandwidth)


def get_ue_sig_power(ue_ap_distance):
    """
    Function to calculate signal power between the UE and AP
    """
    # To avoid ZeroDivisionError
    if ue_ap_distance:
        distance = (10 * math.log10(1 / math.pow(ue_ap_distance, 2)))
        # discretizing the distance
        distance /= 10
        return round(distance)


def get_ue_sla(ue_throughput, ue_required_bandwidth):
    """
    Function to calculate UE's SLA
    """
    return int(ue_throughput >= ue_required_bandwidth)


def main():
    """
    Test locally!
    """
    ap_list = list(range(100, 900, 200))
    print(ap_list)
    assert get_interval(345, ap_list) == (300, 500)
    ue_location = (345, 567)
    neighboring_aps = get_aps_in_grid(ue_location, ap_list)
    print(neighboring_aps)
    print(get_ue_ap_distance(neighboring_aps[0], ue_location))
    closest_ap = get_closest_ap_location(
        neighboring_aps, ue_location)
    print(closest_ap)

    (closest_ap, neighboring_aps) = get_ue_ap(ue_location, ap_list, 1)
    print(neighboring_aps)
    print(closest_ap)

    print("valid neighbors")
    print(get_valid_neighbors((500, 700), ap_list))

    print("Testing extended_neighboring_aps")
    print(get_extended_neighboring_aps(
        [(500, 500), (300, 700), (300, 500), (500, 700)], ap_list, 2))

    print("radius: 1")
    print(get_neighboring_aps(ue_location, ap_list, radius=1))
    print("radius: 2")
    print(get_neighboring_aps(ue_location, ap_list, radius=2))
    print("radius: 3")
    print(get_neighboring_aps(ue_location, ap_list, radius=3))
    print("radius: 4")
    print(get_neighboring_aps(ue_location, ap_list, radius=4))
    print("radius: 5")
    print(get_neighboring_aps(ue_location, ap_list, radius=5))
    print("radius: 6")
    print(get_neighboring_aps(ue_location, ap_list, radius=6))

    print(get_center_grid(100, ap_list))

    ue_ap_distance = 441.367
    assert calculate_distance_factor(ue_ap_distance, 100) == 0.11
    assert calculate_radio_bandwidth(0.11, 10.0) == 1.1
    assert calculate_network_bandwidth(58, 50.0) == 0.862
    assert get_ue_throughput(100, 441.367, 58, 50.0, 10.0, 0.25) == 0.25

    print(get_ue_sig_power(ue_ap_distance))
    return True


if __name__ == '__main__':
    main()
