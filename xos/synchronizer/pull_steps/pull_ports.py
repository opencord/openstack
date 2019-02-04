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

from xossynchronizer.pull_steps.pullstep import PullStep
from xossynchronizer.modelaccessor import Network, Port, OpenStackService, OpenStackServiceInstance

from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))

class OpenStackPortPullStep(PullStep):
    def __init__(self):
        super(OpenStackPortPullStep, self).__init__(observed_model=Port)

    def connect_openstack_admin(self, service, required_version=None):
        import openstack

        if required_version:
            if LooseVersion(openstack.version.__version__) < LooseVersion(required_version):
                raise Exception("Insufficient OpenStack library version",
                                installed_version=openstack.version__version__,
                                required_version=required_version)

        conn = openstack.connect(auth_url=service.auth_url,
                                 project_name="admin",
                                 username=service.admin_user,
                                 password=service.admin_password,
                                 user_domain_name="Default",
                                 project_domain_name="Default")
        return conn

    def pull_records(self):
        service = OpenStackService.objects.first() # TODO(smbaker): Fix, hardcoded
        conn = self.connect_openstack_admin(service)

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

        os_instances = OpenStackServiceInstance.objects.all()
        os_instances_by_handle = {}
        for instance in os_instances:
            if instance.backend_handle:
                os_instances_by_handle[instance.backend_handle] = instance

        os_ports = list(conn.network.ports())
        for os_port in os_ports:
            if os_port.id in ports_by_neutron_port:
                # we already have it
                continue
            if os_port.device_id not in os_instances_by_handle:
                # it's not one of ours
                log.info("No instance for port", os_port=os_port)
                continue
            if os_port.network_id not in networks_by_id:
                # there's no network for it
                log.info("No network for port", os_port=os_port)
                continue
            if not os_port.fixed_ips:
                # there's no ip address
                log.info("No ip for port", os_port=os_port)
                continue
            network = networks_by_id[os_port.network_id]
            instance = os_instances_by_handle[os_port.device_id]
            ip = os_port.fixed_ips[0]["ip_address"]
            mac = os_port.mac_address
            port = Port(network=network,
                        instance=None, # TODO(smbaker): link to openstack instance
                        ip=ip,
                        mac=mac,
                        port_id=os_port.id,
                        service_instance=instance)
            port.save()
            log.info("Created port", port=port, os_port=os_port)
