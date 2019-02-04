
# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from openstacksyncstep import OpenStackSyncStep
from xossynchronizer.modelaccessor import *
from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))

class SyncPorts(OpenStackSyncStep):
    requested_interval = 0 # 3600
    provides=[Port]
    observes=Port

    #     The way it works is to enumerate the all of the ports that neutron
    #     has, and then work backward from each port's network-id to determine
    #     which Network is associated from the port.

    def call(self, failed=[], deletion=False):
        if deletion:
            self.delete_ports()
        else:
            self.sync_ports()

    def get_driver(self, port):
        # We need to use a client driver that specifies the tenant
        # of the destination instance. Nova-compute will not connect
        # ports to instances if the port's tenant does not match
        # the instance's tenant.

        # A bunch of stuff to compensate for OpenStackDriver.client_driver()
        # not being in working condition.
        from synchronizers.openstack.client import OpenStackClient
        from synchronizers.openstack.driver import OpenStackDriver
        controller = port.instance.node.site_deployment.controller
        slice = port.instance.slice
        caller = port.network.owner.creator
        auth = {'username': caller.email,
                'password': caller.remote_password,
                'tenant': slice.name}
        client = OpenStackClient(controller=controller, **auth)
        driver = OpenStackDriver(client=client)

        return driver

    def sync_ports(self):
        log.info("sync'ing Ports [delete=False]")

        ports = Port.objects.all()
        ports_by_id = {}
        ports_by_neutron_port = {}
        for port in ports:
            ports_by_id[port.id] = port
            ports_by_neutron_port[port.port_id] = port

        networks = Network.objects.all()
        networks_by_id = {}
        for network in networks:
            for nd in network.controllernetworks.all():
                networks_by_id[nd.net_id] = network

        instances = Instance.objects.all()
        instances_by_instance_uuid = {}
        for instance in instances:
            instances_by_instance_uuid[instance.instance_uuid] = instance

        # Get all ports in all controllers

        ports_by_id = {}
        templates_by_id = {}
        for controller in Controller.objects.all():
            if not controller.admin_tenant:
                log.info("controller %s has no admin_tenant" % controller)
                continue
            try:
                driver = self.driver.admin_driver(controller = controller)
                ports = driver.shell.neutron.list_ports()["ports"]
            except:
                log.exception("failed to get ports from controller %s" % controller)
                continue

            for port in ports:
                ports_by_id[port["id"]] = port

            # public-nat and public-dedicated networks don't have a net-id anywhere
            # in the data model, so build up a list of which ids map to which network
            # templates.
            try:
                neutron_networks = driver.shell.neutron.list_networks()["networks"]
            except:
                print "failed to get networks from controller %s" % controller
                continue
            for network in neutron_networks:
                for template in NetworkTemplate.objects.all():
                    if template.shared_network_name == network["name"]:
                        templates_by_id[network["id"]] = template

        for port in ports_by_id.values():
            if port["id"] in ports_by_neutron_port:
                # we already have it
                #logger.info("already accounted for port %s" % port["id"])
                continue

            if port["device_owner"] != "compute:nova":
                # we only want the ports that connect to instances
                #logger.info("port %s is not a compute port, it is a %s" % (port["id"], port["device_owner"]))
                continue

            instance = instances_by_instance_uuid.get(port['device_id'], None)
            if not instance:
                log.info("no instance for port %s device_id %s" % (port["id"], port['device_id']))
                continue

            network = networks_by_id.get(port['network_id'], None)
            if not network:
                # maybe it's public-nat or public-dedicated. Search the templates for
                # the id, then see if the instance's slice has some network that uses
                # that template
                template = templates_by_id.get(port['network_id'], None)
                if template and instance.slice:
                    for candidate_network in instance.slice.networks.all():
                         if candidate_network.template == template:
                             network=candidate_network
            if not network:
                log.info("no network for port %s network %s" % (port["id"], port["network_id"]))

                # we know it's associated with a instance, but we don't know
                # which network it is part of.

                continue

            if network.template.shared_network_name:
                # If it's a shared network template, then more than one network
                # object maps to the neutron network. We have to do a whole bunch
                # of extra work to find the right one.
                networks = network.template.network_set.all()
                network = None
                for candidate_network in networks:
                    if (candidate_network.owner == instance.slice):
                        log.info("found network %s" % candidate_network)
                        network = candidate_network

                if not network:
                    log.info("failed to find the correct network for a shared template for port %s network %s" % (port["id"], port["network_id"]))
                    continue

            if not port["fixed_ips"]:
                log.info("port %s has no fixed_ips" % port["id"])
                continue

            ip=port["fixed_ips"][0]["ip_address"]
            mac=port["mac_address"]
            log.info("creating Port (%s, %s, %s, %s)" % (str(network), str(instance), ip, str(port["id"])))

            ns = Port(network=network,
                               instance=instance,
                               ip=ip,
                               mac=mac,
                               port_id=port["id"])

            try:
                ns.save()
            except:
                log.exception("failed to save port %s" % str(ns))
                continue

        # For ports that were created by the user, find that ones
        # that don't have neutron ports, and create them. These are ports
        # with a null port_id and a non-null instance_id.
        ports = Port.objects.all()
        ports = [x for x in ports if ((not x.port_id) and (x.instance_id))]
        for port in ports:
            log.info("XXX working on port %s" % port)
            controller = port.instance.node.site_deployment.controller
            slice = port.instance.slice

            if controller:
                cn=[x for x in port.network.controllernetworks.all() if x.controller_id==controller.id]
                if not cn:
                    log.exception("no controllernetwork for %s" % port)
                    continue
                cn=cn[0]
                if cn.lazy_blocked:
                    cn.lazy_blocked=False
                    cn.save()
                    log.info("deferring port %s because controllerNetwork was lazy-blocked" % port)
                    continue
                if not cn.net_id:
                    log.info("deferring port %s because controllerNetwork does not have a port-id yet" % port)
                    continue
                try:
                    driver = self.get_driver(port)

                    args = {"network_id": cn.net_id}
                    neutron_port_name = port.get_parameters().get("neutron_port_name", None)
                    neutron_port_ip = port.get_parameters().get("neutron_port_ip", None)
                    if neutron_port_name:
                        args["name"] = neutron_port_name
                    if neutron_port_ip:
                        args["fixed_ips"] = [{"ip_address": neutron_port_ip, "subnet_id": cn.subnet_id}]

                    neutron_port = driver.shell.neutron.create_port({"port": args})["port"]
                    port.port_id = neutron_port["id"]
                    if neutron_port["fixed_ips"]:
                        port.ip = neutron_port["fixed_ips"][0]["ip_address"]
                    port.mac = neutron_port["mac_address"]
                    port.xos_created = True
                    log.info("created neutron port %s for %s" % (port.port_id, port))
                except:
                    log.exception("failed to create neutron port for %s" % port)
                    continue
                port.save()

    def delete_ports(self):
        log.info("sync'ing Ports [delete=True]")
        ports = self.fetch_pending(deletion=True)
        for port in ports:
            self.delete_record(port)

    def delete_record(self, port):
        if port.xos_created and port.port_id:
            log.info("calling openstack to destroy port %s" % port.port_id)
            try:
                driver = self.get_driver(port)
                driver.shell.neutron.delete_port(port.port_id)
            except:
                log.exception("failed to delete port %s from neutron" % port.port_id)
                return

        log.info("Purging port %s" % port)
        port.delete(purge=True)

