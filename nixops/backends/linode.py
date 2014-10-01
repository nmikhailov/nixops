# -*- coding: utf-8 -*-
from __future__ import absolute_import

from nixops.backends import MachineDefinition, MachineState
import linode
import nixops.util
import sys
from pprint import pprint

class LinodeDefinition(MachineDefinition):
    """Definition of a linode machine."""

    @classmethod
    def get_type(cls):
        return "linode"

    def __init__(self, xml):
        MachineDefinition.__init__(self, xml)
        self._target_host = xml.find("attrs/attr[@name='targetHost']/string").get("value")

        x = xml.find("attrs/attr[@name='linode']/attrs")
        assert x is not None
        self.api_key = x.find("attr[@name='apiKey']/string").get("value")
        self.plan = x.find("attr[@name='plan']/string").get("value")
        self.datacenter = x.find("attr[@name='datacenter']/string").get("value")


class LinodeState(MachineState):
    """State of a linode machine."""

    @classmethod
    def get_type(cls):
        return "linode"

    target_host = nixops.util.attr_property("targetHost", None)

    def __init__(self, depl, name, id):
        MachineState.__init__(self, depl, name, id)

    def create(self, defn, check, allow_reboot, allow_recreate):
        assert isinstance(defn, LinodeDefinition)
        self.set_common_state(defn)
        self.target_host = defn._target_host

        api = linode.Api(defn.api_key)
        self.log("APIKEY {}".format(pprint(defn)))

        # Step 1: Create VM
        machine_id = self._create_machine(api, defn)
        
        # Step 2: Create fenix configuration & proper disks
        # rescue_config_id = _create_rescue_configuration(api, defn)

        # Step 3: Boot rescue configuration and connect via lish
        # Step 4: Install base image & disconnect
        # Step 5: Create normal configuration & boot it

    def get_ssh_name(self):
        assert self.target_host
        return self.target_host

    def _check(self, res):
        res.exists = True # can't really check
        res.is_up = nixops.util.ping_tcp_port(self.target_host, self.ssh_port)
        if res.is_up:
            MachineState._check(self, res)

    def destroy(self, wipe=False):
        # No-op; just forget about the machine.
        return True

    # Linode specific stuff

    def _create_machine(self, api, defn):
        # Check ids
        datacenter_id = _find_elem('ABBR', defn.datacenter, api.avail.datacenters(),
            "Datacenter '{}'' unavailable. Possible options: {}")['DATACENTERID']
        plan_id = _find_elem('LABEL', defn.plan, api.avail.linodeplans(),
            "Linode plan '{}' unavailable. Possible options: {}.")['PLANID']

        self.log("Creating linode {} ({}) in datacenter {}({})"
            .format(defn.datacenter, datacenter_id, defn.plan, defn.plan_id))

        machine_id = api.linode.create(DatacenterId=datacenter_id, PlanId=plan_id, 
            PaymentTerm=defn.payment_term)['LINODEID']

        self.log("Created linode id {}".format(machine_id))

        return machine_id

    def _create_rescue_configuration(self, api, defn):
        pass

    # Utility stuff

    def _find_elem(prop, value, lst, error_msg):
        try
            (ret,) = filter(lambda x: x[prop] == vals, lst)
            return ret
        except ValueError:
            raise Exception(error_msg.format(value, map(lambda x: x[prop], lst)))


