# -*- coding: utf-8 -*-

from nixops.backends import MachineDefinition, MachineState
import nixops.util
import sys

class LinodeDefinition(MachineDefinition):
    """Definition of a linode machine."""

    @classmethod
    def get_type(cls):
        return "linode"

    def __init__(self, xml):
        MachineDefinition.__init__(self, xml)
        self._target_host = xml.find("attrs/attr[@name='targetHost']/string").get("value")


class LinodeState(MachineState):
    """State of a linode machine."""

    @classmethod
    def get_type(cls):
        return "linode"

    target_host = nixops.util.attr_property("targetHost", None)

    def __init__(self, depl, name, id):
        MachineState.__init__(self, depl, name, id)

    def create(self, defn, check, allow_reboot, allow_recreate):
        assert isinstance(defn, NoneDefinition)
        self.set_common_state(defn)
        self.target_host = defn._target_host

        # Step 1: Create VM
        # Step 2: Create fenix configuration & proper disks
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
