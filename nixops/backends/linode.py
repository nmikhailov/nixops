# -*- coding: utf-8 -*-
from __future__ import absolute_import

from nixops.backends import MachineDefinition, MachineState
import linode
import nixops.util
import sys
from pprint import pprint

RESCUE_CONFIG_NAME = "__nixops_rescue"
# Finnix ids
RESCUE_KERNEL_ID = 61
RESCUE_DISK_ID = 25665
RESCUE_INITRD_ID = 25669

MAX_DISK_COUNT = 8

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

    machine_id = nixops.util.attr_property("machine_id", None)

    def __init__(self, depl, name, id):
        MachineState.__init__(self, depl, name, id)

    def create(self, defn, check, allow_reboot, allow_recreate):
        assert isinstance(defn, LinodeDefinition)
        self.set_common_state(defn)
        self.target_host = defn._target_host

        self.api = linode.Api(defn.api_key)

        # Step 1: Create VM
        self.linode_id = self._create_machine(defn)
        
        # Step 2: Create disks
        # TODO: proper creation
        self._create_disks()

        # Step 2: Create fenix configuration & proper disks
        rescue_config_id = self._create_rescue_configuration(defn)

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

    def _create_machine(self, defn):
        # return 671626
        # Check ids
        datacenter_id = _find_elem('ABBR', defn.datacenter, self.api.avail.datacenters(),
            "Datacenter '{}'' unavailable. Possible options: {}")['DATACENTERID']
        plan_id = _find_elem('LABEL', defn.plan, self.api.avail.linodeplans(),
            "Linode plan '{}' unavailable. Possible options: {}.")['PLANID']

        self.log("Creating linode {} ({}) in datacenter {}({})"
            .format(defn.datacenter, datacenter_id, defn.plan, defn.plan_id))

        linode_id = self.api.linode.create(DatacenterId=datacenter_id, PlanId=plan_id, 
            PaymentTerm=defn.payment_term)['LINODEID']

        self.log("Created linode id {}".format(linode_id))

        return linode_id

    def _create_rescue_configuration(self, defn):
        old_configs = filter(lambda x: x["Label"] == RESCUE_CONFIG_NAME, 
            self.api.linode.config.list(LinodeID=self.linode_id))

        # Delete old configs
        for conf in old_configs:
            self.api.linode.config.delete(LinodeID=self.linode_id, ConfigID=conf['ConfigID'])
        
        self.log("Creating new rescue config")
        descr = {
            "LinodeID": self.linode_id,
            "KernelID": RESCUE_KERNEL_ID,
            "Label": RESCUE_CONFIG_NAME,
            "Comments": "NixOps autogenerated config. Do not edit",
            "RAMLimit": 0, # TODO
            "DiskList": self._make_disk_list(True),
            "RootDeviceNum": 1,

        }
        self.api.linode.config.create(**descr)
    
    def _create_disks(self):
        self.disks = lambda: None
        self.disks.main = {'DISKID':""}
        self.disks.swap = {'DISKID':""}
        #self.disks.swap = self.api.linode.disk.create(LinodeID=self.linode_id, Label="swap",Type="swap",Size=4096)
        #self.disks.main = self.api.linode.disk.create(LinodeID=self.linode_id, Label="main",Type="ext4",Size=1024*16)

    # Utility stuff

    def _make_disk_list(self, rescue):
        disks = [RESCUE_DISK_ID] if rescue else []
        disks += [self.disks.swap['DISKID'], self.disks.main['DISKID']]
        disks += [""] * (MAX_DISK_COUNT - len(disks))
        disks += [RESCUE_INITRD_ID] if rescue else []

        return ','.join(map(str, disks))


    def _find_elem(prop, value, lst, error_msg):
        try:
            (ret,) = filter(lambda x: x[prop] == vals, lst)
            return ret
        except ValueError:
            raise Exception(error_msg.format(value, map(lambda x: x[prop], lst)))

