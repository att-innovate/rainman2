#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Implementation of Cellular network environment model
"""

import logging
from collections import namedtuple, OrderedDict, defaultdict
import simplejson as json
from rainman2.lib.environment import environment_template
from rainman2.lib.environment.cellular.dev import client as dev_client
from rainman2.lib.environment.cellular.prod import client as prod_client
from rainman2.utils import exceptions


__author__ = 'Ari Saha (arisaha@icloud.com)'
__date__ = 'Tuesday, February 20th 2018, 2:06:00 pm'


CLIENTS = {
   'Dev': dev_client.CellularDevClient,
   'Prod': prod_client.CellularProdClient,
}

APPS_ID = {
    "web": 1,
    "video": 2,
    }

ACTIONS = {
    0: "STAY",
    1: "HANDOFF",
}

NETWORK_STATE_ATTRIBUTES = OrderedDict(
    ue_sla=0,
    app=None,
    sig_power=0,
    video_ues=0,
    web_ues=0,
    avg_video_sla=0.0,
    avg_web_sla=0.0,
)

NETWORK_STATE = namedtuple(
    'NETWORK_STATE',
    NETWORK_STATE_ATTRIBUTES.keys())

UE_AP_STATE_ATTRIBUTES = OrderedDict(
    app=None,
    sig_power=0,
    video_ues=0,
    web_ues=0,
    avg_video_sla=0.0,
    avg_web_sla=0.0,
)

UE_AP_STATE = namedtuple(
    'UE_AP_STATE',
    UE_AP_STATE_ATTRIBUTES.keys())


class AP:
    def __init__(self,
                 ap_id=0,
                 location=None,
                 n_ues=None,
                 ues_meeting_sla=None,
                 ):

        # Id of the AP
        self.ap_id = ap_id
        # location of the AP
        self.location = location
        # number of UEs currently connected to the AP
        # Dictionary with App_type as keys and list of ue_id as values
        self.n_ues = n_ues
        # number of UEs meeting their SLAs
        self.ues_meeting_sla = ues_meeting_sla

    @property
    def to_dict(self):
        """
        Formats class AP to a dict
        """
        return self.__dict__

    @property
    def to_json(self):
        """
        Formats class AP to a json serializable format
        """
        return json.dumps(
            self, default=lambda o: o.to_dict, sort_keys=True, indent=4)

    def __repr__(self):
        """
        Helper to represent AP in the form of:
        "AP {'ap_id: 4, 'location': (x, y)}
        """
        return "<AP {}>".format(self.to_dict)


class UE:
    def __init__(self,
                 ue_id=0,
                 ap=None,
                 location=None,
                 neighboring_aps=None,
                 signal_power=None,
                 app=None,
                 sla=None,
                 ):

        # Id of the UE
        self.ue_id = ue_id
        # Access Point UE is conncted to
        self.ap = ap
        # Location of the UE (used for calculating sig_power)
        self.location = location
        # Neighboring APs
        self.neighboring_aps = neighboring_aps
        # Signal power of UE with respect to current AP
        self.signal_power = signal_power
        # application UE is running
        self.app = app
        # Current SLA
        self.sla = sla

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
        "<UE {'ud_id': 1, 'ap': <AP obj>, location': (x, y), 'app': 4,}>
        """
        return "<UE {}>".format(self.to_dict)


def initialize_client(env_config):
    """
    Method to help initialize respective clients
    """
    logger = logging.getLogger(__name__)

    env_type = env_config['TYPE']
    if env_type not in CLIENTS:
        error = "Client for: {} is not implemented!".format(env_type)
        logger.debug(error)
        raise exceptions.ClientNotImplemented(error)
    logger.info(
        "Instantiating Cellular client: {}".format(env_type))
    return CLIENTS[env_type](env_config)


class CellularNetworkEnv(environment_template.Base):
    """
    Implements cellular network environment
    """
    def __init__(self, env_config, client):
        """
        Initializes cellular environment instance
        """
        self.env_config = env_config
        self.logger = logging.getLogger(self.__class__.__name__)

        self._client = client

        # stores information about APs as a dict
        self._ap_dict = OrderedDict()
        # useful to lookup ap id based on ap location
        self._reverse_ap_lookup = {}
        # Stores information about UEs as a dict
        self._ue_dict = OrderedDict()
        self.ue_sla_stats = None

    def execute_client_call(self, call, *args):
        """
        Helper to check if client call is successful
        """
        client_call = getattr(self._client, call)
        try:
            response = client_call(*args)
        except exceptions.ExternalServerError as error:
            self.logger.exceptions(
                "Error during executing client call: {}".format(error))
            raise
        else:
            return response

    def build_ap_dict(self, ap_list):
        """
        Method to parse ap_list and store it as a dictionary
        """
        for ap in ap_list:
            ap_id = ap['ap_id']
            if ap_id not in self._ap_dict:
                location = ap['location']
                # update reverse ap dict
                self._reverse_ap_lookup[tuple(location)] = ap_id
                n_ues = ap['n_ues']
                ues_meeting_sla = ap['ues_meeting_sla']
                self._ap_dict[ap_id] = AP(
                    ap_id=ap_id,
                    location=location,
                    n_ues=n_ues,
                    ues_meeting_sla=ues_meeting_sla,
                )

    def populate_ap_dict(self):
        """
        Method to populate AP list
        """
        self.logger.debug(
            "Fetching latest AP list from the network!"
        )
        ap_list = self.execute_client_call('get_ap_list')
        self.build_ap_dict(ap_list)

    def build_ue_dict(self, ue_list):
        """
        Method to parse ue_list and store it as a dictionary
        """
        self.ue_sla_stats = defaultdict(int)

        for ue in ue_list:
            ue_id = ue['ue_id']
            ue_sla = ue['sla']

            # Update UE SLA Stats
            if ue_sla == 1:
                self.ue_sla_stats["Meets"] += 1
            else:
                self.ue_sla_stats["Doesnot"] += 1

            # Populate UE dict is UE is new
            if ue_id not in self._ue_dict:
                ap = ue['ap']
                location = ue['location']
                ue_app = ue['app']
                ue_neighboring_aps = ue['neighboring_aps']
                neighboring_aps = ue_neighboring_aps
                ue_signal_power = ue['signal_power']
                ue_obj = UE(
                    ue_id=ue_id,
                    ap=ap,
                    location=location,
                    neighboring_aps=neighboring_aps,
                    signal_power=ue_signal_power,
                    app=APPS_ID[ue_app],
                    sla=ue_sla,
                )
                self._ue_dict[ue_id] = ue_obj

    def populate_ue_dict(self):
        """
        Method to populate UE list
        """
        self.logger.debug(
            "Fetching latest UE list from the network!"
        )
        ue_list = self.execute_client_call('get_ue_list')
        self.build_ue_dict(ue_list)

    def get_ue_sla(self, ue_id):
        """
        Method to calculate SLA for a UE
        """
        return self.execute_client_call('get_ue_sla', ue_id)

    def get_ue_signal_power(self, ue_id):
        """
        Method to get UE's signal power to its current AP from the network
        """
        self.logger.debug(
            "Requesting UE:{}'s signal_power from the network".format(ue_id))
        return self._client.get_ue_signal_power(ue_id)

    def get_avg_app_sla(self, n_app_ues, ues_meeting_sla):
        """
        Helper method to calculate avg video sla for the AP.
        """
        avg_app_sla = 0.0
        if n_app_ues and ues_meeting_sla:
            avg_app_sla = ues_meeting_sla / n_app_ues
        return round(avg_app_sla, 1)

    def get_ap_stats(self, ap_id):
        """
        Helper method to get ap stats

        Args
        ----
            ap_id: (int)
                ID of the AP

            app: (int)
                ID of the UE's application.

        Returns
        -------
            n_ues: dict
                Dictionary containing number of UEs for each application.

            avg_sla: dict
                Dictionary containing avg SLA for each application.
        """
        ap = self.validate_ap(ap_id)
        n_ues_dict = defaultdict()
        avg_sla_dict = defaultdict()

        for app in APPS_ID:
            n_ues_app = len(ap.n_ues[app])
            n_ues_dict[app] = n_ues_app
            avg_sla_dict[app] = self.get_avg_app_sla(
                n_ues_app, ap.ues_meeting_sla[app])
        return n_ues_dict, avg_sla_dict

    def get_ue_ap_state(self, ue, ap_id):
        """
        Method to calculate current ue_ap_state from UE's perspective
        """
        self.logger.debug(
            "Generating UE_AP_State for UE:{} and AP:{} pair".format(
                ue.ue_id, ap_id))

        n_ues_dict, avg_sla_dict = self.get_ap_stats(ap_id)

        ue_ap_state = UE_AP_STATE(
            app=ue.app,
            sig_power=ue.signal_power,
            video_ues=n_ues_dict["video"],
            web_ues=n_ues_dict["web"],
            avg_video_sla=avg_sla_dict["video"],
            avg_web_sla=avg_sla_dict["web"]
        )
        self.logger.debug("ue_ap_state: {}".format(ue_ap_state))
        return ue_ap_state

    def get_network_state(self, ue, ap_id):
        """
        Method to calculate current state of the network from UE's perspective
        """
        self.logger.debug(
            "Generating Network_State for UE:{} and AP:{} pair".format(
                ue.ue_id, ap_id))

        n_ues_dict, avg_sla_dict = self.get_ap_stats(ap_id)

        network_state = NETWORK_STATE(
            ue_sla=ue.sla,
            app=ue.app,
            sig_power=ue.signal_power,
            video_ues=n_ues_dict["video"],
            web_ues=n_ues_dict["web"],
            avg_video_sla=avg_sla_dict["video"],
            avg_web_sla=avg_sla_dict["web"]
        )
        self.logger.debug("network_state: {}".format(network_state))
        return network_state

    def validate_ap(self, ap_id):
        """
        Method to validate if AP with requested ap_id exists.

        Args:
            ap_id: (int):
                ID of the AP

        Returns:
            AP: (<AP object>):
                AP object from the ap_dict

        Raises:
            KeyError
        """
        try:
            ap = self.ap_dict[ap_id]
        except KeyError:
            self.logger.debug(
                "AP with ap_id: {} doesnot exists!".format(ap_id))
            raise
        else:
            return ap

    def validate_ue(self, ue_id):
        """
        Method to validate if UE with requested ue_id exists.

        Args:
            ue_id: (int):
                ID of the UE

        Returns:
            UE: (<UE object>):
                UE object from the ue_dict

        Raises:
            KeyError
        """
        try:
            ue = self.ue_dict[ue_id]
        except KeyError:
            self.logger.debug(
                "UE with ue_id: {} doesnot exists!".format(ue_id))
            raise
        else:
            return ue

    def get_updated_ap(self, ap_info):
        """
        Method to update AP's stats
        """
        ap = self.validate_ap(ap_info['ap_id'])
        ap.location = ap_info['location']
        ap.n_ues = ap_info['n_ues']
        ap.ues_meeting_sla = ap_info['ues_meeting_sla']
        return ap

    def get_updated_ap_from_network(self, ap_id):
        """
        Method to update an AP with latest stats
        """
        ap = self.execute_client_call('get_ap_info', ap_id)
        return self.get_updated_ap(ap)

    def get_updated_ue(self, ue_info):
        """
        Method to update UE's stats

        Args
        ----
            ue_info: (dict)
                Contains UE info from the network

        Returns
        -------
            ue: (UE object)
                Instance of updated UE
        """
        ue = self.validate_ue(ue_info['ue_id'])
        ue.ap = ue_info['ap']
        ue.location = ue_info['location']
        ue.neighboring_aps = ue_info['neighboring_aps']
        ue.sla = ue_info['sla']
        return ue

    def get_updated_ue_from_network(self, ue_id):
        """
        Method to update an UE with latest stats
        """
        ue_info = self.execute_client_call('get_ue_info', ue_id)
        return self.get_updated_ue(ue_info)

    def perform_handoff(self, ue_id, ap_id, old_state):
        """
        Method to perform a handoff and re-calculate UE-AP state.

        In this implementation, we are assuming network is providing us with
        updated UE, update OLD_AP stats and update NEW_AP stats.
        This is a hack to minimize number of REST calls to simulated network.
        Ideally if handoff is successful, we should make individual calls
        to fetch latest UE, OLD_AP and NEW_AP stats.
        """
        self.logger.debug(
            "Requesting network to handoff UE: {} to new AP: {}".format(
                ue_id, ap_id
            )
        )

        handoff_result = self.execute_client_call(
            'perform_handoff', ue_id, ap_id)

        if handoff_result['DONE']:
            self.logger.debug("Handoff was successful!")
            self.logger.debug("Updating UE's stats based on new AP")

            # update ue's state after the handoff
            ue = self.get_updated_ue(handoff_result['UE'])

            # update old AP's detail
            old_ap = self.get_updated_ap(handoff_result['OLD_AP'])

            # update new AP's detail
            new_ap = self.get_updated_ap(handoff_result['NEW_AP'])

            self.logger.debug(
                "Updated UE details after handoff: {}".format(
                    ue.to_dict))
            self.logger.debug(
                "Updated old_ap details after handoff: {}".format(
                    old_ap.to_dict))
            self.logger.debug(
                "Updated new_ap details after handoff: {}".format(
                    new_ap.to_dict))

            # return latest state based on ue and new ap
            return self.get_network_state(ue, ap_id)

        # else return old_state
        self.logger.debug("Handoff failed! Returning old_state")
        return old_state

    def reward_based_on_ap_state(self, action, old_state, new_state):
        """
        Method to update reward based on new state and old state
        """
        self.logger.debug(
            "Calculating reward based on old AP's and new AP's state:")

        reward = 0

        # Action was "Handoff"
        if action == 1:
            # based on video SLA
            if (old_state.avg_video_sla != 1.0 and
                    old_state.avg_video_sla == new_state.avg_video_sla):
                reward -= 1
            elif (old_state.avg_video_sla == 1.0 and
                    old_state.avg_video_sla == new_state.avg_video_sla):
                reward -= 0.5
            elif old_state.avg_video_sla < new_state.avg_video_sla:
                reward += 1
            elif old_state.avg_video_sla > new_state.avg_video_sla:
                reward -= 1

            # based on web SLA
            if (old_state.avg_web_sla != 1.0 and
                    old_state.avg_web_sla == new_state.avg_web_sla):
                reward -= 0.5
            elif (old_state.avg_web_sla == 1.0 and
                    old_state.avg_web_sla == new_state.avg_web_sla):
                reward -= 0.25
            elif old_state.avg_web_sla < new_state.avg_web_sla:
                reward += 0.5
            elif old_state.avg_web_sla > new_state.avg_web_sla:
                reward -= 0.5

        # Action was "Stay"
        else:
            # If AP is meeting its video_sla, then reward this action
            if old_state.avg_video_sla == 1.0:
                reward += 1
            # If AP is meeting its web_sla, then reward this action
            if old_state.avg_web_sla == 1.0:
                reward += 0.5

        self.logger.debug("AP based reward: {}".format(reward))
        return reward

    def reward_based_on_ue_state(self, action, old_sla, new_sla):
        """
        Method to update reward based on UE's old SLA and new SLA
        """
        self.logger.debug("Calculating reward based on UE SLA")
        self.logger.debug("UE's old_sla: {}".format(old_sla))
        self.logger.debug("UE's new_sla: {}".format(new_sla))

        # Action was "Handoff"
        if action == 1:
            if not old_sla and not new_sla:
                reward = -2
            elif not old_sla and new_sla:
                reward = 3
            elif old_sla and not new_sla:
                reward = -4
            else:
                reward = -1

        # Action was "Stay"
        else:
            if not old_sla and not new_sla:
                reward = -1
            elif old_sla and new_sla:
                reward = 1

        self.logger.debug("UE based reward: {}".format(reward))
        return reward

    def get_reward(self, action, old_state, new_state, ue, ue_old_sla):
        """
        Implements reward function.
        Calculate reward based on current state, current action
        and next state
        """
        self.logger.debug("Calculating reward!")

        ue_new_sla = ue.sla

        reward = 0

        # calculate UE based reward
        reward += self.reward_based_on_ue_state(
            action, ue_old_sla, ue_new_sla)

        # calculate AP based reward
        reward += self.reward_based_on_ap_state(
            action, old_state, new_state)
        self.logger.debug("Reward based on action: {} is {}".format(
            ACTIONS[action], reward
        ))
        return reward

    @property
    def ap_dict(self):
        """
        Retrive list of all the APs and store them as dictionary
        """
        if not self._ap_dict:
            self.populate_ap_dict()
        return self._ap_dict

    @property
    def ue_dict(self):
        """
        Retrive list of all the UEs and store them as dictionary
        """
        if not self._ue_dict:
            self.populate_ue_dict()
        return self._ue_dict

    """ Must be implemented """
    @property
    def _actions(self):
        """
        Defines type of actions allowed

        0: Stay
        1: Handoff
        """
        return ACTIONS

    @property
    def _state_dim(self):
        """
        Provides shape of the state defined by the environment
        """
        return len(NETWORK_STATE_ATTRIBUTES)

    def _reset(self):
        """
        Resets the environment
        """
        self.logger.debug("Resetting the environment!")

        # Fetch latest AP info
        self.populate_ap_dict()

        # Fetch latest UE info
        self.populate_ue_dict()

        if not self._ue_dict or not self._ap_dict:
            raise exceptions.ExternalServerError(
                "Failed while resetting the environment. Check connectivity!")

    def _step(self, state, action, ue, ap_id):
        """
        Simulates a time step for the UE
        """
        # Check if current ap is same as next ap suggested during action step.
        # If yes, then return current state, else perform handoff and
        # recalculate UE's state and AP's state.
        self.logger.debug("Taking next step for the UE!")
        self.logger.debug("Requested action: {}".format(ACTIONS[action]))

        ue_sla_before_handoff = ue.sla
        next_state = state
        if ue.ap != ap_id:
            next_state = self.perform_handoff(ue.ue_id, ap_id, state)
        # no change happened, return same state
        return next_state, self.get_reward(
            action, state, next_state, ue, ue_sla_before_handoff)
